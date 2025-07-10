import os
import json
from datetime import datetime, timedelta
from supabase import create_client, Client
import threading
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── SUPABASE CLIENT ─────────────────────────────────────────────────────────
supabase: Optional[Client] = None
supabase_lock = threading.Lock()


def initialize_supabase():
    """Initialize Supabase client with proper error handling"""
    global supabase

    if supabase is not None:
        return supabase

    with supabase_lock:
        if supabase is not None:
            return supabase

        try:
            # Get from environment variables
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')

            if not supabase_url or not supabase_key:
                logger.error("❌ SUPABASE_URL or SUPABASE_KEY not found in environment variables")
                logger.error("Please add these to your .env file:")
                logger.error("SUPABASE_URL=your_supabase_project_url")
                logger.error("SUPABASE_KEY=your_supabase_anon_key")
                return None

            # Clean URL and key (remove any whitespace)
            supabase_url = supabase_url.strip()
            supabase_key = supabase_key.strip()

            # Create Supabase client with minimal parameters only
            try:
                supabase = create_client(supabase_url, supabase_key)
                logger.info("✅ Supabase client initialized successfully")
            except TypeError as e:
                if "proxy" in str(e):
                    # Fallback for older versions that don't support certain parameters
                    logger.warning("⚠️ Trying alternative Supabase initialization...")
                    from supabase.client import Client
                    from postgrest import APIError
                    supabase = Client(supabase_url, supabase_key)
                    logger.info("✅ Supabase client initialized with fallback method")
                else:
                    raise e

            # Test connection
            try:
                result = supabase.table('user_limits').select('*').limit(1).execute()
                logger.info("✅ Supabase connection test successful")
            except Exception as e:
                logger.error(f"❌ Supabase connection test failed: {str(e)}")
                logger.error("Make sure your Supabase tables are created")

            return supabase

        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error("Try reinstalling supabase: pip install --force-reinstall supabase==2.0.0")
            return None


# Initialize on import
supabase = initialize_supabase()


# ─── USER LIMITS FUNCTIONS ──────────────────────────────────────────────────
def get_user_usage_current_hour(ip: str) -> int:
    """Get current hour usage for a user"""
    if not supabase:
        logger.error("❌ Supabase not initialized, returning 0 usage")
        return 0

    try:
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')

        result = supabase.table('user_limits').select('count').eq('ip', ip).eq('hour_key', current_hour).execute()

        if result.data:
            return result.data[0]['count']
        return 0

    except Exception as e:
        logger.error(f"❌ Error getting user usage: {str(e)}")
        return 0


def increment_user_usage(ip: str) -> bool:
    """Increment user usage for current hour"""
    if not supabase:
        logger.error("❌ Supabase not initialized, cannot increment usage")
        return False

    try:
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')
        current_usage = get_user_usage_current_hour(ip)

        # Upsert (insert or update)
        data = {
            'ip': ip,
            'hour_key': current_hour,
            'count': current_usage + 1,
            'updated_at': datetime.now().isoformat()
        }

        result = supabase.table('user_limits').upsert(data, on_conflict='ip,hour_key').execute()

        if result.data:
            logger.info(f"✅ User usage incremented for {ip}")
            return True
        return False

    except Exception as e:
        logger.error(f"❌ Error incrementing user usage: {str(e)}")
        return False


def get_current_hour_users() -> int:
    """Get number of unique users in current hour"""
    if not supabase:
        logger.error("❌ Supabase not initialized, returning 0 users")
        return 0

    try:
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')

        result = supabase.table('user_limits').select('ip').eq('hour_key', current_hour).execute()

        if result.data:
            return len(result.data)
        return 0

    except Exception as e:
        logger.error(f"❌ Error getting current hour users: {str(e)}")
        return 0


# ─── OPENAI COST TRACKING ───────────────────────────────────────────────────
def log_openai_cost(cost: float, tokens: int, model: str = "gpt-4o-mini") -> bool:
    """Log OpenAI API cost"""
    if not supabase:
        logger.error("❌ Supabase not initialized, cannot log cost")
        return False

    try:
        data = {
            'cost': cost,
            'tokens': tokens,
            'model': model,
            'date': datetime.now().date().isoformat(),
            'timestamp': datetime.now().isoformat()
        }

        result = supabase.table('openai_costs').insert(data).execute()

        if result.data:
            logger.info(f"✅ OpenAI cost logged: ${cost:.6f}")
            return True
        return False

    except Exception as e:
        logger.error(f"❌ Error logging OpenAI cost: {str(e)}")
        return False


def get_openai_cost_today() -> float:
    """Get today's OpenAI costs"""
    if not supabase:
        logger.error("❌ Supabase not initialized, returning 0 cost")
        return 0.0

    try:
        today = datetime.now().date().isoformat()

        result = supabase.table('openai_costs').select('cost').eq('date', today).execute()

        if result.data:
            return sum(row['cost'] for row in result.data)
        return 0.0

    except Exception as e:
        logger.error(f"❌ Error getting today's costs: {str(e)}")
        return 0.0


def get_openai_cost_month() -> float:
    """Get this month's OpenAI costs"""
    if not supabase:
        logger.error("❌ Supabase not initialized, returning 0 cost")
        return 0.0

    try:
        # Get first day of current month
        first_day = datetime.now().replace(day=1).date().isoformat()

        result = supabase.table('openai_costs').select('cost').gte('date', first_day).execute()

        if result.data:
            return sum(row['cost'] for row in result.data)
        return 0.0

    except Exception as e:
        logger.error(f"❌ Error getting month's costs: {str(e)}")
        return 0.0


# ─── DATABASE STATISTICS ────────────────────────────────────────────────────
def get_database_stats() -> Dict[str, Any]:
    """Get database statistics"""
    if not supabase:
        logger.error("❌ Supabase not initialized, returning empty stats")
        return {
            'total_users': 0,
            'total_requests': 0,
            'today_cost': 0.0,
            'month_cost': 0.0,
            'current_hour_users': 0
        }

    try:
        # Get total unique users
        users_result = supabase.table('user_limits').select('ip').execute()
        unique_users = len(set(row['ip'] for row in users_result.data)) if users_result.data else 0

        # Get total requests
        requests_result = supabase.table('user_limits').select('count').execute()
        total_requests = sum(row['count'] for row in requests_result.data) if requests_result.data else 0

        stats = {
            'total_users': unique_users,
            'total_requests': total_requests,
            'today_cost': get_openai_cost_today(),
            'month_cost': get_openai_cost_month(),
            'current_hour_users': get_current_hour_users()
        }

        logger.info(f"✅ Database stats retrieved: {stats}")
        return stats

    except Exception as e:
        logger.error(f"❌ Error getting database stats: {str(e)}")
        return {
            'total_users': 0,
            'total_requests': 0,
            'today_cost': 0.0,
            'month_cost': 0.0,
            'current_hour_users': 0
        }


def clean_old_cache():
    """Clean old cache entries (older than 7 days)"""
    if not supabase:
        logger.error("❌ Supabase not initialized, cannot clean cache")
        return False

    try:
        # Calculate 7 days ago
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        # Delete old user limits
        result = supabase.table('user_limits').delete().lt('hour_key', seven_days_ago).execute()

        deleted_count = len(result.data) if result.data else 0
        logger.info(f"✅ Cleaned {deleted_count} old cache entries")
        return True

    except Exception as e:
        logger.error(f"❌ Error cleaning old cache: {str(e)}")
        return False


# ─── HEALTH CHECK ───────────────────────────────────────────────────────────
def health_check() -> Dict[str, Any]:
    """Check database health"""
    try:
        if not supabase:
            return {
                'status': 'error',
                'message': 'Supabase client not initialized',
                'suggestions': [
                    'Check SUPABASE_URL in .env file',
                    'Check SUPABASE_KEY in .env file',
                    'Verify Supabase project is active'
                ]
            }

        # Test connection
        result = supabase.table('user_limits').select('*').limit(1).execute()

        return {
            'status': 'healthy',
            'message': 'Database connection successful',
            'tables': ['user_limits', 'openai_costs']
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Database connection failed: {str(e)}',
            'suggestions': [
                'Check internet connection',
                'Verify Supabase project status',
                'Check if tables exist in Supabase'
            ]
        }


# ─── INITIALIZATION CHECK ───────────────────────────────────────────────────
if __name__ == "__main__":
    print("🔍 Testing Supabase connection...")
    health = health_check()
    print(f"Status: {health['status']}")
    print(f"Message: {health['message']}")
    if 'suggestions' in health:
        print("Suggestions:")
        for suggestion in health['suggestions']:
            print(f"  - {suggestion}")