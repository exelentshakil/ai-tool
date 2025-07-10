// Fixed Enhanced Calculator Core with Proper Syntax

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
        console.log('🌍 Localized for:', this.countryName, '(' + this.currency + ')');

        // Load existing cache on startup
        this.loadCacheFromStorage();
    }
// Add these improved methods to your EnhancedCalculatorCore class

// Enhanced currency formatting with proper locale handling
formatCurrency(amount, currency) {
    const currencyCode = currency || this.currency;
    const numericAmount = parseFloat(amount) || 0;

    try {
        return new Intl.NumberFormat(this.locale, {
            style: 'currency',
            currency: currencyCode,
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(numericAmount);
    } catch (error) {
        // Fallback formatting with proper symbol placement
        const symbol = this.getCurrencySymbol(currencyCode);
        const formattedNumber = this.formatNumber(numericAmount);

        // Handle symbol placement based on currency
        if (currencyCode === 'EUR') {
            return formattedNumber + ' €';
        } else if (currencyCode === 'GBP') {
            return '£' + formattedNumber;
        } else {
            return symbol + formattedNumber;
        }
    }
}

// Enhanced number formatting with proper locale
formatNumber(number) {
    const numericValue = parseFloat(number) || 0;
    try {
        return new Intl.NumberFormat(this.locale, {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(numericValue);
    } catch (error) {
        // Fallback formatting
        return numericValue.toLocaleString();
    }
}

// Improved currency elements update
updateCurrencyElements() {
    // Update slider values with local currency
    const currencySliders = document.querySelectorAll('.slider-input[data-format="currency"]');
    for (let i = 0; i < currencySliders.length; i++) {
        const slider = currencySliders[i];
        const valueDisplay = document.getElementById(slider.id + '-value');
        if (valueDisplay) {
            const amount = parseFloat(slider.value) || 0;
            const formattedValue = this.formatCurrency(amount);
            valueDisplay.textContent = formattedValue;

            // Clean up any encoding issues
            valueDisplay.innerHTML = valueDisplay.textContent;
        }
    }

    // Update any currency labels
    const currencyLabels = document.querySelectorAll('[data-currency-label]');
    for (let i = 0; i < currencyLabels.length; i++) {
        const label = currencyLabels[i];
        label.textContent = this.currency;
    }
}

// Add global slider update function
updateSliderValue(slider) {
    const calculator = window.calculator || window.EnhancedCalculatorCore;
    if (!calculator) {
        console.warn('Calculator instance not found');
        return;
    }

    const valueDisplay = document.getElementById(slider.id + '-value');
    if (!valueDisplay) return;

    const value = parseFloat(slider.value) || 0;
    const format = slider.getAttribute('data-format');

    if (format === 'currency') {
        valueDisplay.textContent = calculator.formatCurrency(value);
    } else if (format === 'number') {
        valueDisplay.textContent = calculator.formatNumber(value);
    } else if (format === 'percentage') {
        valueDisplay.textContent = value + '%';
    } else {
        valueDisplay.textContent = value;
    }

    // Clean up any encoding issues
    valueDisplay.innerHTML = valueDisplay.textContent;
}

// Enhanced locale setup
getLocaleFromCountry(countryCode) {
    const locales = {
        "US": "en-US", "UK": "en-GB", "CA": "en-CA", "AU": "en-AU",
        "DE": "de-DE", "FR": "fr-FR", "ES": "es-ES", "IT": "it-IT",
        "NO": "nb-NO", "DK": "da-DK", "SE": "sv-SE", "FI": "fi-FI",
        "NL": "nl-NL", "BE": "nl-BE", "CH": "de-CH", "AT": "de-AT",
        "IE": "en-IE", "NZ": "en-NZ", "PT": "pt-PT", "BR": "pt-BR",
        "IN": "en-IN", "JP": "ja-JP", "KR": "ko-KR", "CN": "zh-CN"
    };
    return locales[countryCode] || "en-US";
}

// Improved currency symbol mapping
getCurrencySymbol(currencyCode) {
    const symbols = {
        "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CAD": "C$",
        "AUD": "A$", "CHF": "CHF", "NOK": "kr", "SEK": "kr", "DKK": "kr",
        "NZD": "NZ$", "CNY": "¥", "INR": "₹", "BRL": "R$", "KRW": "₩",
        "PLN": "zł", "CZK": "Kč", "HUF": "Ft", "RON": "lei", "BGN": "лв"
    };
    return symbols[currencyCode] || currencyCode;
}

// Enhanced UI localization update
updateUILocalization() {
    // Update form labels based on country
    const locationInput = document.querySelector('input[name="location"]');
    if (locationInput && this.countryData.local_term) {
        const formGroup = locationInput.closest('.form-group');
        if (formGroup) {
            const label = formGroup.querySelector('label');
            if (label) {
                const localTerm = this.countryData.local_term;
                label.innerHTML = label.innerHTML.replace(/ZIP code|postal code|postcode/gi, localTerm);
            }
        }
        locationInput.placeholder = 'Enter your ' + this.countryData.local_term;
    }

    // Update currency-related elements
    const currencyElements = document.querySelectorAll('[data-currency]');
    for (let i = 0; i < currencyElements.length; i++) {
        const element = currencyElements[i];
        element.textContent = element.textContent.replace(/\$|USD/g, this.currencySymbol);
    }

    // Fix any existing currency display issues
    this.fixCurrencyDisplayIssues();
}

// New method to fix currency display issues
fixCurrencyDisplayIssues() {
    // Find and fix any malformed currency displays
    const currencyDisplays = document.querySelectorAll('.slider-value, [data-format="currency"]');
    for (let i = 0; i < currencyDisplays.length; i++) {
        const element = currencyDisplays[i];
        let text = element.textContent || element.innerHTML;

        // Fix common currency encoding issues
        text = text.replace(/u20ac/gi, '€');
        text = text.replace(/&euro;/gi, '€');
        text = text.replace(/&#8364;/gi, '€');
        text = text.replace(/u00a3/gi, '£');
        text = text.replace(/&pound;/gi, '£');

        // Update the element
        element.textContent = text;
    }
}

// Add initialization method that sets up currency properly
initializeCurrencyHandling() {
    console.log('🔧 Initializing currency handling for:', this.currency);

    // Set up global slider update function
    if (!window.updateSliderValue) {
        window.updateSliderValue = (slider) => {
            this.updateSliderValue(slider);
        };
    }

    // Fix existing currency displays
    this.updateCurrencyElements();
    this.fixCurrencyDisplayIssues();

    // Set up currency change observers
    this.observeCurrencyChanges();
}

// Method to observe and fix currency changes
observeCurrencyChanges() {
    // Create a mutation observer to watch for currency display changes
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList' || mutation.type === 'characterData') {
                // Check if any currency-related elements were modified
                const target = mutation.target;
                if (target.classList && (
                    target.classList.contains('slider-value') ||
                    target.hasAttribute('data-format')
                )) {
                    setTimeout(() => this.fixCurrencyDisplayIssues(), 100);
                }
            }
        });
    });

    // Start observing
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true
    });
}

// Update the initialization to include currency handling
init() {
    try {
        this.setupModules();
        this.initializeModules();
        this.setupLocalization();
        this.initializeCurrencyHandling(); // Add this line
        console.log('✅ All calculator modules initialized successfully');
    } catch (error) {
        console.error('❌ Calculator initialization failed:', error);
        this.handleInitError(error);
    }
}

// Add method to update slider value (called by global function)
updateSliderValue(slider) {
    const valueDisplay = document.getElementById(slider.id + '-value');
    if (!valueDisplay) return;

    const value = parseFloat(slider.value) || 0;
    const format = slider.getAttribute('data-format');

    if (format === 'currency') {
        valueDisplay.textContent = this.formatCurrency(value);
    } else if (format === 'number') {
        valueDisplay.textContent = this.formatNumber(value);
    } else if (format === 'percentage') {
        valueDisplay.textContent = value + '%';
    } else {
        valueDisplay.textContent = value;
    }
}

// Add this CSS to fix currency display issues
addCurrencyFixCSS() {
    const style = document.createElement('style');
    style.textContent = `
        .slider-value {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            unicode-bidi: embed;
            direction: ltr;
        }
        
        .currency-display {
            white-space: nowrap;
        }
        
        /* Fix for euro symbol display */
        .slider-value::before {
            content: '';
        }
    `;
    document.head.appendChild(style);
}


    // Enhanced number formatting with localization
    formatDate(date, options) {
        options = options || {};
        try {
            const defaultOptions = {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            };
            const finalOptions = Object.assign(defaultOptions, options);
            return new Intl.DateTimeFormat(this.locale, finalOptions).format(new Date(date));
        } catch (error) {
            return new Date(date).toLocaleDateString();
        }
    }

    // Cache management methods
    generateCacheKey(data) {
        // Create comprehensive cache key including all possible fields
        const cacheData = {
            // Tool identification
            tool_slug: this.config.slug,
            tool_category: this.config.category,

            // Country/localization data
            country_code: this.countryData.code || 'US',
            country_name: this.countryName,
            currency: this.currency,
            language: this.language,
            locale: this.locale,

            // All form fields (sorted for consistency)
            form_data: this.sortAndCleanFormData(data),

            // Version info to invalidate cache when tool logic changes
            cache_version: this.getCacheVersion()
        };

        const dataString = JSON.stringify(cacheData);
        const hash = this.hashString(dataString);

        console.log('🔑 Generated cache key for:', {
            tool: this.config.slug,
            fields: Object.keys(data),
            country: this.countryName,
            hash: hash
        });

        return this.config.slug + ':' + hash;
    }

    // Sort and clean form data for consistent cache keys
    sortAndCleanFormData(data) {
        const cleanedData = {};
        const sortedKeys = Object.keys(data).sort();

        for (let i = 0; i < sortedKeys.length; i++) {
            const key = sortedKeys[i];
            let value = data[key];

            // Normalize values for consistent caching
            if (typeof value === 'string') {
                value = value.trim().toLowerCase();

                // Normalize currency values
                if (this.isNumericField(key)) {
                    value = this.normalizeNumericValue(value);
                }
            } else if (typeof value === 'number') {
                value = value.toString();
            } else if (typeof value === 'boolean') {
                value = value ? 'true' : 'false';
            }

            // Only include non-empty values
            if (value !== '' && value !== null && value !== undefined) {
                cleanedData[key] = value;
            }
        }

        return cleanedData;
    }

    // Check if field is numeric (for normalization)
    isNumericField(fieldName) {
        const numericFields = [
            'amount', 'revenue', 'expenses', 'income', 'coverage_amount',
            'home_price', 'down_payment', 'vehicle_price', 'loan_amount',
            'debt_amount', 'tuition_cost', 'financial_aid', 'age', 'height',
            'weight', 'years', 'employees', 'loan_term', 'gpa'
        ];
        return numericFields.includes(fieldName);
    }

    // Normalize numeric values for consistent caching
    normalizeNumericValue(value) {
        if (typeof value === 'string') {
            // Remove currency symbols, commas, spaces
            value = value.replace(/[$€£¥₹,\s]/g, '');

            // Convert to number and back to string for consistency
            const numValue = parseFloat(value);
            if (!isNaN(numValue)) {
                return numValue.toString();
            }
        }
        return value;
    }

    // Get cache version to invalidate when tool logic changes
    getCacheVersion() {
        // You can update this when tool calculation logic changes
        return '1.0.1';
    }

    // Enhanced cache key validation
    validateCacheKey(cacheKey, currentData) {
        // Regenerate key with current data and compare
        const newKey = this.generateCacheKey(currentData);
        return cacheKey === newKey;
    }

    // Get all form data from the current form
    getAllFormData() {
        const formData = {};
        const form = document.getElementById('tool-form');

        if (!form) {
            console.warn('Form not found for cache key generation');
            return formData;
        }

        // Get all form elements
        const elements = form.elements;

        for (let i = 0; i < elements.length; i++) {
            const element = elements[i];
            const name = element.name;

            if (!name) continue; // Skip elements without names

            // Handle different input types
            if (element.type === 'checkbox') {
                formData[name] = element.checked;
            } else if (element.type === 'radio') {
                if (element.checked) {
                    formData[name] = element.value;
                }
            } else if (element.tagName === 'SELECT') {
                formData[name] = element.value;
            } else if (element.type === 'range') {
                formData[name] = element.value;
            } else if (element.type === 'text' || element.type === 'number') {
                formData[name] = element.value;
            }
        }

        console.log('📝 Collected form data for cache:', formData);
        return formData;
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
            const storageKey = 'calculator_cache_' + this.config.slug;
            const stored = localStorage.getItem(storageKey);
            if (stored) {
                const parsed = JSON.parse(stored);
                const now = Date.now();

                const entries = Object.entries(parsed);
                for (let i = 0; i < entries.length; i++) {
                    const key = entries[i][0];
                    const value = entries[i][1];
                    if (now - value.timestamp <= this.cacheExpiry) {
                        this.cache.set(key, value);
                    }
                }

                console.log('📁 Loaded ' + this.cache.size + ' cached results from storage');
            }
        } catch (error) {
            console.warn('Could not load cache from storage:', error);
        }
    }

    saveCacheToStorage() {
        try {
            const cacheObject = {};
            const entries = Array.from(this.cache.entries());
            for (let i = 0; i < entries.length; i++) {
                cacheObject[entries[i][0]] = entries[i][1];
            }

            const storageKey = 'calculator_cache_' + this.config.slug;
            localStorage.setItem(storageKey, JSON.stringify(cacheObject));
        } catch (error) {
            console.warn('Could not save cache to storage:', error);
        }
    }

    clearCache() {
        this.cache.clear();
        try {
            const storageKey = 'calculator_cache_' + this.config.slug;
            localStorage.removeItem(storageKey);
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

    addCountrySpecificStyling() {
        if (!this.countryData.code) return;

        const style = document.createElement('style');
        const countryCode = this.countryData.code.toLowerCase();
        const countryFlag = this.getCountryFlag(this.countryData.code);

        style.textContent =
            '.calculator-container {' +
                '--country-accent: var(--country-color-' + countryCode + ', #007bff);' +
            '}' +

            '.form-header::before {' +
                'content: "' + countryFlag + '";' +
                'font-size: 1.5rem;' +
                'margin-right: 10px;' +
            '}' +

            '.country-indicator {' +
                'background: var(--country-accent);' +
                'color: white;' +
                'padding: 4px 12px;' +
                'border-radius: 12px;' +
                'font-size: 0.8rem;' +
                'position: absolute;' +
                'top: 10px;' +
                'right: 10px;' +
            '}';

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

    // Enhanced calculation process with comprehensive caching
    async processCalculation(formData) {
        this.isCalculating = true;
        this.uiRenderer.updateCalculateButton(true);
        this.uiRenderer.showCalculatingAnimation();

        try {
            // Convert FormData to regular object
            const data = {};
            if (formData instanceof FormData) {
                const formDataEntries = Array.from(formData.entries());
                for (let i = 0; i < formDataEntries.length; i++) {
                    data[formDataEntries[i][0]] = formDataEntries[i][1];
                }
            } else {
                // If it's already an object, use it directly
                Object.assign(data, formData);
            }

            // Get ALL current form data (including any fields not in formData)
            const allFormData = this.getAllFormData();

            // Merge form data with any additional fields
            const completeData = Object.assign({}, allFormData, data);

            // Add comprehensive localization data
            const localizedData = Object.assign({}, completeData, {
                locationData: this.countryData,
                country_data: this.countryData,
                locale: this.locale,
                currency: this.currency,
                currency_symbol: this.currencySymbol,
                country_name: this.countryName,
                language: this.language
            });

            // Generate comprehensive cache key with ALL data
            const cacheKey = this.generateCacheKey(localizedData);

            // Check cache first
            const cachedResult = this.getCachedResult(cacheKey);
            if (cachedResult) {
                console.log('⚡ Using cached result - no API call needed');
                console.log('📋 Cache data includes:', Object.keys(localizedData));
                this.handleCalculationSuccess(cachedResult, true);
                this.notificationManager.show('success', '⚡ Results loaded from cache!');
                return;
            }

            console.log('📊 Sending calculation request with complete data:', {
                tool: this.config.slug,
                dataFields: Object.keys(localizedData),
                country: this.countryName,
                cacheKey: cacheKey
            });

            // Prepare request payload
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

            // Call Flask API
            const response = await fetch(this.apiBaseUrl + '/process-tool', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestPayload)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'HTTP ' + response.status);
            }

            console.log('✅ Calculation result received and cached');

            // Cache the result with the comprehensive key
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

    // Enhanced cache debugging
    debugCacheKey(data) {
        const cacheKey = this.generateCacheKey(data);
        const cleanedData = this.sortAndCleanFormData(data);

        console.group('🔍 Cache Key Debug');
        console.log('Original data:', data);
        console.log('Cleaned data:', cleanedData);
        console.log('Country data:', this.countryData);
        console.log('Generated key:', cacheKey);
        console.log('Cache entries:', this.cache.size);
        console.groupEnd();

        return cacheKey;
    }

    // Cache management with field tracking
    getCacheStats() {
        const stats = {
            totalEntries: this.cache.size,
            maxSize: this.maxCacheSize,
            expiryTime: this.cacheExpiry / (1000 * 60 * 60), // hours
            entries: [],
            fieldCoverage: this.getCacheFieldCoverage()
        };

        const entries = Array.from(this.cache.entries());
        for (let i = 0; i < entries.length; i++) {
            const key = entries[i][0];
            const value = entries[i][1];
            const age = (Date.now() - value.timestamp) / (1000 * 60); // minutes

            // Try to extract field info from cached result
            let fieldCount = 'unknown';
            try {
                if (value.result && value.result.input_data) {
                    fieldCount = Object.keys(value.result.input_data).length;
                }
            } catch (e) {
                // Silent fail
            }

            stats.entries.push({
                key: key,
                ageMinutes: Math.round(age),
                timestamp: new Date(value.timestamp).toLocaleString(),
                fieldCount: fieldCount
            });
        }

        return stats;
    }

    // Analyze which fields are being cached
    getCacheFieldCoverage() {
        const fieldUsage = {};
        const entries = Array.from(this.cache.values());

        for (let i = 0; i < entries.length; i++) {
            try {
                if (entries[i].result && entries[i].result.input_data) {
                    const fields = Object.keys(entries[i].result.input_data);
                    for (let j = 0; j < fields.length; j++) {
                        const field = fields[j];
                        fieldUsage[field] = (fieldUsage[field] || 0) + 1;
                    }
                }
            } catch (e) {
                // Silent fail
            }
        }

        return fieldUsage;
    }

    // Clear cache for specific field combinations (useful for testing)
    clearCacheForFields(fields) {
        let removedCount = 0;
        const keysToRemove = [];

        // Find keys that might match the field combination
        const entries = Array.from(this.cache.entries());
        for (let i = 0; i < entries.length; i++) {
            const key = entries[i][0];
            const value = entries[i][1];

            try {
                if (value.result && value.result.input_data) {
                    const cachedFields = Object.keys(value.result.input_data);
                    const hasAllFields = fields.every(function(field) {
                        return cachedFields.includes(field);
                    });
                    if (hasAllFields) {
                        keysToRemove.push(key);
                    }
                }
            } catch (e) {
                // Silent fail
            }
        }

        // Remove the matching entries
        for (let i = 0; i < keysToRemove.length; i++) {
            this.cache.delete(keysToRemove[i]);
            removedCount++;
        }

        if (removedCount > 0) {
            this.saveCacheToStorage();
            console.log('🗑️ Removed ' + removedCount + ' cache entries with fields:', fields);
        }

        return removedCount;
    }

    handleCalculationSuccess(result, fromCache) {
        fromCache = fromCache || false;
        this.results = result.output;
        this.rateLimitInfo = result.user_info;

        this.uiRenderer.displayResults(result);
        this.chartManager.initializeCharts(result.output);
        this.uiRenderer.addInteractiveFeatures();

        if (fromCache) {
            let message = '⚡ Cached results loaded instantly!';
            if (this.language === 'German') {
                message = '⚡ Zwischengespeicherte Ergebnisse sofort geladen!';
            } else if (this.language === 'French') {
                message = '⚡ Résultats en cache chargés instantanément!';
            }
            this.notificationManager.show('success', message);
            this.trackAnalytics('calculation_completed_cached');
        } else {
            let message = '✅ Analysis complete! Results ready.';
            if (this.language === 'German') {
                message = '✅ Analyse abgeschlossen! Ergebnisse bereit.';
            } else if (this.language === 'French') {
                message = '✅ Analyse terminée! Résultats prêts.';
            }
            this.notificationManager.show('success', message);
            this.trackAnalytics('calculation_completed');
        }
    }

    handleCalculationError(error) {
        let message = '❌ Calculation failed: ' + error.message;
        if (this.language === 'German') {
            message = '❌ Berechnung fehlgeschlagen: ' + error.message;
        } else if (this.language === 'French') {
            message = '❌ Échec du calcul: ' + error.message;
        }

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
    trackAnalytics(event, data) {
        data = data || {};

        const enhancedData = Object.assign({}, data, {
            tool_name: this.config.base_name,
            tool_slug: this.config.slug,
            tool_category: this.config.category,
            country_code: this.countryData.code,
            country_name: this.countryName,
            currency: this.currency,
            language: this.language,
            locale: this.locale
        });

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

    // Public API methods
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
            this.reportGenerator.generateReport(format);
        }
    }

    // Enhanced utility methods
    sanitizeHTML(str) {
        const temp = document.createElement('div');
        temp.textContent = str;
        return temp.innerHTML;
    }

    showCacheStats() {
        const stats = this.getCacheStats();
        console.table(stats.entries);

        const message = 'Cache Statistics:\n' +
            '- Entries: ' + stats.totalEntries + '/' + stats.maxSize + '\n' +
            '- Expiry: ' + stats.expiryTime + ' hours\n' +
            '- Storage Used: ~' + JSON.stringify(stats).length + ' characters';

        if (this.notificationManager) {
            this.notificationManager.show('info', message);
        }
    }
}

// Global instance
window.EnhancedCalculatorCore = EnhancedCalculatorCore;