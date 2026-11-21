# Public BMTC data access

Verified 21 November 2026 by ordinary public GETs, source inspection and publisher documentation. Recheck this document if the interface changes.

## Source chain and interfaces

BMTC operates the buses and the [official commuter app](https://nammabmtcapp.karnataka.gov.in/). Reclaim collects BMTC tracking and publishes its own [map](https://maps.reclaim.city/bmtc/) and [documented public feed](https://api.reclaim.city/docs/#buses). The map identifies `bengaluru_bus/server/bmtc_collector.py` as its collector. The collector implementation and its exact backend request sequence were not verified in a publicly accessible repository during this investigation.

The official commuter site's public `main.50ac63eab887427a0df7.js` identifies `https://bmtcmobileapi.karnataka.gov.in` and POST methods under `/WebAPI/`, including `SearchRoute_v2`, `SearchByRouteDetails_v4_web` and `VehicleTripDetails_v2_web`. These are first-party app implementation details, not a verified public developer contract. No backend POST or authenticated request was made. Community Swagger documents are unofficial.

The map itself fetches `data/*.json`/GeoJSON and `live/vehicles.json`, then `live/delta/<timestamp>.json`; it does not depend on the public GTFS endpoint in its inspected live rendering code. Its own frontend JSON is publicly observable but is an internal application format. Use the documented GTFS interface for agent integration.

## Documented endpoints

All are HTTPS GET. `bengaluru` and `bmtc` are documented aliases; this helper consistently uses `bmtc` for live reads.

| Data | URL |
|---|---|
| Feed catalog and provenance | `https://maps.reclaim.city/gtfs/feeds.json` |
| Static GTFS, preferred bulk download | `https://raw.githubusercontent.com/reclaimchennai/India_GTFS/main/karnataka/bengaluru/bus.zip` |
| Static mirror | `https://maps.reclaim.city/gtfs/bengaluru.zip` |
| GPS observations | `https://maps.reclaim.city/bmtc/rt/vehicle_positions.json` |
| Predicted stop arrivals | `https://maps.reclaim.city/bmtc/rt/trip_updates.json` |
| Publisher freshness/counts | `https://maps.reclaim.city/bmtc/rt/status.json` |

The two live JSON endpoints also have `.pb` Protocol Buffer versions, content type `application/x-protobuf`, GTFS-Realtime 2.0 full datasets. JSON follows protobuf JSON naming: `tripId`, `routeId`, `stopTimeUpdate`, `stopId`; int64 timestamps are strings. No arbitrary query/search filters are documented. Download once into a shared cache and filter locally. The formats are defined by [GTFS Schedule](https://gtfs.org/documentation/schedule/reference/) and [GTFS-Realtime](https://gtfs.org/documentation/realtime/reference/).

### Schema, synthetic example

The example below is invented to demonstrate the protobuf JSON mapping. It is not a captured vehicle observation or a travel recommendation.

```json
{"header":{"gtfsRealtimeVersion":"2.0","incrementality":"FULL_DATASET","timestamp":"1795241540"},"entity":[{"id":"MOCK-BUS","vehicle":{"trip":{"tripId":"MOCK-TRIP","startDate":"20261121","routeId":"MOCK-ROUTE"},"position":{"latitude":13.0,"longitude":77.6,"bearing":90},"timestamp":"1795241516","vehicle":{"id":"MOCK-BUS","label":"MOCK-BUS"}}}]}
```

A corresponding TripUpdate has `trip`, `vehicle`, its own `timestamp`, and `stopTimeUpdate[]` with `stopSequence`, `stopId`, `arrival.time` and `arrival.delay`. Delay is seconds against a matched timetable; it inherits that timetable's quality and matching uncertainty. GPS is an observation; arrival times are predictions. A past observation timestamp is never a future arrival time. No tokens, secrets or driver data are needed.

Static joins: `routes.route_id -> trips.route_id`; `trips.trip_id -> stop_times.trip_id`; `stop_times.stop_id -> stops.stop_id`; `trips.service_id -> calendar/calendar_dates`. Preserve feed version and ID namespace. Short route number is a display name, not a trip identity. Static direction IDs and stop codes are not interchangeable with upstream numeric API IDs or the map's aggregate stop keys.

## Freshness, limits and outages

Publisher guidance: source refresh is approximately three minutes per Bengaluru bus, with feeds regenerated about 15 s after source changes. That is a target, not a per-bus SLA. Header `timestamp` and status `feed_time` are newest GPS time; `written` is generation time. If upstream stops, the last good file stays available.

Observed responses had open read CORS (`Access-Control-Allow-Origin: *`) and `Cache-Control: public, max-age=10`. The documented GTFS fair-use interval is 15–30 s. Use **30 s shared caching**, honor longer headers and conditional responses, pause when idle, and never poll faster to try to force fresh GPS. There is no published numeric BMTC GTFS requests/minute quota or uptime SLA. The 120/min limits elsewhere on the docs page refer to geo/police endpoints, not BMTC. Sustained/bulk use should be agreed with Reclaim. On 429 honor Retry-After; on 401/403 stop without changing identity or borrowing credentials.

## Free access and reuse are different

Documented feed reads require no signup/key and list no per-call price. This permits ordinary access under the publisher's terms, not unlimited load or an operator-authorized commercial redistribution license.

The catalog lists the static feed as ODbL. Retain attribution, license notices and applicable share-alike/database-offer obligations for public derivative databases. [Vonter's source](https://github.com/Vonter/bmtc-gtfs) explicitly notes some individual content is BMTC copyright. The [ODbL text](https://opendatacommons.org/licenses/odbl/1-0/) separates database rights from other rights in individual contents. Reclaim's live documentation does not clearly specify a separate live redistribution/commercial license or show an explicit BMTC licensing agreement. Confirm those rights before publishing a feed mirror, selling/rehosting tracking, or running sustained production access. Do not infer a live-data license from CORS or from the static feed's ODbL label.

Attribution for ordinary answers/views: **BMTC tracking via reclaim.city (unofficial); schedules via Vonter/bmtc-gtfs / India_GTFS (ODbL)**, linked to those sources. OSM/map tile licensing is separate if you later add a map.

## Query helper

```bash
python3 scripts/bmtc_query.py status
python3 scripts/bmtc_query.py index --download
python3 scripts/bmtc_query.py stops --query 'Mahadevapura Ring Road'
python3 scripts/bmtc_query.py stops --lat 12.98868 --lon 77.68904 --limit 6
python3 scripts/bmtc_query.py routes --query '500-D'
python3 scripts/bmtc_query.py routes --stop-id iosIIbDF
python3 scripts/bmtc_query.py route --route-id BMTC:547f8d325735
python3 scripts/bmtc_query.py arrivals --stop-id iosIIbDF --minutes 45
python3 scripts/bmtc_query.py vehicle --vehicle-id DISCOVERED_VEHICLE_ID
```

IDs above were observed on the research date; search again rather than assuming they never change. `index --download` explicitly downloads the community static feed (about 60 MB at investigation time), validates it against the catalog SHA-256, and builds an SQLite index in the temporary cache. `index --gtfs-zip PATH` instead uses an already downloaded file. The feed includes millions of stop-time rows; indexing can take a few minutes. No network request is made by static lookups after indexing.

Use global options **before** the subcommand:

```bash
python3 scripts/bmtc_query.py --cache-dir /tmp/my-bmtc-cache status
python3 scripts/bmtc_query.py --db /tmp/my-bmtc-cache/static.sqlite3 trip --trip-id 'DISCOVERED_ID'
python3 scripts/bmtc_query.py arrivals --stop-id iosIIbDF --at '2026-11-22T01:00:00+05:30' --minutes 120
python3 scripts/bmtc_query.py fetch updates --out /tmp/bmtc-updates.json
```

`fetch` saves a large documented feed to disk instead of dumping it into model context. `status` and `vehicle` work without a static index, although route names require it. `arrivals` returns scheduled and predicted arrays separately; only predictions supported by fresh matched GPS, fresh TripUpdate, compatible static stop/sequence, consistent vehicle trip/date and <=60 s feed skew receive `usable_prediction=true`. That flag means the data passed conservative checks, not a guaranteed boarding recommendation. Run a new vehicle check before a critical decision.

`--snapshot-dir PATH` is for offline fixtures/research. It always reports `historical_snapshot`, with `transport_ok=false`, so it cannot turn saved old data into an actionable live prediction. Unknown fields may require helper updates. This version supports scheduled calendar exceptions and stop-time update skipped/no-data flags; it does not implement every possible GTFS-Realtime extension or a multi-modal router.

Cache defaults to the OS temp directory `/.../bmtc-data-<uid>` and can be removed after use. It contains public feed snapshots and a static index, no credentials or user journey history. Per-feed file locks coalesce agent processes sharing a cache on macOS/Linux. Helpers should share the same cache. No cron job, account change, global installation or remote service is created.
