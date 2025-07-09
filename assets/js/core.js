// themes/hello-elements/tool-js/core.js
// Enhanced Universal Calculator System - Core Module

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

        // Module dependencies (will be injected)
        this.eventHandler = null;
        this.validator = null;
        this.uiRenderer = null;
        this.chartManager = null;
        this.reportGenerator = null;
        this.notificationManager = null;

        console.log('🚀 Enhanced Calculator Core initialized for:', this.config.base_name);

        // Load existing cache on startup
        this.loadCacheFromStorage();
    }

    // Cache management methods
    generateCacheKey(data) {
        // Create a unique key based on tool and input data
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
        // Simple hash function for cache keys
        let hash = 0;
        if (str.length === 0) return hash;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return Math.abs(hash).toString(36);
    }

    getCachedResult(cacheKey) {
        const cached = this.cache.get(cacheKey);
        if (!cached) return null;

        // Check if cache has expired
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
        // Implement LRU cache - remove oldest if at max size
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

                // Filter out expired entries
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
            seo_data: { title: 'Calculator' }
        };
    }

    // Initialize all modules
    init() {
        try {
            this.setupModules();
            this.initializeModules();
            console.log('✅ All calculator modules initialized successfully');
        } catch (error) {
            console.error('❌ Calculator initialization failed:', error);
            this.handleInitError(error);
        }
    }

    setupModules() {
        // Initialize modules in dependency order
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

    // Main calculation process
    async processCalculation(formData) {
        this.isCalculating = true;
        this.uiRenderer.updateCalculateButton(true);
        this.uiRenderer.showCalculatingAnimation();

        try {
            // Prepare data for API
            const data = {};
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }

            // Generate cache key
            const cacheKey = this.generateCacheKey(data);
            // Check cache first
            const cachedResult = this.getCachedResult(cacheKey);
            if (cachedResult) {
                console.log('⚡ Using cached result - no API call needed');
                this.handleCalculationSuccess(cachedResult, true); // true indicates cached
                this.notificationManager.show('success', '⚡ Results loaded from cache!');
                return;
            }

            console.log('📊 Sending calculation request:', { tool: this.config.slug, data });

            // Call Flask API
            const response = await fetch(this.apiBaseUrl + '/process-tool', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tool: this.config.slug, data: data })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'HTTP ' + response.status);
            }

            console.log('✅ Calculation result:', result);
             // Cache the result
            this.setCachedResult(cacheKey, result);

            this.handleCalculationSuccess(result, false); // false indicates fresh API call

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

        this.uiRenderer.displayResults(result);
        this.chartManager.initializeCharts(result.output);
        this.uiRenderer.addInteractiveFeatures();

        if (fromCache) {
            this.notificationManager.show('success', '⚡ Cached results loaded instantly!');
            this.trackAnalytics('calculation_completed_cached');
        } else {
            this.notificationManager.show('success', '✅ Analysis complete! Results ready.');
            this.trackAnalytics('calculation_completed');
        }
    }

    // Add cache stats method
    getCacheStats() {
        const stats = {
            totalEntries: this.cache.size,
            maxSize: this.maxCacheSize,
            expiryTime: this.cacheExpiry / (1000 * 60 * 60), // hours
            entries: []
        };

        this.cache.forEach((value, key) => {
            const age = (Date.now() - value.timestamp) / (1000 * 60); // minutes
            stats.entries.push({
                key: key,
                ageMinutes: Math.round(age),
                timestamp: new Date(value.timestamp).toLocaleString()
            });
        });

        return stats;
    }

    // Add cache management UI methods
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

    handleCalculationError(error) {
        this.notificationManager.show('error', '❌ Calculation failed: ' + error.message);
        this.uiRenderer.displayErrorResults(error);
        this.trackAnalytics('calculation_failed', { error: error.message });
    }

    // Rate limiting
    async checkRateLimit() {
        try {
            const response = await fetch(this.apiBaseUrl + '/check-limits', {
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            this.rateLimitInfo = data;
            return data.limit_info;
        } catch (error) {
            console.warn('Could not check rate limits:', error);
            return null;
        }
    }

    // Analytics tracking
    trackAnalytics(event, data = {}) {
        // Google Analytics 4 tracking
        if (typeof gtag !== 'undefined') {
            gtag('event', event, {
                tool_name: this.config.base_name,
                tool_slug: this.config.slug,
                tool_category: this.config.category,
                custom_data: JSON.stringify(data),
                ...data
            });
        }

        // Facebook Pixel tracking
        if (typeof fbq !== 'undefined') {
            fbq('trackCustom', event, {
                tool_name: this.config.base_name,
                tool_category: this.config.category,
                ...data
            });
        }

        // Custom analytics tracking
        if (window.analytics && typeof window.analytics.track === 'function') {
            window.analytics.track(event, {
                tool_name: this.config.base_name,
                tool_slug: this.config.slug,
                tool_category: this.config.category,
                ...data
            });
        }

        console.log('📊 Analytics event:', event, {
            tool: this.config.slug,
            category: this.config.category,
            ...data
        });
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

    // Utility methods
    sanitizeHTML(str) {
        const temp = document.createElement('div');
        temp.textContent = str;
        return temp.innerHTML;
    }

    formatCurrency(amount, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    }

    formatNumber(number) {
        return new Intl.NumberFormat('en-US').format(number);
    }

    formatDate(date, options = {}) {
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            ...options
        }).format(new Date(date));
    }
}

// Global instance
window.EnhancedCalculatorCore = EnhancedCalculatorCore;