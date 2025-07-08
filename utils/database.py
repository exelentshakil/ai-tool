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
        print(f"🔍 Attempting to initialize database: {file_path}")
        print(f"🔍 File exists: {os.path.exists(file_path)}")
        print(f"🔍 File absolute path: {os.path.abspath(file_path)}")

        db = TinyDB(file_path, storage=CachingMiddleware(JSONStorage))
        print(f"✅ Successfully initialized: {file_path}")
        return db

    except Exception as e:
        print(f"❌ Database error for {file_path}: {e}")
        if "Extra data" in str(e):
            print("🔧 Attempting to repair corrupted JSON...")
            if repair_corrupted_json(file_path):
                print("🔧 Retrying database initialization...")
                return TinyDB(file_path, storage=CachingMiddleware(JSONStorage))
        print(f"❌ Failed to initialize {file_path}")
        return None  # Return None instead of raising


def init_databases():
    """Initialize all databases"""
    global cache_db, analytics_db, usage_db, cost_db, user_limits_db

    print("🔍 Starting database initialization...")
    print(f"🔍 DB_FILES: {DB_FILES}")
    ensure_db_files_exist()
    try:
        print("🔍 Initializing cache_db...")
        cache_db = safe_init_db(DB_FILES['cache'])
        print(f"✅ cache_db initialized: {cache_db is not None}")

        print("🔍 Initializing analytics_db...")
        analytics_db = safe_init_db(DB_FILES['analytics'])
        print(f"✅ analytics_db initialized: {analytics_db is not None}")

        print("🔍 Initializing usage_db...")
        usage_db = safe_init_db(DB_FILES['usage'])
        print(f"✅ usage_db initialized: {usage_db is not None}")

        print("🔍 Initializing cost_db...")
        cost_db = safe_init_db(DB_FILES['cost'])
        print(f"✅ cost_db initialized: {cost_db is not None}")

        print("🔍 Initializing user_limits_db...")
        user_limits_db = safe_init_db(DB_FILES['user_limits'])
        print(f"✅ user_limits_db initialized: {user_limits_db is not None}")

        print("✅ All databases initialized successfully")

        # Verify all databases are not None
        failed_dbs = []
        if cache_db is None: failed_dbs.append('cache_db')
        if analytics_db is None: failed_dbs.append('analytics_db')
        if usage_db is None: failed_dbs.append('usage_db')
        if cost_db is None: failed_dbs.append('cost_db')
        if user_limits_db is None: failed_dbs.append('user_limits_db')

        if failed_dbs:
            print(f"❌ Failed to initialize: {failed_dbs}")
        else:
            print("✅ All databases verified as not None")

    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        import traceback
        traceback.print_exc()


def safe_db_operation(db, lock, operation, *args, **kwargs):
    """Perform thread-safe database operation"""
    if db is None:
        print(f"❌ Database is None in safe_db_operation")
        return None

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

def ensure_db_files_exist():
    """Ensure all database files exist"""
    for db_name, file_path in DB_FILES.items():
        if not os.path.exists(file_path):
            print(f"🔧 Creating missing database file: {file_path}")
            try:
                # Create empty JSON database structure
                empty_db = {"_default": {}}
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(empty_db, f, indent=2)
                print(f"✅ Created {file_path}")
            except Exception as e:
                print(f"❌ Failed to create {file_path}: {e}")