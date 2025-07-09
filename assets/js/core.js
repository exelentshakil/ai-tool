// Enhanced EnhancedCalculatorCore with Localization Support

class EnhancedCalculatorCore {
    constructor() {
        this.config = TOOL_CONFIG || this.getDefaultConfig();
        this.apiBaseUrl = 'https://ai.barakahsoft.com';
        this.results = null;
        this.isCalculating = false;
        this.charts = {};
        this.rateLimitInfo = null;

        // Add cache properties
        this.cache = new Map();
        this.cacheExpiry = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
        this.maxCacheSize = 50; // Maximum cached results

        // Localization properties
        this.countryData = this.config.country_data || {};
        this.currency = this.countryData.currency || 'USD';
        this.currencySymbol = this.getCurrencySymbol(this.currency);
        this.countryName = this.countryData.name || '';
        this.language = this.countryData.language || 'English';
        this.locale = this.getLocaleFromCountry(this.countryData.code);

        console.log('🚀 Enhanced Calculator Core initialized for:', this.config.base_name);
        console.log('🌍 Localized for:', this.countryName, `(${this.currency})`);

        // Load existing cache on startup
        this.loadCacheFromStorage();
    }

    // Enhanced currency formatting with localization
    getCurrencySymbol(currencyCode) {
        const symbols = {
            "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CAD": "C$",
            "AUD": "A$", "CHF": "Fr", "NOK": "kr", "SEK": "kr", "DKK": "kr",
            "NZD": "NZ$", "CNY": "¥", "INR": "₹", "BRL": "R$", "KRW": "₩"
        };
        return symbols[currencyCode] || currencyCode;
    }

    // Get locale from country code
    getLocaleFromCountry(countryCode) {
        const locales = {
            "US": "en-US", "UK": "en-GB", "CA": "en-CA", "AU": "en-AU",
            "DE": "de-DE", "FR": "fr-FR", "ES": "es-ES", "IT": "it-IT",
            "NO": "no-NO", "DK": "da-DK", "SE": "sv-SE", "FI": "fi-FI",
            "NL": "nl-NL", "BE": "nl-BE", "CH": "de-CH", "AT": "de-AT",
            "IE": "en-IE", "NZ": "en-NZ"
        };
        return locales[countryCode] || "en-US";
    }

    // Enhanced number formatting with localization
    formatCurrency(amount, currency = null) {
        const currencyCode = currency || this.currency;
        try {
            return new Intl.NumberFormat(this.locale, {
                style: 'currency',
                currency: currencyCode,
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }).format(amount);
        } catch (error) {
            // Fallback formatting
            return `${this.currencySymbol}${this.formatNumber(amount)}`;
        }
    }

    formatNumber(number) {
        try {
            return new Intl.NumberFormat(this.locale).format(number);
        } catch (error) {
            // Fallback formatting
            return number.toLocaleString();
        }
    }

    formatDate(date, options = {}) {
        try {
            return new Intl.DateTimeFormat(this.locale, {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                ...options
            }).format(new Date(date));
        } catch (error) {
            return new Date(date).toLocaleDateString();
        }
    }

    // Cache management methods (keeping existing methods)
    generateCacheKey(data) {
        const sortedData = Object.keys(data)
            .sort()
            .reduce((result, key) => {
                result[key] = data[key];
                return result;
            }, {});

        const dataString = JSON.stringify(sortedData);
        return `${this.config.slug}:${this.hashString(dataString)}`;
    }

    hashString(str) {
        let hash = 0;
        if (str.length === 0) return hash;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return Math.abs(hash).toString(36);
    }

    getCachedResult(cacheKey) {
        const cached = this.cache.get(cacheKey);
        if (!cached) return null;

        const now = Date.now();
        if (now - cached.timestamp > this.cacheExpiry) {
            this.cache.delete(cacheKey);
            this.saveCacheToStorage();
            return null;
        }

        console.log('✅ Using cached result for:', cacheKey);
        return cached.result;
    }

    setCachedResult(cacheKey, result) {
        if (this.cache.size >= this.maxCacheSize) {
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
        }

        this.cache.set(cacheKey, {
            result: result,
            timestamp: Date.now()
        });

        console.log('💾 Cached result for:', cacheKey);
        this.saveCacheToStorage();
    }

    loadCacheFromStorage() {
        try {
            const stored = localStorage.getItem(`calculator_cache_${this.config.slug}`);
            if (stored) {
                const parsed = JSON.parse(stored);
                const now = Date.now();

                Object.entries(parsed).forEach(([key, value]) => {
                    if (now - value.timestamp <= this.cacheExpiry) {
                        this.cache.set(key, value);
                    }
                });

                console.log(`📁 Loaded ${this.cache.size} cached results from storage`);
            }
        } catch (error) {
            console.warn('Could not load cache from storage:', error);
        }
    }

    saveCacheToStorage() {
        try {
            const cacheObject = {};
            this.cache.forEach((value, key) => {
                cacheObject[key] = value;
            });

            localStorage.setItem(
                `calculator_cache_${this.config.slug}`,
                JSON.stringify(cacheObject)
            );
        } catch (error) {
            console.warn('Could not save cache to storage:', error);
        }
    }

    clearCache() {
        this.cache.clear();
        try {
            localStorage.removeItem(`calculator_cache_${this.config.slug}`);
        } catch (error) {
            console.warn('Could not clear cache from storage:', error);
        }
        console.log('🗑️ Cache cleared');
    }

    getDefaultConfig() {
        return {
            slug: 'default-calculator',
            category: 'general',
            base_name: 'Calculator',
            seo_data: { title: 'Calculator' },
            country_data: {code: "US", language: "English", local_term: "zipcode"}
        };
    }

    // Enhanced initialization with localization
    init() {
        try {
            this.setupModules();
            this.initializeModules();
            this.setupLocalization();
            console.log('✅ All calculator modules initialized successfully');
        } catch (error) {
            console.error('❌ Calculator initialization failed:', error);
            this.handleInitError(error);
        }
    }

    setupLocalization() {
        // Update UI elements with localized text
        this.updateUILocalization();

        // Set up currency formatting for existing elements
        this.updateCurrencyElements();

        // Add country-specific styling
        this.addCountrySpecificStyling();
    }

    updateUILocalization() {
        // Update form labels based on country
        const locationInput = document.querySelector('input[name="location"]');
        if (locationInput && this.countryData.local_term) {
            const label = locationInput.closest('.form-group')?.querySelector('label');
            if (label) {
                const localTerm = this.countryData.local_term;
                label.innerHTML = label.innerHTML.replace(/ZIP code|postal code|postcode/gi, localTerm);
            }
            locationInput.placeholder = `Enter your ${this.countryData.local_term}`;
        }

        // Update currency-related elements
        document.querySelectorAll('[data-currency]').forEach(element => {
            element.textContent = element.textContent.replace(/\$|USD/g, this.currencySymbol);
        });
    }

    updateCurrencyElements() {
        // Update slider values with local currency
        document.querySelectorAll('.slider-input[data-format="currency"]').forEach(slider => {
            const valueDisplay = document.getElementById(slider.id + '-value');
            if (valueDisplay) {
                const amount = parseInt(slider.value);
                valueDisplay.textContent = this.formatCurrency(amount);
            }
        });
    }

    addCountrySpecificStyling() {
        if (!this.countryData.code) return;

        const style = document.createElement('style');
        style.textContent = `
            .calculator-container {
                --country-accent: var(--country-color-${this.countryData.code.toLowerCase()}, #007bff);
            }
            
            .form-header::before {
                content: "${this.getCountryFlag(this.countryData.code)}";
                font-size: 1.5rem;
                margin-right: 10px;
            }
            
            .country-indicator {
                background: var(--country-accent);
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 0.8rem;
                position: absolute;
                top: 10px;
                right: 10px;
            }
        `;
        document.head.appendChild(style);
    }

    getCountryFlag(countryCode) {
        const flags = {
            "US": "🇺🇸", "UK": "🇬🇧", "CA": "🇨🇦", "AU": "🇦🇺", "DE": "🇩🇪",
            "FR": "🇫🇷", "JP": "🇯🇵", "NO": "🇳🇴", "DK": "🇩🇰", "SE": "🇸🇪",
            "FI": "🇫🇮", "CH": "🇨🇭", "AT": "🇦🇹", "BE": "🇧🇪", "NL": "🇳🇱",
            "IE": "🇮🇪", "NZ": "🇳🇿", "ES": "🇪🇸", "IT": "🇮🇹", "PT": "🇵🇹"
        };
        return flags[countryCode] || "🌍";
    }

    setupModules() {
        this.notificationManager = new NotificationManager();
        this.validator = new CalculatorValidator(this.config);
        this.eventHandler = new EventHandler(this);
        this.uiRenderer = new UIRenderer(this.config, this.notificationManager);
        this.chartManager = new ChartManager(this.config);
        this.reportGenerator = new ReportGenerator(this.config, this.chartManager);
    }

    initializeModules() {
        this.eventHandler.init();
        this.checkRateLimit();
        this.uiRenderer.addModernStyling();
        this.uiRenderer.setupMobileOptimizations();
    }

    handleInitError(error) {
        console.error('Initialization error:', error);
        if (this.notificationManager) {
            this.notificationManager.show('error', '❌ Calculator failed to initialize: ' + error.message);
        }
    }

    // Enhanced calculation process with localized data
    async processCalculation(formData) {
        this.isCalculating = true;
        this.uiRenderer.updateCalculateButton(true);
        this.uiRenderer.showCalculatingAnimation();

        try {
            // Prepare data for API with localization
            const data = {};
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }

            // Add comprehensive localization data
            const localizedData = {
                ...data,
                locationData: this.countryData,
                country_data: this.countryData,
                locale: this.locale,
                currency: this.currency,
                currency_symbol: this.currencySymbol,
                country_name: this.countryName,
                language: this.language
            };

            // Generate cache key
            const cacheKey = this.generateCacheKey(localizedData);

            // Check cache first
            const cachedResult = this.getCachedResult(cacheKey);
            if (cachedResult) {
                console.log('⚡ Using cached result - no API call needed');
                this.handleCalculationSuccess(cachedResult, true);
                this.notificationManager.show('success', '⚡ Results loaded from cache!');
                return;
            }

            console.log('📊 Sending calculation request:', {
                tool: this.config.slug,
                data: localizedData,
                country: this.countryName
            });

            // Call Flask API with enhanced localization data
            const response = await fetch(this.apiBaseUrl + '/process-tool', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tool: this.config.slug,
                    data: localizedData,
                    localization: {
                        country_code: this.countryData.code,
                        country_name: this.countryName,
                        currency: this.currency,
                        language: this.language,
                        locale: this.locale
                    }
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'HTTP ' + response.status);
            }

            console.log('✅ Calculation result:', result);

            // Cache the result
            this.setCachedResult(cacheKey, result);

            this.handleCalculationSuccess(result, false);

        } catch (error) {
            console.error('❌ Calculation error:', error);
            this.handleCalculationError(error);
        } finally {
            this.isCalculating = false;
            this.uiRenderer.updateCalculateButton(false);
            this.uiRenderer.hideCalculatingAnimation();
        }
    }

    handleCalculationSuccess(result, fromCache = false) {
        this.results = result.output;
        this.rateLimitInfo = result.user_info;

        // Enhanced results display with localization
        this.uiRenderer.displayLocalizedResults(result, this.countryData);
        this.chartManager.initializeLocalizedCharts(result.output, this.countryData);
        this.uiRenderer.addInteractiveFeatures();

        if (fromCache) {
            const message = this.language === 'German' ?
                '⚡ Zwischengespeicherte Ergebnisse sofort geladen!' :
                this.language === 'French' ?
                '⚡ Résultats en cache chargés instantanément!' :
                '⚡ Cached results loaded instantly!';
            this.notificationManager.show('success', message);
            this.trackAnalytics('calculation_completed_cached');
        } else {
            const message = this.language === 'German' ?
                '✅ Analyse abgeschlossen! Ergebnisse bereit.' :
                this.language === 'French' ?
                '✅ Analyse terminée! Résultats prêts.' :
                '✅ Analysis complete! Results ready.';
            this.notificationManager.show('success', message);
            this.trackAnalytics('calculation_completed');
        }
    }

    handleCalculationError(error) {
        const message = this.language === 'German' ?
            '❌ Berechnung fehlgeschlagen: ' + error.message :
            this.language === 'French' ?
            '❌ Échec du calcul: ' + error.message :
            '❌ Calculation failed: ' + error.message;

        this.notificationManager.show('error', message);
        this.uiRenderer.displayErrorResults(error);
        this.trackAnalytics('calculation_failed', { error: error.message });
    }

    // Enhanced rate limiting with localization
    async checkRateLimit() {
        try {
            const response = await fetch(this.apiBaseUrl + '/check-limits', {
                headers: {
                    'Content-Type': 'application/json',
                    'X-Country-Code': this.countryData.code || 'US',
                    'X-Language': this.language
                }
            });
            const data = await response.json();
            this.rateLimitInfo = data;
            return data.limit_info;
        } catch (error) {
            console.warn('Could not check rate limits:', error);
            return null;
        }
    }

    // Enhanced analytics tracking with localization
    trackAnalytics(event, data = {}) {
        const enhancedData = {
            tool_name: this.config.base_name,
            tool_slug: this.config.slug,
            tool_category: this.config.category,
            country_code: this.countryData.code,
            country_name: this.countryName,
            currency: this.currency,
            language: this.language,
            locale: this.locale,
            ...data
        };

        // Google Analytics 4 tracking
        if (typeof gtag !== 'undefined') {
            gtag('event', event, enhancedData);
        }

        // Facebook Pixel tracking
        if (typeof fbq !== 'undefined') {
            fbq('trackCustom', event, enhancedData);
        }

        // Custom analytics tracking
        if (window.analytics && typeof window.analytics.track === 'function') {
            window.analytics.track(event, enhancedData);
        }

        console.log('📊 Analytics event:', event, enhancedData);
    }

    // Public API methods (keeping existing ones)
    resetForm() {
        if (this.eventHandler) {
            this.eventHandler.resetForm();
        }
    }

    shareResults() {
        if (this.uiRenderer) {
            this.uiRenderer.shareResults();
        }
    }

    downloadReport(format) {
        if (this.reportGenerator) {
            this.reportGenerator.generateLocalizedReport(format, this.countryData);
        }
    }

    // Enhanced utility methods
    sanitizeHTML(str) {
        const temp = document.createElement('div');
        temp.textContent = str;
        return temp.innerHTML;
    }

    // Cache management
    getCacheStats() {
        const stats = {
            totalEntries: this.cache.size,
            maxSize: this.maxCacheSize,
            expiryTime: this.cacheExpiry / (1000 * 60 * 60),
            entries: []
        };

        this.cache.forEach((value, key) => {
            const age = (Date.now() - value.timestamp) / (1000 * 60);
            stats.entries.push({
                key: key,
                ageMinutes: Math.round(age),
                timestamp: new Date(value.timestamp).toLocaleString()
            });
        });

        return stats;
    }

    showCacheStats() {
        const stats = this.getCacheStats();
        console.table(stats.entries);

        const message = `
Cache Statistics:
- Entries: ${stats.totalEntries}/${stats.maxSize}
- Expiry: ${stats.expiryTime} hours
- Storage Used: ~${JSON.stringify(stats).length} characters
        `;

        if (this.notificationManager) {
            this.notificationManager.show('info', message.trim());
        }
    }
}

// Global instance
window.EnhancedCalculatorCore = EnhancedCalculatorCore;