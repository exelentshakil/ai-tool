import os
import json
from datetime import datetime, timedelta
from supabase import create_client, Client
import threading
from config.settings import SUPABASE_URL, SUPABASE_KEY

# ─── SUPABASE CLIENT ────────────────────────────────────────────────────────────
supabase: Client = None
db_lock = threading.Lock()


def init_databases():
    """Initialize Supabase client"""
    global supabase

    try:
        # Get credentials from environment
        url = os.getenv('SUPABASE_URL', SUPABASE_URL)
        key = os.getenv('SUPABASE_KEY', SUPABASE_KEY)

        if not url or not key:
            print("❌ Missing Supabase credentials in .env")
            print("Add SUPABASE_URL and SUPABASE_KEY to your .env file")
            return False

        supabase = create_client(url, key)
        print("✅ Supabase client initialized successfully")

        # Test connection
        test_connection()
        return True

    except Exception as e:
        print(f"❌ Failed to initialize Supabase: {e}")
        return False


def test_connection():
    """Test Supabase connection"""
    try:
        # Try to read from a table (this will fail gracefully if table doesn't exist)
        result = supabase.table('user_limits').select('*').limit(1).execute()
        print("✅ Supabase connection test successful")
        return True
    except Exception as e:
        print(f"⚠️ Supabase connection test: {e}")
        # This is OK - tables might not exist yet
        return True


def safe_db_operation(operation_func, table_name, *args, **kwargs):
    """Perform thread-safe database operation"""
    if supabase is None:
        print(f"❌ Supabase client is None")
        return None

    with db_lock:
        try:
            return operation_func(*args, **kwargs)
        except Exception as e:
            print(f"❌ Database operation failed on {table_name}: {e}")
            return None


# ─── COST TRACKING FUNCTIONS ────────────────────────────────────────────────────
def get_openai_cost_today():
    """Get today's OpenAI costs"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        result = supabase.table('openai_costs').select('cost').eq('date', today).execute()

        if result.data:
            return sum(row['cost'] for row in result.data)
        return 0.0
    except Exception as e:
        print(f"❌ Error getting today's costs: {e}")
        return 0.0


def get_openai_cost_month():
    """Get this month's OpenAI costs"""
    try:
        this_month = datetime.now().strftime("%Y-%m")
        result = supabase.table('openai_costs').select('cost').like('date', f'{this_month}%').execute()

        if result.data:
            return sum(row['cost'] for row in result.data)
        return 0.0
    except Exception as e:
        print(f"❌ Error getting month's costs: {e}")
        return 0.0


def log_openai_cost(tool_slug, prompt_tokens, completion_tokens, cost):
    """Log OpenAI API costs"""
    try:
        data = {
            "tool": tool_slug,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost": cost,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat()
        }

        result = supabase.table('openai_costs').insert(data).execute()
        if result.data:
            print(f"✅ Logged OpenAI cost: ${cost:.4f}")
        return True
    except Exception as e:
        print(f"❌ Error logging OpenAI cost: {e}")
        return False


# ─── USAGE TRACKING FUNCTIONS ───────────────────────────────────────────────────
def get_user_usage_current_hour(ip):
    """Get user usage for current hour"""
    try:
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')

        result = supabase.table('user_limits').select('count').eq('ip', ip).eq('hour_key', current_hour).execute()

        if result.data:
            return result.data[0]['count']
        return 0
    except Exception as e:
        print(f"❌ Error getting user usage: {e}")
        return 0


def increment_user_usage(ip, tool_slug):
    """Increment user usage for current hour"""
    try:
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')
        current_count = get_user_usage_current_hour(ip)

        data = {
            "ip": ip,
            "hour_key": current_hour,
            "count": current_count + 1,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "hour": datetime.now().strftime("%H"),
            "last_used": datetime.now().isoformat(),
            "last_tool": tool_slug
        }

        # Use upsert to update if exists, insert if not
        result = supabase.table('user_limits').upsert(data, on_conflict='ip,hour_key').execute()

        if result.data:
            print(f"✅ Incremented usage for {ip}: {current_count + 1}")
            return True
        return False
    except Exception as e:
        print(f"❌ Error incrementing user usage: {e}")
        return False


# ─── USAGE LOGGING FUNCTIONS ────────────────────────────────────────────────────
def log_usage(tool, input_length, cached=False, ip_address=None):
    """Log tool usage"""
    try:
        data = {
            "tool": tool,
            "input_length": input_length,
            "cached": cached,
            "ip_address": ip_address,
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d")
        }

        result = supabase.table('usage_logs').insert(data).execute()
        return bool(result.data)
    except Exception as e:
        print(f"❌ Error logging usage: {e}")
        return False


# ─── ANALYTICS FUNCTIONS ────────────────────────────────────────────────────────
def log_analytics(event, data=None):
    """Log analytics event"""
    try:
        entry = {
            "event": event,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d")
        }

        result = supabase.table('analytics').insert(entry).execute()
        return bool(result.data)
    except Exception as e:
        print(f"❌ Error logging analytics: {e}")
        return False


# ─── DATABASE MAINTENANCE ───────────────────────────────────────────────────────
def clean_old_cache(hours=24):
    """Clean old cache entries"""
    try:
        cutoff = datetime.now() - timedelta(hours=hours)

        result = supabase.table('cache').delete().lt('created_at', cutoff.isoformat()).execute()
        count = len(result.data) if result.data else 0

        print(f"Cleaned {count} old cache entries")
        return count
    except Exception as e:
        print(f"❌ Cache cleanup error: {e}")
        return 0


def get_database_stats():
    """Get database statistics"""
    try:
        stats = {}

        # Get count for each table
        tables = ['user_limits', 'usage_logs', 'openai_costs', 'analytics', 'cache']

        for table in tables:
            try:
                result = supabase.table(table).select('id', count='exact').execute()
                stats[f"{table}_entries"] = result.count if hasattr(result, 'count') else 0
            except:
                stats[f"{table}_entries"] = 0

        return stats
    except Exception as e:
        print(f"❌ Error getting database stats: {e}")
        return {}


# ─── CACHE FUNCTIONS ────────────────────────────────────────────────────────────
def check_cache(tool_slug, cache_key):
    """Check if result is cached"""
    try:
        result = supabase.table('cache').select('result').eq('tool', tool_slug).eq('cache_key', cache_key).execute()

        if result.data:
            return result.data[0]['result']
        return None
    except Exception as e:
        print(f"❌ Error checking cache: {e}")
        return None


def store_cache(tool_slug, cache_key, result):
    """Store result in cache"""
    try:
        data = {
            "tool": tool_slug,
            "cache_key": cache_key,
            "result": result,
            "created_at": datetime.now().isoformat()
        }

        result = supabase.table('cache').insert(data).execute()
        return bool(result.data)
    except Exception as e:
        print(f"❌ Error storing cache: {e}")
        return False