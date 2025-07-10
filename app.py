# Add this to your existing app.py file

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from dotenv import load_dotenv
import os
from datetime import datetime

# Import our modules
from utils.database import init_databases, get_openai_cost_today
from utils.rate_limiting import get_remote_address, check_user_limit, is_premium_user, increment_user_usage
from utils.validation import validate_tool_inputs
from utils.ai_analysis import generate_ai_analysis, create_fallback_response
from utils.tools_config import load_all_tools
from utils import tools_config
from config.settings import *

# ─── ENV & APP SETUP ────────────────────────────────────────────────────────────
load_dotenv()
app = Flask(__name__)

# Update CORS to include your WordPress site
CORS(app, origins=[
    "https://barakahsoft.com",
    "https://www.barakahsoft.com",
    "https://your-wordpress-site.com"  # Add your actual WordPress domain
])
CORS(app, expose_headers=['Retry-After'])

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "200 per hour", "50 per minute"]
)
limiter.init_app(app)

# Initialize databases
init_databases()

# At the top of your main application file
print("🚀 Starting application...")
load_result = load_all_tools()
print(f"🔍 Tools loaded successfully: {load_result}")


# ─── MAIN API ENDPOINTS ─────────────────────────────────────────────────────────
@app.route('/process-tool', methods=['POST', 'OPTIONS'])
@limiter.limit("50 per minute")
def process_tool():
    """Main tool processing endpoint with AI analysis integration"""
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

        # Generate AI analysis if not rate limited
        if limit_check.get("can_ai", False) and request_ai_analysis:
            ai_analysis = generate_ai_analysis(tool_config, validated_data, ip, localization)
            increment_user_usage(ip, tool_slug)
        else:
            ai_analysis = create_fallback_response(tool_config, validated_data, localization)
            if limit_check.get("blocked", False):
                # Add rate limit message in appropriate language
                rate_limit_messages = {
                    'Spanish': f"\n\n**Límite de Tarifa:** {limit_check.get('message', 'Límite por hora alcanzado')}",
                    'French': f"\n\n**Limite de Taux:** {limit_check.get('message', 'Limite horaire atteinte')}",
                    'German': f"\n\n**Rate Limit:** {limit_check.get('message', 'Stündliches Limit erreicht')}",
                    'Italian': f"\n\n**Limite di Velocità:** {limit_check.get('message', 'Limite orario raggiunto')}"
                }
                language = localization.get('language', 'English')
                rate_message = rate_limit_messages.get(language, f"\n\n**Rate Limit:** {limit_check.get('message', 'Hourly limit reached')}")
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
        return jsonify({
            "error": "Processing failed",
            "message": "Please check your inputs and try again",
            "exception": e
        }), 500

# Import and register all blueprints including face analysis
from routes.tools_routes import tools_bp
from routes.admin_routes import admin_bp
from routes.legacy_routes import legacy_bp
from routes.face_analysis_routes import face_bp  # New face analysis routes

app.register_blueprint(tools_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(legacy_bp)
app.register_blueprint(face_bp)  # Register face analysis blueprint

# ─── HEALTH CHECK ───────────────────────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    daily_cost = get_openai_cost_today()
    return jsonify({
        "status": "healthy",
        "tools_loaded": len(tools_config.ALL_TOOLS),
        "daily_ai_cost": round(daily_cost, 4),
        "budget_remaining": round(DAILY_OPENAI_BUDGET - daily_cost, 4),
        "face_analysis_enabled": True,
        "timestamp": datetime.now().isoformat()
    })

# ─── FACE ANALYSIS UTILITY ENDPOINTS ───────────────────────────────────────────
@app.route('/face-analysis/limits', methods=['GET'])
def get_face_analysis_limits():
    """Get current face analysis limits for user"""
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

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=True
    )