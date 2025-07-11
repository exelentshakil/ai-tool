from openai import OpenAI
from utils.database import get_openai_cost_today, get_openai_cost_month, log_openai_cost, log_openai_cost_enhanced
from config.settings import OPENAI_API_KEY, DAILY_OPENAI_BUDGET, MONTHLY_OPENAI_BUDGET
import re
import html

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_ai_analysis(tool_config, user_data, ip, localization=None):
    import time
    start_time = time.time()  # Start timing the response

    # Convert string budget values to float for comparison
    try:
        daily_budget = float(DAILY_OPENAI_BUDGET)
        monthly_budget = float(MONTHLY_OPENAI_BUDGET)
    except (ValueError, TypeError):
        # If conversion fails, use default values
        daily_budget = 10.0
        monthly_budget = 100.0

    if get_openai_cost_today() >= daily_budget or get_openai_cost_month() >= monthly_budget:
        return create_simple_fallback(tool_config, user_data, localization)

    category = tool_config.get("category", "general")
    tool_name = tool_config.get("seo_data", {}).get("title", "Calculator")

    cleaned_data = clean_user_data(user_data)
    prompt = build_prompt(tool_name, category, cleaned_data, localization)

    try:
        model_name = "gpt-4o-mini"
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": get_system_prompt(localization)},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )

        ai_analysis = response.choices[0].message.content
        pt, ct = response.usage.prompt_tokens, response.usage.completion_tokens
        total_tokens = pt + ct
        cost = (pt * 0.00015 + ct * 0.0006) / 1000

        # Calculate response time
        response_time = int((time.time() - start_time) * 1000)  # milliseconds

        # Use your existing enhanced logging function
        success = log_openai_cost_enhanced(
            cost=cost,
            tokens=total_tokens,
            model=model_name,
            ip=ip,
            tools_slug=tool_name,
            response_time=response_time  # Add this parameter
        )

        if success:
            print(f"✅ Cost logged successfully: {tool_name} took {response_time}ms")
        else:
            print(f"⚠️ Cost logging failed for {tool_name}")

        return generate_html_response(ai_analysis, cleaned_data, tool_config, localization)

    except Exception as e:
        # Calculate error response time
        response_time = int((time.time() - start_time) * 1000)

        print(f"❌ AI analysis failed after {response_time}ms: {str(e)}")

        # Log the error attempt (cost=0 for failed requests)
        try:
            log_openai_cost_enhanced(
                cost=0,
                tokens=0,
                model="error",
                ip=ip,
                tools_slug=tool_name
            )
        except:
            pass  # Don't fail on error logging

def clean_user_data(user_data):
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
            else:
                cleaned[key] = value
        else:
            cleaned[key] = value
    return cleaned


def build_enhanced_prompt(tool_name, category, user_data, localization=None):
    """Enhanced prompt that asks OpenAI to provide specific local recommendations"""

    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    currency = localization.get('currency', 'USD')
    country = localization.get('country_name', '')

    if currency == 'u20ac':
        currency = 'EUR'

    # Extract location details if available
    location_info = ""
    if 'locationData' in user_data and isinstance(user_data['locationData'], dict):
        location_data = user_data['locationData']
        city = location_data.get('city', '')
        region = location_data.get('region', '')
        postal_code = location_data.get('postal_code', '')

        location_info = f"Specific location: {city}, {region}, {country} ({postal_code})"

    # Build user context
    context_items = []
    for key, value in user_data.items():
        if key == 'locationData':
            continue  # Already handled above
        elif isinstance(value, (int, float)) and value > 0:
            if key in ['amount', 'budget', 'income', 'price', 'coverage_amount']:
                context_items.append(f"{key.title()}: {currency} {value:,.0f}")
            else:
                context_items.append(f"{key.title()}: {value}")
        elif isinstance(value, str) and value.strip():
            context_items.append(f"{key.title()}: {value}")

    user_context = " | ".join(context_items[:8])

    return f"""You are a local expert providing specific, actionable advice for {country} residents. Calculate and analyze this {tool_name} request with SPECIFIC LOCAL RECOMMENDATIONS.

USER INPUT: {user_context}
LOCATION: {location_info or country}
CATEGORY: {category}
CURRENCY: {currency}
LANGUAGE: {language}

CRITICAL: Provide SPECIFIC local companies, websites, phone numbers, and experts - NOT generic advice like "use comparison sites" or "contact an advisor."

Provide this structure:

1. **MAIN RESULT** 
Calculate the key number/outcome with {currency} amounts

2. **KEY INSIGHTS** (3 specific points)
Local market insights specific to {country}

3. **RECOMMENDED LOCAL PROVIDERS**
- List 3-5 SPECIFIC companies available in {country} with:
  * Company name
  * Website 
  * Phone number (if known)
  * Why they're good for this situation

4. **LOCAL COMPARISON RESOURCES**
- SPECIFIC websites/portals used in {country} for comparing {category}
- Government/regulatory websites for {country}
- Consumer protection resources in {country}

5. **LOCAL EXPERTS TO CONTACT**
- Specific types of local professionals
- Where to find them in {country}
- Professional associations in {country}

6. **IMMEDIATE ACTION STEPS**
What to do RIGHT NOW with specific local resources

Be EXTREMELY specific to {country}. Use real company names, actual websites, and local phone numbers when possible. Make this incredibly valuable and actionable for someone in {country}.

Respond entirely in {language}."""


def get_enhanced_system_prompt(localization=None):
    """Enhanced system prompt for local expertise"""

    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    currency = localization.get('currency', 'USD')
    country = localization.get('country_name', '')

    if currency == 'u20ac':
        currency = 'EUR'

    prompt = f"""You are a LOCAL EXPERT for {country} with deep knowledge of:

- Local companies and service providers in {country}
- Websites, phone numbers, and contact information
- Government agencies and regulatory bodies in {country}  
- Professional associations and expert networks
- Local market conditions and pricing in {country}
- Consumer protection resources specific to {country}
- Cultural and regulatory context for {country}

ALWAYS provide SPECIFIC, ACTIONABLE local information:
✅ Real company names available in {country}
✅ Actual websites and phone numbers
✅ Specific local resources and portals
✅ Government agency contact info
✅ Professional association details
✅ Local expert recommendations

❌ NEVER give generic advice like "contact an advisor" or "use comparison sites"
❌ Always be specific to {country} context and regulations

Use {currency} for all amounts."""

    if language != 'English':
        prompt += f" Respond entirely in {language} with local terminology."

    return prompt


def generate_enhanced_html_response(ai_analysis, user_data, tool_config, localization=None):
    """Enhanced HTML with better styling for local recommendations"""

    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    currency = localization.get('currency', 'USD')
    country = localization.get('country_name', '')

    if currency == 'u20ac':
        currency = 'EUR'

    tool_name = tool_config.get("seo_data", {}).get("title", "Calculator")

    # Enhanced content formatting for local recommendations
    formatted_content = format_enhanced_content_advanced(ai_analysis, country, language)

    return f"""
<style>
.ai-results {{
    max-width: 900px;
    margin: 20px auto;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    line-height: 1.6;
    color: #333;
}}
.result-header {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 30px;
    border-radius: 12px;
    margin-bottom: 20px;
    text-align: center;
    position: relative;
}}
.country-badge {{
    position: absolute;
    top: 15px;
    right: 20px;
    background: rgba(255,255,255,0.2);
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 500;
}}
.result-title {{
    font-size: 1.8rem;
    font-weight: 700;
    margin-bottom: 8px;
}}
.result-subtitle {{
    opacity: 0.9;
    font-size: 1rem;
}}
.content-section {{
    background: white;
    padding: 30px;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    margin-bottom: 20px;
    border-left: 4px solid #667eea;
}}
.provider-card {{
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border: 1px solid #cbd5e0;
    border-radius: 10px;
    padding: 20px;
    margin: 15px 0;
    transition: transform 0.2s, box-shadow 0.2s;
}}
.provider-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}}
.provider-name {{
    font-size: 1.2rem;
    font-weight: 600;
    color: #2d3748;
    margin-bottom: 8px;
}}
.provider-contact {{
    background: #667eea;
    color: white;
    padding: 8px 16px;
    border-radius: 25px;
    text-decoration: none;
    display: inline-block;
    margin: 5px 5px 5px 0;
    font-size: 0.9rem;
    font-weight: 500;
    transition: background 0.2s;
}}
.provider-contact:hover {{
    background: #5a6fd8;
    color: white;
    text-decoration: none;
}}
.expert-box {{
    background: linear-gradient(135deg, #fed7d7 0%, #fbb6ce 100%);
    border: 1px solid #fc8181;
    border-radius: 10px;
    padding: 20px;
    margin: 15px 0;
}}
.action-step {{
    background: linear-gradient(135deg, #c6f6d5 0%, #9ae6b4 100%);
    border: 1px solid #68d391;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    border-left: 4px solid #38a169;
}}
.content-section h3 {{
    color: #2d3748;
    font-size: 1.4rem;
    margin-bottom: 15px;
    font-weight: 600;
    display: flex;
    align-items: center;
}}
.section-icon {{
    margin-right: 10px;
    font-size: 1.2rem;
}}
.content-section h4 {{
    color: #4a5568;
    font-size: 1.1rem;
    margin: 20px 0 10px 0;
    font-weight: 600;
}}
.content-section p {{
    margin: 12px 0;
    color: #4a5568;
}}
.content-section strong {{
    color: #2d3748;
    font-weight: 600;
}}
.local-badge {{
    background: #38a169;
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 500;
    margin-left: 8px;
}}
@media (max-width: 768px) {{
    .ai-results {{ padding: 10px; }}
    .result-header, .content-section {{ padding: 20px; }}
    .result-title {{ font-size: 1.5rem; }}
    .provider-card {{ padding: 15px; }}
    .country-badge {{ position: static; margin-bottom: 10px; }}
}}
</style>

<div class="ai-results">
    <div class="result-header">
        <div class="country-badge">🌍 {country}</div>
        <div class="result-title">🎯 {tool_name}</div>
        <div class="result-subtitle">{get_text('local_analysis_complete', language)}</div>
    </div>

    <div class="content-section">
        {formatted_content}
    </div>
</div>
"""


import re
import html


def format_enhanced_content(ai_analysis, country, language):
    """Enhanced content formatting with modern material design UI/UX"""

    if not ai_analysis or not isinstance(ai_analysis, str):
        return "<p>No analysis available.</p>"

    # Clean and prepare content
    content = clean_ai_content(ai_analysis)

    # Parse content into structured sections
    sections = parse_ai_sections(content)

    # Format each section
    formatted_sections = []
    for section in sections:
        formatted_section = format_section_by_type(section, country, language)
        if formatted_section:
            formatted_sections.append(formatted_section)

    # Combine all sections
    result = '\n'.join(formatted_sections)

    return f'<div class="modern-ai-analysis">{result}</div>'


def clean_ai_content(content):
    """Clean and normalize AI content"""
    # Remove HTML artifacts
    content = re.sub(r'<[^>]+>', '', content)

    # Fix currency encoding
    content = fix_currency_encoding(content)

    # Normalize whitespace
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
    content = content.strip()

    return content


def parse_ai_sections(content):
    """Parse AI content into structured sections"""
    sections = []

    # Split by section headers (**, ###, numbered sections)
    section_pattern = r'(?:^|\n)\s*(?:#{1,3}\s*|\*\*|(?:\d+\.?\s*)?)([A-Z][A-Z\s]*(?:RESULT|INSIGHT|PROVIDER|COMPARISON|RESOURCE|EXPERT|ACTION|STEP)[A-Z\s]*)\*?\*?\s*(?:\n|$)'

    parts = re.split(section_pattern, content, flags=re.MULTILINE | re.IGNORECASE)

    # Handle intro content (before first section)
    if parts[0].strip():
        sections.append({
            'type': 'intro',
            'title': 'Introduction',
            'content': parts[0].strip()
        })

    # Process remaining sections
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            title = parts[i].strip()
            content_text = parts[i + 1].strip()

            if title and content_text:
                section_type = detect_section_type(title)
                sections.append({
                    'type': section_type,
                    'title': title,
                    'content': content_text
                })

    return sections


def detect_section_type(title):
    """Detect section type from title"""
    title_upper = title.upper()

    if any(word in title_upper for word in ['RESULT', 'CALCULATION', 'ESTIMATE']):
        return 'result'
    elif any(word in title_upper for word in ['INSIGHT', 'ANALYSIS', 'MARKET']):
        return 'insights'
    elif any(word in title_upper for word in ['PROVIDER', 'COMPANY', 'RECOMMEND']):
        return 'providers'
    elif any(word in title_upper for word in ['COMPARISON', 'RESOURCE', 'WEBSITE']):
        return 'resources'
    elif any(word in title_upper for word in ['EXPERT', 'CONTACT', 'PROFESSIONAL']):
        return 'experts'
    elif any(word in title_upper for word in ['ACTION', 'STEP', 'IMMEDIATE']):
        return 'actions'
    else:
        return 'generic'


def format_section_by_type(section, country, language):
    """Format section based on its type"""
    section_type = section['type']
    title = section['title']
    content = section['content']

    if section_type == 'intro':
        return format_intro_section(content)
    elif section_type == 'result':
        return format_result_section(title, content)
    elif section_type == 'insights':
        return format_insights_section(title, content)
    elif section_type == 'providers':
        return format_providers_section(title, content, country)
    elif section_type == 'resources':
        return format_resources_section(title, content)
    elif section_type == 'experts':
        return format_experts_section(title, content)
    elif section_type == 'actions':
        return format_action_steps_section(title, content)
    else:
        return format_generic_section(title, content)


def format_intro_section(content):
    """Format introduction section"""
    paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
    formatted_paragraphs = []

    for p in paragraphs:
        if p.startswith('**') and p.endswith('**'):
            header_text = p.strip('*')
            formatted_paragraphs.append(
                f'<h3 class="section-header"><span class="header-icon">📊</span>{header_text}</h3>')
        else:
            p = format_inline_styling(p)
            formatted_paragraphs.append(f'<p class="intro-text">{p}</p>')

    return f'<div class="intro-section">{" ".join(formatted_paragraphs)}</div>'


def format_result_section(title, content):
    """Format main result section"""
    formatted_content = format_inline_styling(content)

    return f'''
    <div class="content-section generic-section">
        <h3 class="section-title">
            <span class="section-icon">📊</span>
            <span class="title-text">{title}</span>
        </h3>
        <div class="section-content">
            <p>{formatted_content}</p>
        </div>
    </div>
    '''


def format_insights_section(title, content):
    """Format insights with modern info cards"""
    insights = parse_insights_content(content)

    if not insights:
        # If no structured insights found, show as simple content
        formatted_content = format_inline_styling(content)
        return f'''
        <div class="content-section insights-section">
            <h3 class="section-title">
                <span class="section-icon">💡</span>
                <span class="title-text">{title}</span>
            </h3>
            <div class="section-content">
                <p>{formatted_content}</p>
            </div>
        </div>
        '''

    insight_cards = []
    for insight in insights:
        card_html = f'''
        <div class="insight-card">
            <div class="insight-icon">💡</div>
            <div class="insight-content">
                <div class="insight-title">{insight['title']}</div>
                <div class="insight-text">{insight['content']}</div>
            </div>
        </div>
        '''
        insight_cards.append(card_html)

    return f'''
    <div class="content-section insights-section">
        <h3 class="section-title">
            <span class="section-icon">💡</span>
            <span class="title-text">{title}</span>
        </h3>
        <div class="insights-grid">
            {"".join(insight_cards)}
        </div>
    </div>
    '''


def format_providers_section(title, content, country):
    """Format providers with modern card design"""
    providers = parse_providers_content(content)

    if not providers:
        # If no structured providers found, show as simple content
        formatted_content = format_inline_styling(content)
        return f'''
        <div class="content-section providers-section">
            <h3 class="section-title">
                <span class="section-icon">🏢</span>
                <span class="title-text">{title}</span>
                <span class="country-flag">{get_country_flag(country)}</span>
            </h3>
            <div class="section-content">
                <p>{formatted_content}</p>
            </div>
        </div>
        '''

    cards_html = []
    for provider in providers:
        card_html = f'''
        <div class="provider-card">
            <div class="provider-header">
                <div class="provider-name">{provider['name']}</div>
                <div class="provider-rating">
                    <span class="rating-stars">⭐⭐⭐⭐⭐</span>
                    <span class="local-badge">Local Expert</span>
                </div>
            </div>
            <div class="provider-description">
                {provider.get('description', 'Professional service provider')}
            </div>
            <div class="provider-actions">
                {format_provider_contacts(provider)}
            </div>
        </div>
        '''
        cards_html.append(card_html)

    return f'''
    <div class="content-section providers-section">
        <h3 class="section-title">
            <span class="section-icon">🏢</span>
            <span class="title-text">{title}</span>
            <span class="country-flag">{get_country_flag(country)}</span>
        </h3>
        <div class="providers-grid">
            {"".join(cards_html)}
        </div>
    </div>
    '''


def format_resources_section(title, content):
    """Format comparison resources with modern design"""
    resources = parse_resources_content(content)

    if not resources:
        # If no structured resources found, show as simple content
        formatted_content = format_inline_styling(content)
        return f'''
        <div class="content-section resources-section">
            <h3 class="section-title">
                <span class="section-icon">🔍</span>
                <span class="title-text">{title}</span>
            </h3>
            <div class="section-content">
                <p>{formatted_content}</p>
            </div>
        </div>
        '''

    resource_cards = []
    for resource in resources:
        card_html = f'''
        <div class="resource-card">
            <div class="resource-icon">🔍</div>
            <div class="resource-content">
                <div class="resource-name">{resource['name']}</div>
                <div class="resource-description">{resource.get('description', 'Comparison and review platform')}</div>
                <a href="{resource['url']}" target="_blank" class="resource-link">
                    <span class="link-icon">🌐</span>
                    Visit Platform
                </a>
            </div>
        </div>
        '''
        resource_cards.append(card_html)

    return f'''
    <div class="content-section resources-section">
        <h3 class="section-title">
            <span class="section-icon">🔍</span>
            <span class="title-text">{title}</span>
        </h3>
        <div class="resources-grid">
            {"".join(resource_cards)}
        </div>
    </div>
    '''


def format_experts_section(title, content):
    """Format experts section with professional design"""
    experts = parse_experts_content(content)

    if not experts:
        # If no structured experts found, show as simple content
        formatted_content = format_inline_styling(content)
        return f'''
        <div class="content-section experts-section">
            <h3 class="section-title">
                <span class="section-icon">👨‍💼</span>
                <span class="title-text">{title}</span>
            </h3>
            <div class="section-content">
                <p>{formatted_content}</p>
            </div>
        </div>
        '''

    expert_cards = []
    for expert in experts:
        card_html = f'''
        <div class="expert-card">
            <div class="expert-icon">👨‍💼</div>
            <div class="expert-info">
                <div class="expert-name">{expert['name']}</div>
                <div class="expert-specialty">{expert.get('specialty', 'Professional Advisor')}</div>
                <div class="expert-description">{expert.get('description', '')}</div>
                {format_expert_contacts(expert)}
            </div>
        </div>
        '''
        expert_cards.append(card_html)

    return f'''
    <div class="content-section experts-section">
        <h3 class="section-title">
            <span class="section-icon">👨‍💼</span>
            <span class="title-text">{title}</span>
        </h3>
        <div class="experts-grid">
            {"".join(expert_cards)}
        </div>
    </div>
    '''


def format_action_steps_section(title, content):
    """Format action steps with modern checklist design"""
    steps = parse_action_steps_content(content)

    if not steps:
        # If no structured steps found, show as simple content
        formatted_content = format_inline_styling(content)
        return f'''
        <div class="content-section action-section">
            <h3 class="section-title">
                <span class="section-icon">🚀</span>
                <span class="title-text">{title}</span>
            </h3>
            <div class="section-content">
                <p>{formatted_content}</p>
            </div>
        </div>
        '''

    step_items = []
    for i, step in enumerate(steps, 1):
        step_html = f'''
        <div class="action-step">
            <div class="step-number">{i}</div>
            <div class="step-content">
                <div class="step-text">{step}</div>
            </div>
            <div class="step-check">✓</div>
        </div>
        '''
        step_items.append(step_html)

    return f'''
    <div class="content-section action-section">
        <h3 class="section-title">
            <span class="section-icon">🚀</span>
            <span class="title-text">{title}</span>
        </h3>
        <div class="action-steps">
            {"".join(step_items)}
        </div>
    </div>
    '''


def format_generic_section(title, content):
    """Format generic sections"""
    formatted_content = format_inline_styling(content)

    return f'''
    <div class="content-section generic-section">
        <h3 class="section-title">
            <span class="section-icon">📋</span>
            <span class="title-text">{title}</span>
        </h3>
        <div class="section-content">
            <p>{formatted_content}</p>
        </div>
    </div>
    '''


def parse_insights_content(content):
    """Parse insights from content"""
    insights = []

    # Look for numbered or bulleted insights
    lines = content.split('\n')
    current_insight = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for insight headers (numbered, bulleted, or bold)
        if (line.startswith(('1.', '2.', '3.', '4.', '5.')) or
                line.startswith(('-', '•', '*')) or
                (line.startswith('**') and ':' in line)):

            # Save previous insight
            if current_insight:
                insights.append(current_insight)

            # Start new insight
            if line.startswith('**') and line.endswith('**') and ':' in line:
                parts = line.strip('*').split(':', 1)
                title = parts[0].strip()
                content_text = parts[1].strip() if len(parts) > 1 else ''
            else:
                # Remove numbering/bullets
                clean_line = re.sub(r'^[\d\.\-\•\*\s]+', '', line)
                if ':' in clean_line:
                    parts = clean_line.split(':', 1)
                    title = parts[0].strip()
                    content_text = parts[1].strip() if len(parts) > 1 else ''
                else:
                    title = clean_line
                    content_text = ''

            current_insight = {
                'title': title,
                'content': content_text
            }
        elif current_insight:
            # Continue previous insight
            current_insight['content'] += ' ' + line

    # Add last insight
    if current_insight:
        insights.append(current_insight)

    return insights


def parse_providers_content(content):
    """Parse provider information with enhanced link detection"""
    providers = []
    lines = content.split('\n')
    current_provider = {}

    for line in lines:
        line = line.strip()
        if not line:
            # End of provider section
            if current_provider and current_provider.get('name'):
                providers.append(current_provider)
                current_provider = {}
            continue

        # Provider name (usually starts with -, *, or **)
        if (line.startswith(('-', '•', '*')) and not any(keyword in line.lower()
                                                         for keyword in ['website', 'phone', 'why', 'email'])):
            # Save previous provider
            if current_provider and current_provider.get('name'):
                providers.append(current_provider)
                current_provider = {}

            # Extract provider name
            name = re.sub(r'^[\-\•\*\s]+', '', line).strip('*')
            current_provider['name'] = name

        # Website detection - enhanced for various formats
        elif any(keyword in line.lower() for keyword in ['website', 'site', 'web']):
            website = extract_website_from_line(line)
            if website:
                current_provider['website'] = website

        # Phone detection
        elif any(keyword in line.lower() for keyword in ['phone', 'tel', 'call']):
            phone = extract_phone_from_line(line)
            if phone:
                current_provider['phone'] = phone

        # Email detection
        elif any(keyword in line.lower() for keyword in ['email', 'mail']):
            email = extract_email_from_line(line)
            if email:
                current_provider['email'] = email

        # Description (usually starts with "Why" or contains explanation)
        elif any(keyword in line.lower() for keyword in ['why', 'good', 'known', 'offers']):
            description = line.split(':', 1)[-1].strip()
            if description:
                current_provider['description'] = description

        # If line contains a URL, try to extract it
        elif 'http' in line or any(tld in line for tld in ['.com', '.co.uk', '.org', '.net']):
            website = extract_website_from_line(line)
            if website and not current_provider.get('website'):
                current_provider['website'] = website

    # Add last provider
    if current_provider and current_provider.get('name'):
        providers.append(current_provider)

    return providers


def extract_website_from_line(line):
    """Extract website URL from line with enhanced markdown link support"""
    # First, try to extract from markdown link format: [Text](URL)
    markdown_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', line)
    if markdown_match:
        return clean_url(markdown_match.group(2))

    # Try to extract from format: **Website:** [Company](URL)
    markdown_match2 = re.search(r'\*\*[^*]+\*\*\s*\[([^\]]+)\]\(([^)]+)\)', line)
    if markdown_match2:
        return clean_url(markdown_match2.group(2))

    # Extract direct URLs
    url_match = re.search(r'https?://[^\s\])+]+', line)
    if url_match:
        return clean_url(url_match.group())

    # Extract domain patterns
    domain_match = re.search(r'\b(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})\b', line)
    if domain_match:
        domain = domain_match.group()
        if not domain.startswith('http'):
            domain = 'https://' + domain
        return clean_url(domain)

    return None


def extract_phone_from_line(line):
    """Extract phone number from line"""
    # Remove common prefixes
    clean_line = re.sub(r'.*(?:phone|tel|call).*?:?\s*', '', line, flags=re.IGNORECASE)

    # Look for phone patterns
    phone_match = re.search(r'[\+]?[\d\s\-\(\)]{8,}', clean_line)
    if phone_match:
        return phone_match.group().strip()

    return None


def extract_email_from_line(line):
    """Extract email from line"""
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', line)
    if email_match:
        return email_match.group()

    return None


def clean_url(url):
    """Clean and validate URL"""
    if not url:
        return None

    # Remove surrounding characters
    url = url.strip('.,;()[]{}"\' ')

    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Basic validation
    if len(url) > 10 and '.' in url:
        return url

    return None


def parse_resources_content(content):
    """Parse resource information"""
    resources = []
    lines = content.split('\n')

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Remove bullet points
        line = re.sub(r'^[\-\•\*\s]+', '', line)

        # Parse different formats
        resource = None

        # Format: **Name:** [Link](URL) - Description
        markdown_match = re.search(r'\*\*([^*]+)\*\*:?\s*\[([^\]]+)\]\(([^)]+)\)(.*)'
                                   , line)
        if markdown_match:
            name = markdown_match.group(1).strip()
            url = clean_url(markdown_match.group(3))
            description = markdown_match.group(4).strip(' -')
            resource = {'name': name, 'url': url, 'description': description}

        # Format: Name: URL - Description
        elif ':' in line:
            parts = line.split(':', 1)
            name = parts[0].strip('*')
            rest = parts[1].strip()

            # Extract URL and description
            url = extract_website_from_line(rest)
            description = re.sub(r'https?://[^\s]+|www\.[^\s]+|\b[a-zA-Z0-9-]+\.[a-zA-Z]{2,}\b', '', rest).strip(' -')

            if url:
                resource = {
                    'name': name,
                    'url': url,
                    'description': description or 'Comparison and review platform'
                }

        if resource:
            resources.append(resource)

    return resources


def parse_experts_content(content):
    """Parse expert information"""
    experts = []
    lines = content.split('\n')
    current_expert = {}

    for line in lines:
        line = line.strip()
        if not line:
            if current_expert and current_expert.get('name'):
                experts.append(current_expert)
                current_expert = {}
            continue

        # Expert name (usually starts with -, *, or **)
        if (line.startswith(('-', '•', '*')) and not any(keyword in line.lower()
                                                         for keyword in ['website', 'phone', 'contact'])):
            # Save previous expert
            if current_expert and current_expert.get('name'):
                experts.append(current_expert)
                current_expert = {}

            # Extract expert name
            name = re.sub(r'^[\-\•\*\s]+', '', line).strip('*')

            # Check if it's a description line instead
            if ':' in name:
                parts = name.split(':', 1)
                current_expert['name'] = parts[0].strip()
                current_expert['description'] = parts[1].strip()
            else:
                current_expert['name'] = name

        # Website or contact info
        elif any(keyword in line.lower() for keyword in ['website', 'contact', '.com', '.org']):
            website = extract_website_from_line(line)
            if website:
                current_expert['website'] = website
            else:
                # Use as description if no URL found
                if 'description' not in current_expert:
                    current_expert['description'] = line

        # Description line
        elif current_expert and 'description' not in current_expert:
            current_expert['description'] = line

    # Add last expert
    if current_expert and current_expert.get('name'):
        experts.append(current_expert)

    return experts


def parse_action_steps_content(content):
    """Parse action steps"""
    steps = []
    lines = content.split('\n')

    for line in lines:
        line = line.strip()
        if not line or line.lower().startswith('by following'):
            continue

        # Remove numbering and bullet points
        step = re.sub(r'^\d+\.\s*|^[\-\•\*]\s*', '', line)
        step = step.strip('*')  # Remove markdown bold

        if step and len(step) > 10:  # Only include substantial steps
            # Format inline styling
            step = format_inline_styling(step)
            steps.append(step)

    return steps


def format_provider_contacts(provider):
    """Format provider contact information with enhanced support"""
    contacts = []

    if provider.get('website'):
        contacts.append(
            f'<a href="{provider["website"]}" target="_blank" class="contact-btn website-btn">'
            f'<span class="btn-icon">🌐</span>Visit Website</a>'
        )

    if provider.get('phone'):
        contacts.append(
            f'<a href="tel:{provider["phone"]}" class="contact-btn phone-btn">'
            f'<span class="btn-icon">📞</span>Call Now</a>'
        )

    if provider.get('email'):
        contacts.append(
            f'<a href="mailto:{provider["email"]}" class="contact-btn email-btn">'
            f'<span class="btn-icon">✉️</span>Email</a>'
        )

    return ''.join(contacts)


def format_expert_contacts(expert):
    """Format expert contact information"""
    if expert.get('website'):
        return f'<a href="{expert["website"]}" target="_blank" class="expert-contact">View Profile</a>'
    return '<div class="expert-contact">Contact through professional directory</div>'


def fix_currency_encoding(text):
    """Fix currency encoding issues"""
    replacements = {
        'u00a3': '£',
        'u20ac': '€',
        '&pound;': '£',
        '&euro;': '€',
        '&#8364;': '€',
        '&#163;': '£'
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def format_inline_styling(text):
    """Format inline styling like bold and italic with link support"""
    # Handle markdown links first: [text](url)
    text = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        r'<a href="\2" target="_blank">\1</a>',
        text
    )

    # Handle bold text
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

    # Handle italic text (single asterisk, but not part of bold)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)

    # Fix currency encoding
    text = fix_currency_encoding(text)

    return text


def get_country_flag(country):
    """Get country flag emoji"""
    if not country:
        return '🌍'

    flags = {
        'united kingdom': '🇬🇧', 'uk': '🇬🇧', 'britain': '🇬🇧', 'england': '🇬🇧',
        'united states': '🇺🇸', 'usa': '🇺🇸', 'america': '🇺🇸',
        'canada': '🇨🇦', 'australia': '🇦🇺', 'germany': '🇩🇪', 'deutschland': '🇩🇪',
        'france': '🇫🇷', 'spain': '🇪🇸', 'italy': '🇮🇹', 'netherlands': '🇳🇱',
        'sweden': '🇸🇪', 'norway': '🇳🇴', 'denmark': '🇩🇰', 'finland': '🇫🇮',
        'ireland': '🇮🇪', 'belgium': '🇧🇪', 'switzerland': '🇨🇭', 'austria': '🇦🇹',
        'portugal': '🇵🇹', 'poland': '🇵🇱', 'czech republic': '🇨🇿',
        'japan': '🇯🇵', 'south korea': '🇰🇷', 'china': '🇨🇳', 'india': '🇮🇳',
        'brazil': '🇧🇷', 'mexico': '🇲🇽', 'argentina': '🇦🇷'
    }

    return flags.get(country.lower(), '🌍')


def get_modern_css():
    """Return modern CSS styles"""
    return '''
<style>
.modern-ai-analysis {
    max-width: 1200px;
    margin: 0 auto;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.6;
    color: #2d3748;
}

.intro-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 40px;
    border-radius: 16px;
    margin-bottom: 32px;
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.intro-text {
    font-size: 1.1rem;
    margin: 16px 0;
    opacity: 0.95;
}

.content-section {
    background: #ffffff;
    border-radius: 16px;
    padding: 32px;
    margin-bottom: 24px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border: 1px solid #e2e8f0;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.content-section:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
}

.section-title {
    display: flex;
    align-items: center;
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 24px;
    color: #1a202c;
    gap: 12px;
}

.section-icon {
    font-size: 1.8rem;
    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
}

.title-text {
    flex: 1;
}

.country-flag {
    font-size: 1.5rem;
}

/* Provider Cards */
.providers-grid {
    display: grid;
    gap: 24px;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
}

.provider-card {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border: 1px solid #cbd5e0;
    border-radius: 12px;
    padding: 24px;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.provider-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

.provider-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(102, 126, 234, 0.2);
    border-color: #667eea;
}

.provider-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;
}

.provider-name {
    font-size: 1.3rem;
    font-weight: 700;
    color: #1a202c;
    line-height: 1.3;
}

.provider-rating {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
}

.rating-stars {
    font-size: 0.9rem;
    opacity: 0.8;
}

.local-badge {
    background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
    color: white;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(56, 161, 105, 0.3);
}

.provider-description {
    color: #4a5568;
    margin-bottom: 20px;
    line-height: 1.6;
}

.provider-actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}

.contact-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.2s ease;
    border: none;
    cursor: pointer;
}

.website-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.website-btn:hover {
    background: linear-gradient(135deg, #5a6fd8 0%, #6b4490 100%);
    transform: translateY(-1px);
    color: white;
    text-decoration: none;
}

.phone-btn {
    background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
    color: white;
}

.phone-btn:hover {
    background: linear-gradient(135deg, #2f855a 0%, #276749 100%);
    transform: translateY(-1px);
    color: white;
    text-decoration: none;
}

.btn-icon {
    font-size: 1rem;
}

/* Resource Cards */
.resources-grid {
    display: grid;
    gap: 20px;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

.resource-card {
    display: flex;
    align-items: center;
    background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%);
    border: 1px solid #fdba74;
    border-radius: 12px;
    padding: 20px;
    transition: all 0.3s ease;
}

.resource-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(251, 146, 60, 0.2);
}

.resource-icon {
    font-size: 2rem;
    margin-right: 16px;
    opacity: 0.8;
}

.resource-content {
    flex: 1;
}

.resource-name {
    font-weight: 700;
    color: #9a3412;
    margin-bottom: 4px;
}

.resource-description {
    color: #7c2d12;
    font-size: 0.9rem;
    margin-bottom: 8px;
}

.resource-link {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: #ea580c;
    text-decoration: none;
    font-weight: 600;
    font-size: 0.9rem;
}

.resource-link:hover {
    color: #c2410c;
    text-decoration: none;
}

/* Expert Cards */
.experts-grid {
    display: grid;
    gap: 20px;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.expert-card {
    display: flex;
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border: 1px solid #fbbf24;
    border-radius: 12px;
    padding: 20px;
    transition: all 0.3s ease;
}

.expert-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(251, 191, 36, 0.2);
}

.expert-icon {
    font-size: 2.5rem;
    margin-right: 16px;
    opacity: 0.8;
}

.expert-info {
    flex: 1;
}

.expert-name {
    font-weight: 700;
    color: #92400e;
    margin-bottom: 4px;
    font-size: 1.1rem;
}

.expert-specialty {
    color: #b45309;
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 8px;
}

.expert-description {
    color: #78350f;
    font-size: 0.9rem;
    margin-bottom: 12px;
}

.expert-contact {
    display: inline-block;
    color: #d97706;
    text-decoration: none;
    font-weight: 600;
    font-size: 0.9rem;
}

/* Action Steps */
.action-steps {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.action-step {
    display: flex;
    align-items: center;
    background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
    border: 1px solid #86efac;
    border-radius: 12px;
    padding: 20px;
    transition: all 0.3s ease;
}

.action-step:hover {
    transform: translateX(4px);
    box-shadow: 0 4px 16px rgba(34, 197, 94, 0.2);
}

.step-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
    color: white;
    border-radius: 50%;
    font-weight: 700;
    font-size: 1.1rem;
    margin-right: 20px;
    box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
}

.step-content {
    flex: 1;
}

.step-text {
    color: #166534;
    font-weight: 500;
    line-height: 1.5;
}

.step-check {
    font-size: 1.5rem;
    color: #22c55e;
    opacity: 0.7;
    margin-left: 12px;
}

/* Insights */
.insights-grid {
    display: grid;
    gap: 20px;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
}

.insight-card {
    display: flex;
    background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
    border: 1px solid #c4b5fd;
    border-radius: 12px;
    padding: 20px;
    transition: all 0.3s ease;
}

.insight-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(139, 92, 246, 0.2);
}

.insight-icon {
    font-size: 2rem;
    margin-right: 16px;
    opacity: 0.8;
}

.insight-content {
    flex: 1;
}

.insight-title {
    font-weight: 700;
    color: #581c87;
    margin-bottom: 8px;
    font-size: 1.1rem;
}

.insight-text {
    color: #6b21a8;
    line-height: 1.5;
}

/* Responsive Design */
@media (max-width: 768px) {
    .modern-ai-analysis {
        padding: 16px;
    }

    .content-section {
        padding: 24px 20px;
        margin-bottom: 16px;
    }

    .providers-grid,
    .resources-grid,
    .experts-grid,
    .insights-grid {
        grid-template-columns: 1fr;
    }

    .provider-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
    }

    .provider-rating {
        align-items: flex-start;
    }

    .provider-actions {
        flex-direction: column;
    }

    .contact-btn {
        width: 100%;
        justify-content: center;
    }

    .section-title {
        font-size: 1.3rem;
        flex-wrap: wrap;
    }
}

@media (max-width: 480px) {
    .intro-section {
        padding: 24px 20px;
    }

    .resource-card,
    .expert-card {
        flex-direction: column;
        text-align: center;
    }

    .resource-icon,
    .expert-icon {
        margin-right: 0;
        margin-bottom: 12px;
    }

    .action-step {
        flex-direction: column;
        text-align: center;
        gap: 12px;
    }

    .step-number {
        margin-right: 0;
    }
}
</style>
'''


def get_text(key, language):
    """Get localized text"""
    texts = {
        'English': {
            'analysis_complete': 'Local Analysis Complete',
            'local_analysis_complete': 'Local Expert Analysis Complete'
        },
        'Norwegian': {
            'analysis_complete': 'Lokal analyse fullført',
            'local_analysis_complete': 'Lokal ekspertanalyse fullført'
        },
        'German': {
            'analysis_complete': 'Lokale Analyse abgeschlossen',
            'local_analysis_complete': 'Lokale Expertenanalyse abgeschlossen'
        }
    }

    return texts.get(language, texts['English']).get(key, key)

def build_prompt(tool_name, category, user_data, localization=None):
    return build_enhanced_prompt(tool_name, category, user_data, localization)

def get_system_prompt(localization=None):
    return get_enhanced_system_prompt(localization)

def generate_html_response(ai_analysis, user_data, tool_config, localization=None):
    return generate_enhanced_html_response(ai_analysis, user_data, tool_config, localization)


def format_content(content):
    if not content:
        return '<p>No analysis available.</p>'

    formatted = content
    formatted = formatted.replace('**', '<strong>').replace('**', '</strong>')
    formatted = formatted.replace('*', '<em>').replace('*', '</em>')

    lines = formatted.split('\n')
    html_lines = []
    in_list = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('- ') or line.startswith('• '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f'<li>{line[2:]}</li>')
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False

            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                html_lines.append(f'<h{level + 2}>{line.lstrip("# ")}</h{level + 2}>')
            else:
                html_lines.append(f'<p>{line}</p>')

    if in_list:
        html_lines.append('</ul>')

    return '\n'.join(html_lines)