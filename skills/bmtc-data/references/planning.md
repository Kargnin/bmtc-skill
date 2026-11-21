# Composing answers and temporary views

## General questions this supports

| Question | Composition |
|---|---|
| What stops are nearby? | `stops --lat ... --lon ...`, then resolve side/direction. Distances are geometric, not walks. |
| Which routes serve a stop? | `routes --stop-id ...`, then `route` for each relevant pattern. |
| Does this route go to my destination? | Match boarding/alighting stop IDs in increasing sequence on the same pattern. |
| What is scheduled at 07:00 tomorrow? | Date, active calendar and `arrivals --at ...`; keep it labeled scheduled. |
| What buses are approaching now? | `arrivals`, filter desired route/headsign and usable fresh predictions. |
| Where is this actual bus? | `vehicle --vehicle-id ...`, observed GPS time and a Reclaim map link. |
| Is this bus delayed? | Compare published prediction with its matched schedule; state matching and schedule uncertainty. |
| Can I arrive by a deadline? | Build candidate journeys, include access/egress, transfer and risk buffers, and recheck relevant buses near departure. |

For a first usable version, route and live data can be queried directly from this skill. An MCP service is optional, useful for clients without shell/network access or for central caching. Do not install it automatically. A future read-only wrapper could expose:

```text
get_data_status() -> feed health, transport, provenance, age distributions
find_stops(query?, lat?, lon?, radius_m?, limit?) -> directional stop candidates
find_routes(query?, stop_id?, limit?) -> route IDs and names
get_route(route_id, pattern_id?) -> headsigns, ordered stops, service days
get_trip(trip_id, service_date) -> dated schedule, stop sequence, static version
get_arrivals(stop_id, route_id?, at?, window_minutes?) -> separate scheduled/predicted
get_vehicle(vehicle_id) -> observed position/time, inferred trip, freshness
plan_journey(origin, destination, departure_at? XOR arrive_by?, max_transfers?, access_constraints?)
evaluate_rider_alert(vehicle_id, trip_id, service_date, boarding_stop_id, walk_seconds, lead_seconds)
```

The last two need routing/verified access times beyond the helper. Return `unsupported` or partial evidence when inputs/data are insufficient. `evaluate_rider_alert` evaluates one read; it does not create a subscription. Keep all tools read-only. Use standard MCP SDKs/version negotiation for a real wrapper; no MCP server is included in this package.

For network planning, a local GTFS routing engine (e.g. a properly configured OpenTripPlanner instance using permitted OSM data) could handle transfers and access/egress; it would still inherit timetable inaccuracies. A licensed routing API is another option if separately authorized. Never equate app UI visibility with permission to reuse its data. A product's documented commercial API and its billing/terms are separate from its consumer map.

## Airport planning example

For a request to reach Bengaluru airport by a particular time, first resolve the travel date, terminal, starting point and required arrival buffer. Read the current official BMTC airport chart and match candidate routes and boarding directions. Origin departure times cannot be treated as intermediate-stop boarding times.

Check a fresh actual vehicle and its predicted boarding and airport stops near departure time. Keep source timestamps, uncertainty, and terminal/access allowances visible. If no bus can be supported with enough margin, explain the evidence gap and offer official enquiry or an independently checked alternative. Never invent a bus registration, date, terminal, walking time or guaranteed airport arrival. No booking or call is part of this read-only skill.

## Ordinary city demonstration

For “Can I take 500-D from Mahadevapura towards Hebbala now?”:

1. Search the stop and route; in the inspected feed, 500-D is `BMTC:547f8d325735`.
2. The Hebbala-bound pattern uses `iosIIbDF`; the Central Silk Board-bound pattern uses the opposite `o1bD4vQy`. Check the actual ordered pattern, including short-turn variants.
3. Request arrivals for the selected stop and route. Describe an actual registration only when observed; show prediction age and GPS age separately.
4. If all relevant observations are stale, report the route's scheduled possibilities and inability to confirm an approaching bus. Do not call the route unavailable.

## What this cannot reliably answer alone

- Guaranteed boarding, guaranteed airport arrival, exact punctuality probability, or all untracked/cancelled trips.
- Passenger load, free seats, safety of a stop/crossing at night, driver/contact identity, or working wheelchair ramp status.
- Road closures/disruptions without a verified alert source; absence of GTFS alerts is not proof of normal service.
- Exact current fares/payment eligibility from a stale fare table; check current official policy for fare-sensitive advice.
- True door-to-door/optimal transfer planning without a routing engine and verified access/egress assumptions.
- Historical vehicle tracking from the current full snapshot alone, or continuous notifications from a one-shot skill call.

## UI and client compatibility

Use temporary HTML/artifacts available in the invoking client, or simply link the existing map. No reusable UI scaffold is needed initially. A UI is a presentation of the same evidence, not another source. For a bus use `https://maps.reclaim.city/bmtc/?bus=<encoded registration>`; for a route use `?route=<encoded short route name>`. Do not put raw GTFS stop IDs into the map's `?stop=` parameter; the map uses its own aggregate key.

Codex/local agents with shell and outbound HTTPS can read the skill and run this helper. Skills and code must be placed in a location the host can discover; a package install does not itself authorize unrelated configuration changes. Other local agents can consume the same instructions/CLI; some require converting SKILL.md to their own instruction format. Text/JSON tools work independently of whether a host can show HTML.

Cloud agents can use the skill independently of a personal Mac when the files are installed in their own execution environment and that environment provides Python/curl and permitted outbound HTTPS. Installing the skill on a laptop does not install it in a cloud agent or an ordinary mobile chat. If a host cannot execute the helper, report that limitation. An authorized remote MCP integration is an optional alternative for such clients; it is not required for a cloud runtime that can run the helper itself. No hosted service, account, tunnel or persistent connection is included.
