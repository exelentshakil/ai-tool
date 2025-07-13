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
    prompt = build_enhanced_prompt(tool_name, category, tool_slug, cleaned_data, localization)

    try:
        model_name = "gpt-4o-mini"
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": get_expert_system_prompt(localization)},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2500,
            temperature=0.85
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
Market: {location_info['market_info']}

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