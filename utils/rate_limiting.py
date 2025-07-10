from flask import request
from datetime import datetime, timedelta
from utils.database import supabase, get_user_usage_current_hour, increment_user_usage
from config.settings import HOURLY_FREE_LIMIT, RESET_MINUTE, PREMIUM_IPS

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

def check_user_limit(ip, is_premium=False):
    """Check hourly user limit with Supabase"""
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