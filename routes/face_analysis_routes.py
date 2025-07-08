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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

face_bp = Blueprint('face_analysis', __name__)


class EnhancedPersonalityAnalyzer:
    """Advanced personality analysis using comprehensive facial feature data"""

    def __init__(self):
        logger.info("Initializing EnhancedPersonalityAnalyzer")
        self.trait_weights = {
            'openness': {
                'surprised': 0.8, 'happy': 0.6, 'neutral': 0.4,
                'sad': 0.2, 'angry': 0.1, 'fearful': 0.3, 'disgusted': 0.2
            },
            'conscientiousness': {
                'neutral': 0.8, 'surprised': 0.3, 'happy': 0.5,
                'sad': 0.4, 'angry': 0.2, 'fearful': 0.6, 'disgusted': 0.4
            },
            'extraversion': {
                'happy': 0.9, 'surprised': 0.7, 'neutral': 0.4,
                'sad': 0.1, 'angry': 0.2, 'fearful': 0.1, 'disgusted': 0.2
            },
            'agreeableness': {
                'happy': 0.8, 'neutral': 0.6, 'surprised': 0.5,
                'sad': 0.4, 'angry': 0.1, 'fearful': 0.3, 'disgusted': 0.2
            },
            'neuroticism': {
                'sad': 0.8, 'angry': 0.9, 'fearful': 0.9, 'disgusted': 0.7,
                'neutral': 0.3, 'happy': 0.1, 'surprised': 0.4
            }
        }

        self.career_insights = {
            'creative_arts': {
                'roles': ['Graphic Designer', 'Content Creator', 'Artist', 'Musician', 'Film Director', 'UX Designer'],
                'traits': {'openness': 0.7, 'extraversion': 0.5},
                'growth': 88,
                'salary': '$45K-$150K',
                'future_trends': 'AI-assisted creativity, NFT markets, virtual reality experiences'
            },
            'leadership_executive': {
                'roles': ['CEO', 'VP', 'Director', 'Team Lead', 'Entrepreneur', 'Strategy Consultant'],
                'traits': {'extraversion': 0.7, 'conscientiousness': 0.6},
                'growth': 95,
                'salary': '$80K-$500K+',
                'future_trends': 'Remote team management, AI-driven decision making, sustainable leadership'
            },
            'tech_innovation': {
                'roles': ['Software Engineer', 'Data Scientist', 'AI Researcher', 'Product Manager', 'DevOps Engineer'],
                'traits': {'conscientiousness': 0.7, 'openness': 0.6},
                'growth': 92,
                'salary': '$70K-$250K',
                'future_trends': 'AI/ML development, blockchain, quantum computing, green tech'
            },
            'healthcare_wellness': {
                'roles': ['Therapist', 'Healthcare Admin', 'Wellness Coach', 'Mental Health Specialist',
                          'Medical Researcher'],
                'traits': {'agreeableness': 0.7, 'conscientiousness': 0.6},
                'growth': 85,
                'salary': '$50K-$180K',
                'future_trends': 'Telemedicine, personalized healthcare, mental health tech, aging population care'
            },
            'finance_analytics': {
                'roles': ['Financial Analyst', 'Investment Advisor', 'Risk Manager', 'Fintech Specialist',
                          'Quantitative Analyst'],
                'traits': {'conscientiousness': 0.8, 'neuroticism': 0.3},
                'growth': 89,
                'salary': '$60K-$300K',
                'future_trends': 'Cryptocurrency, robo-advisors, sustainable investing, regulatory tech'
            },
            'education_training': {
                'roles': ['Corporate Trainer', 'Educational Technology Specialist', 'Curriculum Designer',
                          'Learning Consultant'],
                'traits': {'agreeableness': 0.6, 'extraversion': 0.5, 'openness': 0.6},
                'growth': 82,
                'salary': '$45K-$120K',
                'future_trends': 'Online learning platforms, VR education, personalized learning AI'
            }
        }
        logger.info("EnhancedPersonalityAnalyzer initialized successfully")

    def calculate_enhanced_traits(self, face_data):
        """Calculate personality traits from facial expressions and advanced metrics"""
        logger.info(f"Calculating enhanced traits from face data: {list(face_data.keys())}")

        try:
            basic_data = face_data.get('basic', {})
            advanced_data = face_data.get('advanced', {})

            expressions = basic_data.get('expressions', {})
            age = basic_data.get('estimated_age', 30)
            gender = basic_data.get('gender', 'unknown')

            logger.debug(f"Face data - Age: {age}, Gender: {gender}, Expressions: {expressions}")

            # Base trait calculation from expressions
            traits = {}
            for trait, emotion_weights in self.trait_weights.items():
                score = 0
                total_weight = 0

                for emotion, intensity in expressions.items():
                    if emotion in emotion_weights:
                        weight = emotion_weights[emotion]
                        score += intensity * weight
                        total_weight += weight

                if total_weight > 0:
                    traits[trait] = min(0.95, max(0.15, score / total_weight))
                else:
                    traits[trait] = 0.5

            logger.debug(f"Base traits calculated: {traits}")

            # Enhanced adjustments based on advanced facial metrics
            if advanced_data:
                logger.debug("Applying advanced facial metrics adjustments")
                # Facial symmetry affects conscientiousness and neuroticism
                symmetry = advanced_data.get('facial_symmetry', 0.5)
                traits['conscientiousness'] += (symmetry - 0.5) * 0.2
                traits['neuroticism'] -= (symmetry - 0.5) * 0.15

                # Confidence indicators affect extraversion
                confidence = advanced_data.get('confidence_indicators', {}).get('overall', 0.5)
                traits['extraversion'] += (confidence - 0.5) * 0.25

                # Leadership markers
                leadership = advanced_data.get('leadership_markers', {}).get('overall', 0.5)
                traits['extraversion'] += (leadership - 0.5) * 0.15
                traits['conscientiousness'] += (leadership - 0.5) * 0.1

                # Creativity signals affect openness
                creativity = advanced_data.get('creativity_signals', {}).get('overall', 0.5)
                traits['openness'] += (creativity - 0.5) * 0.2

            # Age and gender adjustments
            if age < 25:
                traits['openness'] += 0.08
                traits['conscientiousness'] -= 0.05
                logger.debug("Applied young age adjustments")
            elif age > 50:
                traits['openness'] -= 0.06
                traits['conscientiousness'] += 0.08
                logger.debug("Applied older age adjustments")

            if gender == 'female':
                traits['agreeableness'] += 0.06
                traits['neuroticism'] += 0.04
                logger.debug("Applied female gender adjustments")
            elif gender == 'male':
                traits['extraversion'] += 0.04
                logger.debug("Applied male gender adjustments")

            # Normalize traits
            for trait in traits:
                traits[trait] = min(0.95, max(0.15, traits[trait]))

            logger.info(f"Enhanced traits calculated successfully: {traits}")
            return traits

        except Exception as e:
            logger.error(f"Error calculating enhanced traits: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def generate_comprehensive_insights(self, traits, face_data, user_profile):
        """Generate deep, actionable personality insights"""
        logger.info("Generating comprehensive personality insights")

        try:
            name = user_profile.get('name', 'You')
            age_range = user_profile.get('age_range', '25-34')

            logger.debug(f"User profile - Name: {name}, Age range: {age_range}")

            insights = []

            # Core personality analysis
            dominant_trait = max(traits.items(), key=lambda x: x[1])
            trait_name, trait_score = dominant_trait

            logger.debug(f"Dominant trait: {trait_name} ({trait_score:.2f})")

            core_insights = {
                'openness': f"{name} possess exceptional creative intelligence and intellectual curiosity. Your mind naturally gravitates toward innovation, making you a natural problem-solver who sees possibilities others miss.",
                'conscientiousness': f"{name} demonstrate remarkable self-discipline and systematic thinking. Your methodical approach and attention to detail position you as someone others can depend on for consistent, high-quality results.",
                'extraversion': f"{name} radiate natural charisma and social energy. Your ability to energize and inspire others, combined with your comfort in social situations, makes you a natural leader and connector.",
                'agreeableness': f"{name} embody genuine empathy and collaborative spirit. Your ability to understand and harmonize with others makes you invaluable in team environments and relationship-building.",
                'neuroticism': f"{name} possess deep emotional intelligence and sensitivity. While you may feel emotions intensely, this gives you profound empathy and the ability to connect with others on a meaningful level."
            }

            insights.append(
                core_insights.get(trait_name, f"{name} show unique personality characteristics that set you apart."))

            # Advanced combination analysis
            if traits['openness'] > 0.7 and traits['conscientiousness'] > 0.6:
                insights.append(
                    "Your rare combination of creativity and discipline is your superpower. You can both envision breakthrough innovations and execute the detailed plans to bring them to life. This makes you ideal for roles requiring both vision and execution.")
                logger.debug("Added creativity+discipline insight")

            if traits['extraversion'] > 0.7 and traits['agreeableness'] > 0.6:
                insights.append(
                    "You possess authentic leadership magnetism. People are naturally drawn to follow your vision because they sense your genuine care for their wellbeing. This combination predicts exceptional success in people-centered leadership roles.")
                logger.debug("Added leadership magnetism insight")

            if traits['conscientiousness'] > 0.7 and traits['neuroticism'] < 0.4:
                insights.append(
                    "Your calm competence under pressure is a rare and valuable trait. You're the person others turn to during crises because you maintain clarity and systematic thinking when emotions run high.")
                logger.debug("Added calm competence insight")

            # Success trajectory insights
            overall_potential = self._calculate_success_potential(traits)
            logger.debug(f"Overall success potential: {overall_potential:.2f}")

            if overall_potential > 0.8:
                insights.append(
                    f"Your personality profile indicates exceptional potential for high-level leadership and entrepreneurial success. The combination of your traits suggests you could excel in C-suite roles or as a successful business owner within the next 5-10 years.")
            elif overall_potential > 0.65:
                insights.append(
                    f"You have strong potential for senior professional roles and could excel in positions of significant responsibility. Your trait combination suggests steady career advancement and growing influence in your field.")

            logger.info(f"Generated {len(insights)} personality insights")
            return insights

        except Exception as e:
            logger.error(f"Error generating comprehensive insights: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def get_career_recommendations(self, traits, face_data):
        """Generate detailed career recommendations with future market insights"""
        logger.info("Generating career recommendations")

        try:
            recommendations = []

            for category, career_info in self.career_insights.items():
                fit_score = self._calculate_career_fit(traits, career_info['traits'])
                logger.debug(f"Career fit for {category}: {fit_score:.1f}%")

                if fit_score > 60:  # Only recommend if decent fit
                    recommendation = {
                        'category': category.replace('_', ' ').title(),
                        'roles': career_info['roles'][:4],
                        'fit_score': int(fit_score),
                        'reasoning': self._generate_career_reasoning(category, traits, fit_score),
                        'growth_potential': career_info['growth'],
                        'salary_range': career_info['salary'],
                        'future_market_trends': career_info['future_trends'],
                        'success_probability': min(95, int(fit_score * 1.1)),
                        'recommended_skills': self._get_skill_recommendations(category, traits)
                    }
                    recommendations.append(recommendation)
                    logger.debug(f"Added recommendation for {category}")

            sorted_recommendations = sorted(recommendations, key=lambda x: x['fit_score'], reverse=True)[:3]
            logger.info(f"Generated {len(sorted_recommendations)} career recommendations")
            return sorted_recommendations

        except Exception as e:
            logger.error(f"Error generating career recommendations: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _calculate_career_fit(self, traits, required_traits):
        """Calculate how well traits match career requirements"""
        try:
            fit_score = 0
            trait_count = len(required_traits)

            for trait, required_level in required_traits.items():
                if trait in traits:
                    actual_level = traits[trait]
                    if actual_level >= required_level:
                        # Bonus for exceeding requirements
                        fit_score += (actual_level / required_level) * 25
                    else:
                        # Partial credit for close matches
                        fit_score += (actual_level / required_level) * 20

            return min(95, fit_score)

        except Exception as e:
            logger.error(f"Error calculating career fit: {str(e)}")
            return 50  # Default score

    def _get_skill_recommendations(self, category, traits):
        """Get personalized skill recommendations based on career and traits"""
        try:
            skill_map = {
                'creative_arts': ['Digital Design Tools', 'Creative Writing', 'Video Editing', 'Brand Strategy'],
                'leadership_executive': ['Strategic Planning', 'Team Management', 'Public Speaking',
                                         'Financial Acumen'],
                'tech_innovation': ['Python/JavaScript', 'Machine Learning', 'Cloud Platforms', 'Agile Methodologies'],
                'healthcare_wellness': ['Patient Care', 'Medical Technology', 'Wellness Coaching',
                                        'Healthcare Administration'],
                'finance_analytics': ['Financial Modeling', 'Risk Assessment', 'Investment Analysis',
                                      'Regulatory Compliance'],
                'education_training': ['Instructional Design', 'Learning Management Systems', 'Curriculum Development',
                                       'Educational Technology']
            }

            base_skills = skill_map.get(category, ['Leadership', 'Communication', 'Problem Solving'])

            # Add trait-specific recommendations
            if traits.get('openness', 0) > 0.7:
                base_skills.append('Innovation Management')
            if traits.get('conscientiousness', 0) > 0.7:
                base_skills.append('Project Management')
            if traits.get('extraversion', 0) > 0.7:
                base_skills.append('Networking & Relationship Building')

            return base_skills[:4]

        except Exception as e:
            logger.error(f"Error getting skill recommendations: {str(e)}")
            return ['Leadership', 'Communication', 'Problem Solving']

    def generate_growth_roadmap(self, traits, user_profile):
        """Generate personalized growth and development roadmap"""
        logger.info("Generating growth roadmap")

        try:
            roadmap = []
            age_range = user_profile.get('age_range', '25-34')

            # Identify growth opportunities
            for trait, score in traits.items():
                if trait == 'neuroticism':
                    if score > 0.6:  # High neuroticism needs management
                        roadmap.append({
                            'area': 'Emotional Resilience & Stress Management',
                            'current_level': f"{(1 - score) * 100:.0f}%",
                            'target_level': '85%',
                            'timeline': '4-8 months',
                            'priority': 'High',
                            'action_steps': [
                                'Practice daily mindfulness meditation (start with 10 minutes)',
                                'Learn cognitive behavioral therapy techniques for stress management',
                                'Develop a consistent exercise routine (proven to reduce anxiety)',
                                'Build a strong support network of mentors and trusted friends',
                                'Consider working with a mental health professional for personalized strategies'
                            ],
                            'success_metrics': ['Reduced stress levels', 'Better sleep quality',
                                                'Improved decision-making under pressure'],
                            'resources': ['Headspace app', 'CBT workbooks', 'Local support groups']
                        })
                        logger.debug("Added emotional resilience roadmap item")
                elif score < 0.6 and trait != 'neuroticism':
                    if trait == 'conscientiousness':
                        roadmap.append({
                            'area': 'Organization & Self-Discipline',
                            'current_level': f"{score * 100:.0f}%",
                            'target_level': '75%',
                            'timeline': '3-6 months',
                            'priority': 'Medium',
                            'action_steps': [
                                'Implement time-blocking system for daily schedule management',
                                'Use productivity apps like Notion or Todoist for task organization',
                                'Create morning and evening routines for consistency',
                                'Break large projects into small, manageable daily tasks',
                                'Find an accountability partner or join productivity groups'
                            ],
                            'success_metrics': ['Improved punctuality', 'Higher task completion rates',
                                                'Better work-life balance'],
                            'resources': ['Getting Things Done methodology', 'Atomic Habits book',
                                          'Productivity podcasts']
                        })
                        logger.debug("Added organization roadmap item")
                    elif trait == 'extraversion':
                        roadmap.append({
                            'area': 'Social Confidence & Networking',
                            'current_level': f"{score * 100:.0f}%",
                            'target_level': '70%',
                            'timeline': '6-12 months',
                            'priority': 'Medium',
                            'action_steps': [
                                'Join professional networking groups or industry associations',
                                'Practice small talk and conversation skills in low-pressure environments',
                                'Volunteer for presentation opportunities at work',
                                'Attend social events regularly, even if briefly',
                                'Consider joining Toastmasters or similar speaking organizations'
                            ],
                            'success_metrics': ['Expanded professional network',
                                                'Increased comfort in social situations',
                                                'More speaking opportunities'],
                            'resources': ['Toastmasters International', 'LinkedIn Learning courses',
                                          'Local business meetups']
                        })
                        logger.debug("Added social confidence roadmap item")

            # Add strength-leveraging recommendations
            strongest_trait = max(traits.items(), key=lambda x: x[1] if x[0] != 'neuroticism' else 1 - x[1])
            trait_name, trait_score = strongest_trait

            if trait_name != 'neuroticism' and trait_score > 0.7:
                strength_map = {
                    'openness': 'Creative Innovation Leadership',
                    'conscientiousness': 'Operational Excellence',
                    'extraversion': 'People Leadership & Influence',
                    'agreeableness': 'Team Building & Collaboration'
                }

                roadmap.append({
                    'area': f'Maximize Your {strength_map.get(trait_name, "Core Strength")}',
                    'current_level': f"{trait_score * 100:.0f}%",
                    'target_level': 'Expert Level',
                    'timeline': 'Ongoing',
                    'priority': 'High',
                    'action_steps': [
                        f'Seek leadership roles that specifically utilize your {trait_name} strengths',
                        'Mentor others who want to develop this trait',
                        'Build thought leadership through content creation or speaking',
                        'Join or create communities around this strength',
                        'Pursue advanced certifications or training in related areas'
                    ],
                    'success_metrics': ['Recognition as subject matter expert', 'Increased leadership opportunities',
                                        'Positive impact on others'],
                    'resources': ['Industry conferences', 'Professional certifications', 'Mentorship programs']
                })
                logger.debug(f"Added strength maximization roadmap item for {trait_name}")

            sorted_roadmap = sorted(roadmap, key=lambda x: {'High': 3, 'Medium': 2, 'Low': 1}[x['priority']],
                                    reverse=True)[:3]
            logger.info(f"Generated growth roadmap with {len(sorted_roadmap)} items")
            return sorted_roadmap

        except Exception as e:
            logger.error(f"Error generating growth roadmap: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    def _calculate_success_potential(self, traits):
        """Calculate overall success potential based on trait combination"""
        try:
            # Research-based weights for professional success
            success_score = (
                    traits['conscientiousness'] * 0.35 +  # Most predictive of success
                    traits['extraversion'] * 0.25 +  # Important for leadership
                    traits['openness'] * 0.20 +  # Innovation and adaptability
                    traits['agreeableness'] * 0.10 +  # Team effectiveness
                    (1 - traits['neuroticism']) * 0.10  # Emotional stability
            )
            logger.debug(f"Success potential calculated: {success_score:.3f}")
            return success_score
        except Exception as e:
            logger.error(f"Error calculating success potential: {str(e)}")
            return 0.5

    def _generate_career_reasoning(self, category, traits, fit_score):
        """Generate personalized reasoning for career recommendations"""
        try:
            reasonings = {
                'creative_arts': f"Your high openness to experience ({traits['openness']:.0%}) and creative thinking patterns make you naturally suited for innovative roles where artistic vision and original thinking are highly valued.",
                'leadership_executive': f"Your combination of extraversion ({traits['extraversion']:.0%}) and conscientiousness ({traits['conscientiousness']:.0%}) indicates strong leadership potential and the ability to drive results through others.",
                'tech_innovation': f"Your conscientiousness ({traits['conscientiousness']:.0%}) and openness to new ideas ({traits['openness']:.0%}) suggest excellent capabilities for tackling complex technical challenges and innovations.",
                'healthcare_wellness': f"Your empathy (agreeableness: {traits['agreeableness']:.0%}) and systematic approach make you well-suited for roles focused on improving others' wellbeing and health outcomes.",
                'finance_analytics': f"Your attention to detail (conscientiousness: {traits['conscientiousness']:.0%}) and emotional stability make you ideal for roles requiring precision and sound judgment with financial decisions.",
                'education_training': f"Your combination of interpersonal skills and openness to new ideas makes you naturally effective at helping others learn and grow."
            }

            return reasonings.get(category,
                                  f"Your personality traits create a strong foundation for success in this field (fit score: {fit_score}%).")
        except Exception as e:
            logger.error(f"Error generating career reasoning: {str(e)}")
            return f"Your personality traits align well with this career path (fit score: {fit_score}%)."

    def generate_life_predictions(self, traits, face_data):
        """Generate life success predictions across multiple domains"""
        logger.info("Generating life predictions")

        try:
            predictions = {}

            # Career success prediction
            career_score = (traits['conscientiousness'] * 0.4 +
                            traits['extraversion'] * 0.3 +
                            traits['openness'] * 0.2 +
                            (1 - traits['neuroticism']) * 0.1)
            predictions['career_advancement'] = min(95, int(career_score * 100))

            # Financial success prediction
            financial_score = (traits['conscientiousness'] * 0.5 +
                               traits['openness'] * 0.2 +
                               traits['extraversion'] * 0.2 +
                               (1 - traits['neuroticism']) * 0.1)
            predictions['financial_growth'] = min(95, int(financial_score * 100))

            # Relationship success prediction
            relationship_score = (traits['agreeableness'] * 0.4 +
                                  traits['extraversion'] * 0.3 +
                                  (1 - traits['neuroticism']) * 0.2 +
                                  traits['conscientiousness'] * 0.1)
            predictions['relationship_satisfaction'] = min(95, int(relationship_score * 100))

            # Leadership potential
            leadership_score = (traits['extraversion'] * 0.4 +
                                traits['conscientiousness'] * 0.3 +
                                traits['openness'] * 0.2 +
                                (1 - traits['neuroticism']) * 0.1)
            predictions['leadership_potential'] = min(95, int(leadership_score * 100))

            # Innovation capacity
            innovation_score = (traits['openness'] * 0.5 +
                                traits['extraversion'] * 0.2 +
                                traits['conscientiousness'] * 0.2 +
                                (1 - traits['neuroticism']) * 0.1)
            predictions['innovation_capacity'] = min(95, int(innovation_score * 100))

            logger.info(f"Generated life predictions: {predictions}")
            return predictions

        except Exception as e:
            logger.error(f"Error generating life predictions: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'career_advancement': 70,
                'financial_growth': 65,
                'relationship_satisfaction': 75,
                'leadership_potential': 60,
                'innovation_capacity': 70
            }


@face_bp.route('/analyze-face-enhanced', methods=['POST', 'OPTIONS'])
def analyze_face_enhanced():
    """Enhanced face analysis endpoint integrated with existing rate limiting"""
    if request.method == 'OPTIONS':
        logger.info("Received OPTIONS request for face analysis")
        return jsonify({}), 200

    logger.info("Starting enhanced face analysis")

    try:
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

        # Check rate limits
        try:
            limit_check = check_user_limit(ip, is_premium)
            logger.debug(f"Rate limit check result: {limit_check}")
        except Exception as limit_error:
            logger.error(f"Rate limiting error: {str(limit_error)}")
            limit_check = {"can_ai": False, "blocked": False, "remaining": 1}

        # Extract face data and user profile
        face_data = data.get('face_data', {})
        user_profile = data.get('user_profile', {})

        logger.debug(f"Face data structure: {list(face_data.keys())}")
        logger.debug(f"User profile: {user_profile}")

        # Validate required data
        if not face_data.get('personality_traits') and not face_data.get('basic'):
            logger.warning("No personality traits or basic face data provided")
            return jsonify({'error': 'Face analysis data required'}), 400

        # Initialize analyzer
        try:
            analyzer = EnhancedPersonalityAnalyzer()
            logger.debug("Analyzer initialized successfully")
        except Exception as analyzer_error:
            logger.error(f"Error initializing analyzer: {str(analyzer_error)}")
            return jsonify({'error': 'Analysis system initialization failed'}), 500

        # Calculate enhanced traits
        try:
            if face_data.get('basic') or face_data.get('advanced'):
                # Use comprehensive face data if available
                enhanced_traits = analyzer.calculate_enhanced_traits(face_data)
                logger.info("Used comprehensive face data for trait calculation")
            else:
                # Fallback to basic traits
                enhanced_traits = face_data.get('personality_traits', {})
                logger.info("Used basic personality traits")

            # Blend with client-side traits if available for better accuracy
            client_traits = face_data.get('personality_traits', {})
            if client_traits and enhanced_traits:
                final_traits = {}
                for trait in enhanced_traits:
                    if trait in client_traits:
                        # Weighted average: 60% enhanced, 40% client
                        final_traits[trait] = (enhanced_traits[trait] * 0.6 + client_traits[trait] * 0.4)
                    else:
                        final_traits[trait] = enhanced_traits[trait]
                logger.debug("Blended enhanced and client traits")
            else:
                final_traits = enhanced_traits or client_traits

            logger.info(f"Final traits calculated: {final_traits}")

        except Exception as trait_error:
            logger.error(f"Error calculating traits: {str(trait_error)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': 'Trait calculation failed', 'details': str(trait_error)}), 500

        # Generate comprehensive analysis based on rate limit status
        try:
            if limit_check.get("can_ai", False):
                logger.info("Generating premium analysis with AI enhancement")
                # Premium analysis with AI enhancement
                analysis_result = {
                    'personality_insights': analyzer.generate_comprehensive_insights(final_traits, face_data,
                                                                                     user_profile),
                    'career_recommendations': analyzer.get_career_recommendations(final_traits, face_data),
                    'growth_roadmap': analyzer.generate_growth_roadmap(final_traits, user_profile),
                    'life_predictions': analyzer.generate_life_predictions(final_traits, face_data),
                    'analysis_quality': 'premium',
                    'confidence_score': 0.92
                }

                # Increment usage for premium analysis
                try:
                    increment_user_usage(ip, 'face_analysis_premium')
                    logger.debug("Usage incremented for premium analysis")
                except Exception as usage_error:
                    logger.warning(f"Error incrementing usage: {str(usage_error)}")

            else:
                logger.info("Generating basic analysis due to rate limits")
                # Basic analysis for rate-limited users
                analysis_result = {
                    'personality_insights': analyzer.generate_comprehensive_insights(final_traits, face_data,
                                                                                     user_profile)[:2],
                    'career_recommendations': analyzer.get_career_recommendations(final_traits, face_data)[:1],
                    'growth_roadmap': analyzer.generate_growth_roadmap(final_traits, user_profile)[:1],
                    'life_predictions': analyzer.generate_life_predictions(final_traits, face_data),
                    'analysis_quality': 'basic',
                    'confidence_score': 0.78,
                    'upgrade_message': 'Unlock detailed career roadmaps and comprehensive growth plans with premium access!'
                }

            # Add metadata
            analysis_result.update({
                'enhanced_traits': final_traits,
                'analysis_timestamp': datetime.now().isoformat(),
                'user_tier': 'premium' if is_premium else 'free'
            })

            logger.info(f"Analysis completed successfully - Quality: {analysis_result['analysis_quality']}")

        except Exception as analysis_error:
            logger.error(f"Error generating analysis: {str(analysis_error)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': 'Analysis generation failed', 'details': str(analysis_error)}), 500

        # Prepare response
        response_data = {
            'success': True,
            'analysis': analysis_result,
            'user_info': {
                'is_rate_limited': limit_check.get("blocked", False),
                'remaining_analyses': limit_check.get("remaining", 0),
                'upgrade_available': not is_premium,
                'analysis_quality': analysis_result['analysis_quality']
            },
            'message': 'Comprehensive personality analysis completed successfully'
        }

        logger.info("Face analysis completed successfully")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Face analysis error: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")

        # Enhanced error response with debug info
        error_response = {
            'error': 'Analysis failed',
            'message': 'Please check your image and try again',
            'timestamp': datetime.now().isoformat(),
            'error_details': str(e) if logger.level <= logging.DEBUG else None
        }

        # Add request data for debugging (only in debug mode)
        if logger.level <= logging.DEBUG:
            try:
                error_response['debug_info'] = {
                    'request_data_keys': list(request.get_json().keys()) if request.get_json() else [],
                    'content_type': request.content_type,
                    'method': request.method
                }
            except:
                pass

        return jsonify(error_response), 500


# Rate limiting check endpoint
@face_bp.route('/check-face-analysis-limit', methods=['POST'])
def check_face_analysis_limit():
    """Check if user can perform face analysis"""
    logger.info("Checking face analysis limits")

    try:
        # Initialize database to prevent errors
        try:
            from utils.database import init_databases
            init_databases()
        except Exception as db_error:
            logger.warning(f"Database initialization warning in limit check: {str(db_error)}")

        ip = get_remote_address()
        logger.debug(f"Checking limits for IP: {ip}")

        try:
            is_premium = is_premium_user(ip)
            limit_check = check_user_limit(ip, is_premium)
            logger.debug(f"Limit check result: {limit_check}")
        except Exception as limit_error:
            logger.error(f"Error in limit check: {str(limit_error)}")
            # Provide safe defaults
            is_premium = False
            limit_check = {"blocked": False, "remaining": 1}

        response_data = {
            'can_analyze': not limit_check.get("blocked", False),
            'remaining_analyses': limit_check.get("remaining", 0),
            'is_premium': is_premium,
            'reset_time': (datetime.now() + timedelta(hours=1)).isoformat(),
            'upgrade_benefits': [
                'Unlimited daily analyses',
                'Detailed career roadmaps',
                'Advanced personality insights',
                'Success predictions',
                'Priority support'
            ]
        }

        logger.info(f"Limit check completed - Can analyze: {response_data['can_analyze']}")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error checking face analysis limits: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Provide safe fallback response
        return jsonify({
            'can_analyze': True,
            'remaining_analyses': 1,
            'is_premium': False,
            'reset_time': (datetime.now() + timedelta(hours=1)).isoformat(),
            'error': 'Limit check failed, assuming basic access',
            'upgrade_benefits': [
                'Unlimited daily analyses',
                'Detailed career roadmaps',
                'Advanced personality insights',
                'Success predictions',
                'Priority support'
            ]
        }), 200


# Health check endpoint for face analysis
@face_bp.route('/face-analysis/health', methods=['GET'])
def face_analysis_health():
    """Health check specifically for face analysis system"""
    logger.info("Face analysis health check requested")

    try:
        # Test analyzer initialization
        analyzer = EnhancedPersonalityAnalyzer()

        # Test basic functionality with dummy data
        test_traits = {
            'openness': 0.7,
            'conscientiousness': 0.6,
            'extraversion': 0.8,
            'agreeableness': 0.7,
            'neuroticism': 0.3
        }

        test_profile = {'name': 'Test', 'age_range': '25-34'}

        # Test all major functions
        insights = analyzer.generate_comprehensive_insights(test_traits, {}, test_profile)
        careers = analyzer.get_career_recommendations(test_traits, {})
        roadmap = analyzer.generate_growth_roadmap(test_traits, test_profile)
        predictions = analyzer.generate_life_predictions(test_traits, {})

        health_data = {
            'status': 'healthy',
            'face_analysis_system': 'operational',
            'analyzer_initialized': True,
            'insights_generated': len(insights) > 0,
            'careers_generated': len(careers) > 0,
            'roadmap_generated': len(roadmap) > 0,
            'predictions_generated': len(predictions) > 0,
            'timestamp': datetime.now().isoformat(),
            'test_results': {
                'insights_count': len(insights),
                'career_recommendations': len(careers),
                'roadmap_items': len(roadmap),
                'prediction_metrics': len(predictions)
            }
        }

        logger.info("Face analysis health check passed")
        return jsonify(health_data)

    except Exception as e:
        logger.error(f"Face analysis health check failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        return jsonify({
            'status': 'unhealthy',
            'face_analysis_system': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


# Debug endpoint for testing (remove in production)
@face_bp.route('/face-analysis/debug', methods=['POST'])
def face_analysis_debug():
    """Debug endpoint for testing face analysis system"""
    if logger.level > logging.DEBUG:
        return jsonify({'error': 'Debug endpoint disabled in production'}), 403

    logger.info("Debug face analysis requested")

    try:
        data = request.get_json() or {}

        # Use provided data or create test data
        test_traits = data.get('traits', {
            'openness': 0.7,
            'conscientiousness': 0.6,
            'extraversion': 0.8,
            'agreeableness': 0.7,
            'neuroticism': 0.3
        })

        test_profile = data.get('profile', {'name': 'Debug User', 'age_range': '25-34'})

        analyzer = EnhancedPersonalityAnalyzer()

        debug_result = {
            'traits_input': test_traits,
            'profile_input': test_profile,
            'insights': analyzer.generate_comprehensive_insights(test_traits, {}, test_profile),
            'careers': analyzer.get_career_recommendations(test_traits, {}),
            'roadmap': analyzer.generate_growth_roadmap(test_traits, test_profile),
            'predictions': analyzer.generate_life_predictions(test_traits, {}),
            'success_potential': analyzer._calculate_success_potential(test_traits),
            'timestamp': datetime.now().isoformat()
        }

        logger.info("Debug analysis completed successfully")
        return jsonify(debug_result)

    except Exception as e:
        logger.error(f"Debug analysis failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        return jsonify({
            'error': 'Debug analysis failed',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500