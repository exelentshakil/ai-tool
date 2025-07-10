from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from dotenv import load_dotenv
import os
import sys
from datetime import datetime, timedelta

# Load environment variables first
load_dotenv()

# Import our enhanced modules
from utils.database import (
    init_supabase,
    get_openai_cost_today,
    get_openai_cost_month,
    get_database_health,
    get_openai_cost_stats,
    get_user_usage_stats,
    check_rate_limit,
    supabase,
    check_connection
)
from utils.rate_limiting import get_remote_address, check_user_limit, is_premium_user, increment_user_usage
from utils.validation import validate_tool_inputs
from utils.ai_analysis import generate_ai_analysis, create_simple_fallback
from utils.tools_config import load_all_tools
from utils import tools_config
from config.settings import *

# ─── ENV & APP SETUP ────────────────────────────────────────────────────────────
app = Flask(__name__)

# Update CORS to include your WordPress site
CORS(app, origins=[
    "https://barakahsoft.com",
    "https://www.barakahsoft.com",
    "https://your-wordpress-site.com",  # Add your actual WordPress domain
    "http://localhost:3000",  # For development
    "http://127.0.0.1:3000"  # For development
])
CORS(app, expose_headers=['Retry-After'])

# Initialize security if available
try:
    from routes.dashboard_routes import dashboard_bp

    app.register_blueprint(dashboard_bp)
    print("✅ Dashboard routes registered")
except ImportError as e:
    print(f"⚠️ Dashboard routes not found: {e}")

try:
    from utils.security import init_security

    security = init_security(app)


    @app.route('/security-status', methods=['GET'])
    def security_status():
        """Public endpoint to check security status"""
        stats = security.get_security_stats()
        return jsonify({
            'security_active': True,
            'blocked_ips_count': stats['blocked_count'],
            'patterns_monitored': stats['patterns_monitored'],
            'status': 'protected'
        })
except ImportError:
    print("⚠️ Security module not found, continuing without it")

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "200 per hour", "50 per minute"]
)
limiter.init_app(app)

# Initialize Supabase database
print("🔍 Initializing Supabase database...")
if init_supabase():
    print("✅ Supabase initialized successfully")
else:
    print("❌ Failed to initialize Supabase - check your .env file")

# Load tools configuration
print("🚀 Starting application...")
load_result = load_all_tools()
print(f"🔍 Tools loaded successfully: {load_result}")


# ─── DASHBOARD API ENDPOINTS ────────────────────────────────────────────────────
@app.route('/api/health', methods=['GET'])
def api_health():
    """Get database health status for dashboard"""
    try:
        health = get_database_health()
        return jsonify(health)
    except Exception as e:
        return jsonify({
            'connection': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/costs/stats', methods=['GET'])
def api_cost_stats():
    """Get cost statistics for dashboard"""
    try:
        today_cost = get_openai_cost_today()
        month_cost = get_openai_cost_month()

        # Calculate week cost (last 7 days)
        week_start = datetime.now() - timedelta(days=7)
        if supabase:
            week_result = supabase.table('openai_costs') \
                .select('cost') \
                .gte('created_at', week_start.isoformat()) \
                .execute()
            week_cost = sum(float(record.get('cost', 0)) for record in week_result.data) if week_result.data else 0
        else:
            week_cost = 0

        # Calculate average cost per request (today)
        if supabase:
            today = datetime.now().strftime('%Y-%m-%d')
            today_result = supabase.table('user_limits') \
                .select('count') \
                .gte('hour_key', today) \
                .execute()
            total_requests = sum(record.get('count', 0) for record in today_result.data) if today_result.data else 0
            average_cost = today_cost / max(1, total_requests)
        else:
            average_cost = 0

        return jsonify({
            'today': today_cost,
            'week': week_cost,
            'month': month_cost,
            'average': average_cost
        })
    except Exception as e:
        app.logger.error(f"Error getting cost stats: {str(e)}")
        return jsonify({
            'today': 0,
            'week': 0,
            'month': 0,
            'average': 0
        }), 500


@app.route('/api/costs/recent', methods=['GET'])
def api_recent_costs():
    """Get recent cost records for dashboard"""
    try:
        limit = request.args.get('limit', 50, type=int)

        if not supabase:
            return jsonify([])

        result = supabase.table('openai_costs') \
            .select('*') \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()

        return jsonify(result.data if result.data else [])
    except Exception as e:
        app.logger.error(f"Error getting recent costs: {str(e)}")
        return jsonify([]), 500


@app.route('/api/users/stats', methods=['GET'])
def api_user_stats():
    """Get user statistics for dashboard"""
    try:
        if not supabase:
            return jsonify({
                'active_24h': 0,
                'total_requests_today': 0,
                'blocked_count': 0
            })

        # Get active users count (users who made requests in last 24h)
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d-%H')

        result = supabase.table('user_limits') \
            .select('ip') \
            .gte('hour_key', yesterday) \
            .execute()

        unique_ips = set(record['ip'] for record in result.data) if result.data else set()

        # Get total requests today
        today = datetime.now().strftime('%Y-%m-%d')
        today_result = supabase.table('user_limits') \
            .select('count') \
            .gte('hour_key', today) \
            .execute()

        total_requests = sum(record.get('count', 0) for record in today_result.data) if today_result.data else 0

        return jsonify({
            'active_24h': len(unique_ips),
            'total_requests_today': total_requests,
            'blocked_count': 0  # TODO: Implement if you have blocked users tracking
        })
    except Exception as e:
        app.logger.error(f"Error getting user stats: {str(e)}")
        return jsonify({
            'active_24h': 0,
            'total_requests_today': 0,
            'blocked_count': 0
        }), 500


@app.route('/api/users', methods=['GET'])
def api_users():
    """Get user list for dashboard"""
    try:
        limit = request.args.get('limit', 100, type=int)

        if not supabase:
            return jsonify([])

        # Get recent user activity
        yesterday = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d-%H')

        result = supabase.table('user_limits') \
            .select('ip, count, hour_key, tools_slug, updated_at') \
            .gte('hour_key', yesterday) \
            .order('updated_at', desc=True) \
            .limit(limit) \
            .execute()

        if not result.data:
            return jsonify([])

        # Process user data
        users_dict = {}
        for record in result.data:
            ip = record['ip']
            if ip not in users_dict:
                users_dict[ip] = {
                    'ip': ip,
                    'status': 'premium' if is_premium_user(ip) else 'guest',
                    'requests_today': 0,
                    'last_seen': record.get('updated_at'),
                    'tools_used': set()
                }

            # Add to today's count if it's today
            today = datetime.now().strftime('%Y-%m-%d')
            if record['hour_key'].startswith(today):
                users_dict[ip]['requests_today'] += record.get('count', 0)

            # Track tools used
            if record.get('tools_slug'):
                users_dict[ip]['tools_used'].add(record['tools_slug'])

            # Update last seen to most recent
            if record.get('updated_at') and record['updated_at'] > users_dict[ip]['last_seen']:
                users_dict[ip]['last_seen'] = record['updated_at']

        # Convert to list and clean up
        users_list = []
        for user in users_dict.values():
            user['tools_used'] = list(user['tools_used'])  # Convert set to list
            users_list.append(user)

        return jsonify(users_list)
    except Exception as e:
        app.logger.error(f"Error getting users: {str(e)}")
        return jsonify([]), 500


@app.route('/api/users/status', methods=['POST'])
def api_update_user_status():
    """Update user status (for blocking/unblocking)"""
    try:
        data = request.json
        ip = data.get('ip')
        status = data.get('status')

        if not ip or not status:
            return jsonify({'error': 'IP and status required'}), 400

        # TODO: Implement user status update in your database
        # For now, just return success
        return jsonify({'success': True, 'message': f'User {ip} status updated to {status}'})

    except Exception as e:
        app.logger.error(f"Error updating user status: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tools/stats', methods=['GET'])
def api_tools_stats():
    """Get tools usage statistics for dashboard"""
    try:
        if not supabase:
            return jsonify([])

        # Get tools usage from last 30 days
        month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d-%H')

        result = supabase.table('user_limits') \
            .select('tools_slug, count, hour_key') \
            .gte('hour_key', month_ago) \
            .execute()

        if not result.data:
            return jsonify([])

        # Process tools data
        tools_stats = {}
        today = datetime.now().strftime('%Y-%m-%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        for record in result.data:
            tool = record.get('tools_slug', 'unknown')
            count = record.get('count', 0)
            hour_key = record.get('hour_key', '')

            if tool not in tools_stats:
                tools_stats[tool] = {
                    'name': tool.title().replace('-', ' '),
                    'tools_slug': tool,
                    'total_uses': 0,
                    'today': 0,
                    'week': 0,
                    'avg_cost': 0
                }

            tools_stats[tool]['total_uses'] += count

            if hour_key.startswith(today):
                tools_stats[tool]['today'] += count
            elif hour_key >= week_ago:
                tools_stats[tool]['week'] += count

        # Get cost data for average calculation
        cost_result = supabase.table('openai_costs') \
            .select('tools_slug, cost') \
            .gte('created_at', f'{month_ago}T00:00:00') \
            .execute()

        if cost_result.data:
            cost_by_tool = {}
            for record in cost_result.data:
                tool = record.get('tools_slug', 'unknown')
                cost = record.get('cost', 0)
                if tool not in cost_by_tool:
                    cost_by_tool[tool] = []
                cost_by_tool[tool].append(cost)

            # Calculate average cost per tool
            for tool, stats in tools_stats.items():
                if tool in cost_by_tool and cost_by_tool[tool]:
                    stats['avg_cost'] = sum(cost_by_tool[tool]) / len(cost_by_tool[tool])

        return jsonify(list(tools_stats.values()))

    except Exception as e:
        app.logger.error(f"Error getting tools stats: {str(e)}")
        return jsonify([]), 500


@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    """Get/update system settings"""
    if request.method == 'POST':
        try:
            settings = request.json
            # TODO: Implement settings storage in database
            return jsonify({'success': True, 'message': 'Settings saved'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        # Return current settings
        return jsonify({
            'daily_budget': float(getattr(sys.modules.get('config.settings'), 'DAILY_OPENAI_BUDGET', 10.0)),
            'hourly_limit': 50,
            'premium_ips': []
        })


# ─── RATE LIMITING ENDPOINTS ───────────────────────────────────────────────────
@app.route('/check-limits', methods=['GET'])
def check_limits():
    """Check current user limits"""
    try:
        ip = get_remote_address()
        is_premium = is_premium_user(ip)
        limit_check = check_user_limit(ip, is_premium)

        return jsonify({
            'success': True,
            'ip': ip,
            'is_premium': is_premium,
            'usage_count': limit_check.get('usage_count', 0),
            'limit': limit_check.get('limit', 50),
            'remaining': limit_check.get('remaining', 0),
            'blocked': limit_check.get('blocked', False),
            'can_ai': limit_check.get('can_ai', True),
            'reset_time': (datetime.now() + timedelta(hours=1)).isoformat()
        })
    except Exception as e:
        app.logger.error(f"Error checking limits: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'usage_count': 0,
            'blocked': False
        })


# ─── MAIN API ENDPOINTS ─────────────────────────────────────────────────────────
@app.route('/process-tool', methods=['POST', 'OPTIONS'])
@limiter.limit("50 per minute")
def process_tool():
    """Main tool processing endpoint with pure AI analysis"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        data = request.json or {}
        tool_slug = data.get("tool", "").strip()
        user_data = data.get("data", {})
        localization = data.get("localization", {})
        request_ai_analysis = data.get("request_ai_analysis", True)
        tool_config_data = data.get("tool_config", {})

        if not tool_slug:
            return jsonify({"error": "Tool parameter required"}), 400

        # Find tool configuration
        tool_config = tools_config.ALL_TOOLS.get(tool_slug)
        if not tool_config:
            for key in tools_config.ALL_TOOLS.keys():
                if tool_slug.lower() in key.lower() or key.lower() in tool_slug.lower():
                    tool_config = tools_config.ALL_TOOLS[key]
                    break

        if not tool_config:
            return jsonify({
                "error": f"Tool '{tool_slug}' not found",
                "available_tools": list(tools_config.ALL_TOOLS.keys())[:10]
            }), 404

        # Merge tool config with request data
        if tool_config_data:
            tool_config.update(tool_config_data)

        ip = get_remote_address()
        limit_check = check_user_limit(ip, is_premium_user(ip))

        # Enhanced logging
        print(f"Processing tool: {tool_slug}")
        print(f"User data keys: {list(user_data.keys())}")
        print(f"Localization: {localization}")
        print(f"AI Analysis requested: {request_ai_analysis}")
        print(f"Rate limit check: {limit_check}")

        # Validate inputs
        category = tool_config.get("category", "general")
        validated_data = validate_tool_inputs(user_data, category)

        # Generate pure AI analysis if not rate limited
        if limit_check.get("can_ai", False) and request_ai_analysis:
            ai_analysis = generate_ai_analysis(tool_config, validated_data, ip, localization)
            increment_user_usage(ip, tool_slug)
        else:
            ai_analysis = create_simple_fallback(tool_config, validated_data, localization)
            if limit_check.get("blocked", False):
                # Add rate limit message in appropriate language
                rate_limit_messages = {
                    'Spanish': f"\n\n**Límite de Tarifa:** {limit_check.get('message', 'Límite por hora alcanzado')}",
                    'French': f"\n\n**Limite de Taux:** {limit_check.get('message', 'Limite horaire atteinte')}",
                    'German': f"\n\n**Rate Limit:** {limit_check.get('message', 'Stündliches Limit erreicht')}",
                    'Italian': f"\n\n**Limite di Velocità:** {limit_check.get('message', 'Limite orario raggiunto')}"
                }
                language = localization.get('language', 'English')
                rate_message = rate_limit_messages.get(language,
                                                       f"\n\n**Rate Limit:** {limit_check.get('message', 'Hourly limit reached')}")
                ai_analysis += rate_message

        is_rate_limited = limit_check.get("blocked", False)

        return jsonify({
            "output": {
                "ai_analysis": ai_analysis,
                "rate_limited": is_rate_limited,
                "localization": localization
            },
            "tool_info": tool_config,
            "user_info": {
                "current_usage": limit_check.get("usage_count", 0),
                "remaining_free": limit_check.get("remaining", 0),
                "is_rate_limited": is_rate_limited,
                "upgrade_available": not is_premium_user(ip),
                "rate_limit_message": limit_check.get("message") if is_rate_limited else None
            },
            "input_data": validated_data
        }), 200

    except Exception as e:
        app.logger.error(f"Process tool error: {str(e)}")
        import traceback
        traceback.print_exc()

        return jsonify({
            "error": "Processing failed",
            "message": "Please check your inputs and try again",
            "error_type": str(type(e).__name__),
            "error_details": str(e)
        }), 500


# Import and register all blueprints
try:
    from routes.tools_routes import tools_bp

    app.register_blueprint(tools_bp)
    print("✅ Tools routes registered")
except ImportError as e:
    print(f"⚠️ Tools routes not found: {e}")

try:
    from routes.admin_routes import admin_bp

    app.register_blueprint(admin_bp)
    print("✅ Admin routes registered")
except ImportError as e:
    print(f"⚠️ Admin routes not found: {e}")

try:
    from routes.face_analysis_routes import face_bp

    app.register_blueprint(face_bp)
    print("✅ Face analysis routes registered")
except ImportError as e:
    print(f"⚠️ Face analysis routes not found: {e}")


# ─── HEALTH CHECK ───────────────────────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        daily_cost = get_openai_cost_today()
        db_health = get_database_health()

        # Get daily budget from settings, with fallback
        daily_budget = float(getattr(sys.modules.get('config.settings'), 'DAILY_OPENAI_BUDGET', 10.0))

        return jsonify({
            "status": "healthy",
            "database": db_health,
            "tools_loaded": len(tools_config.ALL_TOOLS) if hasattr(tools_config, 'ALL_TOOLS') else 0,
            "daily_ai_cost": round(daily_cost, 4),
            "budget_remaining": round(daily_budget - daily_cost, 4),
            "supabase_connected": supabase is not None,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


# ─── DATABASE STATUS ENDPOINT ──────────────────────────────────────────────────
@app.route('/database-status', methods=['GET'])
def database_status():
    """Get detailed database status"""
    try:
        health = get_database_health()

        return jsonify({
            'success': True,
            'database_health': health,
            'supabase_url_configured': bool(os.getenv('SUPABASE_URL')),
            'supabase_key_configured': bool(os.getenv('SUPABASE_KEY')),
            'client_initialized': supabase is not None,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


# ─── FACE ANALYSIS UTILITY ENDPOINTS ───────────────────────────────────────────
@app.route('/face-analysis/limits', methods=['GET'])
def get_face_analysis_limits():
    """Get current face analysis limits for user"""
    try:
        ip = get_remote_address()
        is_premium = is_premium_user(ip)
        limit_check = check_user_limit(ip, is_premium)

        return jsonify({
            'daily_limit': 50 if is_premium else 5,
            'remaining': limit_check.get("remaining", 0),
            'reset_time': (datetime.now() + timedelta(hours=24)).isoformat(),
            'is_premium': is_premium,
            'can_analyze': not limit_check.get("blocked", False)
        })
    except Exception as e:
        app.logger.error(f"Error getting face analysis limits: {str(e)}")
        return jsonify({
            'error': str(e),
            'daily_limit': 5,
            'remaining': 0,
            'can_analyze': False
        }), 500


# ─── ERROR HANDLERS ─────────────────────────────────────────────────────────────
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "error": "Rate limit exceeded",
        "message": "Too many requests. Please try again later.",
        "retry_after": e.retry_after
    }), 429


@app.errorhandler(500)
def internal_error_handler(e):
    return jsonify({
        "error": "Internal server error",
        "message": "Something went wrong on our end"
    }), 500


# ─── STARTUP CHECKS ─────────────────────────────────────────────────────────────
def run_startup_checks():
    """Run startup checks and display status"""
    print("\n" + "=" * 50)
    print("🚀 AI TOOLS API STARTUP")
    print("=" * 50)

    # Check environment variables
    env_vars = {
        'SUPABASE_URL': os.getenv('SUPABASE_URL'),
        'SUPABASE_KEY': os.getenv('SUPABASE_KEY'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')
    }

    print("\n📋 Environment Variables:")
    for var, value in env_vars.items():
        status = "✅" if value else "❌"
        display_value = f"{value[:20]}..." if value and len(value) > 20 else value or "Not set"
        print(f"  {status} {var}: {display_value}")

    # Check database connection
    print(f"\n🗄️ Database Status:")
    health = get_database_health()
    print(f"  Status: {'Connected' if health.get('connection') else 'Disconnected'}")
    print(f"  Supabase: {'✅' if supabase else '❌'}")
    if health.get('tables'):
        print(f"  Tables: {list(health['tables'].keys())}")

    # Check tools
    print(f"\n🔧 Tools Status:")
    tools_count = len(tools_config.ALL_TOOLS) if hasattr(tools_config, 'ALL_TOOLS') else 0
    print(f"  Loaded tools: {tools_count}")

    # Check costs
    print(f"\n💰 Cost Status:")
    try:
        daily_cost = get_openai_cost_today()
        monthly_cost = get_openai_cost_month()
        daily_budget = float(getattr(sys.modules.get('config.settings'), 'DAILY_OPENAI_BUDGET', 10.0))
        print(f"  Today's cost: ${daily_cost:.4f}")
        print(f"  Monthly cost: ${monthly_cost:.4f}")
        print(f"  Daily budget: ${daily_budget:.2f}")
        print(f"  Budget remaining: ${daily_budget - daily_cost:.4f}")
    except Exception as e:
        print(f"  ❌ Error getting costs: {e}")

    print("\n" + "=" * 50)
    if supabase and env_vars['OPENAI_API_KEY']:
        print("✅ All systems ready!")
        print("🌐 Dashboard available at: http://localhost:5000/api/health")
    else:
        print("❌ Some systems need attention - check errors above")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    # Run startup checks
    run_startup_checks()

    # Start the Flask app
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("DEBUG", "True").lower() == "true"
    )