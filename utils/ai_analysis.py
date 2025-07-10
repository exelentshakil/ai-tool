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