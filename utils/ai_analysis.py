from openai import OpenAI
from utils.database import get_openai_cost_today, get_openai_cost_month, log_openai_cost_enhanced
from config.settings import OPENAI_API_KEY, DAILY_OPENAI_BUDGET, MONTHLY_OPENAI_BUDGET
import time

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_ai_analysis(tool_config, user_data, ip, localization=None):
    """Simple AI analysis function - easy to debug"""

    start_time = time.time()

    # Debug: Print inputs
    print(f"🔍 DEBUG: Tool: {tool_config.get('seo_data', {}).get('title', 'Unknown')}")
    print(f"🔍 DEBUG: User data keys: {list(user_data.keys())}")
    print(f"🔍 DEBUG: IP: {ip}")

    # Check budget limits
    try:
        daily_budget = float(DAILY_OPENAI_BUDGET)
        monthly_budget = float(MONTHLY_OPENAI_BUDGET)
        daily_spent = get_openai_cost_today()
        monthly_spent = get_openai_cost_month()

        print(f"🔍 DEBUG: Daily budget: ${daily_budget}, spent: ${daily_spent}")
        print(f"🔍 DEBUG: Monthly budget: ${monthly_budget}, spent: ${monthly_spent}")

        if daily_spent >= daily_budget or monthly_spent >= monthly_budget:
            print("❌ Budget limit reached")
            return create_budget_limit_response()

    except Exception as e:
        print(f"❌ Budget check failed: {e}")
        daily_budget = 10.0
        monthly_budget = 100.0

    # Get basic info
    tool_name = tool_config.get("seo_data", {}).get("title", "Calculator")
    category = tool_config.get("category", "general")

    # Build simple prompt
    prompt = build_simple_prompt(tool_name, category, user_data, localization)
    print(f"🔍 DEBUG: Prompt length: {len(prompt)} chars")

    try:
        print("🔄 Calling OpenAI API...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": get_simple_system_prompt(localization)},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,  # Reduced for simplicity
            temperature=0.7
        )

        ai_analysis = response.choices[0].message.content
        pt, ct = response.usage.prompt_tokens, response.usage.completion_tokens
        total_tokens = pt + ct
        cost = (pt * 0.00015 + ct * 0.0006) / 1000
        response_time = int((time.time() - start_time) * 1000)

        print(f"✅ OpenAI response: {len(ai_analysis)} chars, ${cost:.6f}, {response_time}ms")

        # Log the cost
        try:
            success = log_openai_cost_enhanced(
                cost=cost,
                tokens=total_tokens,
                model="gpt-4o-mini",
                ip=ip,
                tools_slug=tool_name,
                response_time=response_time
            )
            print(f"💾 Cost logging: {'✅ Success' if success else '❌ Failed'}")
        except Exception as e:
            print(f"❌ Cost logging error: {e}")

        # Return simple HTML response
        return create_simple_html_response(ai_analysis, tool_name, localization)

    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        print(f"❌ OpenAI API failed after {response_time}ms: {str(e)}")

        # Log failed attempt
        try:
            log_openai_cost_enhanced(
                cost=0,
                tokens=0,
                model="error",
                ip=ip,
                tools_slug=tool_name,
                response_time=response_time
            )
        except:
            pass

        return create_error_response(str(e))


def build_simple_prompt(tool_name, category, user_data, localization=None):
    """Build a simple, clean prompt"""

    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    currency = localization.get('currency', 'USD')
    country = localization.get('country_name', '')

    # Fix currency encoding
    if currency == 'u20ac':
        currency = 'EUR'

    # Clean user data
    data_summary = []
    for key, value in user_data.items():
        if key == 'locationData':
            continue
        if isinstance(value, (int, float)) and value > 0:
            data_summary.append(f"{key}: {value}")
        elif isinstance(value, str) and value.strip():
            data_summary.append(f"{key}: {value}")

    user_context = " | ".join(data_summary[:5])  # Limit to 5 items

    prompt = f"""
Analyze this {tool_name} request and provide helpful advice:

USER INPUT: {user_context}
LOCATION: {country}
CATEGORY: {category}
CURRENCY: {currency}

Please provide:
1. Main calculation/result
2. 2-3 key insights
3. Practical recommendations
4. Next steps

Respond in {language}. Keep it concise and actionable.
"""

    return prompt.strip()


def get_simple_system_prompt(localization=None):
    """Simple system prompt"""

    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    currency = localization.get('currency', 'USD')
    country = localization.get('country_name', '')

    if currency == 'u20ac':
        currency = 'EUR'

    prompt = f"""You are a helpful financial and practical advisor.

Provide clear, actionable advice for users in {country}.
Use {currency} for monetary amounts.
Be specific and practical.
Keep responses concise but helpful."""

    if language != 'English':
        prompt += f" Respond in {language}."

    return prompt


def create_simple_html_response(ai_analysis, tool_name, localization=None):
    """Create simple HTML response"""

    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    country = localization.get('country_name', '')

    # Simple text processing
    formatted_content = format_simple_content(ai_analysis)

    html = f"""
<style>
.ai-results {{
    max-width: 800px;
    margin: 20px auto;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    line-height: 1.6;
    color: #333;
}}
.result-header {{
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 20px;
}}
.result-title {{
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
}}
.country-badge {{
    background: rgba(255,255,255,0.2);
    padding: 5px 10px;
    border-radius: 20px;
    font-size: 0.9rem;
    margin-top: 10px;
    display: inline-block;
}}
.content-section {{
    background: white;
    padding: 25px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}}
.content-section h3 {{
    color: #2d3748;
    margin-top: 25px;
    margin-bottom: 15px;
    font-size: 1.2rem;
}}
.content-section p {{
    margin-bottom: 15px;
}}
.content-section ul {{
    margin-bottom: 15px;
    padding-left: 20px;
}}
.content-section li {{
    margin-bottom: 8px;
}}
strong {{
    color: #2d3748;
}}
</style>

<div class="ai-results">
    <div class="result-header">
        <div class="result-title">🎯 {tool_name}</div>
        <div class="country-badge">🌍 {country}</div>
    </div>

    <div class="content-section">
        {formatted_content}
    </div>
</div>
"""

    return html


def format_simple_content(content):
    """Simple content formatting"""

    if not content:
        return "<p>No analysis available.</p>"

    # Basic text cleanup
    content = content.strip()

    # Convert **bold** to <strong>
    content = content.replace('**', '<strong>', 1)
    content = content.replace('**', '</strong>', 1)
    while '**' in content:
        content = content.replace('**', '<strong>', 1)
        if '**' in content:
            content = content.replace('**', '</strong>', 1)

    # Split into paragraphs
    paragraphs = content.split('\n\n')
    formatted_paragraphs = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Check if it's a header (starts with number or #)
        if para.startswith(('#', '1.', '2.', '3.', '4.', '5.')):
            # Remove markdown
            header = para.lstrip('#123456789. ')
            formatted_paragraphs.append(f'<h3>{header}</h3>')
        else:
            # Regular paragraph
            # Handle simple lists
            if '\n-' in para or '\n•' in para:
                lines = para.split('\n')
                list_items = []
                for line in lines:
                    line = line.strip()
                    if line.startswith(('-', '•')):
                        list_items.append(f'<li>{line[1:].strip()}</li>')
                    elif line:
                        if list_items:
                            # End list and start new paragraph
                            formatted_paragraphs.append(f'<ul>{"".join(list_items)}</ul>')
                            list_items = []
                        formatted_paragraphs.append(f'<p>{line}</p>')

                if list_items:
                    formatted_paragraphs.append(f'<ul>{"".join(list_items)}</ul>')
            else:
                formatted_paragraphs.append(f'<p>{para}</p>')

    return '\n'.join(formatted_paragraphs)


def create_budget_limit_response():
    """Simple budget limit message"""
    return """
<div style="max-width: 600px; margin: 20px auto; text-align: center; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">
    <div style="background: #fff3cd; color: #856404; padding: 20px; border-radius: 10px; border: 1px solid #ffeaa7;">
        <h3>⚡ Daily AI Limit Reached</h3>
        <p>Free AI analysis resets at midnight UTC</p>
    </div>
</div>
"""


def create_error_response(error_message):
    """Simple error message"""
    return f"""
<div style="max-width: 600px; margin: 20px auto; text-align: center; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">
    <div style="background: #f8d7da; color: #721c24; padding: 20px; border-radius: 10px; border: 1px solid #f5c6cb;">
        <h3>❌ Analysis Temporarily Unavailable</h3>
        <p>Please try again in a moment</p>
        <small>Error: {error_message[:100]}</small>
    </div>
</div>
"""