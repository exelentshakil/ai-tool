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

        return create_simple_fallback(tool_config, cleaned_data, localization)

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
    formatted_content = format_enhanced_content(ai_analysis, country, language)

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

def format_enhanced_content(ai_analysis, country, language):
    """Enhanced content formatting with modern material design UI/UX"""

    if not ai_analysis or not isinstance(ai_analysis, str):
        return "<p>No analysis available.</p>"

    # Clean the content first
    content = ai_analysis.strip()

    # Remove any existing HTML artifacts
    content = re.sub(r'<[^>]+>', '', content)

    # Split into sections and process
    sections = re.split(r'\n\s*###\s*', content)
    formatted_sections = []

    for i, section in enumerate(sections):
        if not section.strip():
            continue

        # Skip numbering prefixes like "1. ", "2. " etc at start of sections
        section = re.sub(r'^\d+\.\s*', '', section.strip())

        if i == 0:
            # First section is usually intro - format as main content
            formatted_section = format_intro_section(section)
        else:
            formatted_section = format_content_section(section, country)

        if formatted_section:
            formatted_sections.append(formatted_section)

    # Join all sections and add custom CSS
    result = get_modern_css() + '\n'.join(formatted_sections)

    return f'<div class="modern-ai-analysis">{result}</div>'


def format_intro_section(content):
    """Format the introduction/main result section"""
    if not content.strip():
        return ""

    # Clean up currency encoding issues
    content = fix_currency_encoding(content)

    # Convert to paragraphs
    paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
    formatted_paragraphs = []

    for p in paragraphs:
        if p.startswith('**') and p.endswith('**'):
            # This is a header
            header_text = p.strip('*')
            formatted_paragraphs.append(
                f'<h3 class="section-header"><span class="header-icon">📊</span>{header_text}</h3>')
        else:
            # Regular paragraph
            p = format_inline_styling(p)
            formatted_paragraphs.append(f'<p class="intro-text">{p}</p>')

    return f'<div class="intro-section">{" ".join(formatted_paragraphs)}</div>'


def format_content_section(section, country):
    """Format content sections with modern material design"""
    if not section.strip():
        return ""

    lines = [line.strip() for line in section.split('\n') if line.strip()]
    if not lines:
        return ""

    # Get section title from first line
    section_title = lines[0].upper().strip('*')
    section_content = lines[1:] if len(lines) > 1 else []

    # Determine section type and format accordingly
    if 'PROVIDER' in section_title or 'COMPANY' in section_title:
        return format_providers_section(section_title, section_content, country)
    elif 'COMPARISON' in section_title or 'RESOURCE' in section_title:
        return format_resources_section(section_title, section_content)
    elif 'EXPERT' in section_title or 'CONTACT' in section_title:
        return format_experts_section(section_title, section_content)
    elif 'ACTION' in section_title or 'STEP' in section_title:
        return format_action_steps_section(section_title, section_content)
    elif 'INSIGHT' in section_title:
        return format_insights_section(section_title, section_content)
    else:
        return format_generic_section(section_title, section_content)


def format_providers_section(title, content, country):
    """Format providers with modern card design"""
    providers = parse_providers(content)

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
            <span class="title-text">Recommended Local Providers</span>
            <span class="country-flag">{get_country_flag(country)}</span>
        </h3>
        <div class="providers-grid">
            {"".join(cards_html)}
        </div>
    </div>
    '''


def format_resources_section(title, content):
    """Format comparison resources with modern design"""
    resources = parse_resources(content)

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
            <span class="title-text">Comparison Resources</span>
        </h3>
        <div class="resources-grid">
            {"".join(resource_cards)}
        </div>
    </div>
    '''


def format_experts_section(title, content):
    """Format experts section with professional design"""
    experts = parse_experts(content)

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
            <span class="title-text">Local Experts</span>
        </h3>
        <div class="experts-grid">
            {"".join(expert_cards)}
        </div>
    </div>
    '''


def format_action_steps_section(title, content):
    """Format action steps with modern checklist design"""
    steps = parse_action_steps(content)

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
            <span class="title-text">Action Steps</span>
        </h3>
        <div class="action-steps">
            {"".join(step_items)}
        </div>
    </div>
    '''


def format_insights_section(title, content):
    """Format insights with modern info cards"""
    insights = parse_insights(content)

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
            <span class="title-text">Key Insights</span>
        </h3>
        <div class="insights-grid">
            {"".join(insight_cards)}
        </div>
    </div>
    '''


def parse_providers(content):
    """Parse provider information from content"""
    providers = []
    current_provider = {}

    for line in content:
        line = line.strip()
        if not line or line.startswith('-'):
            if current_provider and current_provider.get('name'):
                providers.append(current_provider)
                current_provider = {}
            continue

        if line.startswith('**') and line.endswith('**'):
            # Provider name
            current_provider['name'] = line.strip('*')
        elif 'website' in line.lower():
            # Extract website URL
            url_match = re.search(r'https?://[^\s\]]+|www\.[^\s\]]+|\b[a-zA-Z0-9-]+\.[a-zA-Z]{2,}\b', line)
            if url_match:
                url = url_match.group()
                if not url.startswith('http'):
                    url = 'https://' + url
                current_provider['website'] = url
        elif 'phone' in line.lower():
            # Extract phone number
            phone_match = re.search(r'[\d\s\-\(\)]{8,}', line)
            if phone_match:
                current_provider['phone'] = phone_match.group().strip()
        elif 'why' in line.lower():
            # Description
            current_provider['description'] = line.split(':', 1)[-1].strip()

    # Add the last provider
    if current_provider and current_provider.get('name'):
        providers.append(current_provider)

    return providers


def parse_resources(content):
    """Parse resource information"""
    resources = []

    for line in content:
        line = line.strip('- ')
        if ':' in line:
            parts = line.split(':', 1)
            name = parts[0].strip('*')
            url_part = parts[1] if len(parts) > 1 else ''

            # Extract URL
            url_match = re.search(r'https?://[^\s\]]+|www\.[^\s\]]+|\b[a-zA-Z0-9-]+\.[a-zA-Z]{2,}\b', url_part)
            url = url_match.group() if url_match else '#'
            if not url.startswith('http'):
                url = 'https://' + url

            # Extract description
            description = re.sub(r'\[.*?\]|\(.*?\)|https?://\S+|www\.\S+', '', url_part).strip('- ')

            resources.append({
                'name': name,
                'url': url,
                'description': description or 'Comparison and review platform'
            })

    return resources


def parse_experts(content):
    """Parse expert information"""
    experts = []

    for line in content:
        line = line.strip('- ')
        if line:
            # Simple parsing for experts
            if ':' in line:
                parts = line.split(':', 1)
                name = parts[0].strip('*')
                description = parts[1].strip() if len(parts) > 1 else ''
            else:
                name = line.strip('*')
                description = 'Professional advisor'

            experts.append({
                'name': name,
                'description': description,
                'specialty': 'Financial Expert'
            })

    return experts


def parse_action_steps(content):
    """Parse action steps"""
    steps = []

    for line in content:
        line = line.strip()
        if line and not line.startswith('By following'):
            # Remove numbering and bullet points
            step = re.sub(r'^\d+\.\s*|^-\s*', '', line)
            if step:
                steps.append(step)

    return steps


def parse_insights(content):
    """Parse insights"""
    insights = []

    for line in content:
        line = line.strip()
        if line and ':' in line and line.startswith('**'):
            parts = line.split(':', 1)
            title = parts[0].strip('*')
            content_text = parts[1].strip() if len(parts) > 1 else ''

            insights.append({
                'title': title,
                'content': content_text
            })

    return insights


def format_provider_contacts(provider):
    """Format provider contact information"""
    contacts = []

    if provider.get('website'):
        contacts.append(
            f'<a href="{provider["website"]}" target="_blank" class="contact-btn website-btn"><span class="btn-icon">🌐</span>Visit Website</a>')

    if provider.get('phone'):
        contacts.append(
            f'<a href="tel:{provider["phone"]}" class="contact-btn phone-btn"><span class="btn-icon">📞</span>Call Now</a>')

    return ''.join(contacts)


def format_expert_contacts(expert):
    """Format expert contact information"""
    if expert.get('website'):
        return f'<a href="{expert["website"]}" target="_blank" class="expert-contact">View Profile</a>'
    return '<div class="expert-contact">Contact through professional directory</div>'


def fix_currency_encoding(text):
    """Fix currency encoding issues"""
    # Fix common currency encoding problems
    text = re.sub(r'u00a3', '£', text)
    text = re.sub(r'u20ac', '€', text)
    text = re.sub(r'&pound;', '£', text)
    text = re.sub(r'&euro;', '€', text)
    text = re.sub(r'&#8364;', '€', text)
    return text


def format_inline_styling(text):
    """Format inline styling like bold and italic"""
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    return fix_currency_encoding(text)


def get_country_flag(country):
    """Get country flag emoji"""
    flags = {
        'united kingdom': '🇬🇧',
        'uk': '🇬🇧',
        'united states': '🇺🇸',
        'usa': '🇺🇸',
        'canada': '🇨🇦',
        'australia': '🇦🇺',
        'germany': '🇩🇪',
        'france': '🇫🇷',
        'spain': '🇪🇸',
        'italy': '🇮🇹',
        'netherlands': '🇳🇱',
        'sweden': '🇸🇪',
        'norway': '🇳🇴',
        'denmark': '🇩🇰'
    }
    return flags.get(country.lower(), '🌍')


def format_generic_section(title, content):
    """Format generic sections"""
    formatted_content = []
    for line in content:
        if line.strip():
            line = format_inline_styling(line)
            formatted_content.append(f'<p>{line}</p>')

    return f'''
    <div class="content-section generic-section">
        <h3 class="section-title">
            <span class="section-icon">📋</span>
            <span class="title-text">{title}</span>
        </h3>
        <div class="section-content">
            {"".join(formatted_content)}
        </div>
    </div>
    '''


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


def create_simple_fallback(tool_config, user_data, localization=None):
    """Simple fallback with just donation message"""
    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    tool_name = tool_config.get("seo_data", {}).get("title", "Calculator")

    return f"""
<style>
.simple-fallback {{
    max-width: 600px;
    margin: 20px auto;
    text-align: center;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    padding: 20px;
}}
.fallback-header {{
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    padding: 30px;
    border-radius: 12px;
    margin-bottom: 20px;
}}
.fallback-title {{
    font-size: 1.8rem;
    margin-bottom: 10px;
    font-weight: 700;
}}
.fallback-subtitle {{
    opacity: 0.9;
    font-size: 1rem;
}}
.donation-section {{
    background: #f7fafc;
    padding: 30px;
    border-radius: 12px;
    margin: 20px 0;
}}
.donation-section h3 {{
    color: #2d3748;
    margin-bottom: 15px;
    font-size: 1.3rem;
}}
.donation-section p {{
    color: #4a5568;
    margin-bottom: 20px;
    line-height: 1.6;
}}
.donation-button {{
    display: inline-block;
    margin: 20px 0;
}}
.limit-message {{
    background: #fff3cd;
    color: #856404;
    padding: 15px;
    border-radius: 8px;
    margin: 20px 0;
    border: 1px solid #ffeaa7;
}}
</style>

<div class="simple-fallback">
    <div class="fallback-header">
        <div class="fallback-title">⚡ {tool_name}</div>
        <div class="fallback-subtitle">AI analysis temporarily unavailable</div>
    </div>

    <div class="limit-message">
        <strong>Daily AI limit reached</strong><br>
        Free AI analysis resets at midnight UTC
    </div>

    <div class="donation-section">
        <h3>🚀 Support Our Platform</h3>
        <p>Your support helps us provide advanced AI analysis and keep improving our tools for everyone.</p>

        <div class="donation-button">
            <a href="https://www.buymeacoffee.com/shakdiesel" target="_blank">
                <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Support Us" style="height: 50px;">
            </a>
        </div>

        <p><small>Thank you for using our platform! 🙏</small></p>
    </div>
</div>
"""