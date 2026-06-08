"""
storage.py — MetaPlay by Coinplay
JSON persistence. Includes user preferences for personalization.
"""
import json, os, time, logging
from config import DB_PATH, State

logger = logging.getLogger(__name__)
_db: dict = {}

def _load():
    global _db
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH) as f:
                _db = json.load(f)
        except Exception as e:
            logger.error(f"DB load error: {e}")
            _db = {}

_last_save: float = 0.0
_SAVE_INTERVAL = 2.0

def _save(force: bool = False):
    global _last_save
    import time as _time
    now = _time.time()
    if not force and now - _last_save < _SAVE_INTERVAL:
        return
    _last_save = now
    try:
        tmp = DB_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(_db, f, indent=2)
        os.replace(tmp, DB_PATH)
    except Exception as e:
        logger.error(f"DB save error: {e}")

_load()

def _default(user_id: int, lang: str = "en") -> dict:
    return {
        "user_id":         user_id,
        "lang":            lang,
        "state":           State.NEW,
        "created_at":      time.time(),
        "last_active":     time.time(),
        "message_count":   0,
        "stage_replies":   0,
        "history":         [],
        "ftd_at":          None,
        "repeat_idx":      0,
        "repeat_sent_at":  None,
        "barriers":        [],
        "warmup_signals":  0,
        "bridge_shown":    False,
        "reg_link_sent":   False,
        "onboarding_done": False,
        "onboarding_turn": 0,
        "preferences": {
            "sport":   None,   # "football" | "esports" | "both"
            "leagues": [],     # ["Libertadores", "La Liga", ...]
            "games":   [],     # ["cs2", "lol", "dota2", ...]
            "teams":   [],     # ["River Plate", "NAVI", ...]
            "style":   None,   # "value" | "picks" | "live" | "all"
        },
    }

def get_user(user_id: int, lang: str = "en") -> dict:
    key = str(user_id)
    if key not in _db:
        _db[key] = _default(user_id, lang)
        _save()
    # Backfill preferences for existing users
    if "preferences" not in _db[key]:
        _db[key]["preferences"] = _default(user_id, lang)["preferences"]
        _save()
    return _db[key]

def update_user(user_id: int, **kwargs):
    key = str(user_id)
    if key not in _db:
        _db[key] = _default(user_id)
    _db[key].update(kwargs)
    _db[key]["last_active"] = time.time()
    _save()

def update_preferences(user_id: int, **kwargs):
    """Update individual preference fields without overwriting all."""
    key = str(user_id)
    if key not in _db:
        _db[key] = _default(user_id)
    prefs = _db[key].setdefault("preferences", _default(user_id)["preferences"])
    prefs.update(kwargs)
    _db[key]["last_active"] = time.time()
    _save()

def get_preferences(user_id: int) -> dict:
    return get_user(user_id).get("preferences", {})

def append_history(user_id: int, role: str, text: str, max_entries: int = 14):
    key = str(user_id)
    if key not in _db:
        _db[key] = _default(user_id)
    hist = _db[key].setdefault("history", [])
    hist.append({"role": role, "content": text})
    if len(hist) > max_entries:
        _db[key]["history"] = hist[-max_entries:]
    _save()

def log_barrier(user_id: int, barrier: str):
    key = str(user_id)
    barriers = _db.get(key, {}).get("barriers", [])
    if barrier not in barriers:
        barriers.append(barrier)
        update_user(user_id, barriers=barriers)

def get_all_users() -> list[dict]:
    return list(_db.values())

def increment_warmup_signals(user_id: int):
    u = get_user(user_id)
    update_user(user_id, warmup_signals=u.get("warmup_signals", 0) + 1)
