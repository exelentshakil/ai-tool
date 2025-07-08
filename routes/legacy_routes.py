from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from datetime import datetime
from utils.rate_limiting import get_remote_address, check_user_limit, is_premium_user, increment_user_usage
from utils.cache import check_cache, store_cache
from utils.database import log_usage
from tools.blog_outline_generator import generate_outline
from tools.ai_resume_builder import generate_ai_resume
from config.settings import API_KEY

legacy_bp = Blueprint('legacy', __name__)


# Legacy /process endpoint for backward compatibility
@legacy_bp.route('/process', methods=['POST', 'OPTIONS'])
def process():
    """Legacy process endpoint for existing tools"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    data = request.json or {}
    tool = data.get("tool", "").strip()
    inp = data.get("input", "").strip()

    if not tool or not inp:
        return jsonify({"error": "Missing 'tool' or 'input'"}), 400
    if len(inp) < 3:
        return jsonify({"error": "Input too short."}), 400

    ip = get_remote_address()

    # Check hourly rate limits
    limit_check = check_user_limit(ip, is_premium_user(ip))
    is_rate_limited = limit_check.get("blocked", False)

    # Check cache first
    cached = check_cache(tool, inp)
    if cached:
        log_usage(tool, len(inp), cached=True, ip_address=ip)
        return jsonify({
            "output": cached,
            "cached": True,
            "message": "From cache",
            "rate_limited": is_rate_limited,
            "rate_limit_info": limit_check if is_rate_limited else None
        })

    # If rate limited, provide basic processing without AI enhancement
    if is_rate_limited:
        try:
            if tool == "blog_outline_generator":
                basic_outline = f"""
# {inp}

## Basic Outline Structure
1. Introduction
2. Main Content Points
3. Key Takeaways
4. Conclusion

*Upgrade for AI-enhanced outlines with detailed sections, SEO optimization, and personalized content suggestions.*

Rate Limit: {limit_check.get('message', 'Hourly limit reached')}
"""
                log_usage(tool, len(inp), cached=False, ip_address=ip)
                return jsonify({
                    "output": basic_outline,
                    "cached": False,
                    "rate_limited": True,
                    "rate_limit_info": limit_check
                })

            elif tool == "ai_resume_builder":
                resume = data
                personal = resume.get('personal', {})
                if not personal.get('name') or not personal.get('email'):
                    return jsonify({"error": "Name and email required"}), 400

                basic_resume = f"""
# Resume for {personal.get('name', 'Professional')}

## Contact Information
Email: {personal.get('email', '')}
Phone: {personal.get('phone', 'Not provided')}

## Experience
{len(resume.get('experience', []))} positions listed

## Education  
{len(resume.get('education', []))} educational entries

## Skills
{len(resume.get('skills', []))} skills listed

*Upgrade for AI-enhanced resume with professional formatting, industry-specific optimization, and ATS compatibility.*

Rate Limit: {limit_check.get('message', 'Hourly limit reached')}
"""
                log_usage(tool, len(inp), cached=False, ip_address=ip)
                return jsonify({
                    "output": basic_resume,
                    "cached": False,
                    "rate_limited": True,
                    "rate_limit_info": limit_check
                })

            else:
                return jsonify({
                    "error": "Rate limit reached",
                    "message": limit_check.get('message', 'Hourly limit reached'),
                    "rate_limit_info": limit_check
                }), 200

        except Exception as e:
            return jsonify({
                "error": f"Processing failed: {str(e)}",
                "rate_limited": True,
                "rate_limit_info": limit_check
            }), 500

    # Process with full AI capabilities
    try:
        if tool == "blog_outline_generator":
            options = {
                'content_type': data.get('content_type', 'how-to'),
                'target_audience': data.get('target_audience', 'general'),
                'content_length': data.get('content_length', 'medium'),
                'writing_tone': data.get('writing_tone', 'professional'),
                'include_intro': data.get('include_intro', True),
                'include_conclusion': data.get('include_conclusion', True),
                'include_faq': data.get('include_faq', False),
                'include_cta': data.get('include_cta', False),
                'include_slug': data.get('include_slug', True),
                'include_focus_keywords': data.get('include_focus_keywords', True),
                'include_keywords': data.get('include_keywords', True),
                'include_meta': data.get('include_meta', True),
                'include_title_tags': data.get('include_title_tags', False),
                'include_internal_links': data.get('include_internal_links', False)
            }

            cache_key = f"{inp}:{sorted(options.items())}"
            cached = check_cache(tool, cache_key)
            if cached:
                log_usage(tool, len(inp), cached=True, ip_address=ip)
                return jsonify({"output": cached, "cached": True, "message": "From cache"})

            out = generate_outline(inp, API_KEY, **options)
            store_cache(tool, cache_key, out)
            log_usage(tool, len(inp), cached=False, ip_address=ip)
            increment_user_usage(ip, tool)

            return jsonify({"output": out, "cached": False})

        elif tool == "ai_resume_builder":
            resume = data
            personal = resume.get('personal', {})
            if not personal.get('name') or not personal.get('email'):
                return jsonify({"error": "Name and email required"}), 400

            keystr = str(sorted(resume.items()))
            cache_key = f"resume:{keystr}"
            cached = check_cache(tool, cache_key)
            if cached:
                log_usage(tool, len(keystr), cached=True, ip_address=ip)
                return jsonify({"output": cached, "cached": True, "message": "From cache"})

            out = generate_ai_resume(resume, API_KEY)
            store_cache(tool, cache_key, out)
            log_usage(tool, len(keystr), cached=False, ip_address=ip)
            increment_user_usage(ip, tool)

            return jsonify({"output": out, "cached": False, "message": "Enhanced resume"})

        else:
            return jsonify({"error": "Unknown tool"}), 400

    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500


# Enhanced face analysis endpoint
@legacy_bp.route('/analyze-face-enhanced', methods=['POST', 'OPTIONS'])
def analyze_face_enhanced():
    """Enhanced face analysis with AI insights"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    data = request.get_json() or {}
    face_data = data.get('face_data', {})
    user_profile = data.get('user_profile', {})

    if not face_data:
        return jsonify({"error": "Face analysis data required"}), 400

    ip = get_remote_address()
    limit_check = check_user_limit(ip, is_premium_user(ip))

    # Check rate limits
    if limit_check.get("blocked"):
        return jsonify({
            "error": "Rate limit exceeded",
            "message": limit_check["message"],
            "retry_after": 3600,
            "upgrade_available": not is_premium_user(ip)
        }), 429

    try:
        # Generate enhanced face analysis
        analysis = generate_enhanced_face_analysis(face_data, user_profile, ip)

        # Update usage
        increment_user_usage(ip, "face_enhanced")
        log_usage("face_enhanced", len(str(face_data)), cached=False, ip_address=ip)

        return jsonify({
            "analysis": analysis,
            "cached": False,
            "user_info": {
                "current_usage": limit_check.get("usage_count", 0) + 1,
                "remaining_free": max(0, limit_check.get("remaining", 0) - 1),
                "is_premium": is_premium_user(ip)
            }
        })

    except Exception as e:
        return jsonify({
            "error": "Analysis failed",
            "message": "Please try again later"
        }), 500


def generate_enhanced_face_analysis(face_data, user_profile, ip):
    """Generate comprehensive face analysis (placeholder implementation)"""
    traits = face_data.get('personality_traits', {})
    name = user_profile.get('name', 'You')

    # Basic personality analysis
    analysis = {
        "tier": "ai_enhanced",
        "personality_insights": [
            f"{name} shows strong leadership qualities with excellent communication skills.",
            "Natural tendency toward creative problem-solving and innovative thinking.",
            "High emotional intelligence with strong interpersonal relationships."
        ],
        "career_recommendations": [
            {
                "category": "Leadership & Management",
                "roles": ["Executive", "Team Leader", "Project Manager"],
                "fit_score": 88,
                "reasoning": "Strong leadership indicators in facial analysis"
            }
        ],
        "key_strengths": [
            "Natural charisma and presence",
            "Strong decision-making abilities",
            "Excellent team collaboration skills"
        ],
        "growth_areas": [
            "Continue developing strategic thinking",
            "Enhance public speaking skills",
            "Build broader industry network"
        ]
    }

    return analysis