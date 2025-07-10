"""
Enhanced Database Operations Module
Handles all Supabase database interactions with comprehensive error handling,
logging, and debugging capabilities.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Union
from supabase import create_client, Client
from config.settings import SUPABASE_URL, SUPABASE_KEY

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Optional[Client] = None


def init_supabase() -> bool:
    """Initialize Supabase client with error handling"""
    global supabase

    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.error("❌ Supabase credentials not found in environment")
            return False

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Supabase client initialized successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to initialize Supabase: {str(e)}")
        return False


def check_connection() -> bool:
    """Test database connection"""
    if not supabase:
        logger.warning("⚠️ Supabase not initialized")
        return False

    try:
        # Simple query to test connection
        result = supabase.table('user_limits').select('count(*)').limit(1).execute()
        logger.info("✅ Database connection verified")
        return True

    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        return False


# =============================================================================
# OPENAI COST TRACKING
# =============================================================================

def log_openai_cost(cost: float, tokens: int, model: str = "gpt-4o-mini",
                    ip: str = None, tools_slug: str = None) -> bool:
    """
    Log OpenAI API cost and token usage

    Args:
        cost: API cost in USD
        tokens: Total tokens used (prompt + completion)
        model: OpenAI model name
        ip: User IP address (optional)
        tools_slug: Tool identifier (optional)

    Returns:
        bool: Success status
    """
    if not supabase:
        logger.error("❌ Supabase not initialized, cannot log cost")
        return False

    try:
        data = {
            'cost': round(float(cost), 8),  # Round to prevent precision issues
            'tokens': int(tokens),
            'model': str(model),
            'created_at': datetime.now().isoformat()
        }

        # Add optional fields if provided
        if ip:
            data['ip'] = str(ip)
        if tools_slug:
            data['tools_slug'] = str(tools_slug)

        result = supabase.table('openai_costs').insert(data).execute()

        if result.data:
            logger.info(f"✅ OpenAI cost logged: ${cost:.6f} ({tokens} tokens, {model})")
            return True
        else:
            logger.warning("⚠️ OpenAI cost insert returned no data")
            return False

    except Exception as e:
        logger.error(f"❌ Error logging OpenAI cost: {str(e)}")
        return False


def get_openai_cost_today() -> float:
    """Get total OpenAI cost for today"""
    if not supabase:
        logger.error("❌ Supabase not initialized, cannot get cost")
        return 0.0

    try:
        today = datetime.now().date().isoformat()

        result = supabase.table('openai_costs') \
            .select('cost') \
            .gte('created_at', f'{today}T00:00:00') \
            .lte('created_at', f'{today}T23:59:59') \
            .execute()

        if result.data:
            total_cost = sum(float(record.get('cost', 0)) for record in result.data)
            logger.debug(f"📊 Today's OpenAI cost: ${total_cost:.6f}")
            return total_cost

        logger.debug("📊 No OpenAI costs found for today")
        return 0.0

    except Exception as e:
        logger.error(f"❌ Error getting today's OpenAI cost: {str(e)}")
        return 0.0


def get_openai_cost_month() -> float:
    """Get total OpenAI cost for current month"""
    if not supabase:
        logger.error("❌ Supabase not initialized, cannot get cost")
        return 0.0

    try:
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        result = supabase.table('openai_costs') \
            .select('cost') \
            .gte('created_at', month_start.isoformat()) \
            .execute()

        if result.data:
            total_cost = sum(float(record.get('cost', 0)) for record in result.data)
            logger.debug(f"📊 This month's OpenAI cost: ${total_cost:.6f}")
            return total_cost

        logger.debug("📊 No OpenAI costs found for this month")
        return 0.0

    except Exception as e:
        logger.error(f"❌ Error getting month's OpenAI cost: {str(e)}")
        return 0.0


def get_openai_cost_stats() -> Dict[str, Any]:
    """Get comprehensive OpenAI cost statistics"""
    return {
        'today': get_openai_cost_today(),
        'month': get_openai_cost_month(),
        'connection_status': check_connection()
    }


# =============================================================================
# USER LIMITS & RATE LIMITING
# =============================================================================

def get_user_usage_current_hour(ip: str, tools_slug: str = None) -> int:
    """
    Get user usage for current hour, optionally filtered by tool

    Args:
        ip: User IP address
        tools_slug: Optional tool filter

    Returns:
        int: Usage count for current hour
    """
    if not supabase:
        logger.error("❌ Supabase not initialized, cannot get usage")
        return 0

    try:
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')

        query = supabase.table('user_limits') \
            .select('count') \
            .eq('ip', ip) \
            .eq('hour_key', current_hour)

        # Add tool filter if specified
        if tools_slug:
            query = query.eq('tools_slug', tools_slug)

        result = query.execute()

        if result.data:
            total_usage = sum(int(record.get('count', 0)) for record in result.data)
            logger.debug(f"📊 Current hour usage for {ip}: {total_usage}")
            return total_usage

        logger.debug(f"📊 No usage found for {ip} in current hour")
        return 0

    except Exception as e:
        logger.error(f"❌ Error getting user usage: {str(e)}")
        return 0


def increment_user_usage(ip: str, tools_slug: str = None, increment_by: int = 1) -> bool:
    """
    Increment user usage for current hour

    Args:
        ip: User IP address
        tools_slug: Optional tool identifier
        increment_by: Amount to increment (default: 1)

    Returns:
        bool: Success status
    """
    if not supabase:
        logger.error("❌ Supabase not initialized, cannot increment usage")
        return False

    try:
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')
        current_usage = get_user_usage_current_hour(ip, tools_slug)

        data = {
            'ip': str(ip),
            'hour_key': current_hour,
            'count': current_usage + increment_by,
            'updated_at': datetime.now().isoformat()
        }

        # Add tools_slug if provided
        if tools_slug:
            data['tools_slug'] = str(tools_slug)

        result = supabase.table('user_limits').upsert(data).execute()

        if result.data:
            tool_info = f" (tool: {tools_slug})" if tools_slug else ""
            logger.info(f"✅ Usage incremented for {ip}: +{increment_by}{tool_info}")
            return True
        else:
            logger.warning(f"⚠️ Usage increment returned no data for {ip}")
            return False

    except Exception as e:
        logger.error(f"❌ Error incrementing user usage for {ip}: {str(e)}")
        return False


def get_user_usage_stats(ip: str, hours_back: int = 24) -> Dict[str, Any]:
    """
    Get comprehensive usage statistics for a user

    Args:
        ip: User IP address
        hours_back: How many hours back to analyze

    Returns:
        Dict with usage statistics
    """
    if not supabase:
        logger.error("❌ Supabase not initialized, cannot get stats")
        return {}

    try:
        start_time = datetime.now() - timedelta(hours=hours_back)
        start_hour = start_time.strftime('%Y-%m-%d-%H')

        result = supabase.table('user_limits') \
            .select('*') \
            .eq('ip', ip) \
            .gte('hour_key', start_hour) \
            .execute()

        if not result.data:
            return {
                'current_hour': 0,
                'total_24h': 0,
                'by_tool': {},
                'by_hour': {}
            }

        # Process the data
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')
        current_hour_usage = 0
        total_usage = 0
        by_tool = {}
        by_hour = {}

        for record in result.data:
            count = int(record.get('count', 0))
            hour_key = record.get('hour_key', '')
            tool = record.get('tools_slug', 'unknown')

            total_usage += count

            if hour_key == current_hour:
                current_hour_usage += count

            # Group by tool
            by_tool[tool] = by_tool.get(tool, 0) + count

            # Group by hour
            by_hour[hour_key] = by_hour.get(hour_key, 0) + count

        return {
            'current_hour': current_hour_usage,
            'total_24h': total_usage,
            'by_tool': by_tool,
            'by_hour': by_hour
        }

    except Exception as e:
        logger.error(f"❌ Error getting usage stats for {ip}: {str(e)}")
        return {}


def check_rate_limit(ip: str, limit: int = 50, tools_slug: str = None) -> Dict[str, Any]:
    """
    Check if user has exceeded rate limit

    Args:
        ip: User IP address
        limit: Hourly limit
        tools_slug: Optional tool-specific check

    Returns:
        Dict with rate limit status
    """
    current_usage = get_user_usage_current_hour(ip, tools_slug)
    remaining = max(0, limit - current_usage)
    is_limited = current_usage >= limit

    tool_info = f" for {tools_slug}" if tools_slug else ""

    if is_limited:
        logger.warning(f"⚠️ Rate limit exceeded for {ip}{tool_info}: {current_usage}/{limit}")
    else:
        logger.debug(f"📊 Rate limit OK for {ip}{tool_info}: {current_usage}/{limit}")

    return {
        'is_limited': is_limited,
        'current_usage': current_usage,
        'limit': limit,
        'remaining': remaining,
        'percentage_used': (current_usage / limit) * 100 if limit > 0 else 0
    }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def cleanup_old_records(days_to_keep: int = 30) -> Dict[str, int]:
    """
    Clean up old records from database tables

    Args:
        days_to_keep: Number of days to retain

    Returns:
        Dict with cleanup results
    """
    if not supabase:
        logger.error("❌ Supabase not initialized, cannot cleanup")
        return {}

    try:
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        results = {}

        # Cleanup openai_costs
        try:
            result = supabase.table('openai_costs') \
                .delete() \
                .lt('created_at', cutoff_date) \
                .execute()
            results['openai_costs_deleted'] = len(result.data) if result.data else 0
        except Exception as e:
            logger.error(f"❌ Error cleaning openai_costs: {str(e)}")
            results['openai_costs_deleted'] = 0

        # Cleanup user_limits (convert hour_key to date for comparison)
        try:
            # This is more complex since hour_key is a string format
            # We'll need to be more careful here
            cutoff_hour = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d-%H')
            result = supabase.table('user_limits') \
                .delete() \
                .lt('hour_key', cutoff_hour) \
                .execute()
            results['user_limits_deleted'] = len(result.data) if result.data else 0
        except Exception as e:
            logger.error(f"❌ Error cleaning user_limits: {str(e)}")
            results['user_limits_deleted'] = 0

        total_deleted = sum(results.values())
        logger.info(f"✅ Cleanup completed: {total_deleted} records deleted")

        return results

    except Exception as e:
        logger.error(f"❌ Error during cleanup: {str(e)}")
        return {}


def get_database_health() -> Dict[str, Any]:
    """Get comprehensive database health information"""
    health = {
        'connection': check_connection(),
        'supabase_initialized': supabase is not None,
        'timestamp': datetime.now().isoformat()
    }

    if health['connection']:
        try:
            # Get table counts
            tables_info = {}

            for table in ['openai_costs', 'user_limits']:
                try:
                    result = supabase.table(table).select('count(*)', count='exact').execute()
                    tables_info[table] = {
                        'count': result.count if hasattr(result, 'count') else 0,
                        'status': 'healthy'
                    }
                except Exception as e:
                    tables_info[table] = {
                        'count': 0,
                        'status': f'error: {str(e)}'
                    }

            health['tables'] = tables_info
            health['cost_stats'] = get_openai_cost_stats()

        except Exception as e:
            health['error'] = str(e)

    return health


def log_database_operation(operation: str, table: str, data: Dict = None,
                           success: bool = True, error: str = None):
    """Log database operations for debugging"""
    log_level = logging.INFO if success else logging.ERROR
    status = "✅" if success else "❌"

    message = f"{status} DB Operation: {operation} on {table}"

    if data:
        # Log first few fields for debugging without exposing sensitive data
        safe_data = {k: v for k, v in list(data.items())[:3]}
        message += f" with data: {safe_data}"

    if error:
        message += f" - Error: {error}"

    logger.log(log_level, message)


# Initialize on import
if not supabase:
    init_supabase()