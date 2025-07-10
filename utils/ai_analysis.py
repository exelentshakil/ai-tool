import hashlib
from datetime import datetime
from openai import OpenAI
from utils.database import get_openai_cost_today, get_openai_cost_month, log_openai_cost
from utils.cache import check_cache, store_cache
from config.settings import API_KEY, DAILY_OPENAI_BUDGET, MONTHLY_OPENAI_BUDGET

client = OpenAI(api_key=API_KEY)


def build_analysis_prompt(tool_name, category, user_data, localization=None):
    """Build comprehensive AI analysis prompt with localization support"""
    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    country_name = localization.get('country_name', '')
    currency = localization.get('currency', 'USD')

    context_items = []
    location_data = user_data.get('locationData', {})
    city = location_data.get('city', '')
    region = location_data.get('region', '')
    country = location_data.get('name', location_data.get('country', country_name))
    local_currency = location_data.get('currency', currency)

    # Build user context
    for key, value in user_data.items():
        if key == 'locationData':
            if city and region:
                context_items.append(f"Location: {city}, {region}, {country}")
            elif country:
                context_items.append(f"Country: {country}")
        elif isinstance(value, (int, float)) and value > 1000:
            context_items.append(f"{key.replace('_', ' ').title()}: {local_currency}{value:,.0f}")
        else:
            context_items.append(f"{key.replace('_', ' ').title()}: {value}")

    user_context = " | ".join(context_items[:6])

    prompt = f"""
You are an expert analyst providing comprehensive strategic insights. Generate a complete analysis including:

USER CONTEXT: {user_context}
CATEGORY: {category}
LANGUAGE: {language}
CURRENCY: {local_currency}

Please respond entirely in {language} and provide:

1. KEY INSIGHTS (3-4 strategic observations)
2. STRATEGIC RECOMMENDATIONS (4-5 specific actions)
3. VALUE LADDER (4-step progression with specific values and timelines)
4. KEY METRICS (4 important numbers with labels)
5. COMPARISON TABLE (relevant options with ratings)
6. ACTION ITEMS (4 prioritized tasks with timelines and effort levels)
7. OPTIMIZATION OPPORTUNITIES (3-4 immediate improvements)
8. MARKET INTELLIGENCE (future outlook and timing)

Format as structured sections. Include specific numbers, percentages, and actionable steps. Make everything highly specific to their situation and market context.
"""

    return prompt


def generate_ai_analysis(tool_config, user_data, ip, localization=None):
    """Generate comprehensive AI analysis with all components"""
    if get_openai_cost_today() >= DAILY_OPENAI_BUDGET or get_openai_cost_month() >= MONTHLY_OPENAI_BUDGET:
        return create_fallback_response(tool_config, user_data, localization)

    category = tool_config.get("category", "general")
    tool_name = tool_config.get("seo_data", {}).get("title", "Analysis Tool")
    prompt = build_analysis_prompt(tool_name, category, user_data, localization)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": get_ai_system_prompt(localization)},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )

        ai_analysis = response.choices[0].message.content
        pt, ct = response.usage.prompt_tokens, response.usage.completion_tokens
        cost = (pt * 0.00015 + ct * 0.0006) / 1000
        log_openai_cost(tool_config['slug'], pt, ct, cost)

        # Generate rich HTML response
        rich_response = generate_rich_html_response(ai_analysis, user_data, tool_config, localization)
        return rich_response

    except Exception as e:
        print(f"AI analysis failed: {str(e)}")
        return create_fallback_response(tool_config, user_data, localization)


def get_ai_system_prompt(localization=None):
    """Get AI system prompt with localization support"""
    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    currency = localization.get('currency', 'USD')
    country_name = localization.get('country_name', '')

    base_prompt = f"""You are an expert financial and business analyst. Provide strategic insights that are actionable, data-driven, and tailored to specific contexts.

Use {currency} currency for all calculations. Adapt recommendations to {country_name} market context when relevant. 

Structure your response with clear sections and include specific numbers, percentages, and actionable steps. Make everything highly practical and implementable."""

    if language != 'English':
        base_prompt += f"\n\nRespond entirely in {language}."

    return base_prompt


def generate_rich_html_response(ai_analysis, user_data, tool_config, localization=None):
    """Generate modern material design HTML response"""
    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    currency = localization.get('currency', 'USD')
    category = tool_config.get("category", "general")

    # Parse AI analysis into structured components
    parsed_analysis = parse_ai_analysis(ai_analysis)

    # Generate components
    header_html = generate_header(tool_config, currency, language)
    metrics_html = generate_metrics_from_ai(parsed_analysis.get('metrics', []), currency, language)
    insights_html = generate_insights_from_ai(parsed_analysis.get('insights', []), language)
    ladder_html = generate_value_ladder_from_ai(parsed_analysis.get('ladder', []), currency, language)
    comparison_html = generate_comparison_from_ai(parsed_analysis.get('comparison', []), language)
    actions_html = generate_actions_from_ai(parsed_analysis.get('actions', []), language)
    analysis_html = format_analysis_content(ai_analysis)

    return f"""
{get_modern_css()}
<div class="ai-analysis-container">
    {header_html}
    {metrics_html}
    {insights_html}
    {ladder_html}
    {comparison_html}
    {actions_html}

    <div class="analysis-section">
        <div class="section-header">
            <h3>🤖 {get_localized_text('ai_analysis', language)}</h3>
        </div>
        <div class="analysis-content">
            {analysis_html}
        </div>
    </div>
</div>
"""


def parse_ai_analysis(ai_text):
    """Parse AI analysis into structured components"""
    sections = {
        'insights': [],
        'metrics': [],
        'ladder': [],
        'comparison': [],
        'actions': []
    }

    lines = ai_text.split('\n')
    current_section = None
    current_content = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect sections
        if any(keyword in line.lower() for keyword in ['insight', 'key point', 'observation']):
            current_section = 'insights'
        elif any(keyword in line.lower() for keyword in ['metric', 'number', 'statistic']):
            current_section = 'metrics'
        elif any(keyword in line.lower() for keyword in ['ladder', 'step', 'phase', 'level']):
            current_section = 'ladder'
        elif any(keyword in line.lower() for keyword in ['comparison', 'table', 'option']):
            current_section = 'comparison'
        elif any(keyword in line.lower() for keyword in ['action', 'task', 'todo', 'next step']):
            current_section = 'actions'

        if current_section and line.startswith(('-', '•', '1.', '2.', '3.', '4.')):
            sections[current_section].append(line)

    return sections


def generate_header(tool_config, currency, language):
    """Generate modern header section"""
    tool_name = tool_config.get('seo_data', {}).get('title', 'Analysis Tool')

    return f"""
    <div class="header-section">
        <div class="header-content">
            <div class="result-display">
                <div class="result-icon">🎯</div>
                <div class="result-info">
                    <p class="result-subtitle">{tool_name} {get_localized_text('analysis_complete', language)}</p>
                </div>
            </div>
            <div class="header-badge">
                <span class="ai-badge">🤖 AI-Powered</span>
            </div>
        </div>
    </div>
    """


def generate_metrics_from_ai(metrics_data, currency, language):
    """Generate metrics cards from AI data"""
    if not metrics_data:
        # Generate default metrics based on common patterns
        metrics_data = [
            "Analysis Score: 95%",
            "Confidence Level: High",
            "Implementation Time: 30 days",
            "Expected ROI: 15-25%"
        ]

    metrics_html = ""
    for i, metric in enumerate(metrics_data[:4]):
        # Parse metric value and label
        parts = metric.split(':')
        if len(parts) >= 2:
            label = parts[0].strip()
            value = parts[1].strip()
        else:
            label = f"Metric {i + 1}"
            value = metric.strip()

        icon = ["📊", "🎯", "⏱️", "💡"][i]
        color = ["primary", "success", "warning", "info"][i]

        metrics_html += f"""
        <div class="metric-card {color}">
            <div class="metric-icon">{icon}</div>
            <div class="metric-content">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
        </div>
        """

    return f"""
    <div class="metrics-section">
        <div class="section-header">
            <h3>📊 {get_localized_text('key_metrics', language)}</h3>
        </div>
        <div class="metrics-grid">
            {metrics_html}
        </div>
    </div>
    """


def generate_insights_from_ai(insights_data, language):
    """Generate insights section from AI data"""
    if not insights_data:
        insights_data = [
            "Strategic positioning shows strong potential for growth",
            "Market conditions favor immediate implementation",
            "Risk factors are manageable with proper planning",
            "Optimization opportunities identified for 20% improvement"
        ]

    insights_html = ""
    for i, insight in enumerate(insights_data[:4]):
        icon = ["🎯", "💡", "⚠️", "⚡"][i]
        insights_html += f"""
        <div class="insight-card">
            <div class="insight-icon">{icon}</div>
            <div class="insight-text">{insight.strip('- ')}</div>
        </div>
        """

    return f"""
    <div class="insights-section">
        <div class="section-header">
            <h3>💡 {get_localized_text('key_insights', language)}</h3>
        </div>
        <div class="insights-grid">
            {insights_html}
        </div>
    </div>
    """


def generate_value_ladder_from_ai(ladder_data, currency, language):
    """Generate value ladder from AI data"""
    if not ladder_data:
        # Generate default ladder steps
        ladder_data = [
            "Phase 1: Foundation - Establish baseline (Month 1-2)",
            "Phase 2: Growth - Build momentum (Month 3-6)",
            "Phase 3: Scale - Accelerate progress (Month 7-12)",
            "Phase 4: Optimize - Maximize results (Year 2+)"
        ]

    ladder_html = ""
    for i, step in enumerate(ladder_data[:4]):
        step_number = i + 1
        # Parse step content
        parts = step.split('-')
        if len(parts) >= 2:
            title = parts[0].strip()
            description = '-'.join(parts[1:]).strip()
        else:
            title = f"Step {step_number}"
            description = step.strip('- ')

        ladder_html += f"""
        <div class="ladder-step">
            <div class="step-number">{step_number}</div>
            <div class="step-content">
                <h4 class="step-title">{title}</h4>
                <p class="step-description">{description}</p>
            </div>
            <div class="step-arrow">→</div>
        </div>
        """

    return f"""
    <div class="ladder-section">
        <div class="section-header">
            <h3>🚀 {get_localized_text('value_ladder', language)}</h3>
        </div>
        <div class="ladder-container">
            {ladder_html}
        </div>
    </div>
    """


def generate_comparison_from_ai(comparison_data, language):
    """Generate comparison table from AI data"""
    if not comparison_data:
        return ""

    rows_html = ""
    for item in comparison_data[:5]:
        # Parse comparison data
        parts = item.split('-')
        if len(parts) >= 2:
            option = parts[0].strip()
            details = parts[1].strip()
        else:
            option = item.strip('- ')
            details = "See analysis for details"

        rows_html += f"""
        <tr>
            <td>{option}</td>
            <td>{details}</td>
        </tr>
        """

    return f"""
    <div class="comparison-section">
        <div class="section-header">
            <h3>⚖️ {get_localized_text('comparison', language)}</h3>
        </div>
        <div class="comparison-table">
            <table>
                <thead>
                    <tr>
                        <th>{get_localized_text('option', language)}</th>
                        <th>{get_localized_text('details', language)}</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    </div>
    """


def generate_actions_from_ai(actions_data, language):
    """Generate action items from AI data"""
    if not actions_data:
        actions_data = [
            "Review and validate current approach (High priority, 1 week)",
            "Implement recommended changes (Medium priority, 2-3 weeks)",
            "Monitor progress and adjust strategy (Medium priority, Ongoing)",
            "Optimize based on results (Low priority, Monthly)"
        ]

    actions_html = ""
    priorities = ["high", "medium", "low"]
    for i, action in enumerate(actions_data[:4]):
        priority = priorities[i % 3]

        # Parse action content
        if '(' in action and ')' in action:
            main_text = action.split('(')[0].strip()
            meta_text = action.split('(')[1].split(')')[0]
        else:
            main_text = action.strip('- ')
            meta_text = "Standard priority, 1-2 weeks"

        icon = ["🎯", "⚡", "📊", "🔧"][i]

        actions_html += f"""
        <div class="action-item {priority}">
            <div class="action-header">
                <div class="action-icon">{icon}</div>
                <span class="action-priority">{priority}</span>
            </div>
            <div class="action-content">
                <h4 class="action-title">{main_text}</h4>
                <p class="action-meta">{meta_text}</p>
            </div>
        </div>
        """

    return f"""
    <div class="actions-section">
        <div class="section-header">
            <h3>📋 {get_localized_text('action_items', language)}</h3>
        </div>
        <div class="actions-grid">
            {actions_html}
        </div>
    </div>
    """


def format_analysis_content(ai_analysis):
    """Format the full AI analysis content"""
    # Convert markdown-style formatting to HTML
    html = ai_analysis
    html = html.replace('**', '<strong>').replace('**', '</strong>')
    html = html.replace('*', '<em>').replace('*', '</em>')

    # Convert bullet points to HTML lists
    lines = html.split('\n')
    formatted_lines = []
    in_list = False

    for line in lines:
        line = line.strip()
        if line.startswith(('- ', '• ')):
            if not in_list:
                formatted_lines.append('<ul>')
                in_list = True
            formatted_lines.append(f'<li>{line[2:]}</li>')
        else:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            if line:
                if line.startswith('#'):
                    level = len(line) - len(line.lstrip('#'))
                    formatted_lines.append(f'<h{level + 2}>{line.lstrip("# ")}</h{level + 2}>')
                else:
                    formatted_lines.append(f'<p>{line}</p>')

    if in_list:
        formatted_lines.append('</ul>')

    return '\n'.join(formatted_lines)


def get_localized_text(key, language):
    """Get localized text for UI elements"""
    texts = {
        'ai_analysis': {
            'English': 'AI Strategic Analysis',
            'Spanish': 'Análisis Estratégico IA',
            'French': 'Analyse Stratégique IA',
            'German': 'KI-Strategische Analyse',
            'Italian': 'Analisi Strategica IA'
        },
        'analysis_complete': {
            'English': 'Analysis Complete',
            'Spanish': 'Análisis Completo',
            'French': 'Analyse Terminée',
            'German': 'Analyse Abgeschlossen',
            'Italian': 'Analisi Completa'
        },
        'key_metrics': {
            'English': 'Key Metrics',
            'Spanish': 'Métricas Clave',
            'French': 'Métriques Clés',
            'German': 'Wichtige Kennzahlen',
            'Italian': 'Metriche Chiave'
        },
        'key_insights': {
            'English': 'Key Insights',
            'Spanish': 'Puntos Clave',
            'French': 'Insights Clés',
            'German': 'Wichtige Erkenntnisse',
            'Italian': 'Insights Chiave'
        },
        'value_ladder': {
            'English': 'Value Ladder',
            'Spanish': 'Escalera de Valor',
            'French': 'Échelle de Valeur',
            'German': 'Wertleiter',
            'Italian': 'Scala del Valore'
        },
        'comparison': {
            'English': 'Comparison',
            'Spanish': 'Comparación',
            'French': 'Comparaison',
            'German': 'Vergleich',
            'Italian': 'Confronto'
        },
        'action_items': {
            'English': 'Action Items',
            'Spanish': 'Elementos de Acción',
            'French': 'Éléments d\'Action',
            'German': 'Aktionspunkte',
            'Italian': 'Elementi d\'Azione'
        },
        'option': {
            'English': 'Option',
            'Spanish': 'Opción',
            'French': 'Option',
            'German': 'Option',
            'Italian': 'Opzione'
        },
        'details': {
            'English': 'Details',
            'Spanish': 'Detalles',
            'French': 'Détails',
            'German': 'Details',
            'Italian': 'Dettagli'
        }
    }

    return texts.get(key, {}).get(language, texts.get(key, {}).get('English', key))


def create_fallback_response(tool_config, user_data, localization=None):
    """Create fallback response when AI analysis is unavailable"""
    if not localization:
        localization = {}

    language = localization.get('language', 'English')
    currency = localization.get('currency', 'USD')

    tool_name = tool_config.get("seo_data", {}).get("title", "Analysis Tool")

    return f"""
    {get_modern_css()}
    <div class="ai-analysis-container">
        <div class="fallback-section">
            <div class="upgrade-section">
                <h3>🚀 Get Complete AI Analysis</h3>
                <p>Unlock strategic insights, recommendations, and action plans</p>
                <div class="support-button">
                    <a href="https://www.buymeacoffee.com/shakdiesel" target="_blank">
                        <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 50px;">
                    </a>
                </div>
            </div>
        </div>
    </div>
    """


def get_modern_css():
    """Return modern Material Design CSS"""
    return """
    <style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    .ai-analysis-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        line-height: 1.6;
        color: #1a1a1a;
    }

    /* Header Section */
    .header-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 24px;
        padding: 40px;
        margin-bottom: 32px;
        color: white;
        position: relative;
        overflow: hidden;
    }

    .header-section::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.05); opacity: 0.8; }
    }

    .header-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: relative;
        z-index: 1;
    }

    .result-display {
        display: flex;
        align-items: center;
        gap: 20px;
    }

    .result-icon {
        font-size: 3rem;
        filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
    }

    .result-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .result-subtitle {
        font-size: 1.1rem;
        opacity: 0.9;
        margin: 8px 0 0 0;
    }

    .ai-badge {
        background: rgba(255,255,255,0.2);
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.3);
    }

    /* Section Headers */
    .section-header {
        margin-bottom: 24px;
    }

    .section-header h3 {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2d3748;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    /* Metrics Section */
    .metrics-section {
        margin-bottom: 40px;
    }

    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 20px;
    }

    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        display: flex;
        align-items: center;
        gap: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        transition: left 0.6s;
    }

    .metric-card:hover::before {
        left: 100%;
    }

    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }

    .metric-card.primary { border-left: 4px solid #667eea; }
    .metric-card.success { border-left: 4px solid #48bb78; }
    .metric-card.warning { border-left: 4px solid #ed8936; }
    .metric-card.info { border-left: 4px solid #4299e1; }

    .metric-icon {
        font-size: 2rem;
        width: 64px;
        height: 64px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #f7fafc, #edf2f7);
        border-radius: 16px;
        flex-shrink: 0;
    }

    .metric-content {
        flex: 1;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2d3748;
        margin-bottom: 4px;
    }

    .metric-label {
        color: #718096;
        font-size: 0.9rem;
        font-weight: 500;
    }

    /* Insights Section */
    .insights-section {
        margin-bottom: 40px;
    }

    .insights-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px;
    }

    .insight-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        display: flex;
        align-items: flex-start;
        gap: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
    }

    .insight-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }

    .insight-icon {
        font-size: 1.5rem;
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 12px;
        flex-shrink: 0;
    }

    .insight-text {
        color: #4a5568;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* Value Ladder Section */
    .ladder-section {
        margin-bottom: 40px;
    }

    .ladder-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 32px;
        color: white;
        position: relative;
        overflow: hidden;
    }

    .ladder-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 6s ease-in-out infinite;
    }

    .ladder-step {
        display: flex;
        align-items: center;
        gap: 24px;
        background: rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        transition: all 0.3s ease;
        position: relative;
        z-index: 1;
    }

    .ladder-step:hover {
        background: rgba(255,255,255,0.2);
        transform: translateX(8px);
    }

    .step-number {
        width: 48px;
        height: 48px;
        background: rgba(255,255,255,0.2);
        border: 2px solid rgba(255,255,255,0.4);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        font-weight: 700;
        flex-shrink: 0;
    }

    .step-content {
        flex: 1;
    }

    .step-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 8px;
        color: white;
    }

    .step-description {
        color: rgba(255,255,255,0.9);
        font-size: 0.9rem;
        line-height: 1.5;
    }

    .step-arrow {
        font-size: 1.5rem;
        opacity: 0.7;
        flex-shrink: 0;
    }

    /* Comparison Section */
    .comparison-section {
        margin-bottom: 40px;
    }

    .comparison-table {
        background: white;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
    }

    .comparison-table table {
        width: 100%;
        border-collapse: collapse;
    }

    .comparison-table th {
        background: linear-gradient(135deg, #f7fafc, #edf2f7);
        color: #2d3748;
        padding: 20px;
        text-align: left;
        font-weight: 600;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .comparison-table td {
        padding: 16px 20px;
        border-bottom: 1px solid #e2e8f0;
        color: #4a5568;
    }

    .comparison-table tr:hover {
        background: #f7fafc;
    }

    .comparison-table tr:last-child td {
        border-bottom: none;
    }

    /* Actions Section */
    .actions-section {
        margin-bottom: 40px;
    }

    .actions-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 20px;
    }

    .action-item {
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .action-item::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        transition: left 0.6s;
    }

    .action-item:hover::before {
        left: 100%;
    }

    .action-item:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }

    .action-item.high { border-left: 4px solid #f56565; }
    .action-item.medium { border-left: 4px solid #ed8936; }
    .action-item.low { border-left: 4px solid #48bb78; }

    .action-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }

    .action-icon {
        font-size: 1.5rem;
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #f7fafc, #edf2f7);
        border-radius: 12px;
    }

    .action-priority {
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .action-priority.high {
        background: linear-gradient(135deg, #f56565, #e53e3e);
        color: white;
    }

    .action-priority.medium {
        background: linear-gradient(135deg, #ed8936, #dd6b20);
        color: white;
    }

    .action-priority.low {
        background: linear-gradient(135deg, #48bb78, #38a169);
        color: white;
    }

    .action-content {
        position: relative;
        z-index: 1;
    }

    .action-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 8px;
        line-height: 1.3;
    }

    .action-meta {
        color: #718096;
        font-size: 0.9rem;
        line-height: 1.4;
    }

    /* Analysis Content Section */
    .analysis-section {
        margin-bottom: 40px;
    }

    .analysis-content {
        background: white;
        border-radius: 16px;
        padding: 32px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
    }

    .analysis-content h2,
    .analysis-content h3,
    .analysis-content h4 {
        color: #2d3748;
        margin: 24px 0 16px 0;
        font-weight: 600;
    }

    .analysis-content h2 { font-size: 1.5rem; }
    .analysis-content h3 { font-size: 1.3rem; }
    .analysis-content h4 { font-size: 1.1rem; }

    .analysis-content p {
        color: #4a5568;
        margin: 16px 0;
        line-height: 1.7;
    }

    .analysis-content ul {
        margin: 16px 0;
        padding-left: 0;
    }

    .analysis-content li {
        background: #f7fafc;
        margin: 8px 0;
        padding: 12px 16px;
        border-left: 4px solid #667eea;
        border-radius: 0 8px 8px 0;
        list-style: none;
        color: #4a5568;
    }

    .analysis-content strong {
        color: #2d3748;
        font-weight: 600;
    }

    .analysis-content em {
        color: #667eea;
        font-style: normal;
        font-weight: 500;
    }

    /* Fallback Section */
    .fallback-section {
        text-align: center;
        padding: 40px;
    }

    .fallback-header {
        margin-bottom: 32px;
    }

    .fallback-icon {
        font-size: 4rem;
        margin-bottom: 16px;
    }

    .fallback-header h2 {
        font-size: 2rem;
        font-weight: 700;
        color: #2d3748;
        margin-bottom: 8px;
    }

    .fallback-subtitle {
        color: #718096;
        font-size: 1.1rem;
    }

    .result-card {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 20px;
        padding: 32px;
        margin: 32px 0;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }

    .result-card .result-value {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 12px;
    }

    .result-note {
        opacity: 0.9;
        font-size: 1rem;
    }

    .upgrade-section {
        background: #f7fafc;
        border-radius: 16px;
        padding: 32px;
        margin: 32px 0;
    }

    .upgrade-section h3 {
        color: #2d3748;
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 12px;
    }

    .upgrade-section p {
        color: #4a5568;
        font-size: 1.1rem;
        margin-bottom: 24px;
    }

    .support-button {
        display: flex;
        justify-content: center;
    }

    .support-button img {
        transition: transform 0.3s ease;
    }

    .support-button img:hover {
        transform: scale(1.05);
    }

    /* Responsive Design */
    @media (max-width: 768px) {
        .ai-analysis-container {
            padding: 16px;
        }

        .header-section {
            padding: 24px;
        }

        .header-content {
            flex-direction: column;
            text-align: center;
            gap: 20px;
        }

        .result-display {
            flex-direction: column;
            gap: 16px;
        }

        .result-value {
            font-size: 2rem !important;
        }

        .metrics-grid,
        .insights-grid,
        .actions-grid {
            grid-template-columns: 1fr;
            gap: 16px;
        }

        .metric-card,
        .insight-card,
        .action-item {
            padding: 20px;
        }

        .metric-card {
            flex-direction: column;
            text-align: center;
            gap: 16px;
        }

        .ladder-step {
            flex-direction: column;
            text-align: center;
            gap: 16px;
            padding: 20px;
        }

        .step-arrow {
            transform: rotate(90deg);
        }

        .section-header h3 {
            font-size: 1.3rem;
            justify-content: center;
        }

        .analysis-content {
            padding: 24px;
        }

        .comparison-table th,
        .comparison-table td {
            padding: 12px 16px;
        }
    }

    @media (max-width: 480px) {
        .header-section,
        .ladder-container,
        .analysis-content,
        .upgrade-section {
            padding: 20px;
        }

        .result-icon {
            font-size: 2.5rem;
        }

        .metric-value {
            font-size: 1.5rem;
        }

        .action-title {
            font-size: 1rem;
        }

        .section-header h3 {
            font-size: 1.2rem;
        }
    }

    /* Animation Classes */
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .slide-in {
        animation: slideIn 0.8s ease-out;
    }

    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    /* Loading States */
    .loading {
        position: relative;
        overflow: hidden;
    }

    .loading::after {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        animation: loading 1.5s infinite;
    }

    @keyframes loading {
        0% { left: -100%; }
        100% { left: 100%; }
    }

    /* Accessibility */
    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }

    /* Focus States */
    .action-item:focus,
    .metric-card:focus,
    .insight-card:focus {
        outline: 2px solid #667eea;
        outline-offset: 2px;
    }

    /* Print Styles */
    @media print {
        .ai-analysis-container {
            box-shadow: none;
            border: 1px solid #ddd;
        }

        .header-section,
        .ladder-container {
            background: #f5f5f5 !important;
            color: #333 !important;
        }

        .metric-card,
        .insight-card,
        .action-item,
        .analysis-content {
            box-shadow: none;
            border: 1px solid #ddd;
            page-break-inside: avoid;
        }
    }
    </style>"""