---
name: bmtc-data
description: Answer Bengaluru BMTC questions using documented public schedules, live bus positions and predicted arrivals. Find stops and routes, resolve direction, follow a vehicle, compare travel options, and generate a temporary tracking view when useful. Use for BMTC across the network, including ordinary, Vajra, feeder and airport services.
---

# BMTC data

Use Reclaim's documented public GTFS interfaces, with BMTC as the underlying operator. They are unofficial community feeds. No API key or account is required for these reads. The official app's backend is a separate first-party interface; do not copy its credentials, call undocumented backend methods, or treat community reverse-engineering as operator permission.

Read [references/api.md](references/api.md) for endpoints, identifiers, limits, source permissions and command details. Use `scripts/bmtc_query.py` for ordinary on-demand queries; Python 3.10+, curl, SQLite support and OS timezone data suffice on macOS/Linux or a cloud Linux runtime with permitted outbound HTTPS. Installation alone does not grant execution/network access. If the current host cannot run the helper, report that limitation instead of claiming a live lookup succeeded. Run it from this package's actual directory, never assume a fixed installation path. The helper creates no service and runs no background tracker.

## Answering a question

- Resolve the stop and route rather than guessing IDs from names. Search spelling variants (`Mahadevpura` / `Mahadevapura`, Majestic / Kempegowda Bus Station). Identically named stops can be on opposite sides of a road. Use coordinates, headsign and ordered stop sequence; `direction_id=0` has no universal compass meaning.
- Use the static index for route topology, stop order and schedules. Use VehiclePositions for the observed location of a particular bus, and TripUpdates for predicted arrivals. Keep scheduled and predicted times distinct, even if they coincide. Never report an animated/interpolated map marker as a new GPS observation.
- Check transport status, feed age, **selected bus GPS age**, TripUpdate age, static trip/stop compatibility and matching service date. The feed header represents the newest bus, not every bus. Reclaim matches many buses to a nearby scheduled trip heuristically; a trip ID is not proof of an operator-assigned duty. A vehicle may have a position but no matched trip or ETA.
- Use Asia/Kolkata (IST, UTC+05:30). Require a date for date-specific travel. Interpret GTFS times past 24:00 against their service day, including the previous calendar day. Preserve calendar exceptions and feed validity. Do not invent a flight date, terminal, starting address or permission to read device location.
- For `fresh` observations (age <=180 s), provide the time and usual prediction uncertainty. Mark 180–300 s `aging`; require another current check before time-critical advice. Above 300 s, missing timestamps or >30 s future clock skew: no actionable live ETA or “catch this bus” recommendation. These are conservative skill choices, not provider guarantees. An old HTTP-success response is still old data.
- Empty/unmatched feeds mean “not observed,” not “no service” or “cancelled.” Report cancellations, occupancy, low-floor/accessibility and fares only when a verified source explicitly supplies them. The observed live feed does not supply crowding or accessible-vehicle status.

## Planning and tracking

Compose direct journeys by checking that boarding precedes alighting on the **same pattern**, the service runs on the requested date, and the stop-side/destination is right. Join an approaching vehicle only when its current trip and predicted stops support that journey. Re-fetch at decision time; do not silently substitute another bus after the selected vehicle changes trip or disappears.

For transfers or door-to-door/arrive-by planning, read [references/planning.md](references/planning.md). The helper supplies ingredients, not a full walking/transit routing engine. State missing walking paths, crossing safety, transfer allowance, arrival buffer or terminal access. Do not manufacture a fastest itinerary, walk time, overnight service guarantee or on-time probability from a route line.

If live data is stale or no option is supported, say so, show clearly labeled scheduled possibilities when useful, and give a practical fallback (official BMTC enquiry / existing map / another transport mode). For an airport deadline, retain enough time for an independently checked taxi alternative and terminal transfer; no exact safe cutoff can be calculated without date, terminal, pickup and current journey information.

On “track this bus,” query the actual `vehicle_id` and keep the trip ID plus service date with it. Offer the existing map deep link returned by the helper. Tracking requires repeated observations while the user is engaged, not a promise that a one-shot query will keep updating.

## Temporary UI, when useful

Keep no permanent website or base UI scaffold. Use the host's available UI/artifact capability to create a small temporary view suited to the question. A text answer and existing map link are enough when a new view adds no value.

Every bus view must show: vehicle and route; destination/direction; observed coordinates or position; GPS timestamp and age; ETA source and timestamp if available; scheduled times separately; stale/offline/unmatched state; source attribution and the existing map link. Distinguish a snapshot from auto-refresh. Mock data must be unmistakably marked.

For an explicitly requested active tracker, refresh through a shared adapter/cache every 30 s, only while the view is visible and needed. Respect any longer cache headers, 429 backoff and 401/403 stops; do not use cache-busting or direct per-agent/per-tab loops. A standalone browser may use the documented CORS feed if appropriate, but do not duplicate polling when the agent adapter already fetches it. There is no push endpoint documented. A tool call in chat does not install a lasting watch.

Use raw last-observed GPS by default. Any interpolation must be labeled estimated and stop when stale. When a vehicle changes trips/direction, disappears, or loses fresh GPS/ETA, suspend recommendations and ask the adapter to re-evaluate. Approaching/leave-now alerts require a fresh matched bus, the right stop ahead, and enough verified walking/boarding time; they are estimates. Background notifications or recurring tasks require a supported scheduler and a specific user request; the skill itself starts none.

## Maintenance based on use

When real usage exposes an API change or repeatable reasoning gap, verify the public evidence, update the relevant instructions/helper, and run the focused checks. Do not add a framework or accumulate speculative UI components. Temporary views stay disposable. Propose a reusable component only after repeated use demonstrates its benefit. Preserve source permissions and data-age labeling in revisions. Treat an installed skill package as a released snapshot. Make maintainer changes in the source repository, run the focused checks, bump the release version, and publish a new release; do not silently edit the installed skill copy.
