# routes/face_analysis_routes.py
from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from utils.rate_limiting import get_remote_address, check_user_limit, is_premium_user, increment_user_usage
from utils.database import is_ip_blocked, log_openai_cost_enhanced, log_tool_usage
import json
import random
import math
import time
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

    def generate_ai_personality_analysis(self, traits, face_data, user_profile, ip):
        """Generate comprehensive AI-powered personality analysis with cost tracking"""
        logger.info("Generating AI personality analysis")

        # Start timing for response time tracking
        start_time = time.time()

        try:
            # Prepare the prompt for OpenAI
            prompt = self._create_analysis_prompt(traits, face_data, user_profile)

            logger.debug(f"Sending prompt to OpenAI: {prompt[:200]}...")

            # Call OpenAI API
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
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

            # Calculate response time
            response_time = int((time.time() - start_time) * 1000)  # milliseconds

            # Extract usage data
            usage = response.usage
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = prompt_tokens + completion_tokens

            # Calculate cost (gpt-4o-mini pricing)
            # Input: $0.00015 per 1K tokens, Output: $0.0006 per 1K tokens
            cost = (prompt_tokens * 0.00015 + completion_tokens * 0.0006) / 1000

            logger.info(
                f"OpenAI API usage - Tokens: {total_tokens}, Cost: ${cost:.6f}, Response time: {response_time}ms")

            # Log the OpenAI cost with enhanced tracking
            try:
                log_success = log_openai_cost_enhanced(
                    cost=cost,
                    tokens=total_tokens,
                    model="gpt-4o-mini",
                    ip=ip,
                    tools_slug="face_analysis_ai",
                    response_time=response_time
                )

                if log_success:
                    logger.info(f"✅ OpenAI cost logged successfully: ${cost:.6f}")
                else:
                    logger.warning("⚠️ OpenAI cost logging failed")

            except Exception as cost_log_error:
                logger.error(f"❌ Error logging OpenAI cost: {cost_log_error}")

            # Parse the response
            ai_response = json.loads(response.choices[0].message.content)

            # Structure the response according to our expected format
            structured_response = self._structure_ai_response(ai_response, traits)

            # Add cost and performance metadata
            structured_response.update({
                'api_usage': {
                    'tokens_used': total_tokens,
                    'cost': cost,
                    'response_time_ms': response_time,
                    'model': 'gpt-4o-mini'
                }
            })

            logger.info("AI analysis generated successfully")
            return structured_response

        except Exception as e:
            # Calculate error response time
            error_response_time = int((time.time() - start_time) * 1000)

            # Log failed request (cost=0 for errors)
            try:
                log_openai_cost_enhanced(
                    cost=0,
                    tokens=0,
                    model="gpt-4o-mini-error",
                    ip=ip,
                    tools_slug="face_analysis_ai",
                    response_time=error_response_time
                )
            except:
                pass  # Don't fail on error logging

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
        // 9 deep, personalized insights about their personality, strengths, and unique characteristics
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
        // Provide 4 career recommendations total
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
        // Provide 4 growth recommendations
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
        "communication_style": "How they communicate best",
        "learning_style": "How they learn best",
        "stress_management": "How they cope with stress",
        "risk_tolerance": "Their comfort level with risk"
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

            # Process personality insights to ensure they're strings
            personality_insights = ai_response.get('personality_insights', [])
            processed_insights = []
            for insight in personality_insights:
                if isinstance(insight, dict):
                    insight_text = insight.get('text') or insight.get('message') or insight.get('insight') or str(
                        insight)
                    processed_insights.append(insight_text)
                elif isinstance(insight, str):
                    processed_insights.append(insight)
                else:
                    processed_insights.append(str(insight))

            ai_models = [
                'Claude-Persona-4', 'GPT-PersonaVision', 'Gemini-PersonaCore',
                'NeuraCore-PersonaAI', 'CogniVision-Pro', 'MindScan-Ultra',
                'PsychoCore-4.0', 'DeepInsight-AI', 'PersonalyticAI-3.5'
            ]

            # Structure the response
            structured_response = {
                'personality_insights': processed_insights,
                'career_recommendations': ai_response.get('career_recommendations', []),
                'growth_roadmap': ai_response.get('growth_roadmap', []),
                'life_predictions': ai_response.get('life_predictions', {}),
                'success_factors': ai_response.get('success_factors', {}),
                'motivation_message': ai_response.get('motivation_message', ''),
                'enhanced_traits': enhanced_traits,
                'analysis_quality': 'ai_powered',
                'confidence_score': 0.95,
                'ai_model': random.choice(ai_models),
                'analysis_timestamp': datetime.now().isoformat()
            }

            return structured_response

        except Exception as e:
            logger.error(f"Error structuring AI response: {str(e)}")
            raise Exception(f"Failed to structure AI response: {str(e)}")


@face_bp.route('/analyze-face-enhanced', methods=['POST', 'OPTIONS'])
def analyze_face_enhanced():
    """AI-powered face analysis endpoint with complete tracking"""
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

        data = request.get_json()
        if not data:
            logger.warning("No data provided in request")
            return jsonify({'error': 'No data provided'}), 400

        # Get user IP and check if blocked
        ip = get_remote_address()
        logger.info(f"Processing face analysis request from IP: {ip}")

        # Check if IP is blocked
        try:
            if is_ip_blocked(ip):
                logger.warning(f"🚫 Blocked IP attempted face analysis: {ip}")
                return jsonify({
                    'error': 'Access denied',
                    'message': 'Your IP address has been blocked for policy violations',
                    'blocked': True,
                    'contact': 'Contact support if you believe this is an error'
                }), 403
        except Exception as block_error:
            logger.warning(f"Error checking IP block status: {str(block_error)}")

        # Check premium status
        try:
            is_premium = is_premium_user(ip)
            logger.debug(f"User premium status: {is_premium}")
        except Exception as premium_error:
            logger.warning(f"Error checking premium status: {str(premium_error)}")
            is_premium = False

        # Check rate limits
        try:
            limit_check = check_user_limit(ip, is_premium)
            logger.debug(f"Rate limit check result: {limit_check}")

            # For AI analysis, stricter limits
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

        # Extract and validate face data
        face_data = data.get('face_data', {})
        user_profile = data.get('user_profile', {})

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
            personality_traits = _generate_traits_from_expressions(basic_data.get('expressions', {}))

        # Log tool usage for analytics
        try:
            log_tool_usage('face_analysis_ai', ip, {
                'analysis_type': 'enhanced_ai_analysis',
                'user_tier': 'premium' if is_premium else 'free',
                'has_personality_traits': bool(personality_traits),
                'has_face_data': bool(face_data),
                'timestamp': datetime.now().isoformat()
            })
            logger.debug("Tool usage logged for face analysis")
        except Exception as usage_log_error:
            logger.warning(f"Error logging tool usage: {str(usage_log_error)}")

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

        # Generate AI analysis with cost tracking
        try:
            logger.info("Starting AI analysis generation")
            ai_analysis = analyzer.generate_ai_personality_analysis(
                personality_traits,
                face_data,
                user_profile,
                ip  # Pass IP for cost tracking
            )

            logger.info("AI analysis completed successfully")

            # Increment usage counter for rate limiting
            try:
                increment_user_usage(ip, 'face_analysis_ai')
                logger.debug("Usage incremented for AI face analysis")
            except Exception as usage_error:
                logger.warning(f"Error incrementing usage: {str(usage_error)}")

        except Exception as ai_error:
            logger.error(f"AI analysis failed: {str(ai_error)}")

            # Log the failed attempt
            try:
                log_tool_usage('face_analysis_ai', ip, {
                    'analysis_type': 'failed_ai_analysis',
                    'error': str(ai_error),
                    'timestamp': datetime.now().isoformat()
                })
            except:
                pass

            # Check specific error types
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

        # Calculate remaining analyses
        remaining_count = max(0, (50 if is_premium else 3) - limit_check.get("usage_count", 0) - 1)
        remaining_analyses = 999999 if is_premium and remaining_count >= 50 else remaining_count

        # Add user information to response
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
                'remaining_analyses': remaining_analyses,
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


@face_bp.route('/face-analysis/health', methods=['GET'])
def face_analysis_health():
    """Health check for AI face analysis system"""
    logger.info("AI face analysis health check requested")

    try:
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

        openai_status = 'operational' if test_response.choices[
                                             0].message.content.strip().upper() == 'OK' else 'responding_incorrectly'

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
            'cost_tracking': 'enabled',
            'rate_limiting': 'enabled',
            'ip_blocking': 'enabled',
            'timestamp': datetime.now().isoformat()
        }

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


@face_bp.route('/check-face-analysis-limit', methods=['POST'])
def check_face_analysis_limit():
    """Check if user can perform AI face analysis"""
    logger.info("Checking AI face analysis limits")

    try:
        ip = get_remote_address()

        # Check if IP is blocked
        try:
            if is_ip_blocked(ip):
                logger.warning(f"🚫 Blocked IP attempted limit check: {ip}")
                return jsonify({
                    'can_analyze': False,
                    'remaining_analyses': 0,
                    'is_premium': False,
                    'blocked': True,
                    'message': 'IP address blocked'
                }), 403
        except Exception as block_error:
            logger.warning(f"Error checking IP block status: {str(block_error)}")

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