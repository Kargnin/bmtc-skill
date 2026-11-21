#!/usr/bin/env python3
"""On-demand, keyless reads of Reclaim's documented BMTC GTFS feeds.

No server, account, tracker, credential, or background job. Python 3.10+ and curl.
The small shared cache lives under the OS temporary directory by default.
"""
import argparse
import csv
import datetime as dt
import fcntl
import hashlib
import io
import json
import math
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.parse
import zipfile
from zoneinfo import ZoneInfo

IST = ZoneInfo('Asia/Kolkata')
BASE = 'https://maps.reclaim.city/bmtc/rt/'
URLS = {'status': BASE + 'status.json',
        'vehicles': BASE + 'vehicle_positions.json',
        'updates': BASE + 'trip_updates.json',
        'catalog': 'https://maps.reclaim.city/gtfs/feeds.json'}
STATIC = 'https://raw.githubusercontent.com/reclaimchennai/India_GTFS/main/karnataka/bengaluru/bus.zip'
ATTRIBUTION = 'BMTC tracking via reclaim.city (unofficial); static BMTC via Vonter/bmtc-gtfs and India_GTFS (ODbL).'


def iso(t):
    return dt.datetime.fromtimestamp(float(t), IST).isoformat()


def epoch(value):
    t = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if t.tzinfo is None:
        raise ValueError('Provide an ISO time with an explicit UTC offset, normally +05:30.')
    return t.timestamp()


def freshness(timestamp, now=None):
    now = time.time() if now is None else now
    if timestamp is None:
        return {'state': 'unknown', 'age_seconds': None, 'observed_at': None}
    age = now - float(timestamp)
    state = 'clock_skew' if age < -30 else 'fresh' if age <= 180 else 'aging' if age <= 300 else 'stale'
    return {'state': state, 'age_seconds': round(age), 'observed_at': iso(timestamp)}


class FeedClient:
    def __init__(self, cache, snapshot=None):
        self.cache = Path(cache)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.snapshot = Path(snapshot) if snapshot else None

    def get(self, kind):
        # Coalesce independent agent processes sharing this cache on macOS/Linux.
        with (self.cache / (kind + '.lock')).open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            return self._get(kind)

    def _get(self, kind):
        if self.snapshot:
            names = {'vehicles': 'vehicle_positions.json', 'updates': 'trip_updates.json',
                     'status': 'status.json', 'catalog': 'feeds.json'}
            data = json.loads((self.snapshot / names[kind]).read_text())
            return data, {'source_url': URLS[kind], 'mode': 'historical_snapshot',
                          'retrieved_at': None, 'transport_ok': False,
                          'warning': 'Offline research snapshot; never describe as current live data.'}
        dest = self.cache / (kind + '.json')
        meta_path = self.cache / (kind + '.meta.json')
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        now = time.time()
        age = now - meta.get('fetched_at', 0)
        ttl = max(3600 if kind == 'catalog' else 30, meta.get('source_max_age', 0))
        if dest.exists() and 0 <= age < ttl:
            return json.loads(dest.read_text()), {**meta, 'cache_age_seconds': round(age)}
        if now < meta.get('retry_after', 0) or meta.get('access_blocked'):
            raise RuntimeError('Source blocked or in backoff. Do not retry or change identity; inspect cached metadata and source terms.')
        with tempfile.TemporaryDirectory(dir=self.cache) as td:
            body, headers = Path(td)/'body', Path(td)/'headers'
            command = ['curl', '--silent', '--show-error', '--location', '--max-redirs', '2',
                       '--proto', '=https', '--proto-redir', '=https', '--max-time', '30',
                       '--max-filesize', '20000000', '--dump-header', str(headers),
                       '--output', str(body), '--write-out', '%{http_code}']
            if meta.get('etag') and dest.exists():
                command += ['--header', 'If-None-Match: ' + meta['etag']]
            result = subprocess.run(command + [URLS[kind]], capture_output=True, text=True)
            code = int(result.stdout or 0)
            hdr = {}
            if headers.exists():
                for line in headers.read_text().splitlines():
                    if line.lower().startswith('http/'):
                        hdr = {}
                    elif ':' in line:
                        k, v = line.split(':', 1); hdr[k.lower()] = v.strip()
            if result.returncode or code not in (200, 304):
                retry = now + 60
                if code == 429:
                    raw = hdr.get('retry-after', '60')
                    if raw.isdigit(): retry = now + max(30, int(raw))
                    else:
                        from email.utils import parsedate_to_datetime
                        try: retry = max(now + 30, parsedate_to_datetime(raw).timestamp())
                        except (ValueError, TypeError): pass
                failed = {**meta, 'source_url': URLS[kind], 'transport_ok': False,
                          'http_status': code, 'error_at': iso(now), 'retry_after': retry,
                          'access_blocked': code in (401, 403)}
                meta_path.write_text(json.dumps(failed))
                raise RuntimeError(f'Feed unavailable (HTTP {code}, curl {result.returncode}); no automatic retry, old data has not been relabeled as fresh.')
            if code == 200:
                data = json.loads(body.read_text())
                body.replace(dest)
            else:
                data = json.loads(dest.read_text())
            meta = {'source_url': URLS[kind], 'mode': 'live_read', 'fetched_at': now,
                    'retrieved_at': iso(now), 'transport_ok': True, 'http_status': code,
                    'etag': hdr.get('etag', meta.get('etag')), 'cache_age_seconds': 0}
            # Respect a longer cache lifetime supplied by the source on future revisions.
            import re
            m = re.search(r'max-age=(\d+)', hdr.get('cache-control', ''))
            if m: meta['source_max_age'] = int(m.group(1))
            meta_path.write_text(json.dumps(meta))
            return data, meta


def gtfs_seconds(value):
    h, m, s = map(int, value.split(':'))
    return 3600*h + 60*m + s


def build_index(archive, db_path):
    """Index an explicitly supplied public GTFS zip; never extract archive paths."""
    temporary = Path(str(db_path) + '.building')
    temporary.unlink(missing_ok=True)
    conn = sqlite3.connect(temporary)
    with zipfile.ZipFile(archive) as z:
        for name in ['stops', 'routes', 'trips', 'stop_times', 'calendar', 'calendar_dates', 'feed_info', 'agency']:
            if name+'.txt' not in z.namelist(): continue
            with z.open(name+'.txt') as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
                fields = reader.fieldnames
                if not fields or any(not x.replace('_', '').isalnum() for x in fields):
                    raise ValueError('Unexpected GTFS column name')
                conn.execute(f'CREATE TABLE "{name}" (' + ','.join('"'+f+'" TEXT' for f in fields) + ')')
                sql = f'INSERT INTO "{name}" VALUES (' + ','.join('?' for _ in fields) + ')'
                batch = []
                for row in reader:
                    batch.append(tuple(row.get(f, '') for f in fields))
                    if len(batch) == 10000:
                        conn.executemany(sql, batch); batch.clear()
                if batch: conn.executemany(sql, batch)
        for table, columns in [('stops','stop_id'),('routes','route_id'),('trips','trip_id'),
                               ('trips','route_id'),('stop_times','trip_id'),('stop_times','stop_id')]:
            conn.execute(f'CREATE INDEX "idx_{table}_{columns}" ON "{table}" ("{columns}")')
        conn.execute('CREATE TABLE provenance (sha256 TEXT, indexed_at TEXT)')
        conn.execute('INSERT INTO provenance VALUES (?,?)', (hashlib.sha256(Path(archive).read_bytes()).hexdigest(), iso(time.time())))
        conn.commit()
        counts = {n:conn.execute(f'SELECT COUNT(*) FROM "{n}"').fetchone()[0] for n in ['stops','routes','trips','stop_times']}
    conn.close(); temporary.replace(db_path)
    return {'indexed': counts, 'db': str(db_path), 'licence': 'ODbL', 'attribution': ATTRIBUTION}


class Transit:
    def __init__(self, client, db_path):
        self.client, self.db_path = client, Path(db_path)
        self.db = None

    def rows(self, sql, args=()):
        if self.db is None:
            if not self.db_path.exists(): raise ValueError('Static index missing: run index --gtfs-zip PATH or index --download first.')
            self.db = sqlite3.connect(self.db_path.as_uri()+'?mode=ro', uri=True)
            self.db.row_factory = sqlite3.Row
        return [dict(r) for r in self.db.execute(sql, args)]

    def status(self):
        data, transport = self.client.get('status')
        return {'feed': data, 'feed_freshness': freshness(data.get('feed_time')),
                'transport': transport, 'note': 'Feed time is newest GPS in feed. Check every selected vehicle separately.'}

    def stops(self, query='', lat=None, lon=None, limit=20):
        candidates = self.rows('SELECT * FROM stops WHERE lower(stop_name) LIKE ? LIMIT 11000', ('%'+query.lower()+'%',))
        if (lat is None) != (lon is None): raise ValueError('Supply both latitude and longitude.')
        if lat is not None:
            if not (-90<=lat<=90 and -180<=lon<=180): raise ValueError('Invalid coordinate.')
            for r in candidates:
                a,b,c,d=map(math.radians,[lat,lon,float(r['stop_lat']),float(r['stop_lon'])])
                r['distance_metres']=round(6371000*2*math.asin(min(1,math.sqrt(math.sin((c-a)/2)**2+math.cos(a)*math.cos(c)*math.sin((d-b)/2)**2))))
            candidates.sort(key=lambda x:x['distance_metres'])
        return {'stops': candidates[:limit], 'note':'Distance is straight-line; no pedestrian route or safe crossing is verified.'}

    def routes(self, query='', stop_id=None, limit=30):
        sql = 'SELECT DISTINCT r.* FROM routes r'
        args=[]
        if stop_id:
            sql += ' JOIN trips t ON t.route_id=r.route_id JOIN stop_times s ON s.trip_id=t.trip_id'
        sql += ' WHERE (lower(r.route_short_name) LIKE ? OR lower(r.route_long_name) LIKE ?)'
        args += ['%'+query.lower()+'%']*2
        if stop_id: sql+=' AND s.stop_id=?'; args.append(stop_id)
        sql+=' LIMIT ?'; args.append(limit)
        return {'routes':self.rows(sql,args)}

    def route(self, route_id):
        route=self.rows('SELECT * FROM routes WHERE route_id=?',(route_id,))
        if not route: raise ValueError('Unknown route_id; discover it with routes.')
        patterns=self.rows('SELECT direction_id,shape_id,trip_headsign,MIN(trip_id) AS example_trip_id,COUNT(*) AS trips FROM trips WHERE route_id=? GROUP BY direction_id,shape_id,trip_headsign',(route_id,))
        for p in patterns:
            p['stops']=self.rows('SELECT s.stop_sequence,s.stop_id,b.stop_name,b.stop_lat,b.stop_lon FROM stop_times s JOIN stops b ON b.stop_id=s.stop_id WHERE trip_id=? ORDER BY CAST(stop_sequence AS INTEGER)',(p['example_trip_id'],))
        return {'route':route[0], 'patterns':patterns, 'note':'These are representative trips grouped by shape/headsign. Check the exact selected trip before boarding. direction_id has meaning only within this route; use headsign and ordered stop IDs.'}

    def trip(self, trip_id):
        trips=self.rows('SELECT t.*,r.route_short_name,r.route_long_name FROM trips t JOIN routes r ON r.route_id=t.route_id WHERE trip_id=?',(trip_id,))
        if not trips: raise ValueError('Unknown trip_id; static feed may have changed.')
        return {'trip':trips[0], 'stops':self.rows('SELECT s.*,b.stop_name,b.stop_lat,b.stop_lon FROM stop_times s JOIN stops b ON b.stop_id=s.stop_id WHERE trip_id=? ORDER BY CAST(stop_sequence AS INTEGER)',(trip_id,)),
                'note':'Scheduled GTFS service-day times, possibly above 24:00. They are not live ETAs.'}

    def vehicle(self, vehicle_id):
        data,meta=self.client.get('vehicles')
        entries=[e['vehicle'] for e in data.get('entity',[]) if 'vehicle'in e and e['vehicle'].get('vehicle',{}).get('id')==vehicle_id]
        if not entries: return {'found':False,'vehicle_id':vehicle_id,'transport':meta,'note':'Absent from feed does not prove bus cancelled or not running.'}
        v=entries[0]; trip=v.get('trip',{}); matched=None
        if trip.get('tripId') and self.db_path.exists():
            matched=self.rows('SELECT t.*,r.route_short_name FROM trips t JOIN routes r ON r.route_id=t.route_id WHERE trip_id=?',(trip['tripId'],))
        return {'found':True,'vehicle':v,'gps_freshness':freshness(v.get('timestamp')),
                'static_trip':matched[0] if matched else None, 'transport':meta,
                'trip_match_method':'Reclaim nearest scheduled trip within 30 minutes; inferred, not a verified operator block assignment.',
                'map_url':'https://maps.reclaim.city/bmtc/?bus='+urllib.parse.quote(vehicle_id)}

    def scheduled(self, stop_id, start, end, route_id=None):
        sql='SELECT s.*,t.route_id,t.service_id,t.direction_id,t.trip_headsign,r.route_short_name FROM stop_times s JOIN trips t ON t.trip_id=s.trip_id JOIN routes r ON r.route_id=t.route_id WHERE s.stop_id=?'
        args=[stop_id]
        if route_id: sql+=' AND t.route_id=?'; args.append(route_id)
        rows=self.rows(sql,args)
        calendars={r['service_id']:r for r in self.rows('SELECT * FROM calendar')}
        has_ex=bool(self.rows("SELECT name FROM sqlite_master WHERE type='table' AND name='calendar_dates'"))
        exceptions={(r['service_id'],r['date']):r['exception_type'] for r in self.rows('SELECT * FROM calendar_dates')} if has_ex else {}
        maximum=max((gtfs_seconds(r['arrival_time']) for r in rows if r['arrival_time']),default=0)
        day=dt.datetime.fromtimestamp(start,IST).date()-dt.timedelta(days=maximum//86400)
        last=dt.datetime.fromtimestamp(end,IST).date(); result=[]
        while day<=last:
            ds=day.strftime('%Y%m%d'); weekday=day.strftime('%A').lower(); midnight=dt.datetime.combine(day,dt.time(),IST).timestamp()
            for r in rows:
                c=calendars.get(r['service_id'],{}); ex=exceptions.get((r['service_id'],ds))
                active=ex=='1' or (ex!='2' and c.get(weekday)=='1' and c.get('start_date','99999999')<=ds<=c.get('end_date','00000000'))
                if not active or not r['arrival_time']: continue
                when=midnight+gtfs_seconds(r['arrival_time'])
                if start<=when<=end:
                    result.append({**r,'service_date':ds,'scheduled_epoch':int(when),'scheduled_at':iso(when),'kind':'scheduled'})
            day+=dt.timedelta(days=1)
        return sorted(result,key=lambda r:r['scheduled_epoch'])

    def arrivals(self, stop_id, at=None, minutes=60, route_id=None):
        now=time.time(); start=epoch(at) if at else now; end=start+minutes*60
        schedule=self.scheduled(stop_id,start,end,route_id)
        stop=self.rows('SELECT * FROM stops WHERE stop_id=?',(stop_id,))
        if not stop: raise ValueError('Unknown stop_id.')
        result={'stop':stop[0], 'scheduled':schedule, 'predicted':[], 'timezone':'Asia/Kolkata',
                'note':'Predictions and scheduled arrivals are separate. No live observation does not mean no bus.'}
        # A historical/future request must not receive today's predictions.
        if abs(start-now)>300:
            result['live_note']='Requested time differs from now by over five minutes; schedule only.'
            return result
        try:
            vp,vmeta=self.client.get('vehicles'); tu,tmeta=self.client.get('updates')
        except RuntimeError as e:
            result['live_error']=str(e); return result
        result['transport']={'vehicles':vmeta,'updates':tmeta}
        result['feed_timestamp_skew_seconds']=abs(int(vp['header']['timestamp'])-int(tu['header']['timestamp']))
        observation_now=time.time()
        vehicles={e['vehicle'].get('vehicle',{}).get('id'):e['vehicle'] for e in vp.get('entity',[]) if 'vehicle'in e}
        for entry in tu.get('entity',[]):
            u=entry.get('tripUpdate',{}); trip=u.get('trip',{})
            if route_id and trip.get('routeId')!=route_id: continue
            for s in u.get('stopTimeUpdate',[]):
                arrival=s.get('arrival',{}); when=arrival.get('time')
                if s.get('stopId')!=stop_id or when is None or not start<=int(when)<=end: continue
                vid=u.get('vehicle',{}).get('id'); v=vehicles.get(vid,{})
                gps, prediction=freshness(v.get('timestamp'),observation_now),freshness(u.get('timestamp'),observation_now)
                matched=self.rows('SELECT t.*,r.route_short_name FROM trips t JOIN routes r ON r.route_id=t.route_id WHERE trip_id=?',(trip.get('tripId'),))
                static_stop=self.rows('SELECT stop_id FROM stop_times WHERE trip_id=? AND stop_id=? AND CAST(stop_sequence AS INTEGER)=?',(trip.get('tripId'),stop_id,s.get('stopSequence',-1)))
                same_trip=bool(trip.get('startDate')) and v.get('trip',{}).get('tripId')==trip.get('tripId') and v.get('trip',{}).get('startDate')==trip.get('startDate')
                valid_service=False
                try:
                    day=dt.datetime.strptime(trip.get('startDate',''),'%Y%m%d').date()
                    calendars=self.rows('SELECT * FROM calendar WHERE service_id=?',(matched[0]['service_id'],)) if matched else []
                    c=calendars[0] if calendars else {}
                    ds=day.strftime('%Y%m%d')
                    valid_service=c.get(day.strftime('%A').lower())=='1' and c.get('start_date','99999999')<=ds<=c.get('end_date','00000000')
                    if self.rows("SELECT name FROM sqlite_master WHERE type='table' AND name='calendar_dates'") and matched:
                        ex=self.rows('SELECT exception_type FROM calendar_dates WHERE service_id=? AND date=?',(matched[0]['service_id'],ds))
                        if ex: valid_service=ex[-1]['exception_type']=='1'
                except ValueError:
                    pass
                same_route=bool(matched) and matched[0]['route_id']==trip.get('routeId')
                usable=(int(when)>observation_now and gps['state']=='fresh' and prediction['state']=='fresh' and same_route and valid_service and bool(static_stop) and same_trip and vmeta['transport_ok'] and tmeta['transport_ok'] and result['feed_timestamp_skew_seconds']<=60 and s.get('scheduleRelationship') not in ('SKIPPED','NO_DATA') and trip.get('scheduleRelationship')!='CANCELED')
                result['predicted'].append({'vehicle_id':vid,'trip':trip,'static_trip':matched[0] if matched else None,
                    'stop_sequence':s.get('stopSequence'),'predicted_at':iso(when),'prediction_epoch':int(when),
                    'delay_seconds':arrival.get('delay'),'gps_freshness':gps,'prediction_freshness':prediction,
                    'usable_prediction':usable,'kind':'predicted','position':v.get('position'),
                    'caution':'Trip matching is heuristic; arrival is an estimate, not a guarantee.',
                    'map_url':'https://maps.reclaim.city/bmtc/?bus='+urllib.parse.quote(vid or '')})
        result['predicted'].sort(key=lambda r:r['prediction_epoch'])
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir',default=str(Path(tempfile.gettempdir())/f'bmtc-data-{os.getuid()}'))
    parser.add_argument('--db',help='Optional static index path; default CACHE/static.sqlite3')
    parser.add_argument('--snapshot-dir',help='Offline test/research feeds; always labeled historical_snapshot')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('status')
    p=sub.add_parser('fetch');p.add_argument('kind',choices=URLS);p.add_argument('--out',required=True)
    p=sub.add_parser('index');p.add_argument('--gtfs-zip');p.add_argument('--download',action='store_true')
    p=sub.add_parser('stops');p.add_argument('--query',default='');p.add_argument('--lat',type=float);p.add_argument('--lon',type=float);p.add_argument('--limit',type=int,default=20)
    p=sub.add_parser('routes');p.add_argument('--query',default='');p.add_argument('--stop-id');p.add_argument('--limit',type=int,default=30)
    p=sub.add_parser('route');p.add_argument('--route-id',required=True)
    p=sub.add_parser('trip');p.add_argument('--trip-id',required=True)
    p=sub.add_parser('vehicle');p.add_argument('--vehicle-id',required=True)
    p=sub.add_parser('arrivals');p.add_argument('--stop-id',required=True);p.add_argument('--route-id');p.add_argument('--at');p.add_argument('--minutes',type=int,default=60)
    a=parser.parse_args(); client=FeedClient(a.cache_dir,a.snapshot_dir)
    db=Path(a.db).resolve() if a.db else (client.cache/'static.sqlite3').resolve()
    if a.command=='index':
        if bool(a.gtfs_zip)==bool(a.download): raise ValueError('Choose one of --gtfs-zip or --download.')
        archive=Path(a.gtfs_zip) if a.gtfs_zip else client.cache/'bengaluru.zip'
        if a.download:
            catalog,_=client.get('catalog'); feed=next(f for f in catalog['feeds'] if f['id']=='bengaluru')
            if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest()!=feed['sha256']:
                partial=archive.with_suffix('.partial')
                p=subprocess.run(['curl','--fail','--silent','--show-error','--location','--proto','=https','--proto-redir','=https','--max-time','90','--output',str(partial),STATIC])
                if p.returncode: partial.unlink(missing_ok=True); raise RuntimeError('Static download failed; no retry performed.')
                if hashlib.sha256(partial.read_bytes()).hexdigest()!=feed['sha256']:
                    partial.unlink(missing_ok=True);raise ValueError('Catalog checksum mismatch; stop and inspect the version change.')
                partial.replace(archive)
        result=build_index(archive,db)
    elif a.command=='fetch':
        data,meta=client.get(a.kind);Path(a.out).write_text(json.dumps(data));result={'saved':str(Path(a.out).resolve()),'transport':meta}
    else:
        transit=Transit(client,db)
        if a.command=='status':result=transit.status()
        elif a.command=='stops':result=transit.stops(a.query,a.lat,a.lon,min(max(a.limit,1),100))
        elif a.command=='routes':result=transit.routes(a.query,a.stop_id,min(max(a.limit,1),100))
        elif a.command=='route':result=transit.route(a.route_id)
        elif a.command=='trip':result=transit.trip(a.trip_id)
        elif a.command=='vehicle':result=transit.vehicle(a.vehicle_id)
        elif a.command=='arrivals':
            if not 1<=a.minutes<=1440:raise ValueError('minutes must be 1..1440.')
            result=transit.arrivals(a.stop_id,a.at,a.minutes,a.route_id)
    envelope={'queried_at':iso(time.time()),'attribution':ATTRIBUTION,'data':result}
    if a.command not in ('fetch','index','status') and db.exists():
        provenance=Transit(client,db)
        envelope['static_provenance']={'feed_info':provenance.rows('SELECT * FROM feed_info'),
                                       'index':provenance.rows('SELECT * FROM provenance')}
    print(json.dumps(envelope,ensure_ascii=False,indent=2))


if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError,OSError,KeyError,sqlite3.Error,zipfile.BadZipFile) as e:
        print(json.dumps({'error':str(e),'action':'Stop or use clearly labeled schedules; never infer a live bus from this failure.'}),file=sys.stderr)
        sys.exit(1)
