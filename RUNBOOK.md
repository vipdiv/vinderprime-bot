\# VinderPrime Bot — RUNBOOK



\## What this is

Discord bot that runs a “daily cycle”:

\- pulls RSS signals (Reddit RSS)

\- filters/dedupes

\- posts a brief in Discord

\- pushes tasks to Mission Control via POST /api/tasks/bulk



\## How to run

1\) Activate venv (if used):

&nbsp;  .venv\\Scripts\\activate

2\) Set env vars (in the same terminal):

&nbsp;  set DISCORD\_TOKEN=...

&nbsp;  set CONTROL\_ROOM\_CHANNEL\_ID=...

&nbsp;  set MISSION\_CONTROL\_BASE\_URL=http://localhost:3000

&nbsp;  set VP\_TZ=America/Chicago

3\) Run:

&nbsp;  python -u main.py



\## Manual run

Discord command: !runnow

Expected behavior: runs cycle immediately and pushes tasks to Mission Control.



\## Bug / proof

Local time:

\- CMD: echo %date% %time%

\- PowerShell: (Get-Date).ToUniversalTime()



Observed:

\- A “TEST TASK Fri 02/20/2026 22:33” was createdAt "2026-02-21T04:33:01Z".

This is correct UTC but incorrect for “Today (Chicago)” grouping.



\## Required fix

Bot must compute vpDate using America/Chicago and include vpDate in tasks sent to Mission Control.



vpDate format:

YYYY-MM-DD (Chicago local date at time of creation)

