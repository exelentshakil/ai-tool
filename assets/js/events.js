// themes/hello-elements/tool-js/events.js
// Event Handler Module

class EventHandler {
    constructor(core) {
        this.core = core;
        this.debounceTimers = new Map();
    }

    init() {
        this.setupFormEvents();
        this.setupButtonEvents();
        this.setupValidationEvents();
        this.setupDownloadEvents();
        this.setupKeyboardEvents();
        console.log('✅ Event handlers initialized');
    }

    setupFormEvents() {
        const form = document.getElementById('tool-form');
        if (form) {
            // Remove existing handlers
            form.removeAttribute('onsubmit');

            // Add new submit handler
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));

            // Add input change tracking
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.addEventListener('change', () => this.trackInputChange(input));
            });
        }
    }

    setupButtonEvents() {
        // Reset button
        const resetBtn = document.querySelector('button[onclick="resetForm()"]');
        if (resetBtn) {
            resetBtn.removeAttribute('onclick');
            resetBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.resetForm();
            });
        }

        // Calculate button enhancement
        const calculateBtn = document.querySelector('#tool-form button[type="submit"]');
        if (calculateBtn) {
            // Add loading state management
            calculateBtn.addEventListener('click', (e) => {
                if (this.core.isCalculating) {
                    e.preventDefault();
                    return false;
                }
            });
        }
    }

    setupValidationEvents() {
        const form = document.getElementById('tool-form');
        if (!form) return;

        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            // Real-time validation with debouncing
            input.addEventListener('input', () => this.debounceValidation(input));
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('focus', () => this.clearFieldError(input));
        });
    }

    setupDownloadEvents() {
        // Use event delegation for dynamic download buttons
        document.addEventListener('click', (e) => {
            if (e.target.id === 'download-report' || e.target.closest('#download-report')) {
                e.preventDefault();
                this.core.reportGenerator.showReportModal();
            }

            // Handle share buttons
            if (e.target.classList.contains('share-btn') || e.target.closest('.share-btn')) {
                e.preventDefault();
                this.core.shareResults();
            }

            // Handle copy buttons
            if (e.target.classList.contains('copy-section-btn')) {
                e.preventDefault();
                this.handleCopySection(e.target);
            }
        });
    }

    setupKeyboardEvents() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Enter to submit form
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                const form = document.getElementById('tool-form');
                if (form && !this.core.isCalculating) {
                    e.preventDefault();
                    form.dispatchEvent(new Event('submit'));
                }
            }

            // Escape to close modals
            if (e.key === 'Escape') {
                this.closeAllModals();
            }

            // Ctrl/Cmd + R to reset form
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                this.resetForm();
            }
        });
    }

    async handleFormSubmit(event) {
        event.preventDefault();

        if (this.core.isCalculating) {
            console.log('Calculation already in progress...');
            return;
        }

        const form = event.target;
        const formData = new FormData(form);

        // Validate form
        if (!this.validateForm(form)) {
            this.core.notificationManager.show('error', '❌ Please fill in all required fields correctly');
            this.focusFirstError(form);
            return;
        }

        // Check rate limits
        const rateLimitCheck = await this.core.checkRateLimit();
        if (rateLimitCheck && rateLimitCheck.blocked) {
            this.core.uiRenderer.showRateLimitMessage(rateLimitCheck);
            return;
        }

        // Process calculation
        await this.core.processCalculation(formData);
    }

    validateForm(form) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');

        // Clear previous errors
        form.querySelectorAll('.field-error').forEach(error => {
            error.style.display = 'none';
        });

        // Validate required fields
        requiredFields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        // Check for at least one filled field
        const allFields = form.querySelectorAll('input, select, textarea');
        const hasValue = Array.from(allFields).some(field => field.value.trim());

        if (!hasValue) {
            this.core.notificationManager.show('error', '❌ Please fill in at least one field');
            return false;
        }

        return isValid;
    }

    validateField(field) {
        if (!this.core.validator) {
            console.warn('Validator not available');
            return true;
        }

        const isValid = this.core.validator.validateField(field);

        // Update field styling
        if (isValid) {
            field.classList.remove('error');
            this.clearFieldError(field);
        } else {
            field.classList.add('error');
        }

        return isValid;
    }

    debounceValidation(field) {
        const fieldId = field.name || field.id;

        // Clear existing timer
        if (this.debounceTimers.has(fieldId)) {
            clearTimeout(this.debounceTimers.get(fieldId));
        }

        // Set new timer
        const timer = setTimeout(() => {
            this.validateField(field);
            this.debounceTimers.delete(fieldId);
        }, 300);

        this.debounceTimers.set(fieldId, timer);
    }

    clearFieldError(field) {
        const errorDiv = document.getElementById(field.name + '-error') ||
            field.parentNode.querySelector('.field-error');

        if (errorDiv) {
            errorDiv.innerHTML = '';
            errorDiv.style.display = 'none';
        }

        field.classList.remove('error');
    }

    focusFirstError(form) {
        const firstError = form.querySelector('.error');
        if (firstError) {
            firstError.focus();
            firstError.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }
    }

    trackInputChange(input) {
        this.core.trackAnalytics('input_changed', {
            field_name: input.name || input.id,
            field_type: input.type,
            has_value: !!input.value.trim()
        });
    }

    resetForm() {
        const form = document.getElementById('tool-form');
        if (!form) return;

        // Reset form data
        form.reset();

        // Clear validation errors
        form.querySelectorAll('.error').forEach(field => {
            this.clearFieldError(field);
        });

        // Clear results
        const resultsContainer = document.getElementById('tool-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = this.getResultsPlaceholder();
        }

        // Destroy charts
        if (this.core.chartManager) {
            this.core.chartManager.destroyAllCharts();
        }

        // Reset core state
        this.core.results = null;
        this.core.rateLimitInfo = null;

        this.core.notificationManager.show('info', '📝 Form reset successfully');
        this.core.trackAnalytics('form_reset');
    }

    getResultsPlaceholder() {
        return `
            <div class="results-placeholder">
                <div class="placeholder-icon">🎯</div>
                <h3>Your Results Will Appear Here</h3>
                <p>Fill out the form above and click "Calculate Now" to see your personalized results with AI insights and interactive charts.</p>
                <div class="placeholder-features">
                    <span>📊 Interactive Charts</span>
                    <span>🤖 AI Analysis</span>
                    <span>📄 Downloadable Reports</span>
                </div>
            </div>
        `;
    }

    handleCopySection(button) {
        const section = button.closest('.ai-analysis-section, .metrics-dashboard, .value-ladder-enhanced');
        if (!section) return;

        const text = section.innerText || section.textContent;

        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                this.core.notificationManager.show('success', '📋 Section copied to clipboard!');
                this.animateCopySuccess(button);
            }).catch(() => {
                this.fallbackCopy(text);
            });
        } else {
            this.fallbackCopy(text);
        }
    }

    fallbackCopy(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        document.body.appendChild(textArea);
        textArea.select();

        try {
            document.execCommand('copy');
            this.core.notificationManager.show('success', '📋 Content copied to clipboard!');
        } catch (err) {
            this.core.notificationManager.show('error', '❌ Copy failed. Please copy manually.');
        }

        document.body.removeChild(textArea);
    }

    animateCopySuccess(button) {
        const originalText = button.innerHTML;
        button.innerHTML = '✅ Copied!';
        button.style.background = 'rgba(72, 187, 120, 0.3)';

        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.background = '';
        }, 2000);
    }

    closeAllModals() {
        const modals = document.querySelectorAll('.report-modal-enhanced, .share-modal');
        modals.forEach(modal => {
            if (modal.classList.contains('show')) {
                modal.classList.remove('show');
                setTimeout(() => {
                    if (modal.parentNode) {
                        modal.remove();
                    }
                }, 300);
            }
        });
    }

    // Clean up event listeners
    destroy() {
        // Clear any remaining timers
        this.debounceTimers.forEach(timer => clearTimeout(timer));
        this.debounceTimers.clear();

        console.log('🧹 Event handlers cleaned up');
    }
}

// Export for global access
window.EventHandler = EventHandler;