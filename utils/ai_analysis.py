def create_fallback_response(tool_config, user_data, base_result):
    """Create donation banner when AI is unavailable instead of fallback content"""
    category = tool_config.get("category", "general")
    tool_name = tool_config.get("seo_data", {}).get("title", "Analysis Tool")

    # Get location data for localization
    location_data = user_data.get('locationData', {})
    currency = location_data.get('currency', 'USD')
    country = location_data.get('name', location_data.get('country', ''))

    # Calculate next reset time (assuming daily reset at midnight UTC)
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    next_reset = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    hours_until_reset = int((next_reset - now).total_seconds() / 3600)

    donation_banner_html = f"""
    <div class="donation-banner-container">
        <div class="donation-header">
            <div class="header-icon">🤖</div>
            <h2>AI Analysis Temporarily Unavailable</h2>
            <p class="header-subtitle">Daily AI limit reached for enhanced analysis</p>
        </div>

        <div class="basic-result-display">
            <div class="result-card">
                <h3 class="result-title">📊 {tool_name} Result</h3>
                <div class="result-value">{base_result}</div>
                <p class="result-note">Basic calculation complete - AI insights require support</p>
            </div>
        </div>

        <div class="donation-content">
            <div class="support-message">
                <h3>💡 Want Advanced AI Analysis?</h3>
                <p>Support our platform to unlock:</p>
                <div class="features-grid">
                    <div class="feature-item">
                        <span class="feature-icon">🎯</span>
                        <span class="feature-text">Strategic Insights & Market Intelligence</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">💡</span>
                        <span class="feature-text">Expert Recommendations & Action Plans</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">📊</span>
                        <span class="feature-text">Interactive Charts & Visualizations</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">🚀</span>
                        <span class="feature-text">Personalized Optimization Strategies</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">⚡</span>
                        <span class="feature-text">Risk Assessment & Mitigation Plans</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">🎓</span>
                        <span class="feature-text">Expert Tips & Success Stories</span>
                    </div>
                </div>
            </div>

            <div class="donation-section">
                <div class="donation-card">
                    <h4>☕ Support Our Platform</h4>
                    <p>Your support helps us provide advanced AI analysis and keep improving our tools.</p>

                    <div class="donation-button-container">
                        <p style="text-align:center;"><a href="https://www.buymeacoffee.com/shakdiesel" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;"></a></p>
                    </div>

                    <div class="support-benefits">
                        <div class="benefit-item">
                            <span class="benefit-icon">⚡</span>
                            <span class="benefit-text">Faster AI processing</span>
                        </div>
                        <div class="benefit-item">
                            <span class="benefit-icon">🔓</span>
                            <span class="benefit-text">Higher daily limits</span>
                        </div>
                        <div class="benefit-item">
                            <span class="benefit-icon">🎯</span>
                            <span class="benefit-text">Premium features</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="reset-info">
            <div class="reset-card">
                <div class="reset-icon">🕐</div>
                <div class="reset-content">
                    <h4>AI Analysis Resets In</h4>
                    <div class="countdown-display">
                        <span class="countdown-number">{hours_until_reset}</span>
                        <span class="countdown-label">hour{'' if hours_until_reset == 1 else 's'}</span>
                    </div>
                    <p class="reset-note">Free AI analysis available again at midnight UTC</p>
                </div>
            </div>
        </div>

        <div class="alternative-actions">
            <div class="action-card">
                <h4>🔄 Meanwhile, You Can:</h4>
                <div class="action-list">
                    <div class="action-item">
                        <span class="action-icon">📱</span>
                        <span class="action-text">Save this result for later reference</span>
                    </div>
                    <div class="action-item">
                        <span class="action-icon">🔍</span>
                        <span class="action-text">Try other calculators and tools</span>
                    </div>
                    <div class="action-item">
                        <span class="action-icon">📚</span>
                        <span class="action-text">Explore our resource library</span>
                    </div>
                    <div class="action-item">
                        <span class="action-icon">💌</span>
                        <span class="action-text">Subscribe for updates and tips</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="thank-you-message">
            <h4>🙏 Thank You for Using Our Platform</h4>
            <p>We appreciate your support in helping us provide better financial tools and analysis for everyone.</p>
        </div>
    </div>

    <style>
    {{'''
    .donation-banner-container {{
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
        color: #2c3e50;
    }}

    .donation-header {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 40px 30px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        position: relative;
        overflow: hidden;
    }}

    .donation-header::before {{
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

    .header-icon {{
        font-size: 3rem;
        margin-bottom: 15px;
        position: relative;
        z-index: 1;
    }}

    .donation-header h2 {{
        margin: 0 0 10px 0;
        font-size: 2rem;
        font-weight: 700;
        position: relative;
        z-index: 1;
    }}

    .header-subtitle {{
        font-size: 1.1rem;
        opacity: 0.9;
        margin: 0;
        position: relative;
        z-index: 1;
    }}

    .basic-result-display {{
        margin-bottom: 30px;
    }}

    .result-card {{
        background: #ffffff;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border: 2px solid #e9ecef;
    }}

    .result-title {{
        margin: 0 0 15px 0;
        color: #2c3e50;
        font-size: 1.3rem;
        font-weight: 700;
    }}

    .result-value {{
        font-size: 2.2rem;
        font-weight: 700;
        color: #007bff;
        margin: 0 0 10px 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }}

    .result-note {{
        color: #6c757d;
        margin: 0;
        font-style: italic;
    }}

    .donation-content {{
        display: grid;
        gap: 30px;
        margin-bottom: 30px;
    }}

    .support-message {{
        background: #ffffff;
        border-radius: 15px;
        padding: 30px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border-left: 4px solid #28a745;
    }}

    .support-message h3 {{
        margin: 0 0 15px 0;
        color: #2c3e50;
        font-size: 1.5rem;
        font-weight: 700;
    }}

    .support-message > p {{
        margin: 0 0 20px 0;
        color: #6c757d;
        font-size: 1.1rem;
    }}

    .features-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 15px;
    }}

    .feature-item {{
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 15px;
        background: rgba(40, 167, 69, 0.05);
        border-radius: 10px;
        border: 1px solid rgba(40, 167, 69, 0.1);
        transition: all 0.3s ease;
    }}

    .feature-item:hover {{
        transform: translateX(5px);
        background: rgba(40, 167, 69, 0.1);
        border-color: rgba(40, 167, 69, 0.2);
    }}

    .feature-icon {{
        font-size: 1.3rem;
        flex-shrink: 0;
    }}

    .feature-text {{
        font-weight: 600;
        color: #2c3e50;
    }}

    .donation-section {{
        background: #ffffff;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        overflow: hidden;
    }}

    .donation-card {{
        padding: 30px;
        text-align: center;
        background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
        color: #2c3e50;
    }}

    .donation-card h4 {{
        margin: 0 0 15px 0;
        font-size: 1.4rem;
        font-weight: 700;
    }}

    .donation-card > p {{
        margin: 0 0 25px 0;
        font-size: 1.1rem;
        color: #555;
    }}

    .donation-button-container {{
        margin: 25px 0;
    }}

    .support-benefits {{
        display: flex;
        justify-content: center;
        gap: 30px;
        margin-top: 25px;
        flex-wrap: wrap;
    }}

    .benefit-item {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
    }}

    .benefit-icon {{
        font-size: 1.5rem;
    }}

    .benefit-text {{
        font-size: 0.9rem;
        font-weight: 600;
        color: #2c3e50;
    }}

    .reset-info {{
        margin-bottom: 30px;
    }}

    .reset-card {{
        background: #ffffff;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border-left: 4px solid #007bff;
        display: flex;
        align-items: center;
        gap: 20px;
    }}

    .reset-icon {{
        font-size: 2.5rem;
        color: #007bff;
        flex-shrink: 0;
    }}

    .reset-content {{
        flex: 1;
    }}

    .reset-content h4 {{
        margin: 0 0 10px 0;
        color: #2c3e50;
        font-size: 1.2rem;
        font-weight: 700;
    }}

    .countdown-display {{
        display: flex;
        align-items: baseline;
        gap: 8px;
        margin-bottom: 8px;
    }}

    .countdown-number {{
        font-size: 2.5rem;
        font-weight: 700;
        color: #007bff;
        line-height: 1;
    }}

    .countdown-label {{
        font-size: 1.1rem;
        color: #6c757d;
        font-weight: 600;
    }}

    .reset-note {{
        margin: 0;
        color: #6c757d;
        font-size: 0.9rem;
    }}

    .alternative-actions {{
        margin-bottom: 30px;
    }}

    .action-card {{
        background: #ffffff;
        border-radius: 15px;
        padding: 30px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border-left: 4px solid #ffc107;
    }}

    .action-card h4 {{
        margin: 0 0 20px 0;
        color: #2c3e50;
        font-size: 1.3rem;
        font-weight: 700;
    }}

    .action-list {{
        display: grid;
        gap: 12px;
    }}

    .action-item {{
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 12px 15px;
        background: rgba(255, 193, 7, 0.05);
        border-radius: 10px;
        border: 1px solid rgba(255, 193, 7, 0.1);
        transition: all 0.3s ease;
    }}

    .action-item:hover {{
        transform: translateX(5px);
        background: rgba(255, 193, 7, 0.1);
        border-color: rgba(255, 193, 7, 0.2);
    }}

    .action-icon {{
        font-size: 1.3rem;
        color: #ffc107;
        flex-shrink: 0;
    }}

    .action-text {{
        font-weight: 600;
        color: #2c3e50;
    }}

    .thank-you-message {{
        background: linear-gradient(135deg, #a8e6cf 0%, #7fcdcd 100%);
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        color: #2c3e50;
    }}

    .thank-you-message h4 {{
        margin: 0 0 15px 0;
        font-size: 1.4rem;
        font-weight: 700;
    }}

    .thank-you-message p {{
        margin: 0;
        font-size: 1.1rem;
        line-height: 1.6;
    }}

    @keyframes pulse {{
        0%, 100% {{ transform: scale(1); opacity: 0.5; }}
        50% {{ transform: scale(1.05); opacity: 0.8; }}
    }}

    @media (max-width: 768px) {{
        .donation-banner-container {{ padding: 15px; }}
        .donation-header {{ padding: 30px 20px; }}
        .donation-header h2 {{ font-size: 1.6rem; }}
        .result-value {{ font-size: 1.8rem; }}
        .features-grid {{ grid-template-columns: 1fr; }}
        .support-benefits {{ flex-direction: column; gap: 15px; }}
        .reset-card {{ flex-direction: column; text-align: center; gap: 15px; }}
        .countdown-display {{ justify-content: center; }}
        .donation-card {{ padding: 25px 15px; }}
    }}

    @media (max-width: 480px) {{
        .countdown-number {{ font-size: 2rem; }}
        .header-icon {{ font-size: 2.5rem; }}
        .action-list {{ gap: 8px; }}
        .action-item {{ padding: 10px 12px; }}
    }}
    '''}}
</style>

    """

    return donation_banner_html