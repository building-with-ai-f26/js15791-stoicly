"""Stoicly: a tiny local prototype.

You describe a challenge and an AI model replies with a Stoic reflection.
The server stores nothing: each visitor's history is kept in their own
browser (localStorage), so reflections stay private and survive restarts.

Run:  python app.py   then open http://localhost:5001
(Port 5000 is taken by AirPlay Receiver on macOS; override with PORT in .env.)
"""

import os
import threading
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone

import anthropic
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix
from pydantic import BaseModel
from typing import Literal

from quotes import QUOTES

load_dotenv()  # reads ANTHROPIC_API_KEY (and optional ANTHROPIC_MODEL) from .env

API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
MAX_ENTRY_CHARS = 2000

# Rate limits on the paid AI route (in-memory; fine for one Render instance).
PER_VISITOR_LIMITS = [(5, 60), (30, 24 * 60 * 60)]  # 5/minute and 30/day per IP
GLOBAL_DAILY_LIMIT = int(os.getenv("GLOBAL_DAILY_LIMIT", "500"))  # all visitors; caps spend at ~$0.12/day

SYSTEM_PROMPT = """You are Stoicly, a warm, practical guide to Stoic philosophy.
The user describes an everyday challenge. Respond with:
- in_control: 1-3 short points about what is within the user's control
- not_in_control: 1-3 short points about what is outside their control
- reframe: 2-4 sentences reframing the situation through a Stoic lens, kind and plain-spoken
- quote_id: the id of the ONE quote from the list below that best fits the situation
- action: one small, concrete action the user can take today
Never write quote text yourself; only choose an id. Avoid jargon. You are not a therapist; if the user mentions
self-harm or crisis, set "reframe" to a gentle message urging them to contact the
988 Suicide & Crisis Lifeline (call or text 988 in the US) or local emergency services.

Quotes you may choose from (id: theme):
""" + "\n".join(f"- {qid}: {q['theme']}" for qid, q in QUOTES.items())


class Reflection(BaseModel):
    """The shape every AI reply must have (enforced by structured outputs)."""

    in_control: list[str]
    not_in_control: list[str]
    reframe: str
    quote_id: Literal[tuple(QUOTES)]  # the model can only pick a verified quote
    action: str


app = Flask(__name__)
app.logger.setLevel("INFO")  # so token-usage lines show up in Render's logs too
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # reject oversized request bodies
# Render sits behind one proxy; trust its X-Forwarded-For so we see the real visitor IP.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

_hits = defaultdict(deque)  # key -> timestamps of recent requests
_hits_lock = threading.Lock()


def rate_limited(visitor):
    """Return True if this visitor (or the whole site) is over a limit; else record the hit."""
    now = time.time()
    checks = [(f"ip:{visitor}:{window}", limit, window) for limit, window in PER_VISITOR_LIMITS]
    checks.append(("global", GLOBAL_DAILY_LIMIT, 24 * 60 * 60))
    with _hits_lock:
        for key, limit, window in checks:
            q = _hits[key]
            while q and q[0] <= now - window:
                q.popleft()
            if len(q) >= limit:
                return True
        for key, _, _ in checks:
            _hits[key].append(now)
    return False


@app.after_request
def security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return resp


def ask_model(challenge):
    """Send the challenge to Claude and return the reflection as a dict."""
    client = anthropic.Anthropic(api_key=API_KEY, timeout=60.0)
    response = client.messages.parse(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": challenge}],
        output_format=Reflection,
    )
    u = response.usage  # logged so we can measure real cost per reflection
    app.logger.info("Model usage: %s input / %s output tokens", u.input_tokens, u.output_tokens)
    if response.parsed_output is None:  # e.g. the model declined or was cut off
        raise ValueError(f"No reflection returned (stop_reason={response.stop_reason})")
    reflection = response.parsed_output.model_dump()
    quote = QUOTES[reflection.pop("quote_id")]  # fill in exact wording + source
    reflection.update(quote=quote["text"], quote_author=quote["author"], quote_source=quote["source"])
    return reflection


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/_ipcheck")  # TEMPORARY (Build 3 audit): see which IP headers Render sends. Remove after.
def ipcheck():
    names = ["X-Forwarded-For", "X-Real-Ip", "True-Client-Ip", "Cf-Connecting-Ip", "X-Envoy-External-Address", "Forwarded"]
    raw = request.environ.get("werkzeug.proxy_fix.orig", {})
    return jsonify(remote_addr=request.remote_addr, orig_remote=raw.get("REMOTE_ADDR"),
                   headers={n: request.headers.get(n) for n in names},
                   orig_xff=raw.get("HTTP_X_FORWARDED_FOR"))


@app.post("/api/reflect")
def reflect():
    if rate_limited(request.remote_addr):
        return jsonify(error="You've reached the limit for now. Take a breath and try again in a little while."), 429
    payload = request.get_json(silent=True)
    challenge = payload.get("challenge") if isinstance(payload, dict) else None
    challenge = challenge.strip() if isinstance(challenge, str) else ""
    if not challenge:
        return jsonify(error="Please describe what's on your mind."), 400
    if len(challenge) > MAX_ENTRY_CHARS:
        return jsonify(error=f"Please keep it under {MAX_ENTRY_CHARS} characters."), 400
    if not API_KEY or "replace-with-your-key" in API_KEY:
        app.logger.error("ANTHROPIC_API_KEY is missing (set it in .env locally or in Render's dashboard)")
        return jsonify(error="Stoicly isn't set up correctly right now. Please try again later."), 500

    try:
        reflection = ask_model(challenge)
    except anthropic.AuthenticationError:
        app.logger.error("Anthropic rejected ANTHROPIC_API_KEY")  # details stay in server logs, not the browser
        return jsonify(error="Stoicly couldn't reach the AI just now. Please try again."), 502
    except (anthropic.APIError, ValueError) as exc:
        app.logger.error("Model call failed: %s", exc)
        return jsonify(error="Stoicly couldn't reach the AI just now. Please try again."), 502

    entry = {
        "id": uuid.uuid4().hex,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "challenge": challenge,
        **reflection,
    }
    return jsonify(entry)  # not stored on the server; the browser keeps its own history


if __name__ == "__main__":
    # Debug mode (auto-reload + in-browser debugger) only when FLASK_DEBUG=1, never in production.
    app.run(debug=os.getenv("FLASK_DEBUG") == "1", port=int(os.getenv("PORT", "5001")))
