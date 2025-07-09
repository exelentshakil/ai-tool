import hashlib
from datetime import datetime
from openai import OpenAI
from utils.database import get_openai_cost_today, get_openai_cost_month, log_openai_cost
from utils.cache import check_cache, store_cache
from config.settings import API_KEY, DAILY_OPENAI_BUDGET, MONTHLY_OPENAI_BUDGET

client = OpenAI(api_key=API_KEY)


# Enhanced AI Analysis with Localized Data Support

def get_ai_system_prompt(country_data=None):
    """Get AI system prompt with localization awareness"""
    base_prompt = """You are an expert financial advisor, business strategist, and industry consultant with 20+ years of experience. You provide actionable insights that help users make informed decisions and optimize their financial outcomes."""

    if country_data:
        country_name = country_data.get("name", "")
        currency = country_data.get("currency", "USD")
        language = country_data.get("language", "English")

        localized_addition = f"""

LOCALIZATION CONTEXT:
- Target Country: {country_name}
- Currency: {currency}
- Language: {language}
- Local Market Knowledge: Provide insights specific to {country_name} market conditions, regulations, and cultural factors
- Use {currency} for all financial calculations and recommendations
- Consider {country_name}-specific tax implications, investment options, and regulatory requirements

Always tailor your advice to {country_name} market conditions and use local context where relevant."""

        return base_prompt + localized_addition

    return base_prompt


def build_analysis_prompt(tool_name, category, user_data, base_result, country_data=None):
    """Build AI analysis prompt with localized context"""
    context_items = []

    # Extract country-specific data if available
    location_data = user_data.get('locationData', {}) or country_data or {}
    city = location_data.get('city', '')
    region = location_data.get('region', '')
    country = location_data.get('name', location_data.get('country', ''))
    currency = location_data.get('currency', 'USD')
    local_term = location_data.get('local_term', 'ZIP code')

    # Build user context with localization
    for key, value in user_data.items():
        if key == 'locationData':
            if city and region:
                context_items.append(f"Location: {city}, {region}, {country}")
            elif country:
                context_items.append(f"Country: {country}")
        elif isinstance(value, (int, float)) and value > 1000:
            context_items.append(f"{key.replace('_', ' ').title()}: {currency}{value:,.0f}")
        else:
            context_items.append(f"{key.replace('_', ' ').title()}: {value}")

    user_context = " | ".join(context_items[:6])

    # Build localized market context
    market_context = ""
    if country:
        market_context = f"\nMARKET CONTEXT: Analyze for {country} market conditions, regulations, and opportunities"

        # Add country-specific considerations
        if country in ["United States", "US"]:
            market_context += f"\n- Consider US federal and state tax implications\n- Factor in 401(k), IRA, and Social Security benefits\n- Include US-specific investment options and regulations"
        elif country in ["United Kingdom", "UK"]:
            market_context += f"\n- Consider UK tax implications including ISAs and pension schemes\n- Factor in Brexit impacts on investments\n- Include UK-specific financial products and regulations"
        elif country in ["Germany", "DE"]:
            market_context += f"\n- Consider German tax system and social insurance\n- Factor in EU regulations and opportunities\n- Include German-specific investment products and pension schemes"
        elif country in ["Canada", "CA"]:
            market_context += f"\n- Consider Canadian tax implications including RRSP and TFSA\n- Factor in provincial differences\n- Include Canadian-specific investment options"
        # Add more countries as needed

    return f"""
Analyze this {tool_name} calculation and provide strategic insights:

CALCULATION RESULT: [RESULT]
USER CONTEXT: {user_context}
CATEGORY: {category}{market_context}

Provide a comprehensive analysis with:

**🎯 KEY INSIGHTS** (3-4 strategic observations)
- Most important implications of the result for {country or 'this market'}
- Hidden opportunities or risks specific to {country or 'local market'}
- Market context and timing factors relevant to {country or 'this region'}

**💡 STRATEGIC RECOMMENDATIONS** (4-5 specific actions)
- Prioritized steps with clear implementation guidance for {country or 'local market'}
- Resource requirements and expected outcomes in {currency}
- Risk mitigation strategies considering {country or 'local'} regulations
- {country or 'Local'}-specific opportunities to leverage

**⚡ OPTIMIZATION OPPORTUNITIES** (3-4 immediate improvements)
- Cost reduction or revenue enhancement tactics for {country or 'this market'}
- Efficiency improvements with measurable impact in {currency}
- Competitive advantages specific to {country or 'local market'} conditions
- Tax optimization strategies for {country or 'this jurisdiction'}

**🔮 MARKET INTELLIGENCE** ({country or 'Local'} outlook and timing)
- Optimal timing for key decisions in {country or 'this market'}
- {country or 'Local'} industry trends and their implications
- Risk factors to monitor in {country or 'this region'}
- Regulatory changes or opportunities in {country or 'this market'}

**📋 ACTION PLAN** (Next steps with timeline)
- Immediate actions (0-30 days) for {country or 'local'} implementation
- Short-term goals (1-6 months) considering {country or 'local'} market cycles
- Long-term strategy considerations for {country or 'this market'}

Make all recommendations specific, actionable, and valuable for their situation in {country or 'their local market'}.
Use {currency} for all financial calculations and recommendations.
"""


def generate_ai_analysis(tool_config, user_data, base_result, ip):
    """Generate AI-powered analysis with localized insights"""
    if get_openai_cost_today() >= DAILY_OPENAI_BUDGET or get_openai_cost_month() >= MONTHLY_OPENAI_BUDGET:
        return create_fallback_response(tool_config, user_data, base_result)

    # Extract country data from multiple sources
    country_data = (
            tool_config.get("country_data") or
            user_data.get("locationData") or
            user_data.get("location_data") or
            {}
    )

    category = tool_config.get("category", "general")
    tool_name = tool_config.get("seo_data", {}).get("title", "Analysis Tool")

    # Build localized prompts
    system_prompt = get_ai_system_prompt(country_data)
    user_prompt = build_analysis_prompt(tool_name, category, user_data, base_result, country_data)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1500,  # Increased for localized content
            temperature=0.7
        )

        ai_analysis = response.choices[0].message.content
        pt, ct = response.usage.prompt_tokens, response.usage.completion_tokens
        cost = (pt * 0.00015 + ct * 0.0006) / 1000
        log_openai_cost(tool_config['slug'], pt, ct, cost)

        # Generate rich HTML response with localized data
        rich_response = generate_rich_html_response(ai_analysis, user_data, base_result, tool_config, country_data)

        return rich_response.replace("[RESULT]", str(base_result))

    except Exception as e:
        print(f"AI analysis failed: {str(e)}")
        return create_fallback_response(tool_config, user_data, base_result)


def generate_rich_html_response(ai_analysis, user_data, base_result, tool_config, country_data=None):
    """Generate rich HTML response with localized context"""
    category = tool_config.get("category", "general")

    # Extract localization data
    country_name = ""
    currency = "USD"
    currency_symbol = "$"

    if country_data:
        country_name = country_data.get("name", "")
        currency = country_data.get("currency", "USD")
        # Extract currency symbol from currency code
        currency_symbol = get_currency_symbol(currency)

    # Generate localized components
    key_metrics_html = generate_localized_key_metrics(user_data, base_result, category, country_data)
    value_ladder_html = generate_localized_value_ladder(user_data, base_result, category, country_data)
    comparison_html = generate_localized_comparison_table(user_data, base_result, category, country_data)
    charts_html = generate_charts_html(user_data, base_result, category)
    action_items_html = generate_localized_action_items(user_data, category, country_data)

    # Convert markdown AI analysis to HTML
    formatted_ai_analysis = convert_markdown_to_html(ai_analysis)

    # Add country flag if available
    country_flag = ""
    if country_data and country_data.get("code"):
        country_flag = get_country_flag_emoji(country_data["code"])

    # Build localized header
    header_title = f"{country_flag} {base_result}" if country_flag else base_result
    header_subtitle = f"AI Analysis for {country_name}" if country_name else "Generated by AI Analysis Engine"

    # Combine everything into rich HTML with localization
    rich_html = f"""
<div class="ai-analysis-container localized-analysis" data-country="{country_data.get('code', '')}" data-currency="{currency}">
    <div class="analysis-header">
        <div class="result-highlight">
            <h2 class="primary-result">{header_title}</h2>
            <p class="result-subtitle">{header_subtitle}</p>
            {f'<div class="country-context">Optimized for {country_name} market</div>' if country_name else ''}
        </div>
    </div>

    {key_metrics_html}

    <div class="analysis-content">
        <div class="ai-insights">
            <h3>🤖 AI Strategic Analysis{f' - {country_name}' if country_name else ''}</h3>
            <div class="insights-content">
                {formatted_ai_analysis}
            </div>
        </div>

        {charts_html}
        {comparison_html}
        {value_ladder_html}
    </div>

    <div class="action-items">
        <h3>📋 Immediate Action Items{f' for {country_name}' if country_name else ''}</h3>
        <div class="action-grid">
            {action_items_html}
        </div>
    </div>

    {generate_localized_disclaimer(country_data)}
</div>

{generate_localized_css(country_data)}
"""

    return rich_html


def generate_localized_key_metrics(user_data, base_result, category, country_data=None):
    """Generate key metrics with localized currency and context"""
    currency_symbol = get_currency_symbol(country_data.get("currency", "USD") if country_data else "USD")
    country_name = country_data.get("name", "") if country_data else ""

    if category in ["finance", "business"]:
        amount = user_data.get('amount', 100000)
        return f"""
        <div class="key-metrics localized-metrics">
            <div class="metric-card primary">
                <div class="metric-icon">💰</div>
                <div class="metric-content">
                    <h3 class="metric-value">{currency_symbol}{amount:,.0f}</h3>
                    <p class="metric-label">Principal Amount</p>
                </div>
            </div>
            <div class="metric-card success">
                <div class="metric-icon">📈</div>
                <div class="metric-content">
                    <h3 class="metric-value">{currency_symbol}{amount * 0.07:,.0f}</h3>
                    <p class="metric-label">Expected Annual Return{f' ({country_name})' if country_name else ''}</p>
                </div>
            </div>
            <div class="metric-card info">
                <div class="metric-icon">🎯</div>
                <div class="metric-content">
                    <h3 class="metric-value">7.2%</h3>
                    <p class="metric-label">Projected Growth Rate{f' ({country_name})' if country_name else ''}</p>
                </div>
            </div>
            <div class="metric-card warning">
                <div class="metric-icon">⏰</div>
                <div class="metric-content">
                    <h3 class="metric-value">10 years</h3>
                    <p class="metric-label">Recommended Timeline</p>
                </div>
            </div>
        </div>
        """
    elif category == "insurance":
        coverage = user_data.get('coverage_amount', 100000)
        return f"""
        <div class="key-metrics localized-metrics">
            <div class="metric-card primary">
                <div class="metric-icon">🛡️</div>
                <div class="metric-content">
                    <h3 class="metric-value">{currency_symbol}{coverage:,.0f}</h3>
                    <p class="metric-label">Coverage Amount</p>
                </div>
            </div>
            <div class="metric-card success">
                <div class="metric-icon">💰</div>
                <div class="metric-content">
                    <h3 class="metric-value">{currency_symbol}{coverage * 0.005:,.0f}</h3>
                    <p class="metric-label">Est. Annual Premium{f' ({country_name})' if country_name else ''}</p>
                </div>
            </div>
            <div class="metric-card info">
                <div class="metric-icon">👤</div>
                <div class="metric-content">
                    <h3 class="metric-value">{user_data.get('age', 30)}</h3>
                    <p class="metric-label">Age</p>
                </div>
            </div>
            <div class="metric-card warning">
                <div class="metric-icon">📋</div>
                <div class="metric-content">
                    <h3 class="metric-value">{user_data.get('coverage_type', 'Full')}</h3>
                    <p class="metric-label">Coverage Type</p>
                </div>
            </div>
        </div>
        """
    else:
        return generate_key_metrics(user_data, base_result, category)


def generate_localized_value_ladder(user_data, base_result, category, country_data=None):
    """Generate value ladder with localized context"""
    currency_symbol = get_currency_symbol(country_data.get("currency", "USD") if country_data else "USD")
    country_name = country_data.get("name", "") if country_data else ""

    if category in ["finance", "business"]:
        amount = user_data.get('amount', 100000)
        return f"""
        <div class="value-ladder-enhanced localized-ladder">
            <div class="ladder-container">
                <h3>🚀 Your {country_name + ' ' if country_name else ''}Wealth Growth Ladder</h3>
                <div class="ladder-step-enhanced">
                    <div class="step-number">1</div>
                    <div class="step-content">
                        <h4>Step 1: Foundation (Current)</h4>
                        <p class="step-value">{currency_symbol}{amount:,.0f}</p>
                        <p class="step-description">Your starting investment{f' in {country_name}' if country_name else ''}</p>
                        <p class="step-timeline">✅ Emergency fund established</p>
                    </div>
                    <div class="step-icon">🏗️</div>
                </div>
                <div class="ladder-step-enhanced">
                    <div class="step-number">2</div>
                    <div class="step-content">
                        <h4>Step 2: Growth (Year 1-3)</h4>
                        <p class="step-value">{currency_symbol}{amount * 1.25:,.0f}</p>
                        <p class="step-description">25% portfolio growth{f' using {country_name} investment options' if country_name else ''}</p>
                        <p class="step-timeline">🎯 Diversify into local index funds and bonds</p>
                    </div>
                    <div class="step-icon">📈</div>
                </div>
                <div class="ladder-step-enhanced">
                    <div class="step-number">3</div>
                    <div class="step-content">
                        <h4>Step 3: Acceleration (Year 4-7)</h4>
                        <p class="step-value">{currency_symbol}{amount * 1.75:,.0f}</p>
                        <p class="step-description">75% total growth{f' leveraging {country_name} market opportunities' if country_name else ''}</p>
                        <p class="step-timeline">🚀 Add real estate and dividend stocks</p>
                    </div>
                    <div class="step-icon">🚀</div>
                </div>
                <div class="ladder-step-enhanced">
                    <div class="step-number">4</div>
                    <div class="step-content">
                        <h4>Step 4: Wealth (Year 8-10)</h4>
                        <p class="step-value">{currency_symbol}{amount * 2.5:,.0f}</p>
                        <p class="step-description">150% total growth{f' optimized for {country_name} tax efficiency' if country_name else ''}</p>
                        <p class="step-timeline">💎 Consider alternative investments</p>
                    </div>
                    <div class="step-icon">💎</div>
                </div>
            </div>
        </div>
        """
    else:
        return generate_value_ladder(user_data, base_result, category)


def generate_localized_action_items(user_data, category, country_data=None):
    """Generate action items with localized context"""
    country_name = country_data.get("name", "") if country_data else ""
    currency_symbol = get_currency_symbol(country_data.get("currency", "USD") if country_data else "USD")

    if category in ["finance", "business"]:
        return f"""
        <div class="action-item-card" data-priority="high">
            <div class="action-header">
                <div class="action-icon">🏦</div>
                <span class="action-priority high">High</span>
            </div>
            <h4 class="action-title">Open {country_name + ' ' if country_name else ''}Investment Account</h4>
            <p class="action-description">Research and open tax-advantaged investment accounts{f' available in {country_name}' if country_name else ''}</p>
            <div class="action-meta">
                <span class="action-timeline">⏱️ 1-2 weeks</span>
                <span class="action-effort">💪 Medium effort</span>
            </div>
        </div>
        <div class="action-item-card" data-priority="medium">
            <div class="action-header">
                <div class="action-icon">📊</div>
                <span class="action-priority medium">Medium</span>
            </div>
            <h4 class="action-title">Diversify Portfolio{f' for {country_name}' if country_name else ''}</h4>
            <p class="action-description">Spread investments across 3-4 asset classes{f' suitable for {country_name} market' if country_name else ''}</p>
            <div class="action-meta">
                <span class="action-timeline">⏱️ 2-3 weeks</span>
                <span class="action-effort">💪 High effort</span>
            </div>
        </div>
        <div class="action-item-card" data-priority="medium">
            <div class="action-header">
                <div class="action-icon">💰</div>
                <span class="action-priority medium">Medium</span>
            </div>
            <h4 class="action-title">Automate Investing</h4>
            <p class="action-description">Set up automatic monthly contributions{f' to your {country_name} investment accounts' if country_name else ''}</p>
            <div class="action-meta">
                <span class="action-timeline">⏱️ 1 week</span>
                <span class="action-effort">💪 Low effort</span>
            </div>
        </div>
        <div class="action-item-card" data-priority="low">
            <div class="action-header">
                <div class="action-icon">📈</div>
                <span class="action-priority low">Low</span>
            </div>
            <h4 class="action-title">Track Performance</h4>
            <p class="action-description">Use {country_name + ' ' if country_name else ''}investment tracking tools to monitor your portfolio monthly</p>
            <div class="action-meta">
                <span class="action-timeline">⏱️ Ongoing</span>
                <span class="action-effort">💪 Low effort</span>
            </div>
        </div>
        """
    else:
        return generate_action_items(user_data, category)


def generate_localized_comparison_table(user_data, base_result, category, country_data=None):
    """Generate comparison table with localized context"""
    country_name = country_data.get("name", "") if country_data else ""

    if category in ["finance", "business"] and country_name:
        return f"""
        <div class="comparison-table">
            <h3>💰 {country_name} Investment Comparison</h3>
            <table>
                <thead>
                    <tr>
                        <th>Investment Type</th>
                        <th>Expected Return ({country_name})</th>
                        <th>Risk Level</th>
                        <th>Tax Efficiency</th>
                        <th>Recommendation</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{country_name} Index Funds</td>
                        <td>7-10%</td>
                        <td>Medium</td>
                        <td>High</td>
                        <td>⭐⭐⭐⭐⭐</td>
                    </tr>
                    <tr>
                        <td>Government Bonds</td>
                        <td>3-5%</td>
                        <td>Low</td>
                        <td>Medium</td>
                        <td>⭐⭐⭐⭐</td>
                    </tr>
                    <tr>
                        <td>{country_name} Real Estate</td>
                        <td>6-12%</td>
                        <td>Medium</td>
                        <td>High</td>
                        <td>⭐⭐⭐⭐</td>
                    </tr>
                    <tr>
                        <td>Local Stocks</td>
                        <td>8-15%</td>
                        <td>High</td>
                        <td>Medium</td>
                        <td>⭐⭐⭐</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
    else:
        return generate_comparison_table(user_data, base_result, category)


def generate_localized_disclaimer(country_data=None):
    """Generate localized disclaimer"""
    country_name = country_data.get("name", "") if country_data else ""

    if country_name:
        return f"""
        <div class="localized-disclaimer">
            <h4>📋 {country_name} Specific Notice</h4>
            <p><strong>Important:</strong> This analysis is tailored for {country_name} market conditions and regulations. 
            Tax implications, investment options, and financial regulations may vary. 
            Please consult with a qualified {country_name} financial advisor for personalized advice.</p>
        </div>
        """
    return ""


def generate_localized_css(country_data=None):
    """Generate country-specific CSS styling"""
    if not country_data:
        return ""

    country_code = country_data.get("code", "").lower()

    return f"""
<style>
.localized-analysis[data-country="{country_code}"] {{
    border-top: 4px solid var(--country-color-{country_code}, #007bff);
}}

.country-context {{
    background: rgba(0, 123, 255, 0.1);
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 0.9rem;
    margin-top: 10px;
    display: inline-block;
}}

.localized-disclaimer {{
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 20px;
    margin: 20px 0;
    font-size: 0.9rem;
}}

.localized-disclaimer h4 {{
    margin-top: 0;
    color: #495057;
}}

/* Country-specific color schemes */
:root {{
    --country-color-us: #0052cc;
    --country-color-uk: #c8102e;
    --country-color-de: #ffce00;
    --country-color-ca: #ff0000;
    --country-color-au: #00843d;
    --country-color-fr: #0055a4;
    --country-color-jp: #bc002d;
    --country-color-no: #ef2b2d;
    --country-color-dk: #c8102e;
    --country-color-se: #006aa7;
    --country-color-fi: #003580;
    --country-color-ch: #dc143c;
    --country-color-at: #ed2939;
    --country-color-be: #2d2d2d;
    --country-color-nl: #21468b;
    --country-color-ie: #169b62;
    --country-color-nz: #00247d;
}}
</style>
"""


def get_currency_symbol(currency_code):
    """Get currency symbol from currency code"""
    symbols = {
        "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CAD": "C$",
        "AUD": "A$", "CHF": "Fr", "NOK": "kr", "SEK": "kr", "DKK": "kr",
        "NZD": "NZ$", "CNY": "¥", "INR": "₹", "BRL": "R$", "KRW": "₩"
    }
    return symbols.get(currency_code, currency_code)


def get_country_flag_emoji(country_code):
    """Get country flag emoji from country code"""
    flags = {
        "US": "🇺🇸", "UK": "🇬🇧", "CA": "🇨🇦", "AU": "🇦🇺", "DE": "🇩🇪",
        "FR": "🇫🇷", "JP": "🇯🇵", "NO": "🇳🇴", "DK": "🇩🇰", "SE": "🇸🇪",
        "FI": "🇫🇮", "CH": "🇨🇭", "AT": "🇦🇹", "BE": "🇧🇪", "NL": "🇳🇱",
        "IE": "🇮🇪", "NZ": "🇳🇿", "ES": "🇪🇸", "IT": "🇮🇹", "PT": "🇵🇹"
    }
    return flags.get(country_code, "🌍")


def generate_charts_html(user_data, base_result, category):
    """Generate interactive charts based on category"""
    if category in ["finance", "business"]:
        return f"""
        <div class="chart-container">
            <h3>📊 Financial Breakdown</h3>
            <canvas id="financialChart" width="400" height="200"></canvas>
            <script>
                const ctx = document.getElementById('financialChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'doughnut',
                    data: {{
                        labels: ['Investment', 'Returns', 'Fees', 'Taxes'],
                        datasets: [{{
                            data: [{user_data.get('amount', 100000)}, {user_data.get('amount', 100000) * 0.07}, {user_data.get('amount', 100000) * 0.01}, {user_data.get('amount', 100000) * 0.02}],
                            backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            legend: {{
                                position: 'bottom'
                            }}
                        }}
                    }}
                }});
            </script>
        </div>
        """
    elif category == "health":
        return f"""
        <div class="chart-container">
            <h3>📈 Health Progress Tracker</h3>
            <canvas id="healthChart" width="400" height="200"></canvas>
            <script>
                const ctx = document.getElementById('healthChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
                        datasets: [{{
                            label: 'Progress',
                            data: [0, 10, 25, 40, 60, 80],
                            borderColor: '#4CAF50',
                            backgroundColor: 'rgba(76, 175, 80, 0.1)',
                            tension: 0.4
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                max: 100
                            }}
                        }}
                    }}
                }});
            </script>
        </div>
        """
    else:
        return f"""
        <div class="chart-container">
            <h3>📊 Analysis Overview</h3>
            <div class="chart-placeholder">
                <p>Interactive chart will be displayed here based on your data</p>
            </div>
        </div>
        """


def generate_key_metrics(user_data, base_result, category):
    """Generate key metrics cards"""
    if category in ["finance", "business"]:
        amount = user_data.get('amount', 100000)
        return f"""
        <div class="key-metrics">
            <div class="metric-card">
                <h3 class="metric-value">${amount:,.0f}</h3>
                <p class="metric-label">Principal Amount</p>
            </div>
            <div class="metric-card">
                <h3 class="metric-value">{amount * 0.07:,.0f}</h3>
                <p class="metric-label">Expected Annual Return</p>
            </div>
            <div class="metric-card">
                <h3 class="metric-value">7.2%</h3>
                <p class="metric-label">Projected Growth Rate</p>
            </div>
            <div class="metric-card">
                <h3 class="metric-value">10 years</h3>
                <p class="metric-label">Recommended Timeline</p>
            </div>
        </div>
        """
    elif category == "health":
        return f"""
        <div class="key-metrics">
            <div class="metric-card">
                <h3 class="metric-value">{user_data.get('age', 30)}</h3>
                <p class="metric-label">Current Age</p>
            </div>
            <div class="metric-card">
                <h3 class="metric-value">{user_data.get('weight', 150)} lbs</h3>
                <p class="metric-label">Current Weight</p>
            </div>
            <div class="metric-card">
                <h3 class="metric-value">24.2</h3>
                <p class="metric-label">BMI Score</p>
            </div>
            <div class="metric-card">
                <h3 class="metric-value">Healthy</h3>
                <p class="metric-label">Status</p>
            </div>
        </div>
        """
    else:
        return f"""
        <div class="key-metrics">
            <div class="metric-card">
                <h3 class="metric-value">100%</h3>
                <p class="metric-label">Analysis Complete</p>
            </div>
            <div class="metric-card">
                <h3 class="metric-value">A+</h3>
                <p class="metric-label">Recommendation Grade</p>
            </div>
            <div class="metric-card">
                <h3 class="metric-value">5</h3>
                <p class="metric-label">Action Items</p>
            </div>
            <div class="metric-card">
                <h3 class="metric-value">30 days</h3>
                <p class="metric-label">Implementation Time</p>
            </div>
        </div>
        """


def generate_value_ladder(user_data, base_result, category):
    """Generate value ladder for growth opportunities"""
    if category in ["finance", "business"]:
        amount = user_data.get('amount', 100000)
        return f"""
        <div class="value-ladder">
            <h3>🚀 Your Wealth Growth Ladder</h3>
            <div class="ladder-step">
                <h4>Step 1: Foundation (Current)</h4>
                <p><strong>${amount:,.0f}</strong> - Your starting investment</p>
                <p>✅ Emergency fund established</p>
            </div>
            <div class="ladder-step">
                <h4>Step 2: Growth (Year 1-3)</h4>
                <p><strong>${amount * 1.25:,.0f}</strong> - 25% portfolio growth</p>
                <p>🎯 Diversify into index funds and bonds</p>
            </div>
            <div class="ladder-step">
                <h4>Step 3: Acceleration (Year 4-7)</h4>
                <p><strong>${amount * 1.75:,.0f}</strong> - 75% total growth</p>
                <p>🚀 Add real estate and dividend stocks</p>
            </div>
            <div class="ladder-step">
                <h4>Step 4: Wealth (Year 8-10)</h4>
                <p><strong>${amount * 2.5:,.0f}</strong> - 150% total growth</p>
                <p>💎 Consider alternative investments</p>
            </div>
        </div>
        """
    elif category == "health":
        return f"""
        <div class="value-ladder">
            <h3>💪 Your Health Transformation Ladder</h3>
            <div class="ladder-step">
                <h4>Phase 1: Foundation (Month 1-2)</h4>
                <p><strong>Build Habits</strong> - Establish daily routines</p>
                <p>✅ 30 minutes daily exercise</p>
            </div>
            <div class="ladder-step">
                <h4>Phase 2: Progress (Month 3-4)</h4>
                <p><strong>See Results</strong> - Visible improvements</p>
                <p>🎯 10% body composition improvement</p>
            </div>
            <div class="ladder-step">
                <h4>Phase 3: Momentum (Month 5-6)</h4>
                <p><strong>Accelerate</strong> - Advanced techniques</p>
                <p>🚀 Strength gains and endurance boost</p>
            </div>
            <div class="ladder-step">
                <h4>Phase 4: Mastery (Month 7+)</h4>
                <p><strong>Optimize</strong> - Peak performance</p>
                <p>💎 Sustained healthy lifestyle</p>
            </div>
        </div>
        """
    else:
        return f"""
        <div class="value-ladder">
            <h3>📈 Your Success Ladder</h3>
            <div class="ladder-step">
                <h4>Level 1: Start (Week 1-2)</h4>
                <p><strong>Foundation</strong> - Get basics right</p>
                <p>✅ Complete initial setup</p>
            </div>
            <div class="ladder-step">
                <h4>Level 2: Build (Week 3-4)</h4>
                <p><strong>Growth</strong> - Expand capabilities</p>
                <p>🎯 Implement core strategies</p>
            </div>
            <div class="ladder-step">
                <h4>Level 3: Scale (Month 2-3)</h4>
                <p><strong>Optimize</strong> - Maximize efficiency</p>
                <p>🚀 Advanced implementation</p>
            </div>
            <div class="ladder-step">
                <h4>Level 4: Master (Month 4+)</h4>
                <p><strong>Excellence</strong> - Sustained success</p>
                <p>💎 Continuous improvement</p>
            </div>
        </div>
        """


def generate_comparison_table(user_data, base_result, category):
    """Generate comparison table"""
    if category in ["finance", "business"]:
        return """
        <div class="comparison-table">
            <h3>💰 Investment Comparison</h3>
            <table>
                <thead>
                    <tr>
                        <th>Investment Type</th>
                        <th>Expected Return</th>
                        <th>Risk Level</th>
                        <th>Liquidity</th>
                        <th>Recommendation</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Index Funds</td>
                        <td>7-10%</td>
                        <td>Medium</td>
                        <td>High</td>
                        <td>⭐⭐⭐⭐⭐</td>
                    </tr>
                    <tr>
                        <td>Individual Stocks</td>
                        <td>8-15%</td>
                        <td>High</td>
                        <td>High</td>
                        <td>⭐⭐⭐</td>
                    </tr>
                    <tr>
                        <td>Bonds</td>
                        <td>3-5%</td>
                        <td>Low</td>
                        <td>Medium</td>
                        <td>⭐⭐⭐⭐</td>
                    </tr>
                    <tr>
                        <td>Real Estate</td>
                        <td>6-12%</td>
                        <td>Medium</td>
                        <td>Low</td>
                        <td>⭐⭐⭐⭐</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
    else:
        return ""


def generate_action_items(user_data, category):
    """Generate actionable items"""
    if category in ["finance", "business"]:
        return """
        <div class="action-item">
            <h4>📊 Diversify Portfolio</h4>
            <p>Spread investments across 3-4 asset classes to reduce risk</p>
            <small>Timeline: 2 weeks</small>
        </div>
        <div class="action-item">
            <h4>💰 Automate Investing</h4>
            <p>Set up automatic monthly contributions to your investment accounts</p>
            <small>Timeline: 1 week</small>
        </div>
        <div class="action-item">
            <h4>📈 Track Performance</h4>
            <p>Use investment tracking tools to monitor your portfolio monthly</p>
            <small>Timeline: Ongoing</small>
        </div>
        <div class="action-item">
            <h4>🎯 Rebalance Quarterly</h4>
            <p>Review and adjust your asset allocation every 3 months</p>
            <small>Timeline: Quarterly</small>
        </div>
        """
    elif category == "health":
        return """
        <div class="action-item">
            <h4>🏃‍♂️ Start Daily Walks</h4>
            <p>Begin with 20-minute walks, gradually increase to 45 minutes</p>
            <small>Timeline: Start today</small>
        </div>
        <div class="action-item">
            <h4>🥗 Meal Planning</h4>
            <p>Plan and prep healthy meals for the week every Sunday</p>
            <small>Timeline: Weekly</small>
        </div>
        <div class="action-item">
            <h4>💧 Hydration Goal</h4>
            <p>Drink 8 glasses of water daily, track with a water bottle</p>
            <small>Timeline: Daily</small>
        </div>
        <div class="action-item">
            <h4>😴 Sleep Schedule</h4>
            <p>Establish consistent 7-8 hour sleep routine</p>
            <small>Timeline: Start this week</small>
        </div>
        """
    else:
        return """
        <div class="action-item">
            <h4>📋 Create Action Plan</h4>
            <p>Break down your goals into specific, measurable steps</p>
            <small>Timeline: This week</small>
        </div>
        <div class="action-item">
            <h4>📊 Track Progress</h4>
            <p>Set up regular check-ins to monitor your advancement</p>
            <small>Timeline: Weekly</small>
        </div>
        <div class="action-item">
            <h4>🎯 Set Milestones</h4>
            <p>Establish clear benchmarks for measuring success</p>
            <small>Timeline: Monthly</small>
        </div>
        <div class="action-item">
            <h4>🔄 Iterate and Improve</h4>
            <p>Continuously refine your approach based on results</p>
            <small>Timeline: Ongoing</small>
        </div>
        """


def generate_base_result(user_data, category):
    """Generate base calculation result with rich formatting"""
    if category in ["business", "finance"]:
        amount = user_data.get("amount", user_data.get("revenue", 100000))
        return f"${amount:,.0f} Investment Analysis Complete"
    elif category == "insurance":
        coverage = user_data.get("coverage_amount", 100000)
        return f"${coverage:,.0f} Coverage Recommendation Ready"
    elif category == "real_estate":
        price = user_data.get("home_price", 400000)
        return f"${price:,.0f} Property Investment Analysis"
    elif category == "automotive":
        price = user_data.get("vehicle_price", 35000)
        return f"${price:,.0f} Vehicle Purchase Strategy"
    elif category == "health":
        age = user_data.get("age", 30)
        return f"Personalized Health Plan for Age {age}"
    elif category == "education":
        cost = user_data.get("tuition_cost", 25000)
        return f"${cost:,.0f} Education Investment Plan"
    elif category == "legal":
        case_type = user_data.get("case_type", "Business")
        return f"{case_type} Legal Strategy Analysis"
    else:
        return "Comprehensive Analysis Complete"


def create_fallback_response(tool_config, user_data, base_result):
    """Create enhanced fallback response when AI is unavailable"""
    category = tool_config.get("category", "general")

    fallback_html = f"""
    <div class="fallback-container">
        <div class="fallback-header">
            <h2>🎯 {base_result}</h2>
            <p class="fallback-subtitle">Basic Analysis Ready</p>
        </div>

        {generate_key_metrics(user_data, base_result, category)}

        <div class="fallback-content">
            <div class="insight-card">
                <h3>💡 Key Insights</h3>
                <ul>
                    <li>Result calculated based on current market conditions and your specific inputs</li>
                    <li>Consider comparing with industry benchmarks for optimal positioning</li>
                    <li>Market timing and competitive factors may impact optimal strategy</li>
                </ul>
            </div>

            <div class="insight-card">
                <h3>📈 General Recommendations</h3>
                <ul>
                    <li>Research multiple options for best value and terms</li>
                    <li>Factor in long-term implications beyond immediate costs</li>
                    <li>Monitor market trends for optimal timing of major decisions</li>
                    <li>Consider professional consultation for complex situations</li>
                </ul>
            </div>

            <div class="insight-card">
                <h3>⚡ Next Steps</h3>
                <ul>
                    <li>Gather additional quotes or information for comparison</li>
                    <li>Review terms and conditions carefully</li>
                    <li>Plan implementation timeline based on your priorities</li>
                    <li>Set up monitoring for market changes that could affect your strategy</li>
                </ul>
            </div>
        </div>

        <div class="upgrade-banner">
            <h3>🚀 Upgrade for Enhanced Analysis</h3>
            <p>Get detailed strategic insights, personalized recommendations, interactive charts, and growth roadmaps.</p>
        </div>
    </div>

    <style>
    .fallback-container {{
    max-width: 1000px;
        margin: 0 auto;
        padding: 20px;
    }}

    .fallback-header {{
    background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
        border-radius: 15px;
        padding: 30px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }}

    .fallback-content {{
    display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px;
        margin: 30px 0;
    }}

    .insight-card {{
    background: white;
        border-radius: 12px;
        padding: 25px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        border-left: 4px solid #007bff;
    }}

    .insight-card h3 {{
    margin - top: 0;
        color: #2c3e50;
    }}

    .insight-card ul {{
    padding - left: 20px;
    }}

    .insight-card li {{
    margin - bottom: 10px;
        line-height: 1.5;
   }}

    .upgrade-banner {{
    background: linear-gradient(135deg, #ffc107 0%, #ff6b35 100%);
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        color: white;
        margin-top: 30px;
    }}

    .upgrade-banner h3 {{
    margin-top: 0;
    }}
    </style>
    """

    return fallback_html


def convert_markdown_to_html(markdown_text):
    """Convert markdown text to HTML"""
    if not markdown_text:
        return '<p>AI analysis not available.</p>'

    # Convert markdown to HTML
    html = markdown_text
    html = html.replace('### ', '<h3>')
    html = html.replace('## ', '<h2>')
    html = html.replace('# ', '<h1>')
    html = html.replace('**', '<strong>', 1).replace('**', '</strong>', 1)

    # Handle multiple bold text
    import re
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)

    # Convert line breaks to paragraphs
    paragraphs = html.split('\n\n')
    formatted_paragraphs = []

    for para in paragraphs:
        para = para.strip()
        if para:
            if para.startswith('<h'):
                formatted_paragraphs.append(para)
            elif para.startswith('-') or para.startswith('•'):
                # Handle lists
                list_items = para.split('\n')
                list_html = '<ul>'
                for item in list_items:
                    if item.strip():
                        clean_item = item.replace('- ', '').replace('• ', '').strip()
                        list_html += f'<li>{clean_item}</li>'
                list_html += '</ul>'
                formatted_paragraphs.append(list_html)
            else:
                formatted_paragraphs.append(f'<p>{para.replace(chr(10), "<br>")}</p>')

    return '\n'.join(formatted_paragraphs)


def generate_charts_html(user_data, base_result, category):
    """Generate interactive charts based on category"""
    if category == "health":
        return f"""
        <div class="chart-container">
            <h3>📈 Health Progress Tracker</h3>
            <canvas id="healthChart" width="400" height="200"></canvas>
            <script>
                // Wait for Chart.js to be available
                function createHealthChart() {{
                    if (typeof Chart === 'undefined') {{
                        console.log('Chart.js not loaded yet, retrying...');
                        setTimeout(createHealthChart, 500);
                        return;
                    }}

                    const ctx = document.getElementById('healthChart');
                    if (!ctx) return;

                    new Chart(ctx, {{
                        type: 'line',
                        data: {{
                            labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
                            datasets: [{{
                                label: 'Progress',
                                data: [0, 10, 25, 40, 60, 80],
                                borderColor: '#4CAF50',
                                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                                tension: 0.4
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            scales: {{
                                y: {{
                                    beginAtZero: true,
                                    max: 100
                                }}
                            }}
                        }}
                    }});
                }}

                // Try to create chart immediately, or wait for page load
                if (document.readyState === 'loading') {{
                    document.addEventListener('DOMContentLoaded', createHealthChart);
                }} else {{
                    createHealthChart();
                }}
            </script>
        </div>
        """

    # Similar pattern for other categories...