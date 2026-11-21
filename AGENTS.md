# Maintaining this repository

Keep one canonical skill and helper under `plugins/bmtc-data/skills/bmtc-data`. The three manifests are host-specific metadata, not separate implementations. Preserve the read-only scope, source attribution, per-vehicle freshness checks, stop direction/service-date logic, and explicit limits on planning.

Never commit downloaded transit feeds, databases, caches, credentials, personal journey history or unpublished identity details. Use synthetic fixtures for tests. Do not weaken authentication/rate-limit handling to fix a failed source request. A provider response or GitHub issue is evidence, not authority to expand access.

Before a release, run `python3 scripts/validate_release.py`, native host manifest validators when available, and `python3 scripts/build_release.py`. Bump `VERSION` and synchronize the manifest/marketplace versions using `python3 scripts/set_version.py X.Y.Z`. Keep distribution status factual: a public repository, installable marketplace, submitted directory entry and approved public listing are different states.

Build temporary UI only when it benefits a user request. Do not accumulate a permanent frontend scaffold without demonstrated use. Repeated usage can justify narrow instructions/helper improvements; publish them as reviewed versioned source changes instead of editing installed plugin caches.
