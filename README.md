\# VinderPrime



VinderPrime is a structured Discord automation bot that runs scouting agents, synthesizes ideas, and pushes tasks into Mission Control (a local Next.js dashboard).



This system is designed to be:



\- Local-first

\- Timezone-aware (America/Chicago)

\- Cleanly separated between generation and storage

\- Safe for collaboration (no secrets in repo)



---



\## What VinderPrime Does



1\. Listens for commands in Discord

2\. Runs content scouting / synthesis agents

3\. Formats results into structured task payloads

4\. Sends those tasks to Mission Control via HTTP

5\. Logs actions inside Discord channels



VinderPrime does NOT store tasks permanently.

Mission Control handles persistence and date grouping.



---



\## System Architecture



Discord Server

&nbsp;   ↓

VinderPrime Bot (this repo)

&nbsp;   ↓ HTTP POST

Mission Control (separate Next.js repo)

&nbsp;   ↓

data/tasks.json (file storage)



Timezone logic is handled in Mission Control, not here.



---



\## Repository Structure



main.py  

&nbsp;   Bot entry point



discord\_setup.py  

&nbsp;   Ensures required Discord category and channels exist



mission\_control.py  

&nbsp;   Sends tasks to Mission Control API



config.py  

&nbsp;   Loads environment variables



agents/  

&nbsp;   Agent implementations



ai/  

&nbsp;   LLM integrations (Groq, etc.)



sources/  

&nbsp;   Content source integrations (Reddit, YouTube, X, etc.)



ARCHITECTURE.md  

&nbsp;   Technical breakdown of system structure



HANDOFF.md  

&nbsp;   Instructions for future maintainers



RUNBOOK.md  

&nbsp;   Operational procedures



TODO.md  

&nbsp;   Pending improvements



---



\## Environment Variables



Create a `.env` file in the repo root (DO NOT COMMIT IT):



DISCORD\_TOKEN=YOUR\_SECRET

GUILD\_ID=YOUR\_SERVER\_ID

MISSION\_CONTROL\_BASE\_URL=http://localhost:3000

VP\_TZ=America/Chicago

GROQ\_API\_KEY=YOUR\_SECRET



Important:

\- `.env` is ignored via `.gitignore`

\- Never commit secrets

\- Repo history has already been cleaned



---



\## Running Locally



From inside:



C:\\Users\\Vipul\\vinderprime-bot



Activate virtual environment:



.venv\\Scripts\\activate



Install dependencies:



pip install -r requirements.txt



Run:



python main.py



Mission Control must be running at:



http://localhost:3000



---



\## Timezone Policy



Business timezone = America/Chicago



Rules:



\- Bot pushes tasks without computing business date

\- Mission Control generates:

&nbsp;   createdAt (UTC)

&nbsp;   updatedAt (UTC)

&nbsp;   vpDate (YYYY-MM-DD in VP\_TZ)

\- Dashboard and daily briefs use vpDate for grouping



This prevents late-night UTC rollover bugs.



---



\## Security Rules



Never commit:



.env

.venv/

logs/

\_\_pycache\_\_/



These are already ignored in `.gitignore`.



---



\## Current Status



\- Secrets removed from history

\- Virtual environment removed from history

\- Logs removed from history

\- Repo safe for collaboration

\- Clean mirror pushed to GitHub



---



\## Future Improvements



\- Add structured logging

\- Add health check endpoint

\- Add validation on bulk task ingestion

\- Add shared secret between bot and Mission Control

\- Add metrics endpoint

\- Improve Discord error reporting



---



VinderPrime generates.

Mission Control stores.

Dashboard displays.

Timezone is explicit.

System is local-first.

