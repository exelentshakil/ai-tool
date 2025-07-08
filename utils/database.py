import json
import os  # ← ADD THIS LINE

import shutil
import threading
from datetime import datetime, timedelta  # ← ADD timedelta here too
from tinydb import TinyDB, Query
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import JSONStorage
from config.settings import DB_FILES

# ─── THREAD LOCKS ───────────────────────────────────────────────────────────────
cache_lock = threading.Lock()
analytics_lock = threading.Lock()
usage_lock = threading.Lock()
cost_lock = threading.Lock()
user_limits_lock = threading.Lock()

# ─── DATABASE INSTANCES ─────────────────────────────────────────────────────────
cache_db = None
analytics_db = None
usage_db = None
cost_db = None
user_limits_db = None

# Initialize Q - but make it more robust
try:
    Q = Query()
except Exception as e:
    print(f"Warning: Could not initialize Query object: {e}")
    Q = None


def repair_corrupted_json(file_path):
    """Attempt to repair corrupted JSON file"""
    try:
        backup_path = f"{file_path}.corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if os.path.exists(file_path):
            shutil.copy2(file_path, backup_path)
            print(f"Backed up corrupted file to: {backup_path}")

        empty_db = {"_default": {}}
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(empty_db, f, indent=2)
        print(f"Reset {file_path} to empty database")
        return True

    except Exception as e:
        print(f"Failed to repair {file_path}: {e}")
        return False


def safe_init_db(file_path):
    """Safely initialize TinyDB with error handling"""
    try:
        return TinyDB(file_path, storage=CachingMiddleware(JSONStorage))
    except Exception as e:
        print(f"Database error for {file_path}: {e}")
        if "Extra data" in str(e):
            repair_corrupted_json(file_path)
            return TinyDB(file_path, storage=CachingMiddleware(JSONStorage))
        raise


def init_databases():
    """Initialize all databases"""
    global cache_db, analytics_db, usage_db, cost_db, user_limits_db

    cache_db = safe_init_db(DB_FILES['cache'])
    analytics_db = safe_init_db(DB_FILES['analytics'])
    usage_db = safe_init_db(DB_FILES['usage'])
    cost_db = safe_init_db(DB_FILES['cost'])
    user_limits_db = safe_init_db(DB_FILES['user_limits'])

    print("✅ All databases initialized successfully")


def safe_db_operation(db, lock, operation, *args, **kwargs):
    """Perform thread-safe database operation"""
    with lock:
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            print(f"Database operation failed: {e}")
            return None


# ─── COST TRACKING FUNCTIONS ────────────────────────────────────────────────────
def get_openai_cost_today():
    """Get today's OpenAI costs"""
    today = datetime.now().strftime("%Y-%m-%d")
    costs = safe_db_operation(cost_db, cost_lock, cost_db.search, Q.date == today) or []
    return sum(c.get("cost", 0) for c in costs)


def get_openai_cost_month():
    """Get this month's OpenAI costs"""
    this_month = datetime.now().strftime("%Y-%m")
    costs = safe_db_operation(cost_db, cost_lock, cost_db.search, Q.date.matches(f"^{this_month}")) or []
    return sum(c.get("cost", 0) for c in costs)


def log_openai_cost(tool_slug, prompt_tokens, completion_tokens, cost):
    """Log OpenAI API costs"""
    data = {
        "tool": tool_slug,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost": cost,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat()
    }
    safe_db_operation(cost_db, cost_lock, cost_db.insert, data)


# ─── USAGE LOGGING FUNCTIONS ────────────────────────────────────────────────────
def log_usage(tool, input_length, cached=False, ip_address=None):
    """Log tool usage"""
    data = {
        "tool": tool,
        "input_length": input_length,
        "cached": cached,
        "ip_address": ip_address,
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    safe_db_operation(usage_db, usage_lock, usage_db.insert, data)


# ─── ANALYTICS FUNCTIONS ────────────────────────────────────────────────────────
def log_analytics(event, data=None):
    """Log analytics event"""
    entry = {
        "event": event,
        "data": data or {},
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    safe_db_operation(analytics_db, analytics_lock, analytics_db.insert, entry)


# ─── DATABASE MAINTENANCE ───────────────────────────────────────────────────────
def clean_old_cache(hours=24):
    """Clean old cache entries"""
    try:
        cutoff = datetime.now() - timedelta(hours=hours)
        old_entries = safe_db_operation(cache_db, cache_lock, cache_db.search, Q.created_at < cutoff.isoformat()) or []
        for entry in old_entries:
            safe_db_operation(cache_db, cache_lock, cache_db.remove, Q.key == entry['key'])
        print(f"Cleaned {len(old_entries)} old cache entries")
        return len(old_entries)
    except Exception as e:
        print(f"Cache cleanup error: {e}")
        return 0


def get_database_stats():
    """Get database statistics"""
    return {
        "cache_entries": len(safe_db_operation(cache_db, cache_lock, cache_db.all) or []),
        "usage_entries": len(safe_db_operation(usage_db, usage_lock, usage_db.all) or []),
        "cost_entries": len(safe_db_operation(cost_db, cost_lock, cost_db.all) or []),
        "user_limit_entries": len(safe_db_operation(user_limits_db, user_limits_lock, user_limits_db.all) or []),
        "analytics_entries": len(safe_db_operation(analytics_db, analytics_lock, analytics_db.all) or [])
    }