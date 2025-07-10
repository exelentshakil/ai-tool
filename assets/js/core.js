class EnhancedCalculatorCore {
    constructor() {
        this.config = TOOL_CONFIG || this.getDefaultConfig();
        this.apiBaseUrl = 'https://ai.barakahsoft.com';
        this.isCalculating = false;

        // Simple localization
        this.countryData = this.config.country_data || {};
        this.currency = this.fixCurrency(this.countryData.currency || 'USD');
        this.currencySymbol = this.getCurrencySymbol(this.currency);
        this.countryName = this.countryData.name || '';
        this.language = this.countryData.language || 'English';
        this.locale = this.getLocale(this.countryData.code);

        console.log('🚀 Calculator initialized:', this.config.base_name);
        console.log('🌍 Country:', this.countryName, this.currency);
    }

    fixCurrency(currency) {
        if (currency === 'u20ac' || currency === '€') return 'EUR';
        if (currency === 'u0024' || currency === '$') return 'USD';
        return currency;
    }

    getCurrencySymbol(code) {
        const symbols = {
            "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CAD": "C$",
            "AUD": "A$", "CHF": "CHF", "NOK": "kr", "SEK": "kr", "DKK": "kr",
            "NZD": "NZ$", "CNY": "¥", "INR": "₹", "BRL": "R$", "KRW": "₩"
        };
        return symbols[code] || code;
    }

    getLocale(countryCode) {
        const locales = {
            "US": "en-US", "UK": "en-GB", "CA": "en-CA", "AU": "en-AU",
            "DE": "de-DE", "FR": "fr-FR", "ES": "es-ES", "IT": "it-IT",
            "NL": "nl-NL", "NO": "nb-NO", "DK": "da-DK", "SE": "sv-SE"
        };
        return locales[countryCode] || "en-US";
    }

    formatCurrency(amount) {
        const num = parseFloat(amount) || 0;
        try {
            return new Intl.NumberFormat(this.locale, {
                style: 'currency',
                currency: this.currency
            }).format(num);
        } catch {
            return this.currencySymbol + num.toLocaleString();
        }
    }

    formatNumber(number) {
        const num = parseFloat(number) || 0;
        return num.toLocaleString(this.locale);
    }

    getDefaultConfig() {
        return {
            slug: 'default-calculator',
            category: 'general',
            base_name: 'Calculator',
            seo_data: { title: 'Calculator' },
            country_data: { code: "US", language: "English" }
        };
    }

    getAllFormData() {
        const formData = {};
        const form = document.getElementById('tool-form');
        if (!form) return formData;

        const elements = form.elements;
        for (let i = 0; i < elements.length; i++) {
            const element = elements[i];
            if (!element.name) continue;

            if (element.type === 'checkbox') {
                formData[element.name] = element.checked;
            } else if (element.type === 'radio' && element.checked) {
                formData[element.name] = element.value;
            } else if (element.tagName === 'SELECT' || element.type === 'range' || 
                       element.type === 'text' || element.type === 'number') {
                formData[element.name] = element.value;
            }
        }
        return formData;
    }

    async processCalculation(formData) {
        this.isCalculating = true;
        this.showLoading();

        try {
            const data = {};
            if (formData instanceof FormData) {
                for (let [key, value] of formData.entries()) {
                    data[key] = value;
                }
            } else {
                Object.assign(data, formData);
            }

            const allFormData = this.getAllFormData();
            const completeData = { ...allFormData, ...data };

            const localizedData = {
                ...completeData,
                locationData: this.countryData,
                country_data: this.countryData,
                locale: this.locale,
                currency: this.currency,
                currency_symbol: this.currencySymbol,
                country_name: this.countryName,
                language: this.language
            };

            const requestPayload = {
                tool: this.config.slug,
                data: localizedData,
                localization: {
                    country_code: this.countryData.code || 'US',
                    country_name: this.countryName,
                    currency: this.currency,
                    language: this.language,
                    locale: this.locale
                }
            };

            const response = await fetch(this.apiBaseUrl + '/process-tool', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestPayload)
            });

            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Request failed');

            this.displayResults(result);
            this.showNotification('✅ Analysis complete!', 'success');

        } catch (error) {
            console.error('❌ Calculation error:', error);
            this.showNotification('❌ Error: ' + error.message, 'error');
        } finally {
            this.isCalculating = false;
            this.hideLoading();
        }
    }

    displayResults(result) {
        const container = document.getElementById('results-container') || this.createResultsContainer();
        container.innerHTML = result.output?.ai_analysis || '<p>No results available</p>';
        container.style.display = 'block';
    }

    createResultsContainer() {
        const container = document.createElement('div');
        container.id = 'results-container';
        container.style.marginTop = '20px';
        document.body.appendChild(container);
        return container;
    }

    showLoading() {
        const button = document.querySelector('[onclick*="processCalculation"]') || 
                      document.querySelector('.calculate-btn') ||
                      document.querySelector('button[type="submit"]');
        if (button) {
            button.disabled = true;
            button.textContent = 'Calculating...';
        }
    }

    hideLoading() {
        const button = document.querySelector('[onclick*="processCalculation"]') || 
                      document.querySelector('.calculate-btn') ||
                      document.querySelector('button[type="submit"]');
        if (button) {
            button.disabled = false;
            button.textContent = 'Calculate';
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => notification.remove(), 3000);
    }

    updateSliderValue(slider) {
        const valueDisplay = document.getElementById(slider.id + '-value');
        if (!valueDisplay) return;

        const value = parseFloat(slider.value) || 0;
        const format = slider.getAttribute('data-format');

        if (format === 'currency') {
            valueDisplay.textContent = this.formatCurrency(value);
        } else if (format === 'percentage') {
            valueDisplay.textContent = value + '%';
        } else {
            valueDisplay.textContent = this.formatNumber(value);
        }
    }

    init() {
        console.log('✅ Calculator ready');
        
        // Global slider function
        window.updateSliderValue = (slider) => this.updateSliderValue(slider);
        
        // Auto-update existing sliders
        const sliders = document.querySelectorAll('.slider-input[data-format]');
        sliders.forEach(slider => this.updateSliderValue(slider));
    }
}

// Initialize
window.calculator = new EnhancedCalculatorCore();
window.calculator.init();

// Global function for forms
function processCalculation(formData) {
    window.calculator.processCalculation(formData);
}