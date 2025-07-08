// themes/hello-elements/tool-js/init.js
// Main initialization and orchestration file

(function() {
    'use strict';

    // Global calculator instance
    let universalCalculator = null;

    // Module loading status
    const moduleStatus = {
        core: false,
        events: false,
        validator: false,
        uiRenderer: false,
        chartManager: false,
        reportGenerator: false,
        notifications: false
    };

    // Configuration
    const CONFIG = {
        DEBUG: true,
        AUTO_INIT: true,
        REQUIRED_MODULES: [
            'EnhancedCalculatorCore',
            'EventHandler',
            'CalculatorValidator',
            'UIRenderer',
            'ChartManager',
            'ReportGenerator',
            'NotificationManager'
        ],
        LOAD_TIMEOUT: 10000 // 10 seconds
    };

    // Debug logging
    function debugLog(message, data = null) {
        if (CONFIG.DEBUG) {
            console.log(`[Calculator Init] ${message}`, data || '');
        }
    }

    // Error logging
    function errorLog(message, error = null) {
        console.error(`[Calculator Error] ${message}`, error || '');
    }

    // Check if all required modules are loaded
    function checkModulesLoaded() {
        const loadedModules = [];
        const missingModules = [];

        CONFIG.REQUIRED_MODULES.forEach(moduleName => {
            if (window[moduleName]) {
                loadedModules.push(moduleName);
            } else {
                missingModules.push(moduleName);
            }
        });

        debugLog('Module check:', {
            loaded: loadedModules,
            missing: missingModules,
            total: CONFIG.REQUIRED_MODULES.length
        });

        return {
            allLoaded: missingModules.length === 0,
            loaded: loadedModules,
            missing: missingModules
        };
    }

    // Initialize the calculator system
    function initializeCalculator() {
        debugLog('Starting calculator initialization...');

        try {
            // Check if modules are loaded
            const moduleCheck = checkModulesLoaded();

            if (!moduleCheck.allLoaded) {
                errorLog('Missing required modules:', moduleCheck.missing);
                showFallbackError('Some calculator modules failed to load. Please refresh the page.');
                return false;
            }

            // Create calculator instance
            if (window.EnhancedCalculatorCore) {
                universalCalculator = new window.EnhancedCalculatorCore();

                // Initialize the system
                universalCalculator.init();

                // Make globally available
                window.universalCalculator = universalCalculator;

                debugLog('Calculator initialized successfully');

                // Trigger custom event
                document.dispatchEvent(new CustomEvent('calculatorReady', {
                    detail: { calculator: universalCalculator }
                }));

                return true;
            } else {
                errorLog('EnhancedCalculatorCore not found');
                return false;
            }

        } catch (error) {
            errorLog('Calculator initialization failed:', error);
            showFallbackError('Calculator initialization failed: ' + error.message);
            return false;
        }
    }

    // Show fallback error message
    function showFallbackError(message) {
        const container = document.getElementById('tool-results');
        if (container) {
            container.innerHTML = `
                <div class="calculator-error">
                    <div class="error-icon">⚠️</div>
                    <h3>Calculator Loading Error</h3>
                    <p>${message}</p>
                    <button onclick="location.reload()" class="retry-btn">
                        🔄 Reload Page
                    </button>
                </div>
                <style>
                    .calculator-error {
                        text-align: center;
                        padding: 40px;
                        background: #fff;
                        border-radius: 12px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                        margin: 20px auto;
                        max-width: 500px;
                    }
                    .error-icon {
                        font-size: 3rem;
                        margin-bottom: 15px;
                    }
                    .calculator-error h3 {
                        color: #e53e3e;
                        margin-bottom: 10px;
                    }
                    .calculator-error p {
                        color: #666;
                        margin-bottom: 20px;
                    }
                    .retry-btn {
                        background: #667eea;
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-weight: 600;
                    }
                    .retry-btn:hover {
                        background: #5a6fd8;
                    }
                </style>
            `;
        }
    }

    // Wait for modules to load with timeout
    function waitForModules(callback, timeout = CONFIG.LOAD_TIMEOUT) {
        const startTime = Date.now();

        function checkModules() {
            const moduleCheck = checkModulesLoaded();

            if (moduleCheck.allLoaded) {
                debugLog('All modules loaded successfully');
                callback(true);
                return;
            }

            if (Date.now() - startTime > timeout) {
                errorLog('Module loading timeout. Missing:', moduleCheck.missing);
                callback(false);
                return;
            }

            // Check again after a short delay
            setTimeout(checkModules, 100);
        }

        checkModules();
    }

    // DOM Content Loaded handler
    function onDOMContentLoaded() {
        debugLog('DOM content loaded, waiting for modules...');

        waitForModules((success) => {
            if (success) {
                if (CONFIG.AUTO_INIT) {
                    const initialized = initializeCalculator();
                    if (initialized) {
                        debugLog('Auto-initialization completed');
                    }
                } else {
                    debugLog('Auto-init disabled, manual initialization required');
                }
            } else {
                errorLog('Module loading failed, calculator cannot start');
                showFallbackError('Calculator modules failed to load within the timeout period.');
            }
        });
    }

    // Public API
    window.CalculatorInitializer = {
        // Manual initialization
        init: function() {
            debugLog('Manual initialization requested');
            return initializeCalculator();
        },

        // Get initialization status
        getStatus: function() {
            return {
                initialized: !!universalCalculator,
                modules: checkModulesLoaded(),
                calculator: universalCalculator
            };
        },

        // Reinitialize
        reinit: function() {
            debugLog('Reinitialization requested');

            // Cleanup existing instance
            if (universalCalculator && typeof universalCalculator.destroy === 'function') {
                universalCalculator.destroy();
            }

            universalCalculator = null;
            window.universalCalculator = null;

            // Initialize again
            return this.init();
        },

        // Configuration
        configure: function(options) {
            Object.assign(CONFIG, options);
            debugLog('Configuration updated:', CONFIG);
        },

        // Get configuration
        getConfig: function() {
            return { ...CONFIG };
        },

        // Debug info
        debug: function() {
            return {
                config: CONFIG,
                modules: checkModulesLoaded(),
                calculator: universalCalculator,
                version: '1.0.0',
                buildDate: new Date().toISOString()
            };
        }
    };

    // Auto-start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', onDOMContentLoaded);
    } else {
        // DOM already loaded
        setTimeout(onDOMContentLoaded, 0);
    }

    // Also try to initialize after window load as fallback
    window.addEventListener('load', function() {
        if (!universalCalculator && CONFIG.AUTO_INIT) {
            debugLog('Window loaded, attempting fallback initialization');
            setTimeout(() => {
                const status = window.CalculatorInitializer.getStatus();
                if (!status.initialized) {
                    window.CalculatorInitializer.init();
                }
            }, 500);
        }
    });

    // Global error handler for calculator-related errors
    window.addEventListener('error', function(event) {
        if (event.filename && event.filename.includes('tool-js')) {
            errorLog('JavaScript error in calculator module:', {
                message: event.message,
                filename: event.filename,
                line: event.lineno,
                column: event.colno,
                error: event.error
            });
        }
    });

    // Handle unhandled promise rejections in calculator code
    window.addEventListener('unhandledrejection', function(event) {
        if (event.reason && event.reason.stack && event.reason.stack.includes('Calculator')) {
            errorLog('Unhandled promise rejection in calculator:', event.reason);
        }
    });

    debugLog('Calculator initialization system loaded');

})();

// Backward compatibility aliases
window.initCalculator = function() {
    return window.CalculatorInitializer.init();
};

window.getCalculatorStatus = function() {
    return window.CalculatorInitializer.getStatus();
};