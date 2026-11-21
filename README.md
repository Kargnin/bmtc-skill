# BMTC data skill

A public Agent Skill for Bengaluru BMTC questions: find routes and directional stops, inspect schedules, list predicted arrivals, and locate an observed bus. It uses Reclaim's documented public GTFS interfaces and keeps scheduled times separate from live observations.

This is an independent unofficial project. It is not endorsed by BMTC or Reclaim. No plugin-directory submission, paid publisher account, hosted server, API key, permanent website or fixed UI scaffold is required to install this skill.

## Install

Use the open-source Skills CLI:

```bash
npx skills add Kargnin/bmtc-skill --skill bmtc-data
```

Choose the agents you want to use. To install globally for Codex and Claude Code:

```bash
npx skills add Kargnin/bmtc-skill --skill bmtc-data -g -a codex claude-code
```

Preview discovery without installing:

```bash
npx skills add Kargnin/bmtc-skill --list
```

The CLI currently requires Node.js 22.20 or later. Skill execution requires Python 3.10+, curl, SQLite, timezone data and permitted outbound HTTPS in the agent's macOS/Linux or cloud Linux environment. Installation on one computer does not sync the skill to another environment. Ordinary ChatGPT mobile chats do not automatically load a GitHub skill; the invoking agent must support loading the files and executing the helper.

## Use

Ask a relevant BMTC question or explicitly ask the agent to use `bmtc-data`. For example:

- Which routes serve this stop, in the right direction?
- What is scheduled at this stop tomorrow morning?
- Which buses have fresh predicted arrivals now?
- Where was this particular bus last observed, and how old is its GPS?

The agent can generate a disposable tracking view when useful, or link the existing Reclaim map. The skill requires timestamps, source attribution and stale/unmatched states in any view. It cannot guarantee boarding, operation, occupancy or on-time arrival.

## Run the helper directly

```bash
cd skills/bmtc-data
python3 scripts/bmtc_query.py status
python3 scripts/bmtc_query.py index --download
python3 scripts/bmtc_query.py stops --query 'Mahadevapura Ring Road'
python3 scripts/bmtc_query.py routes --query '500-D'
```

The explicit first index build downloads the published static GTFS and builds a temporary local SQLite index. On-demand live reads use a shared cache of at least 30 seconds; the helper creates no background tracker. Detailed endpoints, schema, source permissions and command examples are in [the API reference](skills/bmtc-data/references/api.md).

## Update and maintain

```bash
npx skills update bmtc-data
```

Use `-g` for globally installed skills. Updates require the agent's environment to reach GitHub. Maintainer checks and releases:

```bash
python3 scripts/validate_release.py
python3 scripts/build_release.py
```

CI runs synthetic checks and builds a portable skill ZIP. See [maintenance](docs/MAINTENANCE.md). [Report issues](https://github.com/Kargnin/bmtc-skill/issues) without private itineraries, locations or credentials.

## License and data

Original code/instructions are MIT licensed. No captured transit feed, database or personal journey history is bundled. Upstream data retains its own terms: static GTFS is published under ODbL, while a separate live redistribution/commercial license was not established. Preserve attribution and source limits; verify rights before mirroring/reselling data or operating at sustained high volume. The full source discussion is in the API reference.
