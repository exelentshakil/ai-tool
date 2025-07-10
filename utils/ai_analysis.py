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


def build_prompt(tool_name, category, user_data, localization=None):
    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    currency = localization.get('currency', 'USD')
    country = localization.get('country_name', '')

    if currency == 'u20ac':
        currency = 'EUR'

    context_items = []
    for key, value in user_data.items():
        if key == 'locationData' and isinstance(value, dict):
            name = value.get('name', country)
            if name:
                context_items.append(f"Location: {name}")
        elif isinstance(value, (int, float)) and value > 0:
            if key in ['amount', 'budget', 'income', 'price', 'coverage_amount']:
                context_items.append(f"{key.title()}: {currency} {value:,.0f}")
            else:
                context_items.append(f"{key.title()}: {value}")
        elif isinstance(value, str) and value.strip():
            context_items.append(f"{key.title()}: {value}")

    user_context = " | ".join(context_items[:6])

    return f"""Calculate and analyze this {tool_name} request:

USER INPUT: {user_context}
CATEGORY: {category}
COUNTRY: {country}
CURRENCY: {currency}
LANGUAGE: {language}

Provide a clear, actionable analysis:

1. MAIN RESULT (calculate the key number/outcome)
2. KEY INSIGHTS (3 important points)
3. RECOMMENDATIONS (3 specific actions)
4. NEXT STEPS (what to do immediately)

Be direct, practical, and valuable. Use {currency} for all money amounts. Respond in {language}."""


def get_system_prompt(localization=None):
    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    currency = localization.get('currency', 'USD')
    country = localization.get('country_name', '')

    if currency == 'u20ac':
        currency = 'EUR'

    prompt = f"You are a practical analyst providing clear, actionable insights. Use {currency} currency. Focus on {country} context when relevant."

    if language != 'English':
        prompt += f" Respond entirely in {language}."

    return prompt


def generate_html_response(ai_analysis, user_data, tool_config, localization=None):
    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    currency = localization.get('currency', 'USD')

    if currency == 'u20ac':
        currency = 'EUR'

    tool_name = tool_config.get("seo_data", {}).get("title", "Calculator")

    formatted_content = format_content(ai_analysis)

    return f"""
<style>
.ai-results {{
    max-width: 800px;
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
}}
.content-section h3 {{
    color: #2d3748;
    font-size: 1.3rem;
    margin-bottom: 15px;
    font-weight: 600;
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
.content-section ul {{
    margin: 15px 0;
    padding-left: 0;
}}
.content-section li {{
    background: #f7fafc;
    margin: 8px 0;
    padding: 12px 16px;
    border-left: 4px solid #667eea;
    border-radius: 0 8px 8px 0;
    list-style: none;
}}
.content-section strong {{
    color: #2d3748;
    font-weight: 600;
}}
@media (max-width: 768px) {{
.ai-analysis {{
    background: linear-gradient(135deg, var(--neutral-50), var(--primary-50));
    border: 1px solid var(--primary-200);
    border-radius: 12px;
    padding: 0px;
    margin: 1.5rem 0;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}}
    .ai-results {{ padding: 10px; }}
    .result-header, .content-section {{ padding: 20px; }}
    .result-title {{ font-size: 1.5rem; }}
}}
</style>

<div class="ai-results">
    <div class="result-header">
        <div class="result-title">🎯 {tool_name}</div>
        <div class="result-subtitle">{get_text('analysis_complete', language)}</div>
    </div>

    <div class="content-section">
        {formatted_content}
    </div>
</div>
"""


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


def get_text(key, language):
    texts = {
        'analysis_complete': {
            'English': 'Analysis Complete',
            'Spanish': 'Análisis Completo',
            'French': 'Analyse Terminée',
            'German': 'Analyse Abgeschlossen',
            'Italian': 'Analisi Completa',
            'Dutch': 'Analyse Voltooid'
        }
    }
    return texts.get(key, {}).get(language, texts.get(key, {}).get('English', key))


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