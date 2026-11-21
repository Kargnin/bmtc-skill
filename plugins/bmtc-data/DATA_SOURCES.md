# Data sources and permissions

Verified against public documentation and ordinary public reads on 21 November 2026.

- Operator: [BMTC](https://mybmtc.karnataka.gov.in/english).
- Independent collector/publisher: [Reclaim](https://maps.reclaim.city/bmtc/), with [documented GTFS interfaces](https://api.reclaim.city/docs/#buses).
- Static feed: [India_GTFS Bengaluru](https://github.com/reclaimchennai/India_GTFS/tree/main/karnataka/bengaluru), based on [Vonter/bmtc-gtfs](https://github.com/Vonter/bmtc-gtfs) with Reclaim additions.
- Static database license: [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/), as listed by the publisher. Vonter notes that some individual contents are BMTC copyright. Preserve attribution, notices and applicable database obligations.
- Live read interface: public, keyless feeds described in the publisher documentation. No separate live redistribution/commercial license or BMTC data-sharing agreement was verified. Open access/CORS are not a blanket redistribution license.

No captured feed, transit database, map tiles, operator logo or personal itinerary is distributed with this plugin. JSON fixtures are synthetic. Runtime reads remain subject to upstream terms and availability. The plugin does not mirror/rehost feeds.

Use this attribution in answers/views: **BMTC tracking via reclaim.city (unofficial); schedules via Vonter/bmtc-gtfs / India_GTFS (ODbL)**, with the links above. Any optional map/tile provider has separate attribution and usage requirements.

The inspected feed's GPS and predicted arrival fields do not establish passenger occupancy, guaranteed operation or accessibility status. Do not promote optional GTFS schema fields into claims that this source actually supplies them. Recheck documented interfaces and permissions when maintaining the plugin.
