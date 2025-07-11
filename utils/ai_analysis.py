from openai import OpenAI
from utils.database import get_openai_cost_today, get_openai_cost_month, log_openai_cost, log_openai_cost_enhanced
from config.settings import OPENAI_API_KEY, DAILY_OPENAI_BUDGET, MONTHLY_OPENAI_BUDGET

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
    """Enhanced content formatting with special styling for local recommendations"""

    content = ai_analysis

    # Add icons to section headers
    content = re.sub(r'\*\*(.*?RESULT.*?)\*\*', r'<h3><span class="section-icon">📊</span>\1</h3>', content)
    content = re.sub(r'\*\*(.*?INSIGHTS.*?)\*\*', r'<h3><span class="section-icon">💡</span>\1</h3>', content)
    content = re.sub(r'\*\*(.*?PROVIDERS.*?)\*\*',
                     r'<h3><span class="section-icon">🏢</span>\1<span class="local-badge">Local</span></h3>', content)
    content = re.sub(r'\*\*(.*?COMPARISON.*?)\*\*', r'<h3><span class="section-icon">🔍</span>\1</h3>', content)
    content = re.sub(r'\*\*(.*?EXPERTS.*?)\*\*', r'<h3><span class="section-icon">👨‍💼</span>\1</h3>', content)
    content = re.sub(r'\*\*(.*?ACTION.*?)\*\*', r'<h3><span class="section-icon">🚀</span>\1</h3>', content)
    content = re.sub(r'\*\*(.*?STEPS.*?)\*\*', r'<h3><span class="section-icon">✅</span>\1</h3>', content)

    # Enhanced formatting for companies/providers
    # Look for patterns like "Company Name (website.com, phone)"
    content = re.sub(
        r'([A-Z][a-zA-Z\s&]+?)\s*\(([^,)]+\.[a-z]{2,4})[^)]*\)',
        r'<div class="provider-card"><div class="provider-name">\1</div><a href="https://\2" target="_blank" class="provider-contact">🌐 Visit Website</a></div>',
        content
    )

    # Format website links
    content = re.sub(
        r'([a-zA-Z0-9-]+\.[a-z]{2,4})',
        r'<a href="https://\1" target="_blank" class="provider-contact">🌐 \1</a>',
        content
    )

    # Format phone numbers
    content = re.sub(
        r'(\+?[\d\s\-\(\)]{8,})',
        r'<a href="tel:\1" class="provider-contact">📞 \1</a>',
        content
    )

    # Enhanced action steps
    content = re.sub(
        r'(\d+\.\s*.*?)(?=\n|$)',
        r'<div class="action-step">\1</div>',
        content
    )

    # Convert markdown-style formatting
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)

    # Convert newlines to proper HTML
    content = content.replace('\n\n', '</p><p>')
    content = f'<p>{content}</p>'

    return content


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