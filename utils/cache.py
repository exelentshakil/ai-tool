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
        old_entries = safe_db_operation(cache_db