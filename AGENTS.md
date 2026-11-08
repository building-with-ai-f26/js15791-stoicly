# AGENTS.md — Coding Agent Operating Manual

> Give this file to your coding agent and check that it is using these instructions. Keep the stack, commands, and ground rules current.

## 1. Project Overview
- **What this repo builds:** Stoicly, an AI-powered reflection app. A user describes an everyday challenge and gets a Stoic reflection (in/out of control, reframe, real quote, one action); reflections are saved so they can track growth over time.
- **Primary user & core workflow:** People seeking self-help guided by Stoicism. Core workflow: describe challenge → Stoic reflection → saved to history. Full PRD in `docs/index.html`. UI must stay simple and user-friendly.
- **Tech stack:** Python 3 / Flask (`app.py`) / plain HTML+JS (`templates/index.html`) / local JSON file (`data/reflections.json`) / OpenRouter API (default model `anthropic/claude-haiku-5.5`, override with `OPENROUTER_MODEL`)

## 2. Commands
- **Install dependencies:** `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- **Run locally:** `python app.py` → http://localhost:5000 (needs `OPENROUTER_API_KEY` in `.env`)
- **Run deterministic tests:** none yet (planned for Build 4)
- **Run model evals:** none yet (planned for Build 4)

## 3. Non-Negotiable Engineering Rules
1. **Plan before coding:** Before touching multiple files, propose a brief plan and wait for approval.
2. **Small batches:** Make small, focused changes that can be reviewed and explained by a human in a single Pull Request.
3. **Explainability:** Avoid unnecessary abstractions or dependencies. Help the human builder understand the main components, what changed, why it matters, what could break, and how it was checked.
4. **Verify changes:** Run relevant checks. For a reproducible logic bug, use a failing test to demonstrate the fix when practical. Record manual checks and known limitations; follow the selected Build 4 evaluation track.
5. **Zero secrets in code:** Never hardcode API keys, tokens, or credentials. Always read from environment variables (`.env`) and update `.env.example` when new variables are needed.
6. **Stop when looping:** If a fix fails twice in a row, stop, summarize what failed, and ask the human before trying a third approach.
