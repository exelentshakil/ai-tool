from openai import OpenAI
from utils.database import get_openai_cost_today, get_openai_cost_month, log_openai_cost_enhanced
from config.settings import OPENAI_API_KEY, DAILY_OPENAI_BUDGET, MONTHLY_OPENAI_BUDGET
import re
import html
import time
import json

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_ai_analysis(tool_config, user_data, ip, localization=None):
    """Ultra-enhanced AI analysis with hyper-local specificity and maximum value"""
    start_time = time.time()

    # Budget check
    try:
        daily_budget = float(DAILY_OPENAI_BUDGET)
        monthly_budget = float(MONTHLY_OPENAI_BUDGET)
    except (ValueError, TypeError):
        daily_budget = 10.0
        monthly_budget = 100.0

    if get_openai_cost_today() >= daily_budget or get_openai_cost_month() >= monthly_budget:
        return create_simple_fallback(tool_config, user_data, localization)

    # Extract comprehensive tool information
    category = tool_config.get("category", "general")
    tool_name = tool_config.get("seo_data", {}).get("title", "Calculator")
    tool_slug = tool_config.get("slug", "")
    category_lower = category.lower()

    if category_lower in ["appearance", "face", "photo", "image"]:
        system_prompt = get_face_system_prompt(localization.get("language", "English"))
    else:
        system_prompt = get_expert_system_prompt(localization)

    # Clean and prepare data with enhanced location handling
    cleaned_data = clean_user_data(user_data)

    # Build the massive, super-detailed prompt
    prompt = build_enhanced_prompt(tool_name, category, tool_slug, cleaned_data, localization)

    try:
        model_name = "gpt-4o"
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            temperature=0.9
        )

        ai_analysis = response.choices[0].message.content
        pt, ct = response.usage.prompt_tokens, response.usage.completion_tokens
        total_tokens = pt + ct

        # Correct gpt-4o cost calculation
        cost = (pt * 2.50 + ct * 10.00) / 1000000

        response_time = int((time.time() - start_time) * 1000)

        # Enhanced logging
        success = log_openai_cost_enhanced(
            cost=cost,
            tokens=total_tokens,
            model=model_name,
            ip=ip,
            tools_slug=tool_name,
            response_time=response_time
        )

        if success:
            print(f"✅ Ultra-analysis completed: {tool_name} took {response_time}ms, cost: ${cost:.4f}")
        else:
            print(f"⚠️ Cost logging failed for {tool_name}")

        # Format with maximum value presentation
        return format_response(ai_analysis, cleaned_data, tool_config, localization)

    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        print(f"❌ AI analysis failed after {response_time}ms: {str(e)}")

        try:
            log_openai_cost_enhanced(cost=0, tokens=0, model="error", ip=ip, tools_slug=tool_name)
        except:
            pass

        return create_simple_fallback(tool_config, cleaned_data, localization)


def clean_user_data(user_data):
    """Enhanced data cleaning with comprehensive location processing"""
    cleaned = {}

    for key, value in user_data.items():
        if key == 'locationData':
            if isinstance(value, dict):
                cleaned[key] = value
            else:
                cleaned[key] = {'name': str(value)}
        elif key in ['currency', 'currency_symbol']:
            if value == 'u20ac':
                cleaned[key] = 'EUR'
            elif value == 'u00a3':
                cleaned[key] = 'GBP'
            else:
                cleaned[key] = value
        else:
            cleaned[key] = value

    return cleaned

def build_enhanced_prompt(tool_name, category, tool_slug, user_data, localization=None):
    """Build the most comprehensive, value-packed prompt with clean formatting"""
    # NEW: Simple category check for personality tools

    category_lower = category.lower()

    # --- NEW: Route for face mega analyzer ---
    if category_lower in ["appearance", "face", "photo", "image"]:
        return build_face_mega_prompt(tool_name, user_data, localization)
    # High-value personality categories get specialized treatment
    if category_lower in ['psychology', 'personality', 'intelligence']:
        return build_psychology_prompt(tool_name, user_data, localization)
    elif category_lower in ['career', 'professional']:
        return build_career_prompt(tool_name, user_data, localization)
    elif category_lower in ['relationships', 'dating']:
        return build_relationship_prompt(tool_name, user_data, localization)
    elif category_lower in ['personal development']:
        return build_development_prompt(tool_name, user_data, localization)

    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    currency = localization.get('currency', 'USD')
    country = localization.get('country_name', '')
    country_code = localization.get('country_code', '')

    if currency == 'u20ac':
        currency = 'EUR'
        currency_symbol = '€'
    elif currency == 'u00a3':
        currency = 'GBP'
        currency_symbol = '£'
    else:
        currency_symbol = '$'

    # Extract hyper-specific location details
    location_info = extract_location_details(user_data, country, localization)

    # Build comprehensive user context
    user_context = build_user_context(user_data, currency, tool_slug)

    # Detect tool intent and purpose from slug/category
    tool_intent = detect_tool_intent(tool_slug, category, tool_name)

    return f"""You are the ULTIMATE LOCAL EXPERT for {location_info['specific_area']} providing comprehensive, actionable analysis.

CRITICAL MISSION: Provide MAXIMUM VALUE that could save users hundreds or thousands of {currency_symbol} through expert guidance.

TOOL REQUEST:
Tool: {tool_name}
Category: {category}
Type: {tool_intent['purpose']}
Intent: {tool_intent['business_value']}

USER DATA:
{user_context}

LOCATION CONTEXT:
Exact Location: {location_info['detailed_location']}
Service Area: {location_info['service_context']}

REQUIREMENTS:
- Reference exact location ({location_info['display_location']}) in calculations
- Provide detailed mathematical breakdowns in {currency_symbol}
- Include specific company names, phone numbers, websites
- Give immediate actionable steps with local contacts
- Include local regulations and compliance requirements
- Provide money-saving strategies and local discounts

FORMAT YOUR RESPONSE WITH THESE EXACT SECTIONS:

CALCULATION RESULT
For {location_info['display_location']}: [Detailed step-by-step calculation]
Total Estimated Amount: {currency_symbol}X,XXX
Potential Annual Savings: {currency_symbol}X,XXX
Local Market Rate: [comparison to {country} average]

LOCAL INSIGHTS
1. [First key insight about local market/regulations]
2. [Second insight about opportunities in your area]  
3. [Third insight about local requirements/deadlines]

LOCAL SERVICE PROVIDERS
1. Company Name
   Website: [Company Name](https://website.com)
   Phone: +1-XXX-XXX-XXXX
   Address: [Local address]
   Specialty: [What they do best]
   Pricing: {currency_symbol}X,XXX typical range

2. [Continue with 4-5 more local companies]

COMPARISON RESOURCES
- [Local comparison website]: [Website Name](https://website.com)
- [Government resource]: [Agency Name](https://gov-website.com)  
- [Consumer protection]: [Organization](https://website.com)

ACTION PLAN
1. [First immediate step with specific contact]
2. [Second step with timeline and requirements]
3. [Third step with local contacts and deadlines]

Timeline: [Specific dates and deadlines for {country}]
Required Documents: [List of needed paperwork]

MONEY-SAVING STRATEGIES
- [Specific way to save money in {location_info['service_area']}]
- [Local discount or program available]
- [Best timing for maximum savings]

EXPERT CONTACTS
- [Type of professional needed]: [Where to find them in {location_info['service_area']}]
- [Professional association]: [Contact information]
- [Recommended specialist]: [Contact details]

SUCCESS FACTORS
✓ [What makes this successful in {country}]
✗ [Common mistake to avoid in {location_info['service_area']}]
📊 [Expected outcome metrics]

Use REAL company names, actual phone numbers, and specific websites. Make this worth hundreds of {currency_symbol} in professional consultation value.

Respond in {language} with local terminology for {country}."""

def get_face_system_prompt(language="English"):
    return f"""You are an AI face analysis assistant. 
You CAN analyze base64-encoded face images provided as user input.
Use them to describe appearance, beauty score, symmetry, smile, age guess, and comparisons.
Do NOT refuse. Be clear, fun, non-medical. Respond in {language}."""

def build_face_mega_prompt(tool_name, user_data, localization=None):
    language = (localization or {}).get("language", "English")
    has_img2 = bool(user_data.get("photo_url_2"))

    return f"""
You are an AI face and personality analyzer. Your role is to give users
a fun but highly detailed, non-medical report from one or two face photos.

Always return information in clear, structured SECTIONS with headers.
Keep tone playful but professional. Avoid medical claims.

INPUT: One or two face photos.
TASK: Provide ALL of these sections:

FACE SYMMETRY
- Symmetry score (0–100)
- 2–3 observations about balance or asymmetry
- What symmetry usually means for attractiveness

BEAUTY SCORE
- Beauty score (0–100)
- Male vs female differences if relevant
- Top 3 factors that raised/lowered the score

AGE GUESS
- Estimated age range
- Features that make them look younger
- Features that make them look older

CELEBRITY LOOKALIKE
- Top 3 lookalikes with similarity %
- Short reason why (jawline, eyes, hairstyle, etc.)

SMILE RATING
- Smile score (1–10)
- Strengths of the smile
- One improvement tip

FACE SHAPE
- Identify shape (oval, round, square, heart, diamond)
- 2 hairstyle tips
- 1 accessory suggestion (e.g., glasses style)

SKIN & EYES
- Undertone (warm/cool/neutral)
- Visible eye color details
- Contrast level (high/medium/low)

{"SIDE BY SIDE COMPARISON\n- Compare A vs B on beauty, age, and smile\n- Give differences in bullet points\n- End with a compatibility % and short playful verdict" if has_img2 else ""}

PRACTICAL TIPS
- 3 short actionable tips anyone can apply right away

QUALITY NOTES
- Confidence: high/medium/low
- Any image quality issues
- Retake advice for clearer results

SHARE PROMPT
- A one-line playful caption for sharing results on social media

Respond in {language}. Keep format clean with clear section titles.
"""


def build_psychology_prompt(tool_name, user_data, localization=None):
    """Ultra-comprehensive psychology prompt for GPT-4o"""

    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    location = user_data.get('location', 'your area')

    # Build detailed context
    context_items = []
    for key, value in user_data.items():
        if key != 'location' and value:
            context_items.append(f"{key.replace('_', ' ').title()}: {value}")

    context_str = " | ".join(context_items) if context_items else "Basic assessment"

    return f"""You are Dr. Elena Volkov, a renowned cognitive scientist with 25 years of experience in personality psychology, intelligence research, and human behavioral analysis. You've published 150+ peer-reviewed papers and consulted for Fortune 500 companies on talent optimization.

ASSESSMENT: {tool_name}
PARTICIPANT PROFILE: {context_str}
ANALYSIS LOCATION: {location}

SCIENTIFIC FRAMEWORK:
Base your analysis on established psychological models including Big Five personality theory, Gardner's multiple intelligences, Sternberg's triarchic theory, and contemporary neuroscience research. Ensure all insights are grounded in peer-reviewed psychological science.

ETHICAL STANDARDS:
- Maintain highest professional standards with balanced, growth-oriented insights
- Avoid pathologizing normal personality variations
- Include appropriate professional consultation disclaimers
- Focus on strengths-based development approaches
- Ensure cultural sensitivity and inclusive language

COMPREHENSIVE ANALYSIS STRUCTURE:

COGNITIVE ARCHITECTURE ASSESSMENT
[Provide detailed analysis of their thinking patterns, information processing style, and cognitive strengths. Reference specific psychological research that supports your observations. Include statistical comparisons to population norms.]

PERSONALITY DYNAMICS PROFILE
Core Traits Analysis: [Big Five dimensions with percentiles and behavioral implications]
Cognitive Processing Style: [How they approach problems, learn, and make decisions]
Interpersonal Patterns: [Communication style, social preferences, leadership tendencies]
Stress Response Profile: [How they handle pressure and uncertainty]
Motivation Drivers: [What energizes and sustains their engagement]

INTELLIGENCE TYPE CLASSIFICATION
Primary Intelligence Domains: [Identify top 2-3 from Gardner's framework with specific examples]
Cognitive Strengths: [Detailed analysis with percentile rankings]
Processing Speed Profile: [How quickly they handle different types of information]
Working Memory Characteristics: [Capacity and efficiency patterns]
Creative Thinking Style: [Approach to innovation and problem-solving]

BEHAVIORAL PREDICTION MODEL
High-Performance Conditions: [Specific environments where they excel]
Potential Challenge Areas: [Situations that may be difficult with coping strategies]
Learning Optimization: [Personalized study and skill development approaches]
Decision-Making Patterns: [How they evaluate options and make choices]
Stress Triggers and Mitigation: [Specific stressors and evidence-based management techniques]

DEVELOPMENT ROADMAP
Immediate Strengths to Leverage: [Top 3 abilities to capitalize on now]
Skill Enhancement Opportunities: [Areas with highest growth potential]
Learning Methodologies: [Specific techniques that match their cognitive style]
Performance Optimization Strategies: [Research-backed approaches for improvement]
Long-term Development Trajectory: [5-year growth potential and milestones]

LOCAL RESOURCES AND OPPORTUNITIES
Professional Development: [Specific programs, courses, or resources in {location}]
Networking Communities: [Relevant professional or interest groups]
Educational Institutions: [Universities, training centers, or workshops]
Mental Health Support: [Qualified professionals for ongoing development]
Career Services: [Local career counseling or coaching resources]

EVIDENCE-BASED RECOMMENDATIONS
Immediate Action Items: [3 specific steps to take this week]
30-Day Challenge: [Structured goal with measurable outcomes]
90-Day Development Plan: [Comprehensive skill-building program]
Annual Growth Objectives: [Long-term goals aligned with their profile]

STATISTICAL INSIGHTS
Population Comparisons: [How they rank on key dimensions]
Personality Rarity: [Percentage of population sharing similar traits]
Cognitive Uniqueness: [Distinctive combinations of abilities]
Performance Predictors: [Research-backed success indicators]

SCIENTIFIC DISCLAIMERS:
This assessment is based on self-reported information and established psychological frameworks. Individual differences, cultural factors, and life circumstances can influence personality expression. For comprehensive psychological evaluation or mental health concerns, consult qualified professionals. Personality can evolve over time through intentional development and life experiences.

RESEARCH REFERENCES: Include relevant citations to psychological research that supports key insights provided.

QUALITY STANDARDS:
- Provide specific, actionable insights rather than generic descriptions
- Include quantitative measures (percentiles, rankings, statistical comparisons)
- Balance scientific rigor with accessible language
- Ensure insights are immediately applicable to their life context
- Maintain optimistic yet realistic tone throughout

Generate analysis that demonstrates deep psychological expertise while remaining accessible and immediately useful for personal development.

Respond in {language} with the authority of a leading research psychologist."""

def build_career_prompt(tool_name, user_data, localization=None):
    """Professional career analysis prompt optimized for GPT-4o"""

    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    location = user_data.get('location', 'your area')
    currency = localization.get('currency', 'USD')

    context_items = []
    for key, value in user_data.items():
        if key != 'location' and value:
            context_items.append(f"{key.replace('_', ' ').title()}: {value}")

    context_str = " | ".join(context_items)

    return f"""You are Marcus Chen, Senior Director of Talent Strategy with 20 years of experience at top-tier consulting firms including McKinsey, Deloitte, and PwC. You've guided 10,000+ professionals through career transitions and have deep expertise in labor market analytics, compensation trends, and organizational psychology.

CAREER ASSESSMENT: {tool_name}
CLIENT PROFILE: {context_str}
MARKET LOCATION: {location}
CURRENCY: {currency}

ANALYSIS FRAMEWORK:
Utilize Holland's RIASEC model, O*NET occupational database, labor market statistics, industry trend analysis, and validated career assessment methodologies. Ground all recommendations in current market data and evidence-based career development theory.

COMPREHENSIVE CAREER ANALYSIS:

PROFESSIONAL PROFILE ASSESSMENT
Core Competencies: [Identify top 5 skills with proficiency levels]
Work Style Preferences: [Detailed analysis of ideal work environment]
Values Alignment: [What matters most in their career satisfaction]
Leadership Potential: [Natural management and influence capabilities]
Collaboration Style: [How they work best with teams and individuals]

MARKET-MATCHED CAREER PATHS
Primary Career Tracks: [3-5 specific roles with detailed descriptions]
Growth Trajectory Analysis: [5-10 year advancement possibilities]
Salary Benchmarks: [Specific compensation ranges for {location}]
Industry Trend Alignment: [How their profile matches emerging sectors]
Skill Gap Analysis: [What additional capabilities would accelerate progress]

COMPETITIVE ADVANTAGE ASSESSMENT
Unique Value Proposition: [What makes them distinctive in the job market]
Transferable Skills Inventory: [Abilities that cross industry boundaries]
Market Differentiation: [How to position themselves competitively]
Personal Branding Strategy: [Professional identity and messaging]
Network Leverage Opportunities: [How to build strategic relationships]

LOCAL MARKET INTELLIGENCE
Industry Landscape in {location}: [Key employers, growth sectors, opportunities]
Compensation Analysis: [Salary ranges, benefits, equity considerations]
Networking Ecosystems: [Professional associations, events, communities]
Educational Pathways: [Local universities, certifications, training programs]
Regulatory Considerations: [Licensing, credentials, legal requirements]

STRATEGIC CAREER ROADMAP
Immediate Opportunities: [Roles they could pursue within 6 months]
Short-term Development: [Skills to build in next 1-2 years]
Medium-term Positioning: [3-5 year strategic moves]
Long-term Vision: [10+ year leadership and expertise goals]
Alternative Pathways: [Entrepreneurship, consulting, portfolio careers]

EXECUTION STRATEGY
Resume Optimization: [Key elements to highlight for their target roles]
Interview Preparation: [Specific talking points and examples to develop]
LinkedIn Strategy: [Profile optimization and networking approach]
Portfolio Development: [Work samples and achievements to showcase]
Reference Network: [Professional relationships to cultivate]

FINANCIAL OPTIMIZATION
Salary Negotiation Strategy: [Research-backed approaches for their market]
Total Compensation Analysis: [Beyond base salary considerations]
Career ROI Calculations: [Investment in education vs. income potential]
Geographic Arbitrage: [Location-based optimization opportunities]
Equity and Benefits Evaluation: [Non-cash compensation optimization]

RISK MITIGATION
Industry Disruption Analysis: [How automation/AI affects their target roles]
Recession-Proofing Strategy: [Building career resilience]
Skill Obsolescence Prevention: [Continuous learning priorities]
Career Pivot Preparation: [Maintaining flexibility and options]
Financial Security Planning: [Building career stability]

IMMEDIATE ACTION PLAN
This Week: [3 specific steps to take immediately]
This Month: [Structured goals with deadlines]
Next Quarter: [Major milestones and achievements]
This Year: [Annual objectives and success metrics]

LOCAL PROFESSIONAL RESOURCES
Career Services: [Specific organizations and professionals in {location}]
Executive Recruiters: [Relevant search firms and placement agencies]
Professional Development: [Local programs, workshops, conferences]
Mentorship Opportunities: [How to find industry mentors and advisors]
Entrepreneurship Support: [Incubators, accelerators, funding sources]

MARKET DATA INSIGHTS
Supply/Demand Analysis: [Competition levels in target roles]
Growth Projections: [Industry expansion forecasts]
Skill Premium Analysis: [Which capabilities command highest compensation]
Geographic Mobility: [Opportunities in other markets]
Remote Work Considerations: [Virtual opportunity assessment]

Generate career guidance that combines strategic thinking with tactical execution, ensuring every recommendation is actionable and market-informed.

Respond in {language} with the expertise of a senior executive search consultant."""

def build_relationship_prompt(tool_name, user_data, localization=None):
    """Comprehensive relationship analysis prompt for GPT-4o"""

    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    location = user_data.get('location', 'your area')

    context_items = []
    for key, value in user_data.items():
        if key != 'location' and value:
            context_items.append(f"{key.replace('_', ' ').title()}: {value}")

    context_str = " | ".join(context_items)

    return f"""You are Dr. Sarah Gottman, a licensed clinical psychologist specializing in relationship dynamics with 18 years of practice. You've studied under John Gottman, completed advanced training in Emotionally Focused Therapy (EFT), and have helped over 3,000 individuals and couples build healthier relationships.

RELATIONSHIP ASSESSMENT: {tool_name}
CLIENT PROFILE: {context_str}
LOCATION: {location}

THEORETICAL FOUNDATION:
Apply Gottman Method principles, attachment theory, communication research, conflict resolution science, and evidence-based relationship interventions. Ensure all insights are grounded in peer-reviewed relationship science and clinical best practices.

COMPREHENSIVE RELATIONSHIP ANALYSIS:

ATTACHMENT AND BONDING PROFILE
Attachment Style Assessment: [Secure, anxious, avoidant, or disorganized patterns]
Bonding Preferences: [How they form and maintain emotional connections]
Trust Development: [Patterns in building and maintaining trust]
Intimacy Comfort: [Physical, emotional, and intellectual intimacy preferences]
Vulnerability Patterns: [How they share personal information and emotions]

COMMUNICATION DYNAMICS
Expression Style: [How they share thoughts, feelings, and needs]
Listening Patterns: [Active listening skills and empathy demonstration]
Conflict Approach: [How they handle disagreements and tensions]
Emotional Regulation: [Managing emotions during difficult conversations]
Repair Behaviors: [How they recover from relationship mistakes or hurts]

COMPATIBILITY FACTORS
Values Alignment: [Core life values and their importance in relationships]
Lifestyle Compatibility: [Daily routines, social preferences, life pace]
Growth Trajectory: [Personal development and shared evolution potential]
Communication Rhythm: [How often and deeply they prefer to connect]
Conflict Resolution Style: [Approach to working through disagreements]

RELATIONSHIP PATTERNS ANALYSIS
Partner Selection: [Unconscious patterns in choosing romantic partners]
Relationship Progression: [How they move through relationship stages]
Maintenance Behaviors: [What they do to nurture ongoing relationships]
Stress Response: [How external pressures affect their relationships]
Boundary Management: [Personal space and autonomy within relationships]

LOVE AND CONNECTION BLUEPRINT
Love Languages Expression: [Primary ways they show affection and care]
Love Languages Reception: [How they best receive love and appreciation]
Emotional Needs Hierarchy: [Most important emotional requirements]
Physical Affection Preferences: [Comfort with various forms of physical touch]
Quality Time Preferences: [How they like to spend time with partners]

PERSONAL GROWTH OPPORTUNITIES
Self-Awareness Development: [Areas for increased emotional intelligence]
Communication Skill Building: [Specific interpersonal abilities to strengthen]
Boundary Setting: [Healthy limit-setting in relationships]
Emotional Regulation: [Managing intense emotions more effectively]
Empathy Enhancement: [Deepening understanding of others' perspectives]

RELATIONSHIP SUCCESS STRATEGIES
Optimal Partnership Conditions: [Environments where their relationships thrive]
Red Flags Recognition: [Warning signs they should be aware of]
Healthy Relationship Habits: [Daily practices that strengthen bonds]
Conflict Prevention: [Proactive strategies to minimize relationship stress]
Repair and Recovery: [How to bounce back from relationship challenges]

LOCAL RELATIONSHIP RESOURCES
Couples Therapy: [Qualified therapists and counselors in {location}]
Support Groups: [Relationship education and support communities]
Workshops and Classes: [Communication and relationship skill building]
Mediation Services: [Professional conflict resolution assistance]
Educational Programs: [Relationship enhancement courses and seminars]

PRACTICAL IMPLEMENTATION GUIDE
Daily Practices: [Simple habits to strengthen current relationships]
Weekly Check-ins: [Structured relationship maintenance activities]
Monthly Goals: [Relationship development objectives]
Quarterly Reviews: [Relationship health assessment and adjustment]
Annual Planning: [Long-term relationship vision and goal-setting]

COMMUNICATION ENHANCEMENT TOOLKIT
Active Listening Techniques: [Specific skills for better understanding]
Emotional Expression: [Healthy ways to share feelings and needs]
Difficult Conversations: [Framework for addressing challenging topics]
Appreciation Practices: [Regular ways to show gratitude and recognition]
Conflict De-escalation: [Techniques for reducing tension and hostility]

RELATIONSHIP HEALTH METRICS
Green Flags: [Signs of healthy relationship dynamics]
Yellow Flags: [Areas requiring attention and improvement]
Red Flags: [Serious concerns requiring professional intervention]
Growth Indicators: [Signs that relationships are developing positively]
Success Measures: [How to evaluate relationship satisfaction and progress]

PROFESSIONAL DISCLAIMERS:
This assessment provides general relationship insights based on established psychological research. For serious relationship conflicts, domestic violence concerns, or mental health issues, please consult qualified mental health professionals. Individual circumstances may require personalized therapeutic intervention.

Create analysis that empowers healthy relationship development while maintaining appropriate clinical boundaries and ethical standards.

Respond in {language} with the compassionate expertise of a seasoned relationship therapist."""

def build_development_prompt(tool_name, user_data, localization=None):
    """Comprehensive personal development prompt for GPT-4o"""

    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    location = user_data.get('location', 'your area')

    context_items = []
    for key, value in user_data.items():
        if key != 'location' and value:
            context_items.append(f"{key.replace('_', ' ').title()}: {value}")

    context_str = " | ".join(context_items)

    return f"""You are Dr. James Clear, combining the expertise of a behavioral scientist, performance coach, and personal development researcher with 15 years of experience. You've studied habit formation, goal achievement psychology, motivation science, and have guided thousands through transformational growth journeys.

PERSONAL DEVELOPMENT ASSESSMENT: {tool_name}
INDIVIDUAL PROFILE: {context_str}
DEVELOPMENT LOCATION: {location}

SCIENTIFIC FOUNDATION:
Apply behavioral psychology principles, neuroplasticity research, goal-setting theory, habit formation science, motivation psychology, and evidence-based personal development methodologies. Ground all recommendations in peer-reviewed research and proven behavioral change techniques.

COMPREHENSIVE GROWTH ANALYSIS:

CURRENT STATE ASSESSMENT
Strengths Inventory: [Core capabilities and natural talents with specific examples]
Growth Edge Identification: [Areas with highest development potential]
Value System Analysis: [Core beliefs and principles that drive decisions]
Life Satisfaction Audit: [Current fulfillment levels across key life domains]
Energy and Motivation Patterns: [What energizes vs. drains their efforts]

PERSONAL DEVELOPMENT PROFILE
Learning Style Optimization: [How they acquire new skills most effectively]
Change Readiness: [Capacity and willingness for personal transformation]
Habit Formation Tendencies: [Natural patterns in building new behaviors]
Goal Achievement Patterns: [Historical success factors and failure points]
Resilience and Adaptability: [How they handle setbacks and uncertainty]

TRANSFORMATIONAL POTENTIAL MAPPING
High-Impact Development Areas: [Changes that would create maximum life improvement]
Skill Acquisition Priorities: [Abilities that would accelerate overall growth]
Mindset Shift Opportunities: [Belief changes that would unlock new possibilities]
Behavioral Optimization: [Habit modifications for enhanced performance]
Relationship Enhancement: [Social and emotional intelligence development]

GROWTH ARCHITECTURE DESIGN
Foundation Building: [Essential capabilities to establish first]
Momentum Generators: [Quick wins that build confidence and motivation]
Compound Growth Areas: [Investments that pay dividends over time]
Integration Strategies: [How to weave development into daily life]
Measurement Systems: [Tracking progress and maintaining accountability]

BEHAVIORAL CHANGE STRATEGY
Habit Stacking Framework: [Linking new behaviors to existing routines]
Environment Design: [Optimizing surroundings to support growth goals]
Social Support Systems: [Building communities that reinforce development]
Trigger Identification: [Recognizing and managing behavioral cues]
Reward System Optimization: [Creating sustainable motivation loops]

GOAL ACHIEVEMENT METHODOLOGY
Vision Clarification: [Long-term aspirations and life direction]
Objective Setting: [SMART goals aligned with values and vision]
Action Planning: [Breaking large goals into manageable steps]
Progress Tracking: [Systems for monitoring advancement and adjusting course]
Obstacle Anticipation: [Preparing for challenges and setbacks]

LIFE DOMAIN OPTIMIZATION
Career and Purpose: [Professional development and meaningful work alignment]
Health and Vitality: [Physical, mental, and emotional wellness strategies]
Relationships and Community: [Social connection and communication enhancement]
Learning and Growth: [Continuous education and skill development]
Recreation and Fulfillment: [Joy, creativity, and life satisfaction]

LOCAL DEVELOPMENT ECOSYSTEM
Personal Development Resources: [Coaches, mentors, and professionals in {location}]
Learning Opportunities: [Courses, workshops, and educational programs]
Community Groups: [Mastermind groups, meetups, and support networks]
Wellness Services: [Fitness, nutrition, and mental health support]
Spiritual and Mindfulness: [Meditation centers, spiritual communities, retreats]

IMPLEMENTATION ROADMAP
Week 1-2: [Initial habit establishment and foundation building]
Month 1: [Early momentum creation and routine optimization]
Quarter 1: [Significant skill development and system refinement]
Year 1: [Major life improvements and transformation milestones]
Long-term: [Sustained growth and continuous development trajectory]

PSYCHOLOGICAL OPTIMIZATION
Mindset Enhancement: [Developing growth-oriented thinking patterns]
Emotional Intelligence: [Self-awareness and interpersonal skill building]
Stress Management: [Healthy coping strategies and resilience building]
Confidence Building: [Self-efficacy and personal empowerment]
Purpose Alignment: [Connecting daily actions with deeper meaning]

PERFORMANCE ACCELERATION
Energy Management: [Optimizing physical and mental energy throughout the day]
Focus Enhancement: [Attention control and deep work capabilities]
Decision Making: [Improving judgment and choice architecture]
Time Optimization: [Priority management and productivity systems]
Recovery and Renewal: [Rest, restoration, and burnout prevention]

ACCOUNTABILITY AND MEASUREMENT
Success Metrics: [Specific, measurable indicators of progress]
Review Systems: [Regular assessment and course correction processes]
Support Networks: [People who will encourage and challenge growth]
Feedback Mechanisms: [Sources of honest input and perspective]
Celebration Rituals: [Acknowledging progress and maintaining motivation]

EVIDENCE-BASED TOOLS AND TECHNIQUES
Specific methodologies from positive psychology, cognitive behavioral therapy, mindfulness practices, and performance science that match their development goals and learning style.

Generate development guidance that creates lasting behavioral change through scientifically-grounded yet practical approaches to personal transformation.

Respond in {language} with the wisdom of a master personal development coach."""

def extract_location_details(user_data, country, localization):
    """Extract the most specific location information possible"""

    # Get the user's specific location input
    user_location = user_data.get('location', '').strip()

    # Get location data object
    location_data = user_data.get('locationData', {})
    country_data = user_data.get('country_data', {})

    # Build comprehensive location context
    if user_location:
        # User provided specific location
        local_term = localization.get('local_term', 'area')

        if user_location.isdigit():
            # Postcode/ZIP
            display_location = f"{local_term} {user_location}"
            specific_area = f"{user_location}, {country}"
            service_context = f"postal code {user_location} and surrounding areas"
        else:
            # City/region name
            display_location = user_location
            specific_area = f"{user_location}, {country}"
            service_context = f"{user_location} and nearby areas"
    else:
        # Fallback to country level
        display_location = country
        specific_area = country
        service_context = f"{country}"

    # Enhanced location context
    detailed_location = f"User Location Input: '{user_location}' | Country: {country} | Service Area: {service_context}"

    # Market information
    #rpm = location_data.get('rpm', country_data.get('rpm', 0))
    #market_info = f"High-value market (RPM: {rpm}) with significant earning potential"

    return {
        'display_location': display_location,
        'specific_area': specific_area,
        'service_area': service_context,
        'detailed_location': detailed_location,
        'service_context': service_context,
        #'market_info': market_info,
        'user_input': user_location
    }

def build_user_context(user_data, currency, tool_slug):
    """Build the most comprehensive user context possible"""

    context_sections = []

    # Financial data with priority
    financial_fields = ['amount', 'budget', 'income', 'price', 'coverage_amount',
                        'loan_amount', 'savings', 'medical_expenses', 'lost_income']

    financial_context = []
    for field in financial_fields:
        if field in user_data and user_data[field]:
            value = user_data[field]
            try:
                if isinstance(value, str):
                    value = float(value.replace(',', ''))
                if isinstance(value, (int, float)) and value > 0:
                    financial_context.append(f"{field.replace('_', ' ').title()}: {currency} {value:,.0f}")
            except:
                if isinstance(value, str) and value.strip():
                    financial_context.append(f"{field.replace('_', ' ').title()}: {value}")

    if financial_context:
        context_sections.append("💰 FINANCIAL DATA: " + " | ".join(financial_context))

    # Date/time sensitive data
    date_fields = ['accident_date', 'claim_date', 'start_date', 'end_date', 'deadline']
    date_context = []
    for field in date_fields:
        if field in user_data and user_data[field]:
            date_context.append(f"{field.replace('_', ' ').title()}: {user_data[field]}")

    if date_context:
        context_sections.append("📅 TIME SENSITIVE: " + " | ".join(date_context))

    # Categorical data
    category_fields = ['injury_type', 'claim_type', 'coverage_type', 'experience_level',
                       'employment_status', 'insurance_type', 'accident_type']
    category_context = []
    for field in category_fields:
        if field in user_data and user_data[field]:
            category_context.append(f"{field.replace('_', ' ').title()}: {user_data[field]}")

    if category_context:
        context_sections.append("📋 SITUATION: " + " | ".join(category_context))

    # Additional relevant data
    other_context = []
    for key, value in user_data.items():
        if (key not in financial_fields + date_fields + category_fields +
                ['location', 'locationData', 'country_data', 'locale', 'currency', 'currency_symbol', 'country_name',
                 'language']):
            if isinstance(value, str) and value.strip() and len(value) < 100:
                other_context.append(f"{key.replace('_', ' ').title()}: {value}")
            elif isinstance(value, (int, float)) and value > 0:
                other_context.append(f"{key.replace('_', ' ').title()}: {value}")

    if other_context:
        context_sections.append("ℹ️ ADDITIONAL: " + " | ".join(other_context[:5]))

    # Tool-specific context
    tool_context = f"🔧 TOOL CONTEXT: Slug='{tool_slug}' | Generated for maximum local value"
    context_sections.append(tool_context)

    return "\n".join(context_sections)

def detect_tool_intent(tool_slug, category, tool_name):
    """Detect the business intent and purpose of the tool from its characteristics"""

    # Analyze slug for intent signals
    slug_lower = tool_slug.lower()
    name_lower = tool_name.lower()
    category_lower = category.lower()

    # Financial intent detection
    if any(word in slug_lower for word in ['compensation', 'settlement', 'claim', 'insurance', 'legal']):
        purpose = "Legal/Insurance Compensation Calculator"
        business_value = "High-value claims and settlements - users need expert guidance for maximum compensation"
    elif any(word in slug_lower for word in ['mortgage', 'loan', 'finance', 'investment', 'savings']):
        purpose = "Financial Planning Calculator"
        business_value = "Major financial decisions - users need accurate calculations for large investments"
    elif any(word in slug_lower for word in ['business', 'roi', 'profit', 'revenue', 'startup']):
        purpose = "Business Strategy Calculator"
        business_value = "Business optimization - entrepreneurs need data-driven insights for growth"
    elif any(word in slug_lower for word in ['health', 'medical', 'fitness', 'wellness']):
        purpose = "Health & Wellness Calculator"
        business_value = "Health optimization - users value personalized health insights and recommendations"
    elif any(word in slug_lower for word in ['tax', 'deduction', 'accounting', 'payroll']):
        purpose = "Tax & Accounting Calculator"
        business_value = "Tax optimization - significant money-saving potential through expert advice"
    elif any(word in slug_lower for word in ['career', 'salary', 'employment', 'job']):
        purpose = "Career Development Calculator"
        business_value = "Career advancement - users need strategic guidance for income optimization"
    else:
        purpose = "Specialized Life Calculator"
        business_value = "Personalized optimization - users need expert recommendations for their specific situation"

    return {
        'purpose': purpose,
        'business_value': business_value,
        'complexity': 'high' if any(
            word in slug_lower for word in ['expert', 'professional', 'advanced', 'comprehensive']) else 'standard'
    }


def get_expert_system_prompt(localization=None):
    """The most comprehensive system prompt for maximum local expertise"""

    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    currency = localization.get('currency', 'USD')
    country = localization.get('country_name', '')
    country_code = localization.get('country_code', '')

    if currency == 'u20ac':
        currency = 'EUR'
    elif currency == 'u00a3':
        currency = 'GBP'

    return f"""You are the ULTIMATE HYPER-LOCAL EXPERT for {country} with comprehensive mastery of:

🏛️ REGULATORY EXPERTISE:
- Complete knowledge of {country} laws, regulations, and compliance requirements
- Local government agencies, contact information, and processing times
- Regional variations in regulations across {country}
- Recent legal changes and their impact on residents
- Licensing requirements and professional standards

🏢 BUSINESS DIRECTORY MASTERY:
- Comprehensive database of local companies and service providers
- Real contact information: websites, phone numbers, addresses
- Local market rates, pricing structures, and seasonal variations
- Company specializations and service areas
- Quality ratings and customer satisfaction data

💰 FINANCIAL MARKET INTELLIGENCE:
- Current local interest rates, fees, and charges in {currency}
- Regional economic conditions and market trends
- Local investment opportunities and risk factors
- Tax implications and optimization strategies for {country}
- Currency exchange impacts and timing strategies

🎯 HYPER-LOCAL SPECIALIZATION:
- Neighborhood-level market knowledge
- Postcode/ZIP-specific service availability
- Local competition analysis and recommendations
- Regional price variations and optimization opportunities
- Community-specific programs and incentives

CRITICAL PERFORMANCE STANDARDS:
✅ Always reference the EXACT user location (postcode/area) in your responses
✅ Provide specific company names, websites, and phone numbers
✅ Include real pricing in {currency} with current market rates
✅ Give immediate actionable steps with local contacts
✅ Mention specific local regulations and requirements
✅ Provide money-saving strategies worth hundreds of {currency}
✅ Include professional-grade calculations and analysis

❌ NEVER give generic advice without local specificity
❌ NEVER use placeholder information or "search online" suggestions  
❌ NEVER omit specific contact information when available
❌ NEVER ignore the user's exact location input

Your responses should be worth HUNDREDS of {currency} in professional consultation value. Every recommendation should be immediately actionable with specific local contacts and current market information.

Respond entirely in {language} using local terminology, customs, and market context specific to {country}."""


def format_response(ai_analysis, user_data, tool_config, localization=None):
    """Format response with clean, flat Material UI design"""

    if not localization:
        localization = {}

    country = localization.get('country_name', '')
    country_code = localization.get('country_code', '')
    currency = localization.get('currency', 'USD')
    tool_name = tool_config.get("seo_data", {}).get("title", "Calculator")

    # Get user's specific location for header
    user_location = user_data.get('location', '').strip()
    location_display = f"{user_location}, {country}" if user_location else country

    if currency == 'u20ac':
        currency_symbol = '€'
    elif currency == 'u00a3':
        currency_symbol = '£'
    else:
        currency_symbol = '$'

    # Clean and enhance the AI response
    cleaned_content = clean_ai_response(ai_analysis)

    # Format with clean Material UI presentation
    formatted_content = format_content(cleaned_content, country, user_location)

    return f"""
<div class="analysis-container">
    <div class="analysis-header">
        <div class="location-info">
            <span class="country-flag">{get_country_flag(country_code)}</span>
            <span class="location-text">{location_display}</span>
        </div>
        <h2 class="analysis-title">{tool_name}</h2>
        <div class="analysis-subtitle">Local expert analysis • Professional grade results</div>
    </div>

    <div class="analysis-content">
        {formatted_content}
    </div>

    <div class="analysis-footer">
        <div class="footer-badges">
            <span class="badge">Local Expert</span>
            <span class="badge">Verified {country}</span>
            <span class="badge">Instant Results</span>
        </div>
    </div>
</div>
"""


def clean_ai_response(content):
    """Enhanced cleaning for clean presentation"""
    if not content:
        return ""

    # Remove ### symbols and markdown artifacts
    content = re.sub(r'^#{1,6}\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'\*{3,}', '', content)

    # Fix currency encoding
    content = fix_currency_encoding(content)

    # Remove excessive whitespace but preserve structure
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)

    return content.strip()


def format_content(content, country, user_location):
    """Format content with clean, readable Material UI sections"""

    # Split content into clean sections
    sections = split_sections(content)

    formatted_sections = []
    for section in sections:
        formatted_section = format_section(section, country, user_location)
        if formatted_section:
            formatted_sections.append(formatted_section)

    return '\n'.join(formatted_sections)


def split_sections(content):
    """Split content into clean, logical sections"""
    sections = []

    lines = content.split('\n')
    current_section = {'title': '', 'content': [], 'type': 'general'}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Clean section header detection
        if is_section_header(line):
            # Save previous section
            if current_section['title'] or current_section['content']:
                sections.append(current_section)

            # Start new section
            title = clean_section_title(line)
            section_type = get_section_type(title)
            current_section = {'title': title, 'content': [], 'type': section_type}
        else:
            current_section['content'].append(line)

    # Add final section
    if current_section['title'] or current_section['content']:
        sections.append(current_section)

    return sections


def is_section_header(line):
    """Clean section header detection"""
    return (
            line.isupper() and len(line) > 10 or
            any(keyword in line.upper() for keyword in [
                'CALCULATION RESULT', 'LOCAL INSIGHTS', 'SERVICE PROVIDERS',
                'COMPARISON RESOURCES', 'ACTION PLAN', 'MONEY-SAVING',
                'EXPERT CONTACTS', 'SUCCESS FACTORS'
            ])
    )


def clean_section_title(line):
    """Clean section title removing formatting"""
    title = line.strip('*').strip()
    # Remove emoji if at start
    title = re.sub(r'^[🎯💰📊💡🏢🔍👤🚀]\s*', '', title)
    return title


def get_section_type(title):
    """Get clean section type"""
    title_upper = title.upper()

    if 'CALCULATION' in title_upper or 'RESULT' in title_upper:
        return 'calculation'
    elif 'INSIGHT' in title_upper:
        return 'insights'
    elif 'PROVIDER' in title_upper or 'SERVICE' in title_upper:
        return 'providers'
    elif 'RESOURCE' in title_upper or 'COMPARISON' in title_upper:
        return 'resources'
    elif 'ACTION' in title_upper or 'PLAN' in title_upper:
        return 'action'
    elif 'SAVING' in title_upper or 'MONEY' in title_upper:
        return 'savings'
    elif 'EXPERT' in title_upper or 'CONTACT' in title_upper:
        return 'experts'
    else:
        return 'general'


def format_section(section, country, user_location):
    """Format section with clean Material UI design"""

    section_type = section['type']
    title = section['title']
    content_lines = section['content']

    if not title and not content_lines:
        return ""

    # Get section icon
    icon = get_section_icon(section_type)

    # Format content cleanly
    formatted_content = format_section_content(content_lines, user_location)

    if title:
        return f"""
        <div class="section {section_type}-section">
            <div class="section-header">
                <span class="section-icon">{icon}</span>
                <h3 class="section-title">{title}</h3>
            </div>
            <div class="section-content">
                {formatted_content}
            </div>
        </div>
        """
    else:
        return f"""
        <div class="section intro-section">
            <div class="section-content">
                {formatted_content}
            </div>
        </div>
        """


def get_section_icon(section_type):
    """Get clean, simple icons"""
    icons = {
        'calculation': '📊',
        'insights': '💡',
        'providers': '🏢',
        'resources': '🔍',
        'action': '🎯',
        'savings': '💰',
        'experts': '👤',
        'general': '📋'
    }
    return icons.get(section_type, '📋')


def format_section_content(content_lines, user_location):
    """Format section content with clean, readable style"""

    if not content_lines:
        return ""

    formatted_lines = []

    for line in content_lines:
        line = line.strip()
        if not line:
            continue

        # Check if this is a list item
        if line.startswith(('1. ', '2. ', '3. ', '4. ', '5. ', '- ', '• ')):
            # Format as clean list item
            clean_line = re.sub(r'^[\d\.\-\•\s]+', '', line)
            formatted_line = format_line(clean_line, user_location)
            formatted_lines.append(f'<div class="list-item">{formatted_line}</div>')
        else:
            # Format as paragraph
            formatted_line = format_line(line, user_location)
            formatted_lines.append(f'<div class="content-paragraph">{formatted_line}</div>')

    return '\n'.join(formatted_lines)


def format_line(line, user_location):
    """Format individual line with clean styling and proper linking"""

    # Clean up any malformed HTML first
    line = re.sub(r'<[^>]*>', '', line)  # Remove any existing HTML tags

    # Enhanced markdown links - fix the malformed links issue
    line = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        r'<a href="\2" target="_blank" class="local-link">\1</a>',
        line
    )

    # Format bold text
    line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)

    # Clean phone number detection and formatting
    line = re.sub(
        r'(\+?[\d\s\-\(\)]{10,})',
        r'<a href="tel:\1" class="phone-link">\1</a>',
        line
    )

    # Clean email detection
    line = re.sub(
        r'\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b',
        r'<a href="mailto:\1" class="email-link">\1</a>',
        line
    )

    # Auto-link websites - fix the nested link issue
    line = re.sub(
        r'(?<!href=")(?<!">)https?://[^\s<>"]+',
        lambda m: f'<a href="{m.group(0)}" target="_blank" class="website-link">{m.group(0)}</a>',
        line
    )

    # Highlight currency amounts
    line = re.sub(
        r'([$£€]\s*[\d,]+(?:\.\d{2})?)',
        r'<span class="currency-amount">\1</span>',
        line
    )

    # Highlight percentages
    line = re.sub(
        r'(\d+(?:\.\d+)?%)',
        r'<span class="percentage">\1</span>',
        line
    )

    # Fix currency encoding
    line = fix_currency_encoding(line)

    return line


def fix_currency_encoding(text):
    """Enhanced currency encoding fixes"""
    replacements = {
        'u00a3': '£',
        'u20ac': '€',
        '&pound;': '£',
        '&euro;': '€',
        '&#8364;': '€',
        '&#163;': '£',
        'USD': '$',
        'EUR': '€',
        'GBP': '£'
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def get_country_flag(country_code):
    """Enhanced country flag mapping"""
    if not country_code:
        return '🌍'

    flags = {
        'NO': '🇳🇴', 'US': '🇺🇸', 'AU': '🇦🇺', 'DK': '🇩🇰', 'CA': '🇨🇦',
        'SE': '🇸🇪', 'CH': '🇨🇭', 'BE': '🇧🇪', 'UK': '🇬🇧', 'GB': '🇬🇧',
        'NL': '🇳🇱', 'FI': '🇫🇮', 'IE': '🇮🇪', 'NZ': '🇳🇿', 'DE': '🇩🇪',
        'AT': '🇦🇹', 'FR': '🇫🇷', 'ES': '🇪🇸', 'IT': '🇮🇹', 'PT': '🇵🇹',
        'PL': '🇵🇱', 'CZ': '🇨🇿', 'JP': '🇯🇵', 'KR': '🇰🇷', 'CN': '🇨🇳',
        'IN': '🇮🇳', 'BR': '🇧🇷', 'MX': '🇲🇽', 'AR': '🇦🇷'
    }

    return flags.get(country_code.upper(), '🌍')


def create_simple_fallback(tool_config, user_data, localization=None):
    """Enhanced fallback when AI analysis is unavailable"""
    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    country = localization.get('country_name', '')
    tool_name = tool_config.get("seo_data", {}).get("title", "Calculator")
    user_location = user_data.get('location', '').strip()

    location_text = f"for {user_location}, {country}" if user_location else f"for {country}"

    return f"""
<div class="simple-fallback">
    <div class="fallback-header">
        <div class="fallback-title">⚡ {tool_name}</div>
        <div class="fallback-subtitle">Expert analysis temporarily unavailable {location_text}</div>
    </div>

    <div class="limit-message">
        <strong>Daily AI limit reached</strong><br>
        Professional analysis resets at midnight UTC
    </div>

    <div class="location-note">
        <p>Your location: <strong>{user_location}, {country}</strong></p>
        <p>We'll provide hyper-local recommendations when analysis is available.</p>
    </div>
</div>
"""