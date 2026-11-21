# BMTC Data for AI agents

An unofficial, read-only skill for Bengaluru BMTC questions: discover routes and directional stops, inspect schedules, find predicted arrivals, and locate an observed vehicle. It uses Reclaim's documented public GTFS interfaces. It is independent of BMTC and Reclaim and does not claim their endorsement.

The same skill and Python helper are packaged for ChatGPT/Codex and Claude. A supported cloud runtime can read the public feeds without a personal Mac. The runtime needs Python 3.10+, curl, SQLite, timezone data and permitted outbound HTTPS. Installing a plugin does not automatically provide those capabilities. No hosted MCP server, new website, fixed UI scaffold, credentials or background tracking service is included.

## Install in Codex

```bash
codex plugin marketplace add https://github.com/Kargnin/bmtc-agent-plugin.git
codex plugin add bmtc-data@bmtc-agent-plugins
```

Start a new session and ask a BMTC question or select the `bmtc-data` skill. Marketplace installation is distinct from a public OpenAI directory listing. See [distribution status](docs/DISTRIBUTION.md).

## Install in Claude Code

```bash
claude plugin marketplace add Kargnin/bmtc-agent-plugin
claude plugin install bmtc-data@bmtc-agent-plugins
```

Start a new session. Invoke `/bmtc-data:bmtc-data` or ask a relevant question. Claude Code distribution through this public marketplace is distinct from a listing in Anthropic's directory for Claude chat/Cowork.

## ChatGPT, mobile and Claude chat

Download the release ZIP for the target platform. ChatGPT/Codex public-directory publication and Claude directory publication require separate publisher submissions and approval. No local installation automatically syncs the skill to cloud/mobile. Check [distribution status](docs/DISTRIBUTION.md) rather than assuming this repository is already an approved listing. The plugin's public package is under [`plugins/bmtc-data`](plugins/bmtc-data).

## Try the helper directly

```bash
cd plugins/bmtc-data/skills/bmtc-data
python3 scripts/bmtc_query.py status
python3 scripts/bmtc_query.py index --download
python3 scripts/bmtc_query.py stops --query 'Mahadevapura Ring Road'
python3 scripts/bmtc_query.py routes --query '500-D'
```

The first static-index build downloads approximately 60 MB at the investigated feed version. Subsequent lookups use a temporary local SQLite index. Vehicle/status queries do not require the index. Full live feeds are cached for at least 30 seconds across agent processes using the same cache; there is no polling loop in the helper.

## Data quality and permissions

Live GPS and ETA are different from a timetable. Every answer should identify the selected bus's observation age, not just the newest feed timestamp. The skill withholds actionable predictions when observations are stale, unmatched or inconsistent. It cannot guarantee a bus is operating, seats are available, a stop is safe, or a deadline will be met.

Code and original instructions are MIT licensed. Upstream transit data is not bundled or relicensed. Static data is published under ODbL with separate attribution/conditions; the upstream live redistribution license was not established. Read [data sources and permissions](plugins/bmtc-data/DATA_SOURCES.md), [privacy](plugins/bmtc-data/PRIVACY.md), and [terms](plugins/bmtc-data/TERMS.md).

## Maintain and release

```bash
python3 scripts/validate_release.py
python3 scripts/build_release.py
```

CI runs offline checks and creates deterministic platform ZIPs. See [maintenance](docs/MAINTENANCE.md) for versioning, source verification, release and directory update steps. Report bugs through [GitHub issues](https://github.com/Kargnin/bmtc-agent-plugin/issues). Do not include private itineraries, credentials or precise personal locations in public issues.
