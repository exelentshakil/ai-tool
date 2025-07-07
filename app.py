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
from utils.ai_analysis import generate_ai_analysis, generate_base_result, create_fallback_response
from utils.tools_config import load_all_tools, ALL_TOOLS
from config.settings import *

# ─── ENV & APP SETUP ────────────────────────────────────────────────────────────
load_dotenv()
app = Flask(__name__)
CORS(app, origins=["https://barakahsoft.com"])
CORS(app, expose_headers=['Retry-After'])

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "200 per hour", "50 per minute"]
)
limiter.init_app(app)

# Initialize databases
init_databases()

# Load tools configuration
load_all_tools()


# ─── MAIN API ENDPOINTS ─────────────────────────────────────────────────────────
@app.route('/process-tool', methods=['POST', 'OPTIONS'])
@limiter.limit("50 per minute")
def process_tool():
    """Main tool processing endpoint"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        data = request.json or {}
        tool_slug = data.get("tool", "").strip()
        user_data = data.get("data", {})

        if not tool_slug:
            return jsonify({"error": "Tool parameter required"}), 400

        # Find tool configuration
        tool_config = ALL_TOOLS.get(tool_slug)
        if not tool_config:
            for key in ALL_TOOLS.keys():
                if tool_slug.lower() in key.lower() or key.lower() in tool_slug.lower():
                    tool_config = ALL_TOOLS[key]
                    break

        if not tool_config:
            return jsonify({
                "error": f"Tool '{tool_slug}' not found",
                "available_tools": list(ALL_TOOLS.keys())[:10]
            }), 404

        ip = get_remote_address()
        limit_check = check_user_limit(ip, is_premium_user(ip))

        # Validate inputs
        category = tool_config.get("category", "general")
        validated_data = validate_tool_inputs(user_data, category)
        base_result = generate_base_result(validated_data, category)

        # Generate AI analysis if not rate limited
        if limit_check.get("can_ai", False):
            ai_analysis = generate_ai_analysis(tool_config, validated_data, base_result, ip)
            increment_user_usage(ip, tool_slug)
        else:
            ai_analysis = create_fallback_response(tool_config, validated_data, base_result)
            ai_analysis += f"\n\n**Rate Limit:** {limit_check.get('message', 'Hourly limit reached')}"

        is_rate_limited = limit_check.get("blocked", False)
        return jsonify({
            "output": {
                "base_result": base_result,
                "ai_analysis": ai_analysis,
                "rate_limited": limit_check.get("blocked", False)
            },
            "tool_info": tool_config,
            "user_info": {
                "current_usage": limit_check.get("usage_count", 0),
                "remaining_free": limit_check.get("remaining", 0),
                "is_rate_limited": limit_check.get("blocked", False),
                "upgrade_available": not is_premium_user(ip),
                "rate_limit_message": limit_check.get("message") if is_rate_limited else None
            }
        }), 200

    except Exception as e:
        app.logger.error(f"Process tool error: {str(e)}")
        return jsonify({
            "error": "Processing failed",
            "message": "Please check your inputs and try again"
        }), 500


# Import and register all other endpoints
from routes.tools_routes import tools_bp
from routes.admin_routes import admin_bp
from routes.legacy_routes import legacy_bp

app.register_blueprint(tools_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(legacy_bp)


# ─── HEALTH CHECK ───────────────────────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    daily_cost = get_openai_cost_today()
    return jsonify({
        "status": "healthy",
        "tools_loaded": len(ALL_TOOLS),
        "daily_ai_cost": round(daily_cost, 4),
        "budget_remaining": round(DAILY_OPENAI_BUDGET - daily_cost, 4),
        "timestamp": datetime.now().isoformat()
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=True
    )