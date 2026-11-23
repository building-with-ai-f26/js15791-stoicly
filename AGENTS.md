# AGENTS.md — Coding Agent Operating Manual

> Give this file to your coding agent and check that it is using these instructions. Keep the stack, commands, and ground rules current.

## 1. Project Overview
- **What this repo builds:** Stoicly, an AI-powered reflection app. A user describes an everyday challenge and gets a Stoic reflection (in/out of control, reframe, real quote, one action); reflections are saved in the visitor's own browser so they can track growth over time.
- **Primary user & core workflow:** People seeking self-help guided by Stoicism. Core workflow: describe challenge → Stoic reflection → saved to history (in the browser). Full PRD in `docs/index.html`. UI must stay simple and user-friendly.
- **Tech stack:** Python 3 / Flask (`app.py`) / plain HTML+JS (`templates/index.html`) / no database: history in browser `localStorage` / hosted on Render (gunicorn) / Anthropic API via the `anthropic` Python SDK with structured outputs (default model `claude-haiku-5-5`, override with `ANTHROPIC_MODEL`)

## 2. Project Structure
```
app.py                 Flask server: serves the page, calls Claude, rate-limits; stores nothing
quotes.py              Verified Stoic quotes (exact public-domain wording + source); the model may only pick an id
templates/index.html   The whole app UI (HTML + CSS + vanilla JS) and PostHog snippet/events
docs/index.html        Public Product Page + Living PRD + build log (GitHub Pages, main /docs)
docs/screenshot.png    Prototype screenshot shown on the Product Page
.env.example           Template for local secrets; copy to .env (never commit .env)
requirements.txt       Python dependencies (flask, anthropic, python-dotenv, gunicorn)
render.yaml            Render blueprint (build + start commands; API key is set in Render, not here)
SECURITY.md            Security audit: what was checked, found, fixed, and still open
tests/                 Build 4 verification guidance (no automated tests yet)
journal/               Optional weekly working notes
```

**Request flow (one reflection):** browser form → `POST /api/reflect` (`app.py`) → `ask_model()` calls Claude with the system prompt + a `Reflection` schema (structured outputs; `quote_id` is an enum of `quotes.py` keys) → JSON reply is validated, the quote id is swapped for its exact text/author/source, and returned (nothing is stored on the server) → `templates/index.html` renders it and saves it to `localStorage` (`stoicly.history`, max 100). Before any of this, `rate_limited()` checks 5/min + 30/day per visitor IP and a site-wide daily cap (`GLOBAL_DAILY_LIMIT`, default 500) and returns 429 if exceeded.

## 3. Setup & Run
1. **Requirements:** Python 3.10+, an Anthropic API key (console.anthropic.com → Settings → API Keys).
2. **Install:** `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
3. **Configure:** `cp .env.example .env`, then set `ANTHROPIC_API_KEY`. Optional: `ANTHROPIC_MODEL` (default `claude-haiku-5-5`), `PORT` (default `5001`), `GLOBAL_MINUTE_LIMIT` (default `20`), `GLOBAL_DAILY_LIMIT` (default `500`), `FLASK_DEBUG=1` for auto-reload while developing.
4. **Run:** `python app.py` → open http://localhost:5001. (Port 5000 is taken by AirPlay Receiver on macOS.)
5. **Check it works:** submit a challenge; the terminal logs `Model usage: N input / M output tokens` for each call, and the reflection appears under "Your past reflections".
6. **Production-like run:** `gunicorn app:app --bind 127.0.0.1:5001 --timeout 90` (what Render runs).
- **Run deterministic tests:** none yet (planned for Build 4)
- **Run model evals:** none yet (planned for Build 4)

## 4. Analytics (PostHog)
- One PostHog project (US cloud) is used by both the Product Page (`docs/index.html`) and the local app (`templates/index.html`). The `phc_…` project token is public by design; never add a personal API key (`phx_…`).
- **App events:** `$pageview` (automatic), `reflection_submitted` (`entry_length`), `reflection_received` (`latency_ms`), `reflection_failed` (`error`), `reflection_rated` (`rating`: helpful / generic / preachy), `past_reflection_opened`. Product Page: `$pageview`, `clicked_try_product`.
- **Privacy:** never put journal text or AI replies in event properties. The result card and history carry `ph-mask` (masked in replays) and `ph-no-capture` (autocapture ignores clicks there; otherwise it records the clicked text, e.g. a history summary). Replays also mask all inputs. Both pages tell visitors they are recorded.

## 5. Shipping (deploy to Render)
Live app: https://js15791-stoicly.onrender.com (Render free tier, Web Service deployed from the **public repo URL**: the class GitHub org hasn't approved the Render GitHub app, so there is **no auto-deploy**). Product Page: GitHub Pages from `main` `/docs`.

**First-time setup (human does this once):** Render → **New → Web Service → Public Git Repository** → `https://github.com/building-with-ai-f26/js15791-stoicly`, branch `main`, runtime Python 3, build `pip install -r requirements.txt`, start `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 90`, instance Free; env vars `ANTHROPIC_API_KEY` (pasted only in Render) and `PYTHON_VERSION=3.13`. Then in the Anthropic Console set a monthly spend limit. (If the org later approves the Render GitHub app, `render.yaml` works as a Blueprint with auto-deploy.)

**Every deploy (agent follows these steps):**
1. `git status` is clean and you are on `main` (or a branch that was reviewed and merged).
2. Run checks: `python -c "import app"`; start gunicorn locally and submit one reflection; `pip-audit -r requirements.txt` shows no high-severity issues.
3. Secret scan, must print nothing: `git grep -nE "sb_secret_|service_role|sk-or-|sk-ant-|sk-proj-|sk_live_" -- . ':!.env.example'`
4. `git push origin main`, then **ask the human to click Render → js15791-stoicly → Manual Deploy → Deploy latest commit** (≈1–2 min) and wait for **Live**. Ask the human if it fails.
5. Smoke test the live URL: page loads on a phone, one reflection works, `curl -s https://js15791-stoicly.onrender.com/ | grep -cE "sk-ant-|sk-or-"` prints 0.
6. **Rollback:** Render dashboard → the service → **Events** → pick the last good deploy → **Rollback**. Or `git revert <bad commit>` and push.

Keep gunicorn at **one worker** (the default): the rate limiter lives in memory, so more workers would each get their own limits.

## 6. Ask Me First (agent must stop and get explicit approval)
- **Deleting or changing data:** deleting files or folders, `git reset --hard`, `git push --force`, rewriting history, clearing anyone's `localStorage`, deleting PostHog data or persons, adding or changing a database.
- **Keys, secrets, permissions:** creating, rotating, reading out or moving any API key; editing `.env` or Render environment variables; changing GitHub, Render, Anthropic or PostHog settings, access or sharing.
- **Anything that costs money:** switching to a more expensive model, raising rate limits or `GLOBAL_DAILY_LIMIT`, upgrading a Render/Anthropic/PostHog plan, running more than ~20 real AI calls in a test.
- **Public changes:** pushing to `main` (it deploys), publishing new pages or links.

## 7. Non-Negotiable Engineering Rules
0. **No model-written quotes:** never let the model generate quote text. Add new quotes to `quotes.py` only after copying them exactly from a translation, with the source.
1. **Plan before coding:** Before touching multiple files, propose a brief plan and wait for approval.
2. **Small batches:** Make small, focused changes that can be reviewed and explained by a human in a single Pull Request.
3. **Explainability:** Avoid unnecessary abstractions or dependencies. Help the human builder understand the main components, what changed, why it matters, what could break, and how it was checked.
4. **Verify changes:** Run relevant checks. For a reproducible logic bug, use a failing test to demonstrate the fix when practical. Record manual checks and known limitations; follow the selected Build 4 evaluation track.
5. **Zero secrets in code:** Never hardcode API keys, tokens, or credentials. Always read from environment variables (`.env`) and update `.env.example` when new variables are needed.
6. **Stop when looping:** If a fix fails twice in a row, stop, summarize what failed, and ask the human before trying a third approach.

### Rules learned from real mistakes
7. **Check what analytics actually send, not just what replays show.** (Build 2: the agent masked journal text in session replay but PostHog autocapture still sent the text of a clicked history entry. Found only by reading the PostHog event list.) After any analytics change, open PostHog Activity and read the event properties.
8. **Never fill in numbers the human didn't give you.** (Build 2: the agent changed the logged hours from 1 to 1.5 without asking.) Hours, spend, tester counts and results in the build log come from the human; leave a clear `[TODO]` and ask.
9. **Test the live URL, not just localhost.** (Build 3: the per-visitor rate limit passed locally but a faked `X-Forwarded-For` header bypassed it on Render.) Security checks count only when run against the deployed site.
10. **Verify which server you are testing.** (Build 3: a rate-limit test hit a leftover dev server on port 5001 instead of the new gunicorn server.) Before testing, check `lsof -iTCP:<port> -sTCP:LISTEN` and stop stale servers.
