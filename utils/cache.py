import hashlib
from datetime import datetime, timedelta
from tinydb import Query
from utils.database import cache_db, cache_lock, safe_db_operation

Q = Query()

def get_cache_key(tool, input_text):
    """Generate cache key from tool and input"""
    combined = f"{tool}:{input_text.lower().strip()}"
    return hashlib.sha256(combined.encode()).hexdigest()

def check_cache(tool, input_text):
    """Check if result exists in cache"""
    key = get_cache_key(tool, input_text)
    rec = safe_db_operation(cache_db, cache_lock, cache_db.get, Q.key == key)
    return rec["output"] if rec else None

def store_cache(tool, input_text, output):
    """Store result in cache"""
    key = get_cache_key(tool, input_text)
    data = {
        "key": key,
        "output": output,
        "tool": tool,
        "created_at": datetime.now().isoformat()
    }
    safe_db_operation(cache_db, cache_lock, cache_db.upsert, data, Q.key == key)

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

def get_cache_stats():
    """Get cache statistics"""
    all_entries = safe_db_operation(cache_db, cache_lock, cache_db.all) or []
    return {
        "total_entries": len(all_entries),
        "cache_size_mb": sum(len(str(entry.get('output', ''))) for entry in all_entries) / (1024 * 1024),
        "oldest_entry": min([entry.get('created_at', '') for entry in all_entries]) if all_entries else None,
        "newest_entry": max([entry.get('created_at', '') for entry in all_entries]) if all_entries else None
    }

def clear_all_cache():
    """Clear all cache entries"""
    try:
        safe_db_operation(cache_db, cache_lock, cache_db.truncate)
        print("All cache entries cleared")
        return True
    except Exception as e:
        print(f"Error clearing cache: {e}")
        return False