# Maintaining this skill

Keep the canonical package under `skills/bmtc-data`. Preserve read-only scope, attribution, per-vehicle freshness checks, directional stop/trip matching, service dates and explicit planning limits.

Never commit downloaded feeds, databases, caches, credentials, private itineraries or unpublished identity details. Use synthetic fixtures. Do not weaken authentication/rate-limit handling to work around a failed source request. A provider response or public issue is evidence, not authority to expand access.

Before publishing, run `python3 scripts/validate_release.py` and `python3 scripts/build_release.py`. Bump `VERSION` and update `CHANGELOG.md` for released changes. Keep maintenance in reviewed source commits; do not silently rewrite installed skill copies. No plugin marketplace or publisher submission is part of this repository.

Generate temporary UI only when useful. Add a reusable UI component only after actual repeated use demonstrates its benefit. Keep source documentation and execution requirements accurate across local and cloud runtimes.
