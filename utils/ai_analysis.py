import hashlib
from datetime import datetime
from openai import OpenAI
from utils.database import get_openai_cost_today, get_openai_cost_month, log_openai_cost
from utils.cache import check_cache, store_cache
from config.settings import API_KEY, DAILY_OPENAI_BUDGET, MONTHLY_OPENAI_BUDGET

client = OpenAI(api_key=API_KEY)


def get_ai_system_prompt(country_data=None):
    """Get AI system prompt for analysis"""
    base_prompt = """You are an expert financial advisor, business strategist, and industry consultant with 20+ years of experience. You provide actionable insights that help users make informed decisions and optimize their financial outcomes.
    
    Your expertise spans:
    - Financial Planning: Investments, loans, insurance, and wealth building
    - Business Strategy: Operations, growth, market positioning, and competitive analysis  
    - Market Intelligence: Current trends, timing analysis, and risk assessment
    - Technology Integration: AI adoption, automation opportunities, and digital transformation
    
    You transform basic calculations into strategic intelligence by:
    - Identifying hidden opportunities and optimization strategies
    - Providing personalized recommendations based on user context
    - Explaining market timing and competitive advantages
    - Offering specific action plans with clear next steps
    
    Always provide practical, actionable advice that delivers measurable value."""
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


def build_analysis_prompt(tool_name, category, user_data, base_result, country_data=None):
    """Build AI analysis prompt"""
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

    return f"""
Analyze this {tool_name} calculation and provide strategic insights:

CALCULATION RESULT: [RESULT]
USER CONTEXT: {user_context}
CATEGORY: {category}

Provide a comprehensive analysis with:

**🎯 KEY INSIGHTS** (3-4 strategic observations)
- Most important implications of the result
- Hidden opportunities or risks to consider
- Market context and timing factors

**💡 STRATEGIC RECOMMENDATIONS** (4-5 specific actions)
- Prioritized steps with clear implementation guidance
- Resource requirements and expected outcomes
- Risk mitigation strategies

**⚡ OPTIMIZATION OPPORTUNITIES** (3-4 immediate improvements)
- Cost reduction or revenue enhancement tactics
- Efficiency improvements with measurable impact
- Competitive advantages to leverage

**🔮 MARKET INTELLIGENCE** (Future outlook and timing)
- Optimal timing for key decisions
- Industry trends and their implications
- Risk factors to monitor

**📋 ACTION PLAN** (Next steps with timeline)
- Immediate actions (0-30 days)
- Short-term goals (1-6 months)
- Long-term strategy considerations

Make recommendations specific, actionable, and valuable for their situation.
"""


def generate_ai_analysis(tool_config, user_data, base_result, ip):
    """Generate AI-powered analysis with rich HTML output"""
    if get_openai_cost_today() >= DAILY_OPENAI_BUDGET or get_openai_cost_month() >= MONTHLY_OPENAI_BUDGET:
        return create_fallback_response(tool_config, user_data, base_result)

    # cache_key = hashlib.sha256(f"{tool_config['slug']}:{str(user_data)}".encode()).hexdigest()
    # cached = check_cache("ai_" + tool_config['slug'], cache_key)
    #
    # if cached:
    #     return cached.replace("[RESULT]", str(base_result))

    category = tool_config.get("category", "general")
    tool_name = tool_config.get("seo_data", {}).get("title", "Analysis Tool")
    prompt = build_analysis_prompt(tool_name, category, user_data, base_result)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": get_ai_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1200,
            temperature=0.7
        )

        ai_analysis = response.choices[0].message.content
        pt, ct = response.usage.prompt_tokens, response.usage.completion_tokens
        cost = (pt * 0.00015 + ct * 0.0006) / 1000
        log_openai_cost(tool_config['slug'], pt, ct, cost)

        # Generate rich HTML response with charts and value ladder
        rich_response = generate_rich_html_response(ai_analysis, user_data, base_result, tool_config)

        # store_cache("ai_" + tool_config['slug'], cache_key, rich_response)
        return rich_response.replace("[RESULT]", str(base_result))

    except Exception as e:
        print(f"AI analysis failed: {str(e)}")
        return create_fallback_response(tool_config, user_data, base_result)


def generate_rich_html_response(ai_analysis, user_data, base_result, tool_config):
    """Generate rich HTML response with charts, graphs and value ladder"""
    category = tool_config.get("category", "general")

    # Generate charts data based on category
    # charts_html = generate_charts_html(user_data, base_result, category)

    # Generate value ladder
    value_ladder_html = generate_value_ladder(user_data, base_result, category)

    # Generate key metrics
    key_metrics_html = generate_key_metrics(user_data, base_result, category)

    # Generate comparison table
    comparison_html = generate_comparison_table(user_data, base_result, category)

    # Convert markdown AI analysis to HTML
    formatted_ai_analysis = convert_markdown_to_html(ai_analysis)

    # Generate charts data based on category
    charts_html = generate_charts_html(user_data, base_result, category)

    # Combine everything into rich HTML
    rich_html = f"""
<div class="ai-analysis-container">
    <div class="analysis-header">
        <div class="result-highlight">
            <h2 class="primary-result">🎯 {base_result}</h2>
            <p class="result-subtitle">Generated by AI Analysis Engine</p>
        </div>
    </div>

    {key_metrics_html}

    <div class="analysis-content">
        <div class="ai-insights">
            <h3>🤖 AI Strategic Analysis</h3>
            <div class="insights-content">
                {formatted_ai_analysis}
            </div>
        </div>

        {charts_html}

        {comparison_html}

        {value_ladder_html}
    </div>

    <div class="action-items">
        <h3>📋 Immediate Action Items</h3>
        <div class="action-grid">
            {generate_action_items(user_data, category)}
        </div>
    </div>
</div>

<style>
.ai-analysis-container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}}

.analysis-header {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 15px;
    padding: 30px;
    color: white;
    text-align: center;
    margin-bottom: 30px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}}

.primary-result {{
    font-size: 2.5rem;
    font-weight: bold;
    margin: 0;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}}

.result-subtitle {{
    font-size: 1.1rem;
    opacity: 0.9;
    margin: 10px 0 0 0;
}}

.key-metrics {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}}

.metric-card {{
    background: white;
    border-radius: 12px;
    padding: 25px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.08);
    border-left: 4px solid #4CAF50;
    transition: transform 0.3s ease;
}}

.metric-card:hover {{
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}}

.metric-value {{
    font-size: 2rem;
    font-weight: bold;
    color: #2c3e50;
    margin: 0;
}}

.metric-label {{
    color: #7f8c8d;
    font-size: 0.9rem;
    margin: 5px 0 0 0;
}}

.chart-container {{
    background: white;
    border-radius: 12px;
    padding: 25px;
    margin: 20px 0;
    box-shadow: 0 5px 15px rgba(0,0,0,0.08);
}}

.value-ladder {{
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    border-radius: 15px;
    padding: 30px;
    margin: 30px 0;
    color: white;
}}

.ladder-step {{
    background: rgba(255,255,255,0.2);
    border-radius: 10px;
    padding: 20px;
    margin: 15px 0;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.3);
}}

.action-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
}}

.action-item {{
    background: #f8f9fa;
    border-radius: 10px;
    padding: 20px;
    border-left: 4px solid #007bff;
}}

.comparison-table {{
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 5px 15px rgba(0,0,0,0.08);
    margin: 20px 0;
}}

.comparison-table table {{
    width: 100%;
    border-collapse: collapse;
}}

.comparison-table th,
.comparison-table td {{
    padding: 15px;
    text-align: left;
    border-bottom: 1px solid #eee;
}}

.comparison-table th {{
    background: #f8f9fa;
    font-weight: 600;
    color: #2c3e50;
}}

@media (max-width: 768px) {{
    .key-metrics {{
        grid-template-columns: 1fr;
    }}

    .action-grid {{
        grid-template-columns: 1fr;
    }}

    .primary-result {{
        font-size: 2rem;
    }}
}}

/* Enhanced Calculator Sections CSS */

/* Section Titles */
.section-title {{
    font-size: 1.5rem;
    font-weight: 700;
    color: #2c3e50;
    margin: 0 0 25px 0;
    padding-bottom: 10px;
    border-bottom: 2px solid #e9ecef;
    display: flex;
    align-items: center;
    gap: 10px;
}}

/* Action Items Section */
.action-items-section {{
    background: #ffffff;
    border-radius: 16px;
    padding: 30px;
    margin: 30px 0;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    position: relative;
    overflow: hidden;
}}

.action-items-section::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #4CAF50, #2196F3, #FF9800, #9C27B0);
    border-radius: 16px 16px 0 0;
}}

.action-items-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 20px;
    margin-top: 20px;
}}

.action-item-card {{
    background: #ffffff;
    border-radius: 12px;
    padding: 24px;
    border: 2px solid #e9ecef;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    cursor: pointer;
}}

.action-item-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
    transition: left 0.6s;
}}

.action-item-card:hover::before {{
    left: 100%;
}}

.action-item-card:hover {{
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
    border-color: #007bff;
}}

.action-item-card[data-priority="high"] {{
    border-left: 4px solid #dc3545;
    background: linear-gradient(135deg, #ffffff 0%, #fff5f5 100%);
}}

.action-item-card[data-priority="medium"] {{
    border-left: 4px solid #ffc107;
    background: linear-gradient(135deg, #ffffff 0%, #fffbf0 100%);
}}

.action-item-card[data-priority="low"] {{
    border-left: 4px solid #28a745;
    background: linear-gradient(135deg, #ffffff 0%, #f8fff9 100%);
}}

.action-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}}

.action-icon {{
    font-size: 1.5rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 45px;
    height: 45px;
    background: rgba(0, 123, 255, 0.1);
    border-radius: 10px;
    border: 2px solid rgba(0, 123, 255, 0.2);
}}

.action-priority {{
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.action-priority.high {{
    background: linear-gradient(135deg, #dc3545, #c82333);
    color: white;
    box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
}}

.action-priority.medium {{
    background: linear-gradient(135deg, #ffc107, #e0a800);
    color: #212529;
    box-shadow: 0 2px 8px rgba(255, 193, 7, 0.3);
}}

.action-priority.low {{
    background: linear-gradient(135deg, #28a745, #1e7e34);
    color: white;
    box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
}}

.action-title {{
    font-size: 1.1rem;
    font-weight: 600;
    color: #2c3e50;
    margin: 0 0 10px 0;
    line-height: 1.3;
}}

.action-description {{
    color: #6c757d;
    margin: 0 0 15px 0;
    line-height: 1.5;
    font-size: 0.95rem;
}}

.action-meta {{
    display: flex;
    gap: 15px;
    flex-wrap: wrap;
}}

.action-timeline,
.action-effort {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 6px 12px;
    background: rgba(108, 117, 125, 0.1);
    border-radius: 20px;
    font-size: 0.85rem;
    color: #495057;
    font-weight: 500;
}}

/* Metrics Dashboard */
.metrics-dashboard {{
    background: #ffffff;
    border-radius: 16px;
    padding: 30px;
    margin: 30px 0;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    position: relative;
    overflow: hidden;
}}

.metrics-dashboard::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #667eea, #764ba2);
    border-radius: 16px 16px 0 0;
}}

.metrics-grid-enhanced {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin-top: 20px;
}}

.metric-card-enhanced {{
    background: #ffffff;
    border-radius: 12px;
    padding: 24px;
    border: 2px solid #e9ecef;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 20px;
}}

.metric-card-enhanced::before {{
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
    transition: left 0.6s;
}}

.metric-card-enhanced:hover::before {{
    left: 100%;
}}

.metric-card-enhanced:hover {{
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}}

.metric-card-enhanced.primary {{
    border-color: #007bff;
    background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
}}

.metric-card-enhanced.success {{
    border-color: #28a745;
    background: linear-gradient(135deg, #ffffff 0%, #f8fff9 100%);
}}

.metric-card-enhanced.info {{
    border-color: #17a2b8;
    background: linear-gradient(135deg, #ffffff 0%, #f0fdff 100%);
}}

.metric-card-enhanced.warning {{
    border-color: #ffc107;
    background: linear-gradient(135deg, #ffffff 0%, #fffbf0 100%);
}}

.metric-icon {{
    font-size: 2rem;
    width: 60px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 123, 255, 0.1);
    border-radius: 12px;
    flex-shrink: 0;
}}

.metric-content {{
    flex: 1;
}}

.metric-value {{
    font-size: 1.8rem;
    font-weight: 700;
    color: #2c3e50;
    margin: 0 0 5px 0;
    line-height: 1.2;
}}

.metric-label {{
    color: #6c757d;
    font-size: 0.9rem;
    margin: 0 0 8px 0;
    font-weight: 500;
}}

.metric-change {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
}}

.metric-change.positive {{
    background: rgba(40, 167, 69, 0.1);
    color: #28a745;
}}

.metric-change.negative {{
    background: rgba(220, 53, 69, 0.1);
    color: #dc3545;
}}

.metric-change.neutral {{
    background: rgba(108, 117, 125, 0.1);
    color: #6c757d;
}}

/* Value Ladder Enhanced */
.value-ladder-enhanced {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 30px;
    margin: 30px 0;
    color: white;
    position: relative;
    overflow: hidden;
}}

.value-ladder-enhanced::before {{
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
    animation: pulse 4s ease-in-out infinite;
    pointer-events: none;
}}

@keyframes pulse {{
    0%, 100% {{ transform: scale(1); opacity: 0.5; }}
    50% {{ transform: scale(1.05); opacity: 0.8; }}
}}

.ladder-container {{
    position: relative;
    z-index: 1;
}}

.ladder-step-enhanced {{
    background: rgba(255, 255, 255, 0.15);
    border-radius: 12px;
    padding: 24px;
    margin: 20px 0;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 20px;
    position: relative;
    overflow: hidden;
}}

.ladder-step-enhanced::before {{
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.6s;
}}

.ladder-step-enhanced:hover::before {{
    left: 100%;
}}

.ladder-step-enhanced:hover {{
    background: rgba(255, 255, 255, 0.25);
    transform: translateX(10px);
}}

.step-number {{
    width: 50px;
    height: 50px;
    background: rgba(255, 255, 255, 0.2);
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    font-weight: 700;
    flex-shrink: 0;
}}

.step-content {{
    flex: 1;
}}

.step-title {{
    font-size: 1.2rem;
    font-weight: 600;
    margin: 0 0 8px 0;
    color: white;
}}

.step-description {{
    color: rgba(255, 255, 255, 0.9);
    margin: 0 0 10px 0;
    line-height: 1.4;
}}

.step-value {{
    font-size: 1.1rem;
    font-weight: 700;
    color: #ffd700;
    margin: 0 0 5px 0;
}}

.step-timeline {{
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.8);
    font-weight: 500;
}}

.step-icon {{
    font-size: 2rem;
    width: 60px;
    height: 60px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}}

/* Copy Button */
.copy-section-btn {{
    position: absolute;
    top: 15px;
    right: 15px;
    background: rgba(0, 0, 0, 0.1);
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    cursor: pointer;
    font-size: 12px;
    transition: all 0.3s ease;
    opacity: 0.7;
    color: #6c757d;
    font-weight: 500;
}}

.copy-section-btn:hover {{
    background: rgba(0, 0, 0, 0.2);
    opacity: 1;
    transform: translateY(-1px);
}}

/* Responsive Design */
@media (max-width: 768px) {{
    .action-items-grid {{
        grid-template-columns: 1fr;
        gap: 15px;
    }}
    
    .metrics-grid-enhanced {{
        grid-template-columns: 1fr;
        gap: 15px;
    }}
    
    .action-item-card,
    .metric-card-enhanced {{
        padding: 20px;
    }}
    
    .metric-card-enhanced {{
        flex-direction: column;
        text-align: center;
        gap: 15px;
    }}
    
    .ladder-step-enhanced {{
        flex-direction: column;
        text-align: center;
        gap: 15px;
        padding: 20px;
    }}
    
    .section-title {{
        font-size: 1.3rem;
        flex-direction: column;
        gap: 5px;
        text-align: center;
    }}
}}

@media (max-width: 480px) {{
    .action-items-section,
    .metrics-dashboard,
    .value-ladder-enhanced {{
        padding: 20px;
        margin: 20px 0;
    }}
    
    .metric-value {{
        font-size: 1.5rem;
    }}
    
    .action-title {{
        font-size: 1rem;
    }}
}}
</style>
"""

    return rich_html


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
    
.ai-analysis-container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}}

.analysis-header {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 15px;
    padding: 30px;
    color: white;
    text-align: center;
    margin-bottom: 30px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}}

.primary-result {{
    font-size: 2.5rem;
    font-weight: bold;
    margin: 0;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}}

.result-subtitle {{
    font-size: 1.1rem;
    opacity: 0.9;
    margin: 10px 0 0 0;
}}

.key-metrics {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}}

.metric-card {{
    background: white;
    border-radius: 12px;
    padding: 25px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.08);
    border-left: 4px solid #4CAF50;
    transition: transform 0.3s ease;
}}

.metric-card:hover {{
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}}

.metric-value {{
    font-size: 2rem;
    font-weight: bold;
    color: #2c3e50;
    margin: 0;
}}

.metric-label {{
    color: #7f8c8d;
    font-size: 0.9rem;
    margin: 5px 0 0 0;
}}

.chart-container {{
    background: white;
    border-radius: 12px;
    padding: 25px;
    margin: 20px 0;
    box-shadow: 0 5px 15px rgba(0,0,0,0.08);
}}

.value-ladder {{
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    border-radius: 15px;
    padding: 30px;
    margin: 30px 0;
    color: white;
}}

.ladder-step {{
    background: rgba(255,255,255,0.2);
    border-radius: 10px;
    padding: 20px;
    margin: 15px 0;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.3);
}}

.action-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
}}

.action-item {{
    background: #f8f9fa;
    border-radius: 10px;
    padding: 20px;
    border-left: 4px solid #007bff;
}}

.comparison-table {{
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 5px 15px rgba(0,0,0,0.08);
    margin: 20px 0;
}}

.comparison-table table {{
    width: 100%;
    border-collapse: collapse;
}}

.comparison-table th,
.comparison-table td {{
    padding: 15px;
    text-align: left;
    border-bottom: 1px solid #eee;
}}

.comparison-table th {{
    background: #f8f9fa;
    font-weight: 600;
    color: #2c3e50;
}}

@media (max-width: 768px) {{
    .key-metrics {{
        grid-template-columns: 1fr;
    }}

    .action-grid {{
        grid-template-columns: 1fr;
    }}

    .primary-result {{
        font-size: 2rem;
    }}
}}

/* Enhanced Calculator Sections CSS */

/* Section Titles */
.section-title {{
    font-size: 1.5rem;
    font-weight: 700;
    color: #2c3e50;
    margin: 0 0 25px 0;
    padding-bottom: 10px;
    border-bottom: 2px solid #e9ecef;
    display: flex;
    align-items: center;
    gap: 10px;
}}

/* Action Items Section */
.action-items-section {{
    background: #ffffff;
    border-radius: 16px;
    padding: 30px;
    margin: 30px 0;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    position: relative;
    overflow: hidden;
}}

.action-items-section::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #4CAF50, #2196F3, #FF9800, #9C27B0);
    border-radius: 16px 16px 0 0;
}}

.action-items-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 20px;
    margin-top: 20px;
}}

.action-item-card {{
    background: #ffffff;
    border-radius: 12px;
    padding: 24px;
    border: 2px solid #e9ecef;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    cursor: pointer;
}}

.action-item-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
    transition: left 0.6s;
}}

.action-item-card:hover::before {{
    left: 100%;
}}

.action-item-card:hover {{
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
    border-color: #007bff;
}}

.action-item-card[data-priority="high"] {{
    border-left: 4px solid #dc3545;
    background: linear-gradient(135deg, #ffffff 0%, #fff5f5 100%);
}}

.action-item-card[data-priority="medium"] {{
    border-left: 4px solid #ffc107;
    background: linear-gradient(135deg, #ffffff 0%, #fffbf0 100%);
}}

.action-item-card[data-priority="low"] {{
    border-left: 4px solid #28a745;
    background: linear-gradient(135deg, #ffffff 0%, #f8fff9 100%);
}}

.action-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}}

.action-icon {{
    font-size: 1.5rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 45px;
    height: 45px;
    background: rgba(0, 123, 255, 0.1);
    border-radius: 10px;
    border: 2px solid rgba(0, 123, 255, 0.2);
}}

.action-priority {{
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.action-priority.high {{
    background: linear-gradient(135deg, #dc3545, #c82333);
    color: white;
    box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
}}

.action-priority.medium {{
    background: linear-gradient(135deg, #ffc107, #e0a800);
    color: #212529;
    box-shadow: 0 2px 8px rgba(255, 193, 7, 0.3);
}}

.action-priority.low {{
    background: linear-gradient(135deg, #28a745, #1e7e34);
    color: white;
    box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
}}

.action-title {{
    font-size: 1.1rem;
    font-weight: 600;
    color: #2c3e50;
    margin: 0 0 10px 0;
    line-height: 1.3;
}}

.action-description {{
    color: #6c757d;
    margin: 0 0 15px 0;
    line-height: 1.5;
    font-size: 0.95rem;
}}

.action-meta {{
    display: flex;
    gap: 15px;
    flex-wrap: wrap;
}}

.action-timeline,
.action-effort {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 6px 12px;
    background: rgba(108, 117, 125, 0.1);
    border-radius: 20px;
    font-size: 0.85rem;
    color: #495057;
    font-weight: 500;
}}

/* Metrics Dashboard */
.metrics-dashboard {{
    background: #ffffff;
    border-radius: 16px;
    padding: 30px;
    margin: 30px 0;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    position: relative;
    overflow: hidden;
}}

.metrics-dashboard::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #667eea, #764ba2);
    border-radius: 16px 16px 0 0;
}}

.metrics-grid-enhanced {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin-top: 20px;
}}

.metric-card-enhanced {{
    background: #ffffff;
    border-radius: 12px;
    padding: 24px;
    border: 2px solid #e9ecef;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 20px;
}}

.metric-card-enhanced::before {{
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
    transition: left 0.6s;
}}

.metric-card-enhanced:hover::before {{
    left: 100%;
}}

.metric-card-enhanced:hover {{
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}}

.metric-card-enhanced.primary {{
    border-color: #007bff;
    background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
}}

.metric-card-enhanced.success {{
    border-color: #28a745;
    background: linear-gradient(135deg, #ffffff 0%, #f8fff9 100%);
}}

.metric-card-enhanced.info {{
    border-color: #17a2b8;
    background: linear-gradient(135deg, #ffffff 0%, #f0fdff 100%);
}}

.metric-card-enhanced.warning {{
    border-color: #ffc107;
    background: linear-gradient(135deg, #ffffff 0%, #fffbf0 100%);
}}

.metric-icon {{
    font-size: 2rem;
    width: 60px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 123, 255, 0.1);
    border-radius: 12px;
    flex-shrink: 0;
}}

.metric-content {{
    flex: 1;
}}

.metric-value {{
    font-size: 1.8rem;
    font-weight: 700;
    color: #2c3e50;
    margin: 0 0 5px 0;
    line-height: 1.2;
}}

.metric-label {{
    color: #6c757d;
    font-size: 0.9rem;
    margin: 0 0 8px 0;
    font-weight: 500;
}}

.metric-change {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
}}

.metric-change.positive {{
    background: rgba(40, 167, 69, 0.1);
    color: #28a745;
}}

.metric-change.negative {{
    background: rgba(220, 53, 69, 0.1);
    color: #dc3545;
}}

.metric-change.neutral {{
    background: rgba(108, 117, 125, 0.1);
    color: #6c757d;
}}

/* Value Ladder Enhanced */
.value-ladder-enhanced {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 30px;
    margin: 30px 0;
    color: white;
    position: relative;
    overflow: hidden;
}}

.value-ladder-enhanced::before {{
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
    animation: pulse 4s ease-in-out infinite;
    pointer-events: none;
}}

@keyframes pulse {{
    0%, 100% {{ transform: scale(1); opacity: 0.5; }}
    50% {{ transform: scale(1.05); opacity: 0.8; }}
}}

.ladder-container {{
    position: relative;
    z-index: 1;
}}

.ladder-step-enhanced {{
    background: rgba(255, 255, 255, 0.15);
    border-radius: 12px;
    padding: 24px;
    margin: 20px 0;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 20px;
    position: relative;
    overflow: hidden;
}}

.ladder-step-enhanced::before {{
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.6s;
}}

.ladder-step-enhanced:hover::before {{
    left: 100%;
}}

.ladder-step-enhanced:hover {{
    background: rgba(255, 255, 255, 0.25);
    transform: translateX(10px);
}}

.step-number {{
    width: 50px;
    height: 50px;
    background: rgba(255, 255, 255, 0.2);
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    font-weight: 700;
    flex-shrink: 0;
}}

.step-content {{
    flex: 1;
}}

.step-title {{
    font-size: 1.2rem;
    font-weight: 600;
    margin: 0 0 8px 0;
    color: white;
}}

.step-description {{
    color: rgba(255, 255, 255, 0.9);
    margin: 0 0 10px 0;
    line-height: 1.4;
}}

.step-value {{
    font-size: 1.1rem;
    font-weight: 700;
    color: #ffd700;
    margin: 0 0 5px 0;
}}

.step-timeline {{
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.8);
    font-weight: 500;
}}

.step-icon {{
    font-size: 2rem;
    width: 60px;
    height: 60px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}}

/* Copy Button */
.copy-section-btn {{
    position: absolute;
    top: 15px;
    right: 15px;
    background: rgba(0, 0, 0, 0.1);
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    cursor: pointer;
    font-size: 12px;
    transition: all 0.3s ease;
    opacity: 0.7;
    color: #6c757d;
    font-weight: 500;
}}

.copy-section-btn:hover {{
    background: rgba(0, 0, 0, 0.2);
    opacity: 1;
    transform: translateY(-1px);
}}

/* Responsive Design */
@media (max-width: 768px) {{
    .action-items-grid {{
        grid-template-columns: 1fr;
        gap: 15px;
    }}
    
    .metrics-grid-enhanced {{
        grid-template-columns: 1fr;
        gap: 15px;
    }}
    
    .action-item-card,
    .metric-card-enhanced {{
        padding: 20px;
    }}
    
    .metric-card-enhanced {{
        flex-direction: column;
        text-align: center;
        gap: 15px;
    }}
    
    .ladder-step-enhanced {{
        flex-direction: column;
        text-align: center;
        gap: 15px;
        padding: 20px;
    }}
    
    .section-title {{
        font-size: 1.3rem;
        flex-direction: column;
        gap: 5px;
        text-align: center;
    }}
}}

@media (max-width: 480px) {{
    .action-items-section,
    .metrics-dashboard,
    .value-ladder-enhanced {{
        padding: 20px;
        margin: 20px 0;
    }}
    
    .metric-value {{
        font-size: 1.5rem;
    }}
    
    .action-title {{
        font-size: 1rem;
    }}
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