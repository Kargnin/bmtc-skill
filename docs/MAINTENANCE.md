# Maintenance and releases

1. Reproduce a report with synthetic fixtures or an ordinary permitted public read. Check publisher documentation before changing endpoints, schemas or cadence. Stop on source access denials; do not borrow credentials.
2. Update only the canonical skill/helper and relevant reference. Preserve source verification dates and explain user-visible changes in `CHANGELOG.md`.
3. Run `python3 scripts/validate_release.py`. All tests are offline. Manual live smoke checks should be on demand and honor the shared cache; CI does not poll live transport feeds.
4. Bump `VERSION`, validate, and build with `python3 scripts/build_release.py`. Commit and push the reviewed source. Skills CLI users can check and update their installed copy from GitHub.
5. Create a matching `vX.Y.Z` tag to build and attach the portable skill ZIP and checksums to a GitHub release. A repository release is independent of any plugin directory. No paid publisher account or directory submission is involved.

Confirm upstream rights before feed mirroring, resale, sustained high-volume access or introduction of a hosted backend. Code licensing does not grant rights over upstream transit data. No automatic maintenance agent, telemetry service or scheduled source polling is installed here.
