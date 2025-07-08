// themes/hello-elements/tool-js/core.js
// Enhanced Universal Calculator System - Core Module

class EnhancedCalculatorCore {
    constructor() {
        this.config = window.TOOL_CONFIG || this.getDefaultConfig();
        this.apiBaseUrl = 'https://ai.barakahsoft.com';
        this.results = null;
        this.isCalculating = false;
        this.charts = {};
        this.rateLimitInfo = null;

        // Module dependencies (will be injected)
        this.eventHandler = null;
        this.validator = null;
        this.uiRenderer = null;
        this.chartManager = null;
        this.reportGenerator = null;
        this.notificationManager = null;

        console.log('🚀 Enhanced Calculator Core initialized for:', this.config.base_name);
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
            this.handleCalculationSuccess(result);

        } catch (error) {
            console.error('❌ Calculation error:', error);
            this.handleCalculationError(error);
        } finally {
            this.isCalculating = false;
            this.uiRenderer.updateCalculateButton(false);
            this.uiRenderer.hideCalculatingAnimation();
        }
    }

    handleCalculationSuccess(result) {
        this.results = result.output;
        this.rateLimitInfo = result.user_info;

        this.uiRenderer.displayResults(result);
        this.chartManager.initializeCharts(result.output);
        this.uiRenderer.addInteractiveFeatures();

        this.notificationManager.show('success', '✅ Analysis complete! Results ready.');
        this.trackAnalytics('calculation_completed');
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