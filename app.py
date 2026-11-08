"""Stoicly: a tiny local prototype.

You describe a challenge, an AI model replies with a Stoic reflection,
and each reflection is saved to data/reflections.json so you can look back.

Run:  python app.py   then open http://localhost:5000
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()  # reads OPENROUTER_API_KEY (and optional OPENROUTER_MODEL) from .env

API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-haiku-5.5")
DATA_FILE = Path(__file__).parent / "data" / "reflections.json"
MAX_ENTRY_CHARS = 2000

SYSTEM_PROMPT = """You are Stoicly, a warm, practical guide to Stoic philosophy.
The user describes an everyday challenge. Reply ONLY with a JSON object with these keys:
- "in_control": 1-3 short bullet strings: what is within the user's control
- "not_in_control": 1-3 short bullet strings: what is outside their control
- "reframe": 2-4 sentences reframing the situation through a Stoic lens, kind and plain-spoken
- "quote": a real, well-known quote from Marcus Aurelius, Epictetus, or Seneca
- "quote_author": the author of the quote
- "action": one small, concrete action the user can take today
Do not invent quotes. Avoid jargon. You are not a therapist; if the user mentions
self-harm or crisis, set "reframe" to a gentle message urging them to contact the
988 Suicide & Crisis Lifeline (call or text 988 in the US) or local emergency services."""

app = Flask(__name__)


def load_reflections():
    if not DATA_FILE.exists():
        return []
    return json.loads(DATA_FILE.read_text())


def save_reflection(entry):
    DATA_FILE.parent.mkdir(exist_ok=True)
    reflections = load_reflections()
    reflections.insert(0, entry)  # newest first
    DATA_FILE.write_text(json.dumps(reflections, indent=2))


def ask_model(challenge):
    """Send the challenge to OpenRouter and return the parsed reflection dict."""
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": challenge},
            ],
            "response_format": {"type": "json_object"},
        },
        timeout=60,
    )
    response.raise_for_status()
    text = response.json()["choices"][0]["message"]["content"].strip()
    # Some models wrap JSON in ```json fences; strip them if present.
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    return json.loads(text)


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/reflections")
def list_reflections():
    return jsonify(load_reflections())


@app.post("/api/reflect")
def reflect():
    challenge = (request.get_json(silent=True) or {}).get("challenge", "").strip()
    if not challenge:
        return jsonify(error="Please describe what's on your mind."), 400
    if len(challenge) > MAX_ENTRY_CHARS:
        return jsonify(error=f"Please keep it under {MAX_ENTRY_CHARS} characters."), 400
    if not API_KEY or "replace-with-your-key" in API_KEY:
        return jsonify(error="No OpenRouter API key found. Add one to your .env file."), 500

    try:
        reflection = ask_model(challenge)
    except (requests.RequestException, KeyError, ValueError) as exc:
        app.logger.error("Model call failed: %s", exc)
        return jsonify(error="Stoicly couldn't reach the AI just now. Please try again."), 502

    entry = {
        "id": uuid.uuid4().hex,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "challenge": challenge,
        **reflection,
    }
    save_reflection(entry)
    return jsonify(entry)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
