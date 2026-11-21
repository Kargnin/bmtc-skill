# Privacy

BMTC Data has no publisher-operated server, user accounts, analytics or telemetry. The bundled helper makes read-only HTTPS requests to the public Reclaim feed endpoints and, when explicitly building an index, to the public India_GTFS GitHub download. The helper downloads shared network datasets and filters route, stop and vehicle questions locally; it does not send the user's question, location, itinerary or flight details to those data sources.

Requests expose ordinary network metadata, including the execution host's IP address, to the contacted services. Those services and the AI host apply their own privacy policies and retention practices. Temporary public feed snapshots and the static SQLite index are stored in the execution environment's OS temporary directory or a user-selected cache directory. They remain until removed or cleaned by the environment; there is no automatic retention-deletion guarantee. The helper does not save a user journey history or collect credentials.

Any temporary UI or chat output is handled by the invoking AI host. Opening the optional existing Reclaim map link sends its bus/route selection and network metadata to Reclaim. Do not submit private locations, itineraries or secrets in public GitHub issues. For project questions use https://github.com/Kargnin/bmtc-agent-plugin/issues.
