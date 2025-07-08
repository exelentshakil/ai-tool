from flask import request
from datetime import datetime, timedelta
from tinydb import Query
from utils.database import user_limits_db, user_limits_lock, safe_db_operation
from config.settings import HOURLY_FREE_LIMIT, RESET_MINUTE, PREMIUM_IPS

Q = Query()


def get_remote_address():
    """Get the real client IP address, handling proxies"""
    headers_to_check = [
        'X-Forwarded-For', 'X-Real-IP', 'X-Client-IP', 'CF-Connecting-IP',
        'X-Forwarded', 'Forwarded-For', 'Forwarded'
    ]

    for header in headers_to_check:
        ip = request.headers.get(header)
        if ip:
            if ',' in ip:
                ip = ip.split(',')[0].strip()
            if ip and ip != '127.0.0.1' and ip != 'localhost':
                return ip

    return request.environ.get('REMOTE_ADDR', '127.0.0.1')


def get_user_limit_key(ip):
    """Generate hourly limit key based on current hour"""
    now = datetime.now()
    hour_key = now.strftime("%Y-%m-%d:%H")
    return f"{ip}:{hour_key}"


def get_user_usage_current_hour(ip):
    """Get user usage for current hour with safety checks"""
    if user_limits_db is None:
        print("❌ user_limits_db is None, returning 0 usage")
        return 0

    current_hour = datetime.now().strftime('%Y-%m-%d-%H')
    key = f"{ip}_{current_hour}"

    try:
        rec = safe_db_operation(
            user_limits_db,
            user_limits_lock,
            lambda db: db.get(Q.key == key)
        )
        return rec['count'] if rec else 0
    except Exception as e:
        print(f"❌ Error getting user usage: {e}")
        return 0


def increment_user_usage(ip, tool_slug):
    """Increment user usage for current hour with safety checks"""
    if user_limits_db is None:
        print("❌ user_limits_db is None, cannot increment usage")
        return False

    try:
        key = get_user_limit_key(ip)
        current = get_user_usage_current_hour(ip)

        data = {
            "key": key,
            "ip": ip,
            "count": current + 1,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "hour": datetime.now().strftime("%H"),
            "last_used": datetime.now().isoformat(),
            "last_tool": tool_slug
        }

        result = safe_db_operation(user_limits_db, user_limits_lock, user_limits_db.upsert, data, Q.key == key)
        if result is None:
            print("❌ Failed to increment user usage")
            return False

        print(f"✅ Incremented usage for {ip}: {current + 1}")
        return True

    except Exception as e:
        print(f"❌ Error incrementing user usage: {e}")
        return False


def check_user_limit(ip, is_premium=False):
    """Check hourly user limit with safety checks"""
    try:
        usage = get_user_usage_current_hour(ip)
        limit = HOURLY_FREE_LIMIT
        limit_display = "unlimited" if is_premium else limit

        if not is_premium and usage >= limit:
            reset = datetime.now().replace(minute=RESET_MINUTE, second=0, microsecond=0) + timedelta(hours=1)
            minutes_until_reset = max(1, int((reset - datetime.now()).total_seconds() / 60))

            return {
                "blocked": True,
                "message": f"You've reached your hourly limit of {limit} analyses. Limit resets in {minutes_until_reset} minutes.",
                "minutes_until_reset": minutes_until_reset,
                "can_calculate": True,
                "can_ai": False,
                "usage_count": usage,
                "limit": limit_display
            }

        return {
            "blocked": False,
            "can_calculate": True,
            "can_ai": True,
            "usage_count": usage,
            "limit": limit_display,
            "remaining": "unlimited" if is_premium else limit - usage
        }

    except Exception as e:
        print(f"❌ Error in check_user_limit: {e}")
        # Return safe fallback
        return {
            "blocked": False,
            "can_calculate": True,
            "can_ai": True,
            "usage_count": 0,
            "limit": "unknown",
            "remaining": "unknown",
            "error": str(e)
        }


def is_premium_user(ip):
    """Check if user is premium"""
    return ip in PREMIUM_IPS and ip != ""


def get_reset_time():
    """Get the next reset time"""
    now = datetime.now()
    reset = now.replace(minute=RESET_MINUTE, second=0, microsecond=0) + timedelta(hours=1)
    return reset


def get_user_response_mode(ip, current_usage):
    """Get user response mode based on hourly usage"""
    from config.settings import ResponseMode, HOURLY_BASIC_LIMIT

    if is_premium_user(ip):
        return ResponseMode.FULL_AI

    hourly_usage = get_user_usage_current_hour(ip)

    if hourly_usage < HOURLY_FREE_LIMIT:
        return ResponseMode.SMART_AI
    elif hourly_usage < HOURLY_BASIC_LIMIT:
        return ResponseMode.BASIC_AI
    else:
        return ResponseMode.SMART_AI


def get_hourly_usage_stats(ip):
    """Get detailed hourly usage statistics"""
    current_usage = get_user_usage_current_hour(ip)
    reset_time = get_reset_time()
    now = datetime.now()

    return {
        "current_hour_usage": current_usage,
        "hourly_limit": HOURLY_FREE_LIMIT,
        "remaining_requests": max(0, HOURLY_FREE_LIMIT - current_usage),
        "reset_time": reset_time.isoformat(),
        "minutes_until_reset": max(1, int((reset_time - now).total_seconds() / 60)),
        "is_premium": is_premium_user(ip)
    }