"""
Persistent storage for the Yen government system.

State is stored as a single JSON file on disk. Everything is kept in memory
in the STATE dict and written back to disk after every mutation via save().
This is intentionally simple: a small Discord bot does not need a real
database, and JSON is easy to inspect, back up, and reason about.

Data shape:

{
    "guilds": {
        "<guild_id>": {
            "role_id": <int or None>,
            "laws": {
                "<LAW ID>": {
                    "type": "<law type key>",
                    "description": "<human readable description>",
                    "params": {...},
                    "violation_text": "<flavor text shown on violation>",
                    "permission_action": "<phrase used in grant commands>",
                    "created_at": <unix timestamp>
                },
                ...
            },
            "exemptions": {
                "<LAW ID>": [<user_id>, ...]
            },
            "last_message_ts": {
                "<user_id>": <unix timestamp>
            }
        }
    }
}
"""

import json
import os
import threading

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_BASE_DIR, "data")
_DATA_FILE = os.path.join(_DATA_DIR, "state.json")

_lock = threading.Lock()

_DEFAULT_STATE = {"guilds": {}}

_DEFAULT_GUILD_STATE = {
    "role_id": None,
    "laws": {},
    "exemptions": {},
    "last_message_ts": {},
}


def _ensure_data_dir():
    os.makedirs(_DATA_DIR, exist_ok=True)


def _read_from_disk():
    _ensure_data_dir()
    if not os.path.exists(_DATA_FILE):
        return json.loads(json.dumps(_DEFAULT_STATE))
    try:
        with open(_DATA_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            if "guilds" not in data:
                data["guilds"] = {}
            return data
    except (json.JSONDecodeError, OSError):
        # Corrupted or unreadable file. Do not crash the bot; start clean
        # rather than losing the ability to boot. The bad file is preserved
        # alongside for manual inspection.
        if os.path.exists(_DATA_FILE):
            try:
                os.replace(_DATA_FILE, _DATA_FILE + ".corrupt")
            except OSError:
                pass
        return json.loads(json.dumps(_DEFAULT_STATE))


# In-memory state, loaded once at import time and mutated in place.
STATE = _read_from_disk()


def save():
    """Persist the current in-memory STATE to disk atomically."""
    _ensure_data_dir()
    with _lock:
        tmp_path = _DATA_FILE + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(STATE, handle, indent=2)
        os.replace(tmp_path, _DATA_FILE)


def get_guild_state(guild_id):
    """Return the mutable state dict for a guild, creating it if needed."""
    key = str(guild_id)
    guilds = STATE.setdefault("guilds", {})
    if key not in guilds:
        guilds[key] = json.loads(json.dumps(_DEFAULT_GUILD_STATE))
        save()
    else:
        # Backfill any keys added to the schema after this guild was created.
        changed = False
        for field, default in _DEFAULT_GUILD_STATE.items():
            if field not in guilds[key]:
                guilds[key][field] = json.loads(json.dumps(default))
                changed = True
        if changed:
            save()
    return guilds[key]
