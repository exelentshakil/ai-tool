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
from utils.ai_analysis import generate_ai_analysis, generate_base_result, create_fallback_response
from utils.tools_config import load_all_tools, ALL_TOOLS
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
print(f"🔍 Available tools after loading: {list(ALL_TOOLS.keys()) if ALL_TOOLS else 'None'}")


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


# Import and register all blueprints including face analysis
from routes.tools_routes import tools_bp
from routes.admin_routes import admin_bp
from routes.legacy_routes import legacy_bp
from routes.face_analysis_routes import face_bp  # New face analysis routes

app.register_blueprint(tools_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(legacy_bp)
app.register_blueprint(face_bp)  # Register face analysis blueprint


# ─── FACE ANALYSIS SPECIFIC ENDPOINTS ──────────────────────────────────────────
@app.route('/analyze-face-simple', methods=['POST', 'OPTIONS'])
@limiter.limit("20 per hour")
def analyze_face_simple():
    """Simplified face analysis endpoint for WordPress integration"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        ip = get_remote_address()
        is_premium = is_premium_user(ip)
        limit_check = check_user_limit(ip, is_premium)

        # Check if user can perform analysis
        if limit_check.get("blocked", False):
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': limit_check.get("message", "Daily limit reached"),
                'upgrade_available': not is_premium,
                'reset_time': (datetime.now() + timedelta(hours=1)).isoformat()
            }), 429

        # Extract personality traits from client
        traits = data.get('personality_traits', {})
        user_profile = data.get('user_profile', {})

        if not traits:
            return jsonify({'error': 'Personality traits required'}), 400

        # Generate basic analysis for WordPress plugin
        from routes.face_analysis_routes import EnhancedPersonalityAnalyzer
        analyzer = EnhancedPersonalityAnalyzer()

        # Create simplified analysis
        analysis = {
            'personality_insights': analyzer.generate_comprehensive_insights(traits, {}, user_profile)[:2],
            'career_match': analyzer.get_career_recommendations(traits, {})[:1],
            'success_predictions': analyzer.generate_life_predictions(traits, {}),
            'confidence_score': 0.85,
            'analysis_timestamp': datetime.now().isoformat()
        }

        # Increment usage
        increment_user_usage(ip, 'face_analysis_simple')

        return jsonify({
            'success': True,
            'analysis': analysis,
            'user_info': {
                'remaining_analyses': limit_check.get("remaining", 0) - 1,
                'is_premium': is_premium
            }
        })

    except Exception as e:
        app.logger.error(f"Simple face analysis error: {str(e)}")
        return jsonify({
            'error': 'Analysis failed',
            'message': str(e)
        }), 500


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


@app.route('/face-analysis/demo', methods=['POST'])
@limiter.limit("5 per hour")
def face_analysis_demo():
    """Demo endpoint with sample personality analysis"""
    try:
        # Sample traits for demo
        demo_traits = {
            'openness': 0.75,
            'conscientiousness': 0.68,
            'extraversion': 0.82,
            'agreeableness': 0.71,
            'neuroticism': 0.34
        }

        demo_profile = {
            'name': 'Demo User',
            'age_range': '25-34'
        }

        from routes.face_analysis_routes import EnhancedPersonalityAnalyzer
        analyzer = EnhancedPersonalityAnalyzer()

        demo_analysis = {
            'personality_insights': [
                "You demonstrate exceptional leadership potential with high extraversion and strong organizational skills.",
                "Your openness to new experiences combined with conscientiousness makes you ideal for innovative leadership roles."
            ],
            'career_recommendations': analyzer.get_career_recommendations(demo_traits, {})[:1],
            'success_predictions': analyzer.generate_life_predictions(demo_traits, {}),
            'is_demo': True,
            'demo_message': 'This is a sample analysis. Upload your photo for personalized results!'
        }

        return jsonify({
            'success': True,
            'analysis': demo_analysis,
            'demo': True
        })

    except Exception as e:
        return jsonify({'error': 'Demo failed', 'message': str(e)}), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=True
    )