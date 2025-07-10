// themes/hello-elements/tool-js/ui-renderer.js
// UI Rendering and Animation Module

// Simple currency mapping based on high RPM countries
const COUNTRY_CURRENCY_MAP = {
    "NO": { symbol: "kr", currency: "NOK" },
    "US": { symbol: "$", currency: "USD" },
    "AU": { symbol: "A$", currency: "AUD" },
    "DK": { symbol: "kr", currency: "DKK" },
    "CA": { symbol: "C$", currency: "CAD" },
    "SE": { symbol: "kr", currency: "SEK" },
    "CH": { symbol: "CHF", currency: "CHF" },
    "BE": { symbol: "€", currency: "EUR" },
    "UK": { symbol: "£", currency: "GBP" },
    "NL": { symbol: "€", currency: "EUR" },
    "FI": { symbol: "€", currency: "EUR" },
    "IE": { symbol: "€", currency: "EUR" },
    "NZ": { symbol: "NZ$", currency: "NZD" },
    "DE": { symbol: "€", currency: "EUR" },
    "AT": { symbol: "€", currency: "EUR" }
};

class UIRenderer {
    constructor(config, notificationManager) {
        this.config = config;
        this.notificationManager = notificationManager;
        console.log('✅ UI Renderer initialized');
        this.initializeSliders();
    }

    getCurrentCurrencyInfo() {
        let countryCode = 'US';
        if (typeof TOOL_CONFIG !== 'undefined' && TOOL_CONFIG.country_data && TOOL_CONFIG.country_data.code) {
            countryCode = TOOL_CONFIG.country_data.code;
        }
        return COUNTRY_CURRENCY_MAP[countryCode] || { symbol: "$", currency: "USD" };
    }

    updateSliderValue(slider) {
        const value = parseFloat(slider.value);
        const format = slider.getAttribute('data-format') || 'number';
        const valueDisplay = document.getElementById(slider.id + '-value');

        if (!valueDisplay) return;

        let formattedValue;
        const currencyInfo = this.getCurrentCurrencyInfo();
        const currencySymbol = currencyInfo.symbol;

        switch (format) {
            case 'currency':
                if (value >= 1000000) {
                    formattedValue = currencySymbol + (value / 1000000).toFixed(1) + 'M';
                } else if (value >= 1000) {
                    formattedValue = currencySymbol + (value / 1000).toFixed(0) + 'K';
                } else {
                    formattedValue = currencySymbol + value.toLocaleString();
                }
                break;
            case 'percentage':
                formattedValue = value + '%';
                break;
            case 'years':
                formattedValue = value + (value === 1 ? ' year' : ' years');
                break;
            default:
                formattedValue = value.toLocaleString();
        }

        valueDisplay.textContent = formattedValue;
        valueDisplay.style.transform = 'scale(1.1)';
        setTimeout(() => valueDisplay.style.transform = 'scale(1)', 150);
    }

    formatCurrency(amount) {
        const currencyInfo = this.getCurrentCurrencyInfo();
        const currencySymbol = currencyInfo.symbol;

        if (amount >= 1000000) {
            return currencySymbol + (amount / 1000000).toFixed(1) + 'M';
        } else if (amount >= 1000) {
            return currencySymbol + (amount / 1000).toFixed(0) + 'K';
        }
        return currencySymbol + amount.toLocaleString();
    }

    formatNumber(number) {
        return number.toLocaleString();
    }

    initializeSliders() {
        const initSliders = () => {
            const sliders = document.querySelectorAll('.slider-input');
            sliders.forEach(slider => {
                this.updateSliderValue(slider);
                slider.addEventListener('input', () => this.updateSliderValue(slider));
            });
            console.log('✅ Initialized', sliders.length, 'sliders');
        };

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initSliders);
        } else {
            initSliders();
        }
    }

    displayResults(result) {
        const container = document.getElementById('tool-results') || this.createResultsContainer();
        const output = result.output || {};
        
        container.innerHTML = this.createResultsHTML(output, result);
        container.style.display = 'block';
        container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        this.addBasicAnimations();
    }

    createResultsContainer() {
        const container = document.createElement('div');
        container.id = 'tool-results';
        container.style.marginTop = '20px';
        document.body.appendChild(container);
        return container;
    }

    createResultsHTML(output, fullResult) {
        const timestamp = new Date().toLocaleString();
        const title = this.config.seo_data?.title || this.config.base_name;

        return `
            <div class="results-container">
                <div class="results-header">
                    <h2>🎯 ${title} Results</h2>
                    <div class="result-meta">
                        <span>📅 ${timestamp}</span>
                        <span>🤖 AI Powered</span>
                    </div>
                </div>
                
                <div class="ai-analysis">
                    ${output.ai_analysis || '<p>No analysis available</p>'}
                </div>
                
                ${fullResult.user_info?.is_rate_limited ? this.createRateLimitBanner() : ''}
            </div>
        `;
    }

    createRateLimitBanner() {
        return `
            <div class="rate-limit-banner">
                <div class="banner-content">
                    <span class="banner-icon">⏰</span>
                    <div class="banner-text">
                        <strong>Rate Limit Notice</strong>
                        <p>You've reached your usage limit. Upgrade for unlimited access!</p>
                    </div>
                </div>
            </div>
        `;
    }

    addBasicAnimations() {
        const container = document.querySelector('.results-container');
        if (container) {
            container.style.opacity = '0';
            container.style.transform = 'translateY(20px)';
            setTimeout(() => {
                container.style.transition = 'all 0.3s ease';
                container.style.opacity = '1';
                container.style.transform = 'translateY(0)';
            }, 50);
        }
    }

    updateCalculateButton(isCalculating) {
        const submitBtn = document.querySelector('#tool-form button[type="submit"]') ||
                         document.querySelector('.calculate-btn') ||
                         document.querySelector('button[onclick*="processCalculation"]');
        
        if (!submitBtn) return;

        if (isCalculating) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Calculating...';
            submitBtn.style.opacity = '0.8';
        } else {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Calculate';
            submitBtn.style.opacity = '1';
        }
    }

    showCalculatingAnimation() {
        const overlay = document.createElement('div');
        overlay.className = 'calculating-overlay';
        overlay.innerHTML = `
            <div class="calculating-content">
                <div class="spinner"></div>
                <h3>🤖 Analyzing...</h3>
                <p>Generating your results...</p>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    hideCalculatingAnimation() {
        const overlay = document.querySelector('.calculating-overlay');
        if (overlay) {
            overlay.style.opacity = '0';
            setTimeout(() => overlay.remove(), 300);
        }
    }

    displayErrorResults(error) {
        const container = document.getElementById('tool-results') || this.createResultsContainer();
        container.innerHTML = `
            <div class="error-results">
                <div class="error-icon">❌</div>
                <h3>Calculation Error</h3>
                <p>We encountered an issue:</p>
                <div class="error-message">${error.message}</div>
                <div class="error-actions">
                    <button onclick="location.reload()" class="btn-primary">🔄 Refresh</button>
                </div>
            </div>
        `;
    }

    addModernStyling() {
        if (document.getElementById('simple-calculator-styles')) return;

        const style = document.createElement('style');
        style.id = 'simple-calculator-styles';
        style.textContent = `
            .results-container {
                max-width: 800px;
                margin: 20px auto;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                border-radius: 12px;
                overflow: hidden;
            }

            .results-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }

            .results-header h2 {
                margin: 0 0 15px 0;
                font-size: 1.8rem;
                font-weight: 700;
            }

            .result-meta {
                display: flex;
                justify-content: center;
                gap: 20px;
                flex-wrap: wrap;
            }

            .result-meta span {
                background: rgba(255,255,255,0.2);
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.9rem;
            }

            .ai-analysis {
                background: white;
                padding: 30px;
                line-height: 1.6;
                color: #333;
            }

            .ai-analysis h3 {
                color: #2d3748;
                margin: 20px 0 15px 0;
                font-size: 1.3rem;
            }

            .ai-analysis h4 {
                color: #4a5568;
                margin: 15px 0 10px 0;
                font-size: 1.1rem;
            }

            .ai-analysis p {
                margin: 12px 0;
                color: #4a5568;
            }

            .ai-analysis ul {
                margin: 15px 0;
                padding-left: 0;
            }

            .ai-analysis li {
                background: #f7fafc;
                margin: 8px 0;
                padding: 12px 16px;
                border-left: 4px solid #667eea;
                border-radius: 0 8px 8px 0;
                list-style: none;
            }

            .ai-analysis strong {
                color: #2d3748;
                font-weight: 600;
            }

            .rate-limit-banner {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
            }

            .banner-content {
                display: flex;
                align-items: center;
                gap: 15px;
            }

            .banner-icon {
                font-size: 1.5rem;
            }

            .banner-text strong {
                color: #856404;
                display: block;
                margin-bottom: 5px;
            }

            .banner-text p {
                margin: 0;
                color: #856404;
            }

            .error-results {
                text-align: center;
                padding: 40px 20px;
                background: white;
            }

            .error-icon {
                font-size: 3rem;
                margin-bottom: 20px;
            }

            .error-results h3 {
                color: #e53e3e;
                margin-bottom: 15px;
            }

            .error-message {
                background: #fed7d7;
                color: #c53030;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                font-family: monospace;
            }

            .error-actions {
                margin-top: 20px;
            }

            .btn-primary {
                background: #667eea;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
            }

            .btn-primary:hover {
                background: #5a67d8;
                transform: translateY(-1px);
            }

            .calculating-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                transition: opacity 0.3s ease;
            }

            .calculating-content {
                background: white;
                padding: 40px;
                border-radius: 12px;
                text-align: center;
                max-width: 400px;
            }

            .spinner {
                width: 40px;
                height: 40px;
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            .calculating-content h3 {
                margin: 0 0 10px 0;
                color: #333;
            }

            .calculating-content p {
                margin: 0;
                color: #666;
            }

            @media (max-width: 768px) {
                .results-container {
                    margin: 10px;
                }
                
                .results-header {
                    padding: 20px;
                }
                
                .results-header h2 {
                    font-size: 1.5rem;
                }
                
                .ai-analysis {
                    padding: 20px;
                }
                
                .result-meta {
                    flex-direction: column;
                    gap: 10px;
                }
            }
        `;
        document.head.appendChild(style);
    }

    setupMobileOptimizations() {
        if ('ontouchstart' in window) {
            document.body.classList.add('touch-device');
            
            const touchElements = document.querySelectorAll('.btn-primary, .slider-input');
            touchElements.forEach(element => {
                element.style.minHeight = '44px';
                element.addEventListener('touchstart', () => {
                    element.style.transform = 'scale(0.98)';
                });
                element.addEventListener('touchend', () => {
                    setTimeout(() => element.style.transform = '', 150);
                });
            });
        }
        console.log('✅ Mobile optimizations applied');
    }

    addInteractiveFeatures() {
        const cards = document.querySelectorAll('.ai-analysis');
        cards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-2px)';
            });
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
            });
        });
    }

    shareResults() {
        const shareData = {
            title: `${this.config.seo_data?.title || this.config.base_name} Results`,
            text: `Check out my analysis results! 🎯`,
            url: window.location.href
        };

        if (navigator.share) {
            navigator.share(shareData).then(() => {
                this.notificationManager.show('success', '🔗 Results shared!');
            }).catch(() => {
                this.fallbackShare(shareData);
            });
        } else {
            this.fallbackShare(shareData);
        }
    }

    fallbackShare(shareData) {
        const url = encodeURIComponent(shareData.url);
        const text = encodeURIComponent(shareData.text);

        const modal = document.createElement('div');
        modal.innerHTML = `
            <div style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:10000;display:flex;align-items:center;justify-content:center;">
                <div style="background:white;padding:30px;border-radius:12px;max-width:400px;text-align:center;">
                    <h3>🔗 Share Results</h3>
                    <div style="display:flex;flex-direction:column;gap:10px;margin:20px 0;">
                        <a href="https://twitter.com/intent/tweet?text=${text}&url=${url}" target="_blank" style="padding:10px;background:#1da1f2;color:white;text-decoration:none;border-radius:6px;">🐦 Twitter</a>
                        <a href="https://www.facebook.com/sharer/sharer.php?u=${url}" target="_blank" style="padding:10px;background:#4267b2;color:white;text-decoration:none;border-radius:6px;">📘 Facebook</a>
                        <button onclick="navigator.clipboard.writeText('${shareData.url}');alert('Link copied!')" style="padding:10px;background:#666;color:white;border:none;border-radius:6px;cursor:pointer;">📋 Copy Link</button>
                    </div>
                    <button onclick="this.parentElement.parentElement.remove()" style="padding:8px 16px;background:#ccc;border:none;border-radius:6px;cursor:pointer;">Close</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
}

// Export UIRenderer
window.UIRenderer = UIRenderer;

// Global updateSliderValue function with currency support
window.updateSliderValue = function(slider) {
    const value = parseFloat(slider.value);
    const format = slider.getAttribute('data-format') || 'number';
    const valueDisplay = document.getElementById(slider.id + '-value');
    
    if (!valueDisplay) return;
    
    let formattedValue;
    
    // Get country code from TOOL_CONFIG
    let countryCode = 'US';
    if (typeof TOOL_CONFIG !== 'undefined' && TOOL_CONFIG.country_data && TOOL_CONFIG.country_data.code) {
        countryCode = TOOL_CONFIG.country_data.code;
    }
    
    // Get currency symbol from mapping
    const currencyInfo = COUNTRY_CURRENCY_MAP[countryCode] || { symbol: "$", currency: "USD" };
    const currencySymbol = currencyInfo.symbol;
    
    switch (format) {
        case 'currency':
            if (value >= 1000000) {
                formattedValue = currencySymbol + (value / 1000000).toFixed(1) + 'M';
            } else if (value >= 1000) {
                formattedValue = currencySymbol + (value / 1000).toFixed(0) + 'K';
            } else {
                formattedValue = currencySymbol + value.toLocaleString();
            }
            break;
        case 'percentage':
            formattedValue = value + '%';
            break;
        case 'years':
            formattedValue = value + (value === 1 ? ' year' : ' years');
            break;
        default:
            formattedValue = value.toLocaleString();
    }
    
    valueDisplay.textContent = formattedValue;
    valueDisplay.style.transform = 'scale(1.1)';
    setTimeout(() => valueDisplay.style.transform = 'scale(1)', 150);
};

// Fix currency sliders on page load
function fixCurrencySliders() {
    const sliders = document.querySelectorAll('.slider-input[data-format="currency"]');
    sliders.forEach(slider => {
        window.updateSliderValue(slider);
    });
}

// Run when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(fixCurrencySliders, 100);
    });
} else {
    setTimeout(fixCurrencySliders, 100);
}

// Debug function
window.debugCurrency = function() {
    console.log('TOOL_CONFIG:', typeof TOOL_CONFIG !== 'undefined' ? TOOL_CONFIG : 'Not found');
    if (typeof TOOL_CONFIG !== 'undefined' && TOOL_CONFIG.country_data) {
        const code = TOOL_CONFIG.country_data.code;
        console.log('Country code:', code);
        console.log('Currency mapping:', COUNTRY_CURRENCY_MAP[code]);
    }
};