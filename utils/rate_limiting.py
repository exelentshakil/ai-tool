from flask import request
from datetime import datetime, timedelta
from utils.database import supabase, get_user_usage_current_hour, increment_user_usage
from config.settings import HOURLY_FREE_LIMIT, RESET_MINUTE, PREMIUM_IPS
from database import is_ip_blocked, log_tool_usage

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

def check_user_limit(ip, is_premium=False):
    """Check user rate limits with IP blocking"""
    # First check if IP is blocked - earliest exit point
    if is_ip_blocked(ip):
        return {
            "blocked": True,
            "can_ai": False,
            "message": "IP address blocked for policy violations",
            "usage_count": 0,
            "remaining": 0,
            "reason": "ip_blocked"
        }

    # Continue with existing rate limit logic
    if not supabase:
        return {"blocked": False, "can_ai": True, "usage_count": 0, "remaining": 50}

    try:
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')

        result = supabase.table('user_limits').select('*').eq('ip', ip).eq('hour_key', current_hour).execute()

        if result.data:
            usage_count = result.data[0]['count']
        else:
            usage_count = 0

        # Set limits based on user type
        if is_premium:
            hourly_limit = 1000  # Premium users get higher limits
        else:
            hourly_limit = int(os.getenv('HOURLY_FREE_LIMIT', '50'))

        remaining = max(0, hourly_limit - usage_count)
        is_rate_limited = usage_count >= hourly_limit

        return {
            "blocked": is_rate_limited,
            "can_ai": not is_rate_limited,
            "usage_count": usage_count,
            "remaining": remaining,
            "limit": hourly_limit,
            "message": f"Rate limit exceeded. {remaining} requests remaining this hour." if is_rate_limited else None,
            "reason": "rate_limit" if is_rate_limited else None
        }

    except Exception as e:
        print(f"Error checking user limit: {e}")
        return {"blocked": False, "can_ai": True, "usage_count": 0, "remaining": 50}