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

    # Clean and prepare data with enhanced location handling
    cleaned_data = clean_user_data(user_data)

    # Build the massive, super-detailed prompt
    prompt = build_ultra_enhanced_prompt(tool_name, category, tool_slug, cleaned_data, localization)

    try:
        model_name = "gpt-4o-mini"
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": get_hyper_local_expert_system_prompt(localization)},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2500,  # Increased for comprehensive responses
            temperature=0.85  # Higher creativity for local recommendations
        )

        ai_analysis = response.choices[0].message.content
        pt, ct = response.usage.prompt_tokens, response.usage.completion_tokens
        total_tokens = pt + ct
        cost = (pt * 0.00015 + ct * 0.0006) / 1000

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
            print(f"✅ Ultra-analysis completed: {tool_name} took {response_time}ms")
        else:
            print(f"⚠️ Cost logging failed for {tool_name}")

        # Format with maximum value presentation
        return format_ultra_value_response(ai_analysis, cleaned_data, tool_config, localization)

    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        print(f"❌ AI analysis failed after {response_time}ms: {str(e)}")

        try:
            log_openai_cost_enhanced(cost=0, tokens=0, model="error", ip=ip, tools_slug=tool_name)
        except:
            pass

        #return create_simple_fallback(tool_config, cleaned_data, localization)


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


def build_ultra_enhanced_prompt(tool_name, category, tool_slug, user_data, localization=None):
    """Build the most comprehensive, value-packed prompt possible"""

    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    currency = localization.get('currency', 'USD')
    country = localization.get('country_name', '')
    country_code = localization.get('country_code', '')

    if currency == 'u20ac':
        currency = 'EUR (€)'
    elif currency == 'u00a3':
        currency = 'GBP (£)'

    # Extract hyper-specific location details
    location_info = extract_hyper_local_details(user_data, country, localization)

    # Build comprehensive user context
    user_context = build_comprehensive_context(user_data, currency, tool_slug)

    # Detect tool intent and purpose from slug/category
    tool_intent = detect_tool_intent(tool_slug, category, tool_name)

    return f"""You are the ULTIMATE LOCAL EXPERT for {location_info['specific_area']} providing the most comprehensive, actionable analysis possible.

CRITICAL MISSION: Provide MAXIMUM VALUE that could save users hundreds or thousands of {currency} through your expert guidance.

TOOL ANALYSIS REQUEST:
🎯 Tool: {tool_name}
📊 Category: {category}
🔧 Type: {tool_intent['purpose']}
💼 Intent: {tool_intent['business_value']}

USER PROFILE & DATA:
{user_context}

HYPER-SPECIFIC LOCATION TARGETING:
📍 Exact Location: {location_info['detailed_location']}
🏘️ Service Area: {location_info['service_context']}
🌍 Market Context: {location_info['market_info']}

LANGUAGE & CURRENCY:
🗣️ Response Language: {language}
💰 Currency: {currency}
🏛️ Regulatory Context: {country} ({country_code})

ULTIMATE VALUE REQUIREMENTS:
1. HYPER-LOCAL SPECIFICITY: Mention the exact location/postcode in results
2. REAL CALCULATIONS: Provide detailed mathematical breakdowns in {currency}
3. IMMEDIATE ACTIONABLE STEPS: What to do RIGHT NOW
4. LOCAL CONTACTS: Specific companies, phone numbers, websites for {location_info['service_area']}
5. COST SAVINGS: How to save significant money through your recommendations
6. REGULATORY COMPLIANCE: Local laws, requirements, and deadlines for {country}
7. MARKET INSIGHTS: Current local rates, trends, and opportunities

RESPONSE STRUCTURE (NO ### symbols, clean headers):

LOCATION-SPECIFIC CALCULATION RESULT
🎯 For {location_info['display_location']}: [Detailed calculation with step-by-step breakdown]
💰 Potential Savings: {currency}X,XXX per year
📊 Local Market Rate: Compared to {country} average

KEY LOCAL INSIGHTS FOR {location_info['display_location']}
💡 3 critical insights specific to your area including local regulations and market conditions

VERIFIED LOCAL SERVICE PROVIDERS
🏢 5+ REAL companies serving {location_info['service_area']} with:
- ✅ Company Name & Specialty
- 🌐 Website: [Company](https://realwebsite.com)
- 📞 Phone: +XX XXX XXX XXX
- 📍 Address/Service Area
- 💯 Why recommended for your specific situation
- 💰 Typical pricing in {currency}

LOCAL COMPARISON RESOURCES & PLATFORMS
🔍 SPECIFIC websites and apps used in {country} for comparing this service
🏛️ Government resources and regulatory bodies for {country}
👥 Consumer protection organizations in {location_info['service_area']}

IMMEDIATE ACTION PLAN
🚀 Step-by-step plan with specific local contacts and deadlines
⏰ Timeline with exact dates and local business hours
📋 Required documents and local requirements for {country}

MONEY-SAVING STRATEGIES
💰 Specific ways to save {currency} in {location_info['service_area']}
🎯 Local discounts, programs, and incentives available
📈 Best timing for maximum savings in your area

LOCAL EXPERT CONTACTS
👨‍💼 Where to find qualified professionals in {location_info['service_area']}
🏢 Professional associations and licensing bodies in {country}
⭐ Recommended specialists with contact information

CRITICAL SUCCESS FACTORS
✅ What makes this successful in {country}
⚠️ Common mistakes to avoid in {location_info['service_area']}
🎯 Success metrics and expected outcomes

Make this response INCREDIBLY valuable - worth hundreds of {currency} in professional consultation. Use REAL company names, actual websites, and specific local information. Reference the exact location ({location_info['display_location']}) throughout your response.

Focus on immediate, actionable value that justifies why this tool is essential for anyone in {location_info['service_area']}.

Respond entirely in {language} using local terminology and context."""


def extract_hyper_local_details(user_data, country, localization):
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
    rpm = location_data.get('rpm', country_data.get('rpm', 0))
    market_info = f"High-value market (RPM: {rpm}) with significant earning potential"

    return {
        'display_location': display_location,
        'specific_area': specific_area,
        'service_area': service_context,
        'detailed_location': detailed_location,
        'service_context': service_context,
        'market_info': market_info,
        'user_input': user_location
    }


def build_comprehensive_context(user_data, currency, tool_slug):
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


def get_hyper_local_expert_system_prompt(localization=None):
    """The most comprehensive system prompt for maximum local expertise"""

    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    currency = localization.get('currency', 'USD')
    country = localization.get('country_name', '')
    country_code = localization.get('country_code', '')

    if currency == 'u20ac':
        currency = 'EUR (€)'
    elif currency == 'u00a3':
        currency = 'GBP (£)'

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

📊 VALUE MAXIMIZATION EXPERTISE:
- Cost-saving strategies specific to {country}
- Local discount programs and government incentives
- Timing optimization for maximum savings
- Negotiation strategies with local providers
- Long-term financial planning in local context

🗣️ COMMUNICATION EXCELLENCE:
- Native-level fluency in {language}
- Local terminology, customs, and communication styles
- Cultural sensitivity and appropriate business etiquette
- Professional presentation of complex information
- Clear action-oriented guidance

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


def format_ultra_value_response(ai_analysis, user_data, tool_config, localization=None):
    """Format response with maximum value presentation and local specificity"""

    if not localization:
        localization = {}

    country = localization.get('country_name', '')
    country_code = localization.get('country_code', '')
    currency = localization.get('currency', 'USD')
    tool_name = tool_config.get("seo_data", {}).get("title", "Calculator")

    # Get user's specific location for header
    user_location = user_data.get('location', '').strip()
    location_display = f"📍 {user_location}, {country}" if user_location else f"📍 {country}"

    if currency == 'u20ac':
        currency_symbol = '€'
    elif currency == 'u00a3':
        currency_symbol = '£'
    else:
        currency_symbol = '$'

    # Clean and enhance the AI response
    cleaned_content = clean_ai_response(ai_analysis)

    # Format with ultra-value presentation
    formatted_content = format_ultra_value_content(cleaned_content, country, user_location)

    return f"""
{get_ultra_value_css()}

<div class="ultra-value-container">
    <div class="premium-header">
        <div class="location-banner">
            <span class="country-flag">{get_country_flag(country_code)}</span>
            <span class="location-text">{location_display}</span>
            <span class="premium-badge">EXPERT ANALYSIS</span>
        </div>
        <h1 class="analysis-title">
            <span class="tool-icon">🎯</span>
            {tool_name}
        </h1>
        <div class="value-promise">
            <span class="value-icon">💰</span>
            <span class="value-text">Professional-grade analysis worth {currency_symbol}500+ in consultation fees</span>
        </div>
    </div>

    <div class="analysis-content premium-content">
        {formatted_content}
    </div>

    <div class="premium-footer">
        <div class="expertise-badges">
            <div class="badge local-expert">
                <span class="badge-icon">🏆</span>
                <span class="badge-text">Local Expert Certified</span>
            </div>
            <div class="badge verified-data">
                <span class="badge-icon">✅</span>
                <span class="badge-text">Data Verified {country}</span>
            </div>
            <div class="badge instant-value">
                <span class="badge-icon">⚡</span>
                <span class="badge-text">Instant Actionable Results</span>
            </div>
        </div>
    </div>
</div>
"""


def clean_ai_response(content):
    """Enhanced cleaning for ultra-value presentation"""
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


def format_ultra_value_content(content, country, user_location):
    """Format content with maximum value presentation"""

    # Split content into sections
    sections = split_into_value_sections(content)

    formatted_sections = []
    for i, section in enumerate(sections):
        formatted_section = format_premium_section(section, country, user_location, i)
        if formatted_section:
            formatted_sections.append(formatted_section)

    return '\n'.join(formatted_sections)


def split_into_value_sections(content):
    """Split content into high-value sections"""
    sections = []

    lines = content.split('\n')
    current_section = {'title': '', 'content': [], 'type': 'intro'}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect section headers with enhanced recognition
        if (is_section_header(line)):
            # Save previous section
            if current_section['title'] or current_section['content']:
                sections.append(current_section)

            # Start new section
            title = clean_section_title(line)
            section_type = determine_section_type(title, line)
            current_section = {'title': title, 'content': [], 'type': section_type}
        else:
            current_section['content'].append(line)

    # Add final section
    if current_section['title'] or current_section['content']:
        sections.append(current_section)

    return sections


def is_section_header(line):
    """Enhanced section header detection"""
    # Check for various header patterns
    if (line.isupper() and len(line) > 5 or
            (line.startswith('**') and line.endswith('**')) or
            any(keyword in line.upper() for keyword in [
                'CALCULATION', 'RESULT', 'INSIGHT', 'PROVIDER', 'RESOURCE',
                'EXPERT', 'ACTION', 'STEP', 'SAVING', 'CONTACT', 'LOCAL',
                'IMMEDIATE', 'STRATEGY', 'PLAN', 'CRITICAL'
            ]) or
            re.match(r'^[🎯💰📊💡🏢🔍👨‍💼🚀⚡💯]', line)):
        return True
    return False


def clean_section_title(line):
    """Clean section title removing formatting"""
    title = line.strip('*').strip()
    # Remove emoji if at start and add back strategically
    title = re.sub(r'^[🎯💰📊💡🏢🔍👨‍💼🚀⚡💯]\s*', '', title)
    return title


def determine_section_type(title, line):
    """Determine the type of section for optimal formatting"""
    title_upper = title.upper()

    if any(word in title_upper for word in ['CALCULATION', 'RESULT']):
        return 'calculation'
    elif any(word in title_upper for word in ['INSIGHT', 'KEY']):
        return 'insights'
    elif any(word in title_upper for word in ['PROVIDER', 'COMPANY', 'SERVICE']):
        return 'providers'
    elif any(word in title_upper for word in ['RESOURCE', 'COMPARISON', 'PLATFORM']):
        return 'resources'
    elif any(word in title_upper for word in ['EXPERT', 'CONTACT', 'PROFESSIONAL']):
        return 'experts'
    elif any(word in title_upper for word in ['ACTION', 'STEP', 'IMMEDIATE', 'PLAN']):
        return 'action'
    elif any(word in title_upper for word in ['SAVING', 'MONEY', 'COST']):
        return 'savings'
    else:
        return 'general'


def format_premium_section(section, country, user_location, index):
    """Format each section with premium value presentation"""

    section_type = section['type']
    title = section['title']
    content_lines = section['content']

    if not title and not content_lines:
        return ""

    # Get section styling
    section_config = get_section_config(section_type)

    # Format content with enhanced value presentation
    formatted_content = format_premium_content(content_lines, user_location, country)

    if title:
        return f"""
        <div class="premium-section {section_type}-section">
            <div class="section-header premium-header">
                <span class="section-icon">{section_config['icon']}</span>
                <h3 class="section-title">{title}</h3>
                <span class="value-indicator">{section_config['value_tag']}</span>
            </div>
            <div class="section-content premium-content">
                {formatted_content}
            </div>
        </div>
        """
    else:
        return f"""
        <div class="premium-section intro-section">
            <div class="section-content premium-content">
                {formatted_content}
            </div>
        </div>
        """


def get_section_config(section_type):
    """Get configuration for each section type"""
    configs = {
        'calculation': {'icon': '🎯', 'value_tag': 'CRITICAL RESULT'},
        'insights': {'icon': '💡', 'value_tag': 'EXPERT INSIGHT'},
        'providers': {'icon': '🏢', 'value_tag': 'VERIFIED CONTACTS'},
        'resources': {'icon': '🔍', 'value_tag': 'LOCAL PLATFORMS'},
        'experts': {'icon': '👨‍💼', 'value_tag': 'PROFESSIONAL NETWORK'},
        'action': {'icon': '🚀', 'value_tag': 'IMMEDIATE ACTION'},
        'savings': {'icon': '💰', 'value_tag': 'MONEY SAVER'},
        'general': {'icon': '📋', 'value_tag': 'IMPORTANT INFO'}
    }
    return configs.get(section_type, configs['general'])


def format_premium_content(content_lines, user_location, country):
    """Format content with premium value presentation and location specificity"""

    if not content_lines:
        return ""

    formatted_lines = []
    in_list = False

    for line in content_lines:
        line = line.strip()
        if not line:
            continue

        # Enhanced location mention
        if user_location and user_location not in line:
            # Smart location insertion for relevant content
            if any(keyword in line.lower() for keyword in ['result', 'calculation', 'for you', 'your area', 'local']):
                line = line.replace('your area', f'{user_location} area')
                line = line.replace('your location', f'your location ({user_location})')

        # Check if this is a list item
        if line.startswith(('- ', '• ', '* ', '✅', '🏢', '🔍', '📞')) or re.match(r'^\d+\.?\s', line):
            if not in_list:
                formatted_lines.append('<div class="premium-list">')
                in_list = True

            # Enhanced list item formatting
            clean_line = re.sub(r'^[\-\•\*✅🏢🔍📞\d\.]+\s*', '', line)
            formatted_line = format_premium_line(clean_line, user_location)

            # Determine list item type for special styling
            item_type = get_list_item_type(line)
            formatted_lines.append(f'<div class="premium-list-item {item_type}-item">{formatted_line}</div>')
        else:
            if in_list:
                formatted_lines.append('</div>')
                in_list = False

            formatted_line = format_premium_line(line, user_location)
            formatted_lines.append(f'<div class="premium-paragraph">{formatted_line}</div>')

    if in_list:
        formatted_lines.append('</div>')

    return '\n'.join(formatted_lines)


def get_list_item_type(line):
    """Determine the type of list item for special styling"""
    if any(keyword in line.lower() for keyword in ['website', 'www', 'http']):
        return 'website'
    elif any(keyword in line.lower() for keyword in ['phone', 'tel', 'call']):
        return 'phone'
    elif any(keyword in line.lower() for keyword in ['email', 'mail', '@']):
        return 'email'
    elif any(keyword in line.lower() for keyword in ['save', 'discount', 'cheaper', 'money']):
        return 'savings'
    elif any(keyword in line.lower() for keyword in ['contact', 'address', 'location']):
        return 'contact'
    else:
        return 'standard'


def format_premium_line(line, user_location):
    """Format individual line with premium styling and enhanced linking"""

    # Enhanced markdown links with styling classes
    line = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        r'<a href="\2" target="_blank" class="premium-link website-link"><span class="link-icon">🌐</span>\1</a>',
        line
    )

    # Format bold text with premium styling
    line = re.sub(r'\*\*(.*?)\*\*', r'<strong class="premium-bold">\1</strong>', line)

    # Enhanced phone number detection and formatting
    line = re.sub(
        r'(\+?[\d\s\-\(\)]{10,})',
        r'<a href="tel:\1" class="premium-link phone-link"><span class="link-icon">📞</span>\1</a>',
        line
    )

    # Enhanced email detection
    line = re.sub(
        r'\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b',
        r'<a href="mailto:\1" class="premium-link email-link"><span class="link-icon">✉️</span>\1</a>',
        line
    )

    # Auto-link websites with enhanced detection
    line = re.sub(
        r'\b(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)\b',
        lambda
            m: f'<a href="{"https://" if not m.group(0).startswith("http") else ""}{m.group(0)}" target="_blank" class="premium-link auto-link"><span class="link-icon">🔗</span>{m.group(0)}</a>',
        line
    )

    # Highlight currency amounts
    line = re.sub(
        r'([$£€]\s*[\d,]+(?:\.\d{2})?)',
        r'<span class="currency-highlight">\1</span>',
        line
    )

    # Highlight percentages
    line = re.sub(
        r'(\d+(?:\.\d+)?%)',
        r'<span class="percentage-highlight">\1</span>',
        line
    )

    # Highlight savings mentions
    if user_location:
        line = re.sub(
            rf'\b(save|saving|discount)s?\b',
            r'<span class="savings-highlight">\1</span>',
            line, flags=re.IGNORECASE
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
        'USD': '',
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


def format_ultra_value_response(ai_analysis, user_data, tool_config, localization=None):
    """Format response with maximum value presentation and local specificity - NO CSS INCLUDED"""

    if not localization:
        localization = {}

    country = localization.get('country_name', '')
    country_code = localization.get('country_code', '')
    currency = localization.get('currency', 'USD')
    tool_name = tool_config.get("seo_data", {}).get("title", "Calculator")

    # Get user's specific location for header
    user_location = user_data.get('location', '').strip()
    location_display = f"📍 {user_location}, {country}" if user_location else f"📍 {country}"

    if currency == 'u20ac':
        currency_symbol = '€'
    elif currency == 'u00a3':
        currency_symbol = '£'
    else:
        currency_symbol = ''

    # Clean and enhance the AI response
    cleaned_content = clean_ai_response(ai_analysis)

    # Format with ultra-value presentation
    formatted_content = format_ultra_value_content(cleaned_content, country, user_location)

    return f"""
<div class="ultra-value-container">
    <div class="premium-header">
        <div class="location-banner">
            <span class="country-flag">{get_country_flag(country_code)}</span>
            <span class="location-text">{location_display}</span>
            <span class="premium-badge">EXPERT ANALYSIS</span>
        </div>
        <h1 class="analysis-title">
            <span class="tool-icon">🎯</span>
            {tool_name}
        </h1>
        <div class="value-promise">
            <span class="value-icon">💰</span>
            <span class="value-text">Professional-grade analysis worth {currency_symbol}500+ in consultation fees</span>
        </div>
    </div>

    <div class="analysis-content premium-content">
        {formatted_content}
    </div>

    <div class="premium-footer">
        <div class="expertise-badges">
            <div class="badge local-expert">
                <span class="badge-icon">🏆</span>
                <span class="badge-text">Local Expert Certified</span>
            </div>
            <div class="badge verified-data">
                <span class="badge-icon">✅</span>
                <span class="badge-text">Data Verified {country}</span>
            </div>
            <div class="badge instant-value">
                <span class="badge-icon">⚡</span>
                <span class="badge-text">Instant Actionable Results</span>
            </div>
        </div>
    </div>
</div>
"""


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


# Additional utility functions for enhanced functionality

def extract_tool_value_metrics(tool_slug, user_data):
    """Extract value metrics from tool usage for optimization"""

    value_indicators = {
        'financial_impact': 0,
        'urgency_level': 'medium',
        'complexity_score': 1,
        'local_importance': 'high'
    }

    # Analyze financial data
    financial_fields = ['amount', 'budget', 'income', 'medical_expenses', 'lost_income', 'coverage_amount']
    total_financial_value = 0

    for field in financial_fields:
        if field in user_data:
            try:
                value = float(str(user_data[field]).replace(',', ''))
                total_financial_value += value
            except:
                pass

    value_indicators['financial_impact'] = total_financial_value

    # Determine urgency from dates and tool type
    if any(word in tool_slug.lower() for word in ['accident', 'emergency', 'urgent', 'deadline']):
        value_indicators['urgency_level'] = 'high'
    elif any(word in tool_slug.lower() for word in ['planning', 'future', 'long-term']):
        value_indicators['urgency_level'] = 'low'

    # Complexity based on tool features
    if any(word in tool_slug.lower() for word in ['expert', 'professional', 'comprehensive', 'advanced']):
        value_indicators['complexity_score'] = 3
    elif any(word in tool_slug.lower() for word in ['smart', 'detailed', 'enhanced']):
        value_indicators['complexity_score'] = 2

    return value_indicators


def generate_location_specific_insights(user_location, country, tool_category):
    """Generate location-specific insights for enhanced local value"""

    insights = []

    if user_location:
        insights.append(f"Specific to {user_location}: Local market conditions and regulations apply")
        insights.append(f"Service providers in {user_location} area: Enhanced local network available")
        insights.append(f"Regional advantages: {country} residents in {user_location} have specific benefits")

    # Category-specific local insights
    if 'insurance' in tool_category.lower():
        insights.append(f"Insurance regulations: {country}-specific compliance requirements")
    elif 'financial' in tool_category.lower():
        insights.append(f"Financial planning: {country} tax implications and opportunities")
    elif 'legal' in tool_category.lower():
        insights.append(f"Legal framework: {country} jurisdiction and local court systems")

    return insights


def optimize_for_revenue_generation(tool_analysis, user_data, localization):
    """Optimize the analysis for maximum revenue generation potential"""

    # Add value propositions based on user data
    revenue_optimizations = []

    # High-value user indicators
    if any(field in user_data for field in ['income', 'budget', 'amount']):
        revenue_optimizations.append("premium_user_detected")

    # Location-based revenue optimization
    country_data = user_data.get('country_data', {})
    rpm = country_data.get('rpm', 0)

    if rpm > 20:  # High RPM country
        revenue_optimizations.append("high_value_market")

    # Tool complexity revenue factor
    tool_slug = user_data.get('tool_slug', '')
    if any(word in tool_slug for word in ['expert', 'professional', 'comprehensive']):
        revenue_optimizations.append("premium_tool_complexity")

    return revenue_optimizations