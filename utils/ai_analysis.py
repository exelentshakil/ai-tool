from openai import OpenAI
from utils.database import get_openai_cost_today, get_openai_cost_month, log_openai_cost
from config.settings import API_KEY, DAILY_OPENAI_BUDGET, MONTHLY_OPENAI_BUDGET

client = OpenAI(api_key=API_KEY)


def generate_ai_analysis(tool_config, user_data, ip, localization=None):
    if get_openai_cost_today() >= DAILY_OPENAI_BUDGET or get_openai_cost_month() >= MONTHLY_OPENAI_BUDGET:
        return create_fallback_response(tool_config, user_data, localization)

    category = tool_config.get("category", "general")
    tool_name = tool_config.get("seo_data", {}).get("title", "Calculator")

    cleaned_data = clean_user_data(user_data)
    prompt = build_prompt(tool_name, category, cleaned_data, localization)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": get_system_prompt(localization)},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )

        ai_analysis = response.choices[0].message.content
        pt, ct = response.usage.prompt_tokens, response.usage.completion_tokens
        cost = (pt * 0.00015 + ct * 0.0006) / 1000
        log_openai_cost(tool_config['slug'], pt, ct, cost)

        return generate_html_response(ai_analysis, cleaned_data, tool_config, localization)

    except Exception as e:
        print(f"AI analysis failed: {str(e)}")
        return create_fallback_response(tool_config, cleaned_data, localization)


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
            if key in ['amount', 'budget', 'income', 'price']:
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
    .ai-results {{ padding: 16px; }}
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


def create_fallback_response(tool_config, user_data, localization=None):
    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    tool_name = tool_config.get("seo_data", {}).get("title", "Calculator")

    return f"""
<style>
.fallback-results {{
    max-width: 600px;
    margin: 20px auto;
    text-align: center;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}}
.fallback-header {{
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    padding: 40px;
    border-radius: 12px;
    margin-bottom: 20px;
}}
.fallback-title {{
    font-size: 2rem;
    margin-bottom: 10px;
}}
.upgrade-section {{
    background: #f7fafc;
    padding: 30px;
    border-radius: 12px;
}}
.upgrade-button {{
    display: inline-block;
    margin-top: 20px;
}}
</style>

<div class="fallback-results">
    <div class="fallback-header">
        <div class="fallback-title">⚡ {tool_name}</div>
        <p>AI analysis temporarily unavailable</p>
    </div>

    <div class="upgrade-section">
        <h3>🚀 Get AI Analysis</h3>
        <p>Support us to unlock detailed insights and recommendations</p>
        <div class="upgrade-button">
            <a href="https://www.buymeacoffee.com/shakdiesel" target="_blank">
                <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Support" style="height: 50px;">
            </a>
        </div>
    </div>
</div>
"""