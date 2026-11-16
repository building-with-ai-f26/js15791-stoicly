# AGENTS.md — Coding Agent Operating Manual

> Give this file to your coding agent and check that it is using these instructions. Keep the stack, commands, and ground rules current.

## 1. Project Overview
- **What this repo builds:** Stoicly, an AI-powered reflection app. A user describes an everyday challenge and gets a Stoic reflection (in/out of control, reframe, real quote, one action); reflections are saved so they can track growth over time.
- **Primary user & core workflow:** People seeking self-help guided by Stoicism. Core workflow: describe challenge → Stoic reflection → saved to history. Full PRD in `docs/index.html`. UI must stay simple and user-friendly.
- **Tech stack:** Python 3 / Flask (`app.py`) / plain HTML+JS (`templates/index.html`) / local JSON file (`data/reflections.json`) / Anthropic API via the `anthropic` Python SDK with structured outputs (default model `claude-haiku-5-5`, override with `ANTHROPIC_MODEL`)

## 2. Project Structure
```
app.py                 Flask server: serves the page, calls Claude, saves reflections
quotes.py              Verified Stoic quotes (exact public-domain wording + source); the model may only pick an id
templates/index.html   The whole app UI (HTML + CSS + vanilla JS) and PostHog snippet/events
data/reflections.json  Saved reflections, newest first (created on first run; git-ignored)
docs/index.html        Public Product Page + Living PRD + build log (GitHub Pages, main /docs)
docs/screenshot.png    Prototype screenshot shown on the Product Page
.env.example           Template for local secrets; copy to .env (never commit .env)
requirements.txt       Python dependencies (flask, anthropic, python-dotenv)
tests/                 Build 4 verification guidance (no automated tests yet)
journal/               Optional weekly working notes
```

**Request flow (one reflection):** browser form → `POST /api/reflect` (`app.py`) → `ask_model()` calls Claude with the system prompt + a `Reflection` schema (structured outputs; `quote_id` is an enum of `quotes.py` keys) → JSON reply is validated, the quote id is swapped for its exact text/author/source, saved to `data/reflections.json`, and returned → `templates/index.html` renders it. `GET /api/reflections` loads history.

## 3. Setup & Run
1. **Requirements:** Python 3.10+, an Anthropic API key (console.anthropic.com → Settings → API Keys).
2. **Install:** `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
3. **Configure:** `cp .env.example .env`, then set `ANTHROPIC_API_KEY`. Optional: `ANTHROPIC_MODEL` (default `claude-haiku-5-5`), `PORT` (default `5001`).
4. **Run:** `python app.py` → open http://localhost:5001. (Port 5000 is taken by AirPlay Receiver on macOS.)
5. **Check it works:** submit a challenge; the terminal logs `Model usage: N input / M output tokens` for each call, and the reflection appears under "Your past reflections".
- **Run deterministic tests:** none yet (planned for Build 4)
- **Run model evals:** none yet (planned for Build 4)

## 4. Analytics (PostHog)
- One PostHog project (US cloud) is used by both the Product Page (`docs/index.html`) and the local app (`templates/index.html`). The `phc_…` project token is public by design; never add a personal API key (`phx_…`).
- **App events:** `$pageview` (automatic), `reflection_submitted` (`entry_length`), `reflection_received` (`latency_ms`), `reflection_failed` (`error`), `reflection_rated` (`rating`: helpful / generic / preachy), `past_reflection_opened`. Product Page: `$pageview`, `clicked_try_product`.
- **Privacy:** never put journal text or AI replies in event properties. The result card and history carry `ph-mask` (masked in replays) and `ph-no-capture` (autocapture ignores clicks there; otherwise it records the clicked text, e.g. a history summary). Replays also mask all inputs. Both pages tell visitors they are recorded.

## 5. Non-Negotiable Engineering Rules
0. **No model-written quotes:** never let the model generate quote text. Add new quotes to `quotes.py` only after copying them exactly from a translation, with the source.
1. **Plan before coding:** Before touching multiple files, propose a brief plan and wait for approval.
2. **Small batches:** Make small, focused changes that can be reviewed and explained by a human in a single Pull Request.
3. **Explainability:** Avoid unnecessary abstractions or dependencies. Help the human builder understand the main components, what changed, why it matters, what could break, and how it was checked.
4. **Verify changes:** Run relevant checks. For a reproducible logic bug, use a failing test to demonstrate the fix when practical. Record manual checks and known limitations; follow the selected Build 4 evaluation track.
5. **Zero secrets in code:** Never hardcode API keys, tokens, or credentials. Always read from environment variables (`.env`) and update `.env.example` when new variables are needed.
6. **Stop when looping:** If a fix fails twice in a row, stop, summarize what failed, and ask the human before trying a third approach.
