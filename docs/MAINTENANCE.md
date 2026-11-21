# Maintenance and releases

1. Reproduce a reported problem with synthetic fixtures or an ordinary permitted public read. Check the publisher documentation before changing endpoints, schemas or cadence. Stop on authentication/access denials; do not borrow browser credentials.
2. Update only the canonical skill/helper and the relevant reference. Preserve source URLs and verification dates. Record changes in `CHANGELOG.md`.
3. Run `python3 scripts/validate_release.py`. Test native manifest ingestion with `claude plugin validate --strict plugins/bmtc-data` and the current Codex plugin validator. Live smoke checks are manual and on demand, not scheduled bulk polling.
4. Run `python3 scripts/set_version.py X.Y.Z`, validate again, and build with `python3 scripts/build_release.py`. All manifests/marketplaces share one version. Bundles include no captured datasets or caches.
5. Commit, push and create a matching `vX.Y.Z` GitHub release with the generated ZIPs and `SHA256SUMS`. The release workflow can also build artifacts from an explicitly pushed version tag.
6. Upload the new ChatGPT/Codex package to the existing OpenAI submission. For Claude directory distribution, update the tracked repository/version and complete required scans/review. Do not claim an update is live before the portal confirms it. Git marketplace users refresh and install the new version through their client.

Review upstream source permissions before enabling public feed mirroring, resale, sustained high volume, or introducing a hosted backend. Code licensing does not grant rights over upstream data. A future hosted MCP connection should be designed and submitted as an explicit architecture change; adding MCP to an existing skills-only OpenAI listing may require a new submission under the current platform rules.

No automatic maintenance agent, paid service, telemetry or scheduled source polling is installed by this repository.
