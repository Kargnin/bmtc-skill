#!/usr/bin/env python3
"""Focused offline checks for travel decisions; all fixtures are synthetic."""
import copy
import datetime as dt
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import bmtc_query as b


class FakeFeeds:
    def __init__(self, now):
        trip={'tripId':'MOCK-T','routeId':'MOCK-R','startDate':'20261121'}
        self.vp={'header':{'timestamp':str(int(now))},'entity':[{'vehicle':{
            'vehicle':{'id':'MOCK-BUS'},'trip':copy.deepcopy(trip),
            'timestamp':str(int(now-20)),'position':{'latitude':13,'longitude':77.6}}}]}
        self.tu={'header':{'timestamp':str(int(now))},'entity':[{'tripUpdate':{
            'trip':copy.deepcopy(trip),'vehicle':{'id':'MOCK-BUS'},'timestamp':str(int(now-20)),
            'stopTimeUpdate':[{'stopId':'MOCK-S','stopSequence':1,'arrival':{'time':str(int(now+120))}}]}}]}
        self.live=True

    def get(self, kind):
        return (self.vp if kind=='vehicles' else self.tu), {'transport_ok':self.live,'mode':'mock'}


class Decisions(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Path(self.tmp.name)/'test.sqlite3'
        c=sqlite3.connect(self.db)
        c.executescript('''
          CREATE TABLE stops(stop_id,stop_name,stop_lat,stop_lon);
          INSERT INTO stops VALUES('MOCK-S','Synthetic stop',13,77.6);
          CREATE TABLE routes(route_id,route_short_name,route_long_name);
          INSERT INTO routes VALUES('MOCK-R','MOCK','Synthetic route');
          CREATE TABLE trips(trip_id,route_id,service_id,direction_id,trip_headsign);
          INSERT INTO trips VALUES('MOCK-T','MOCK-R','MOCK-SERVICE','0','Synthetic destination');
          CREATE TABLE stop_times(trip_id,stop_id,stop_sequence,arrival_time,departure_time);
          INSERT INTO stop_times VALUES('MOCK-T','MOCK-S','1','25:10:00','25:10:00');
          CREATE TABLE calendar(service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date);
          INSERT INTO calendar VALUES('MOCK-SERVICE','1','1','1','1','1','1','1','20260101','20261231');
          CREATE TABLE calendar_dates(service_id,date,exception_type);
        ''')
        c.commit();c.close()
        self.now=b.epoch('2026-11-21T11:00:00+05:30')
        self.feeds=FakeFeeds(self.now)
        self.transit=b.Transit(self.feeds,self.db)

    def tearDown(self):
        if self.transit.db:self.transit.db.close()
        self.tmp.cleanup()

    def arrivals(self):
        with patch.object(b.time,'time',return_value=self.now):
            return self.transit.arrivals('MOCK-S')['predicted']

    def test_fresh_data_can_support_prediction(self):
        self.assertTrue(self.arrivals()[0]['usable_prediction'])

    def test_fresh_feed_cannot_mask_old_vehicle(self):
        self.feeds.vp['entity'][0]['vehicle']['timestamp']=str(self.now-900)
        row=self.arrivals()[0]
        self.assertFalse(row['usable_prediction'])
        self.assertEqual(row['gps_freshness']['state'],'stale')

    def test_saved_snapshot_is_never_actionable(self):
        self.feeds.live=False
        self.assertFalse(self.arrivals()[0]['usable_prediction'])

    def test_vehicle_trip_change_cannot_be_silently_joined(self):
        self.feeds.vp['entity'][0]['vehicle']['trip']['tripId']='MOCK-OTHER'
        self.assertFalse(self.arrivals()[0]['usable_prediction'])

    def test_clock_skew_is_not_fresh(self):
        self.assertEqual(b.freshness(self.now+60,self.now)['state'],'clock_skew')

    def test_skipped_stop_does_not_support_boarding(self):
        self.feeds.tu['entity'][0]['tripUpdate']['stopTimeUpdate'][0]['scheduleRelationship']='SKIPPED'
        self.assertFalse(self.arrivals()[0]['usable_prediction'])

    def test_service_date_exception_removes_prediction(self):
        c=sqlite3.connect(self.db);c.execute("INSERT INTO calendar_dates VALUES('MOCK-SERVICE','20261121','2')");c.commit();c.close()
        self.assertFalse(self.arrivals()[0]['usable_prediction'])

    def test_previous_service_day_after_midnight(self):
        start=b.epoch('2026-11-22T01:00:00+05:30')
        rows=self.transit.scheduled('MOCK-S',start,start+1800)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['service_date'],'20261121')
        self.assertEqual(rows[0]['scheduled_at'],'2026-11-22T01:10:00+05:30')

    def test_schedule_exception_removes_overnight_service(self):
        c=sqlite3.connect(self.db);c.execute("INSERT INTO calendar_dates VALUES('MOCK-SERVICE','20261121','2')");c.commit();c.close()
        start=b.epoch('2026-11-22T01:00:00+05:30')
        self.assertEqual(self.transit.scheduled('MOCK-S',start,start+1800),[])

    def test_naive_dates_are_rejected(self):
        with self.assertRaises(ValueError):b.epoch('2026-11-22T01:00:00')

    def test_unknown_vehicle_is_not_a_cancellation(self):
        result=self.transit.vehicle('MOCK-MISSING')
        self.assertFalse(result['found'])
        self.assertIn('does not prove',result['note'])


class Caching(unittest.TestCase):
    def test_longer_cache_header_is_respected(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls=[]
            def curl(args,**kwargs):
                calls.append(args)
                Path(args[args.index('--output')+1]).write_text('{"network":"mock"}')
                Path(args[args.index('--dump-header')+1]).write_text('HTTP/2 200\nCache-Control: public, max-age=300\nETag: "mock"\n')
                return type('Result',(),{'returncode':0,'stdout':'200'})()
            client=b.FeedClient(tmp)
            with patch.object(b.subprocess,'run',side_effect=curl),patch.object(b.time,'time',return_value=1000):client.get('status')
            with patch.object(b.subprocess,'run',side_effect=curl),patch.object(b.time,'time',return_value=1100):client.get('status')
            self.assertEqual(len(calls),1)

    def test_rate_limit_does_not_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            def curl(args,**kwargs):
                Path(args[args.index('--output')+1]).write_text('{}')
                Path(args[args.index('--dump-header')+1]).write_text('HTTP/2 429\nRetry-After: 600\n')
                return type('Result',(),{'returncode':0,'stdout':'429'})()
            client=b.FeedClient(tmp)
            with patch.object(b.subprocess,'run',side_effect=curl) as run:
                with self.assertRaises(RuntimeError):client.get('status')
                with self.assertRaises(RuntimeError):client.get('status')
                self.assertEqual(run.call_count,1)


if __name__=='__main__':unittest.main(verbosity=2)
