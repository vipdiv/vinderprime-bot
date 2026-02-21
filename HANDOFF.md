\# VinderPrime Bot — HANDOFF



\## What this is



VinderPrime is a local Discord bot (Python) that:



\- Pulls RSS signals (Reddit RSS feeds)

\- Processes / filters signals

\- Generates tasks

\- Posts a daily brief in a Discord "Control Room"

\- Pushes tasks to Mission Control (Next.js app) via HTTP API



Mission Control runs separately at:

http://localhost:3000



---



\## Folder Structure



\- main.py → Bot entrypoint

\- discord\_setup.py → Discord bot initialization and command registration

\- mission\_control.py → Handles POST to Mission Control API

\- config.py → Environment configuration

\- agents/ → Task generation / AI logic

\- ai/ → AI integration logic

\- sources/ → RSS / external signal logic

\- logs/ → Runtime logs (should not be committed long-term)

\- requirements.txt → Python dependencies



---



\## How to Run



1\) Activate venv:

&nbsp;  .venv\\Scripts\\activate



2\) Set environment variables (same terminal):



&nbsp;  set DISCORD\_TOKEN=...

&nbsp;  set CONTROL\_ROOM\_CHANNEL\_ID=...

&nbsp;  set MISSION\_CONTROL\_BASE\_URL=http://localhost:3000

&nbsp;  set VP\_TZ=America/Chicago



3\) Run:

&nbsp;  python -u main.py



---



\## Manual Execution



Discord command:

!runnow



Expected behavior:

\- Runs daily cycle

\- Posts brief in Control Room

\- Pushes tasks to:

&nbsp; POST http://localhost:3000/api/tasks/bulk



---



\## Current Issue



Timezone handling is inconsistent.



Observed:

If local time is:

Fri 02/20/2026 10:30 PM (Chicago)



Bot stores:

createdAt = 2026-02-21T04:30:00Z (UTC)



This is correct UTC, but breaks business-day grouping.



Mission Control originally derived "Today" from createdAt,

which caused tasks to appear as the wrong day.



---



\## Required Fix



Introduce and enforce business-day key:



vpDate = YYYY-MM-DD in America/Chicago



Rules:

\- Bot MUST compute vpDate using VP\_TZ.

\- vpDate MUST be included in every task sent to Mission Control.

\- Never derive business-day from UTC timestamp.

\- Discord brief should print both local Chicago date and UTC.



---



\## Acceptance Criteria



If Chicago time is:

2026-02-20 22:30



Then:

createdAt = 2026-02-21T04:30:00Z

vpDate    = 2026-02-20



Mission Control must count it as Feb 20.



---



\## Non-Goals



\- Do not hardcode timezone offsets.

\- Do not remove UTC storage.

\- Do not move business-day logic into UI only.



Source of truth:

VP\_TZ environment variable.

