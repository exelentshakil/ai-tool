# routes/face_analysis_routes.py
from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from utils.rate_limiting import get_remote_address, check_user_limit, is_premium_user, increment_user_usage
from utils.ai_analysis import generate_ai_analysis
import json
import random
import math
from datetime import datetime, timedelta
import logging
import traceback
import os
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

face_bp = Blueprint('face_analysis', __name__)

# Initialize OpenAI client
try:
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {str(e)}")
    openai_client = None


class AIPersonalityAnalyzer:
    """AI-powered personality analysis using OpenAI GPT-4"""

    def __init__(self):
        logger.info("Initializing AIPersonalityAnalyzer")
        if not openai_client:
            raise Exception("OpenAI client not available")

    def generate_ai_personality_analysis(self, traits, face_data, user_profile):
        """Generate comprehensive AI-powered personality analysis"""
        logger.info("Generating AI personality analysis")

        try:
            # Prepare the prompt for OpenAI
            prompt = self._create_analysis_prompt(traits, face_data, user_profile)

            logger.debug(f"Sending prompt to OpenAI: {prompt[:200]}...")

            # Call OpenAI API
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Using the latest efficient model
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert personality psychologist and career advisor with deep knowledge of the Big Five personality traits, career psychology, and human development. Provide detailed, actionable, and insightful personality analysis based on facial expression data and personality traits."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=3000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            logger.info("Received response from OpenAI")

            # Parse the response
            ai_response = json.loads(response.choices[0].message.content)

            # Structure the response according to our expected format
            structured_response = self._structure_ai_response(ai_response, traits)

            logger.info("AI analysis generated successfully")
            return structured_response

        except Exception as e:
            logger.error(f"Error generating AI analysis: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"AI analysis failed: {str(e)}")

    def _create_analysis_prompt(self, traits, face_data, user_profile):
        """Create a comprehensive prompt for OpenAI"""

        name = user_profile.get('name', 'the user')
        age_range = user_profile.get('age_range', '25-34')

        # Format traits data
        traits_str = "\n".join([f"- {trait.title()}: {score:.1%}" for trait, score in traits.items()])

        # Add face data context if available
        face_context = ""
        if face_data.get('age'):
            face_context += f"- Estimated age: {face_data['age']}\n"
        if face_data.get('gender'):
            face_context += f"- Gender: {face_data['gender']}\n"
        if face_data.get('expressions'):
            top_emotions = sorted(face_data['expressions'].items(), key=lambda x: x[1], reverse=True)[:3]
            face_context += f"- Top facial expressions: {', '.join([f'{emotion} ({intensity:.1%})' for emotion, intensity in top_emotions])}\n"

        prompt = f"""
Analyze the personality profile for {name} (age range: {age_range}) and provide a comprehensive personality analysis.

PERSONALITY TRAITS DATA:
{traits_str}

FACIAL ANALYSIS DATA:
{face_context}

Please provide a detailed JSON response with the following structure:

{{
    "personality_insights": [
        // 4-5 deep, personalized insights about their personality, strengths, and unique characteristics
        // Each insight should be 2-3 sentences and actionable
        // Focus on their dominant traits and how they combine
    ],
    "career_recommendations": [
        {{
            "category": "Career Field Name",
            "roles": ["Specific Job 1", "Specific Job 2", "Specific Job 3", "Specific Job 4"],
            "fit_score": 85, // 1-100 based on trait alignment
            "reasoning": "Detailed explanation of why this career fits their personality",
            "salary_range": "$XX,XXX - $XXX,XXX",
            "growth_potential": 90, // 1-100 growth outlook
            "success_probability": 88, // 1-100 likelihood of success
            "recommended_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4"],
            "future_market_trends": "What's happening in this field"
        }}
        // Provide 3 career recommendations total
    ],
    "growth_roadmap": [
        {{
            "area": "Development Area Name",
            "current_level": "XX%",
            "target_level": "XX%", 
            "timeline": "X-X months",
            "priority": "High/Medium/Low",
            "action_steps": [
                "Specific action 1",
                "Specific action 2", 
                "Specific action 3"
            ],
            "success_metrics": ["Metric 1", "Metric 2"],
            "resources": ["Resource 1", "Resource 2"]
        }}
        // Provide 2-3 growth recommendations
    ],
    "life_predictions": {{
        "career_advancement": 85, // 1-100 prediction
        "financial_growth": 78,
        "leadership_potential": 82,
        "innovation_capacity": 88,
        "relationship_satisfaction": 76
    }},
    "success_factors": {{
        "top_strengths": ["Strength 1", "Strength 2", "Strength 3"],
        "key_challenges": ["Challenge 1", "Challenge 2"],
        "optimal_environment": "Description of ideal work/life environment",
        "decision_making_style": "How they make decisions",
        "communication_style": "How they communicate best"
    }},
    "motivation_message": "A powerful, personalized motivational message (2-3 sentences) that inspires them based on their unique strengths and potential"
}}

IMPORTANT GUIDELINES:
1. Make all content highly personalized and specific to their trait combination
2. Avoid generic advice - be specific and actionable
3. Focus on their unique strengths and how to leverage them
4. Provide realistic but optimistic predictions
5. Include current market trends and future opportunities
6. Make the career recommendations specific with real job titles
7. Ensure all scores and percentages are realistic and evidence-based
8. Write in an inspiring yet professional tone
9. Address them by name ({name}) in insights where appropriate
10. Consider their age range for career and development recommendations
"""

        return prompt

    def _structure_ai_response(self, ai_response, traits):
        """Structure the AI response to match our expected format"""

        try:
            # Add enhanced traits to the response
            enhanced_traits = traits.copy()

            # Calculate additional metrics based on Big Five
            enhanced_traits['confidence'] = (
                    traits.get('extraversion', 0.5) * 0.6 +
                    (1 - traits.get('neuroticism', 0.5)) * 0.4
            )
            enhanced_traits['creativity'] = (
                    traits.get('openness', 0.5) * 0.8 +
                    traits.get('extraversion', 0.5) * 0.2
            )
            enhanced_traits['leadership'] = (
                    traits.get('extraversion', 0.5) * 0.5 +
                    traits.get('conscientiousness', 0.5) * 0.3 +
                    (1 - traits.get('neuroticism', 0.5)) * 0.2
            )

            # Structure the response
            structured_response = {
                'personality_insights': ai_response.get('personality_insights', []),
                'career_recommendations': ai_response.get('career_recommendations', []),
                'growth_roadmap': ai_response.get('growth_roadmap', []),
                'life_predictions': ai_response.get('life_predictions', {}),
                'success_factors': ai_response.get('success_factors', {}),
                'motivation_message': ai_response.get('motivation_message', ''),
                'enhanced_traits': enhanced_traits,
                'analysis_quality': 'ai_powered',
                'confidence_score': 0.95,
                'ai_model': 'gpt-4o-mini',
                'analysis_timestamp': datetime.now().isoformat()
            }

            return structured_response

        except Exception as e:
            logger.error(f"Error structuring AI response: {str(e)}")
            raise Exception(f"Failed to structure AI response: {str(e)}")


@face_bp.route('/analyze-face-enhanced', methods=['POST', 'OPTIONS'])
def analyze_face_enhanced():
    """AI-powered face analysis endpoint - ONLY uses AI, no fallbacks"""
    if request.method == 'OPTIONS':
        logger.info("Received OPTIONS request for face analysis")
        return jsonify({}), 200

    logger.info("Starting AI-powered face analysis")

    try:
        # Check if OpenAI is available
        if not openai_client:
            logger.error("OpenAI client not available")
            return jsonify({
                'error': 'AI analysis service unavailable',
                'message': 'The AI analysis service is currently unavailable. Please try again later.',
                'service_status': 'offline'
            }), 503

        # Initialize database to prevent upsert errors
        try:
            from utils.database import init_databases
            init_databases()
            logger.debug("Database initialized successfully")
        except Exception as db_error:
            logger.warning(f"Database initialization warning: {str(db_error)}")

        data = request.get_json()
        logger.debug(f"Received request data keys: {list(data.keys()) if data else 'None'}")

        if not data:
            logger.warning("No data provided in request")
            return jsonify({'error': 'No data provided'}), 400

        # Get user IP for rate limiting
        ip = get_remote_address()
        logger.info(f"Processing request from IP: {ip}")

        try:
            is_premium = is_premium_user(ip)
            logger.debug(f"User premium status: {is_premium}")
        except Exception as premium_error:
            logger.warning(f"Error checking premium status: {str(premium_error)}")
            is_premium = False

        # Check rate limits - AI analysis requires higher limits
        try:
            limit_check = check_user_limit(ip, is_premium)
            logger.debug(f"Rate limit check result: {limit_check}")

            # For AI analysis, we need stricter limits
            if not is_premium and limit_check.get("usage_count", 0) >= 3:
                logger.info("Rate limit exceeded for non-premium user")
                return jsonify({
                    'error': 'AI Analysis Limit Reached',
                    'message': 'You have reached your daily limit for AI-powered analysis. Upgrade to premium for unlimited access.',
                    'remaining_analyses': 0,
                    'upgrade_required': True,
                    'is_rate_limited': True
                }), 429

        except Exception as limit_error:
            logger.error(f"Rate limiting error: {str(limit_error)}")
            return jsonify({
                'error': 'Rate limiting service unavailable',
                'message': 'Unable to verify usage limits. Please try again.'
            }), 503

        # Extract face data and user profile
        face_data = data.get('face_data', {})
        user_profile = data.get('user_profile', {})

        logger.debug(f"Face data structure: {list(face_data.keys())}")
        logger.debug(f"User profile: {user_profile}")

        # Validate required data
        personality_traits = face_data.get('personality_traits')
        if not personality_traits:
            basic_data = face_data.get('basic', {})
            if not basic_data.get('expressions'):
                logger.warning("No personality traits or facial expression data provided")
                return jsonify({
                    'error': 'Insufficient data for AI analysis',
                    'message': 'Please provide personality traits or facial expression data for AI analysis.'
                }), 400

            # Generate basic traits from expressions if not provided
            personality_traits = self._generate_traits_from_expressions(basic_data.get('expressions', {}))

        # Initialize AI analyzer
        try:
            analyzer = AIPersonalityAnalyzer()
            logger.debug("AI analyzer initialized successfully")
        except Exception as analyzer_error:
            logger.error(f"Error initializing AI analyzer: {str(analyzer_error)}")
            return jsonify({
                'error': 'AI service initialization failed',
                'message': 'The AI analysis service is currently unavailable. Please try again later.'
            }), 503

        # Generate AI analysis
        try:
            logger.info("Starting AI analysis generation")
            ai_analysis = analyzer.generate_ai_personality_analysis(
                personality_traits,
                face_data,
                user_profile
            )

            logger.info("AI analysis completed successfully")

            # Increment usage for AI analysis
            try:
                increment_user_usage(ip, 'ai_face_analysis')
                logger.debug("Usage incremented for AI analysis")
            except Exception as usage_error:
                logger.warning(f"Error incrementing usage: {str(usage_error)}")

        except Exception as ai_error:
            logger.error(f"AI analysis failed: {str(ai_error)}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            # Check if it's an OpenAI API error
            if "rate_limit" in str(ai_error).lower():
                return jsonify({
                    'error': 'AI service temporarily overloaded',
                    'message': 'The AI analysis service is currently experiencing high demand. Please try again in a few minutes.',
                    'retry_after': 300
                }), 429
            elif "insufficient_quota" in str(ai_error).lower():
                return jsonify({
                    'error': 'AI service quota exceeded',
                    'message': 'The AI analysis service has reached its daily quota. Please try again tomorrow.',
                    'service_status': 'quota_exceeded'
                }), 503
            else:
                return jsonify({
                    'error': 'AI analysis failed',
                    'message': 'The AI analysis could not be completed. Please try again.',
                    'technical_details': str(ai_error) if logger.level <= logging.DEBUG else None
                }), 500

        # Add user information to response
        # NEW CODE (fixed):
        remaining_count = max(0, (50 if is_premium else 3) - limit_check.get("usage_count", 0) - 1)

        # Handle infinity/unlimited for premium users
        if is_premium and remaining_count >= 50:
            remaining_analyses = 999999  # Use large number instead of Infinity
        else:
            remaining_analyses = remaining_count

        ai_analysis.update({
            'user_tier': 'premium' if is_premium else 'free',
            'remaining_analyses': remaining_analyses
        })

        # Prepare final response
        response_data = {
            'success': True,
            'analysis': ai_analysis,
            'user_info': {
                'analysis_quality': 'premium' if is_premium else 'basic',
                'is_rate_limited': False,
                'remaining_analyses': remaining_analyses,  # Now safe for JSON
                'upgrade_available': not is_premium,
                'ai_powered': True
            },
            'message': 'AI-powered personality analysis completed successfully'
        }

        logger.info("AI face analysis completed successfully")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Face analysis error: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")

        return jsonify({
            'error': 'Analysis system error',
            'message': 'An unexpected error occurred during analysis. Please try again.',
            'timestamp': datetime.now().isoformat(),
            'support_message': 'If this error persists, please contact support.'
        }), 500


def _generate_traits_from_expressions(expressions):
    """Generate basic personality traits from facial expressions"""
    if not expressions:
        return {
            'openness': 0.5,
            'conscientiousness': 0.5,
            'extraversion': 0.5,
            'agreeableness': 0.5,
            'neuroticism': 0.5
        }

    # Simple mapping from expressions to traits
    traits = {
        'openness': expressions.get('surprised', 0) * 0.8 + expressions.get('happy', 0) * 0.4,
        'conscientiousness': expressions.get('neutral', 0) * 0.7 + expressions.get('happy', 0) * 0.3,
        'extraversion': expressions.get('happy', 0) * 0.8 + expressions.get('surprised', 0) * 0.5,
        'agreeableness': expressions.get('happy', 0) * 0.7 + expressions.get('neutral', 0) * 0.4,
        'neuroticism': expressions.get('sad', 0) * 0.6 + expressions.get('angry', 0) * 0.8 + expressions.get('fearful',
                                                                                                             0) * 0.7
    }

    # Normalize to 0.2-0.9 range
    for trait in traits:
        traits[trait] = max(0.2, min(0.9, traits[trait] + 0.3))

    return traits


# Health check endpoint for AI face analysis
@face_bp.route('/face-analysis/health', methods=['GET'])
def face_analysis_health():
    """Health check specifically for AI face analysis system"""
    logger.info("AI face analysis health check requested")

    try:
        # Test OpenAI connection
        if not openai_client:
            return jsonify({
                'status': 'unhealthy',
                'ai_service': 'unavailable',
                'openai_client': 'not_initialized',
                'timestamp': datetime.now().isoformat()
            }), 503

        # Test basic OpenAI API call
        test_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello, respond with just 'OK'"}],
            max_tokens=5
        )

        if test_response.choices[0].message.content.strip().upper() == 'OK':
            openai_status = 'operational'
        else:
            openai_status = 'responding_incorrectly'

        health_data = {
            'status': 'healthy',
            'ai_service': 'operational',
            'openai_client': 'initialized',
            'openai_api': openai_status,
            'model': 'gpt-4o-mini',
            'features': [
                'AI-powered personality insights',
                'Career recommendations',
                'Growth roadmaps',
                'Success predictions',
                'Motivational analysis'
            ],
            'timestamp': datetime.now().isoformat()
        }

        logger.info("AI face analysis health check passed")
        return jsonify(health_data)

    except Exception as e:
        logger.error(f"AI face analysis health check failed: {str(e)}")

        return jsonify({
            'status': 'unhealthy',
            'ai_service': 'error',
            'error': str(e),
            'openai_client': 'initialized' if openai_client else 'not_initialized',
            'timestamp': datetime.now().isoformat()
        }), 500


# Rate limiting check endpoint
@face_bp.route('/check-face-analysis-limit', methods=['POST'])
def check_face_analysis_limit():
    """Check if user can perform AI face analysis"""
    logger.info("Checking AI face analysis limits")

    try:
        ip = get_remote_address()
        is_premium = is_premium_user(ip)
        limit_check = check_user_limit(ip, is_premium)

        # AI analysis has stricter limits
        daily_limit = 50 if is_premium else 3
        current_usage = limit_check.get("usage_count", 0)
        remaining = max(0, daily_limit - current_usage)

        response_data = {
            'can_analyze': remaining > 0 and openai_client is not None,
            'remaining_analyses': remaining,
            'daily_limit': daily_limit,
            'is_premium': is_premium,
            'ai_service_available': openai_client is not None,
            'reset_time': (datetime.now() + timedelta(hours=24)).isoformat(),
            'upgrade_benefits': [
                'Unlimited daily AI analyses',
                'Advanced personality insights',
                'Detailed career roadmaps',
                'Success predictions',
                'Priority AI processing'
            ]
        }

        logger.info(f"AI limit check completed - Can analyze: {response_data['can_analyze']}")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error checking AI face analysis limits: {str(e)}")

        return jsonify({
            'can_analyze': False,
            'remaining_analyses': 0,
            'is_premium': False,
            'ai_service_available': False,
            'error': 'Limit check service unavailable',
            'timestamp': datetime.now().isoformat()
        }), 500