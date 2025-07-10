from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

# Load environment variables first
load_dotenv()

# Import our modules
from utils.database import (
    initialize_supabase,
    get_openai_cost_today,
    health_check as db_health_check,
    supabase
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
supabase_client = initialize_supabase()
if supabase_client:
    print("✅ Supabase initialized successfully")
else:
    print("❌ Failed to initialize Supabase - check your .env file")

# Load tools configuration
print("🚀 Starting application...")
load_result = load_all_tools()
print(f"🔍 Tools loaded successfully: {load_result}")


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
        db_health = db_health_check()

        # Get daily budget from settings, with fallback
        daily_budget = getattr(sys.modules.get('config.settings'), 'DAILY_OPENAI_BUDGET', 10.0)

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
        health = db_health_check()

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
    health = db_health_check()
    print(f"  Status: {health['status']}")
    print(f"  Message: {health['message']}")

    # Check tools
    print(f"\n🔧 Tools Status:")
    tools_count = len(tools_config.ALL_TOOLS) if hasattr(tools_config, 'ALL_TOOLS') else 0
    print(f"  Loaded tools: {tools_count}")

    print("\n" + "=" * 50)
    if supabase and env_vars['OPENAI_API_KEY']:
        print("✅ All systems ready!")
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