"""
Minimal Flask server used only to satisfy Render's web-service health
checks so the Discord bot process stays alive. Runs in a background
thread alongside the bot's event loop.
"""

import os
from threading import Thread

from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "The Yen government is currently operational."


@app.route("/health")
def health():
    return {"status": "ok"}


def _run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    thread = Thread(target=_run, daemon=True)
    thread.start()
