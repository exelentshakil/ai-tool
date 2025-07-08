// themes/hello-elements/tool-js/validator.js
// Input Validation Module

class CalculatorValidator {
    constructor(config) {
        this.config = config;
        this.rules = this.loadValidationRules();
        console.log('✅ Validator initialized for category:', config.category);
    }

    loadValidationRules() {
        const baseRules = {
            required: {
                test: (value) => value.trim().length > 0,
                message: 'This field is required'
            },
            number: {
                test: (value) => !isNaN(parseFloat(value)) && isFinite(value),
                message: 'Please enter a valid number'
            },
            positiveNumber: {
                test: (value) => parseFloat(value) > 0,
                message: 'Value must be greater than 0'
            },
            nonNegativeNumber: {
                test: (value) => parseFloat(value) >= 0,
                message: 'Value cannot be negative'
            },
            email: {
                test: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
                message: 'Please enter a valid email address'
            },
            phone: {
                test: (value) => /^[\+]?[1-9][\d]{0,15}$/.test(value.replace(/[\s\-\(\)]/g, '')),
                message: 'Please enter a valid phone number'
            },
            url: {
                test: (value) => {
                    try {
                        new URL(value);
                        return true;
                    } catch {
                        return false;
                    }
                },
                message: 'Please enter a valid URL'
            }
        };

        // Add category-specific rules
        return {
            ...baseRules,
            ...this.getCategorySpecificRules()
        };
    }

    getCategorySpecificRules() {
        const category = this.config.category;

        switch (category) {
            case 'finance':
            case 'business':
                return {
                    currency: {
                        test: (value) => /^\d+(\.\d{1,2})?$/.test(value),
                        message: 'Please enter a valid currency amount (e.g., 1000.50)'
                    },
                    percentage: {
                        test: (value) => {
                            const num = parseFloat(value);
                            return num >= 0 && num <= 100;
                        },
                        message: 'Percentage must be between 0 and 100'
                    },
                    interestRate: {
                        test: (value) => {
                            const num = parseFloat(value);
                            return num >= 0 && num <= 50;
                        },
                        message: 'Interest rate must be between 0% and 50%'
                    },
                    years: {
                        test: (value) => {
                            const num = parseInt(value);
                            return num >= 1 && num <= 100;
                        },
                        message: 'Years must be between 1 and 100'
                    }
                };

            case 'health':
                return {
                    age: {
                        test: (value) => {
                            const num = parseInt(value);
                            return num >= 1 && num <= 120;
                        },
                        message: 'Age must be between 1 and 120'
                    },
                    weight: {
                        test: (value) => {
                            const num = parseFloat(value);
                            return num >= 20 && num <= 1000;
                        },
                        message: 'Weight must be between 20 and 1000 lbs'
                    },
                    height: {
                        test: (value) => {
                            const num = parseFloat(value);
                            return num >= 24 && num <= 108; // inches
                        },
                        message: 'Height must be between 24 and 108 inches'
                    },
                    bmi: {
                        test: (value) => {
                            const num = parseFloat(value);
                            return num >= 10 && num <= 60;
                        },
                        message: 'BMI must be between 10 and 60'
                    }
                };

            case 'legal':
                return {
                    caseValue: {
                        test: (value) => {
                            const num = parseFloat(value);
                            return num >= 0 && num <= 10000000; // Max 10M
                        },
                        message: 'Case value must be between $0 and $10,000,000'
                    },
                    dateOfIncident: {
                        test: (value) => {
                            const date = new Date(value);
                            const now = new Date();
                            const tenYearsAgo = new Date(now.getFullYear() - 10, now.getMonth(), now.getDate());
                            return date >= tenYearsAgo && date <= now;
                        },
                        message: 'Incident date must be within the last 10 years'
                    }
                };

            default:
                return {};
        }
    }

    validateField(field) {
        const value = field.value.trim();
        const fieldType = field.type;
        const fieldName = field.name || field.id;

        // Skip validation for empty non-required fields
        if (!value && !field.required) {
            return true;
        }

        // Required field validation
        if (field.required && !this.rules.required.test(value)) {
            this.showFieldError(field, this.rules.required.message);
            return false;
        }

        // Skip other validations if field is empty and not required
        if (!value) {
            return true;
        }

        // Type-based validation
        const validationResult = this.validateByType(field, value);
        if (!validationResult.isValid) {
            this.showFieldError(field, validationResult.message);
            return false;
        }

        // Attribute-based validation
        const attributeResult = this.validateByAttributes(field, value);
        if (!attributeResult.isValid) {
            this.showFieldError(field, attributeResult.message);
            return false;
        }

        // Custom validation rules
        const customResult = this.validateCustomRules(field, value);
        if (!customResult.isValid) {
            this.showFieldError(field, customResult.message);
            return false;
        }

        // Field is valid
        this.clearFieldError(field);
        return true;
    }

    validateByType(field, value) {
        const fieldType = field.type;

        switch (fieldType) {
            case 'number':
                if (!this.rules.number.test(value)) {
                    return { isValid: false, message: this.rules.number.message };
                }

                // Check for negative numbers unless explicitly allowed
                if (!field.hasAttribute('allow-negative') && !this.rules.nonNegativeNumber.test(value)) {
                    return { isValid: false, message: this.rules.nonNegativeNumber.message };
                }
                break;

            case 'email':
                if (!this.rules.email.test(value)) {
                    return { isValid: false, message: this.rules.email.message };
                }
                break;

            case 'tel':
                if (!this.rules.phone.test(value)) {
                    return { isValid: false, message: this.rules.phone.message };
                }
                break;

            case 'url':
                if (!this.rules.url.test(value)) {
                    return { isValid: false, message: this.rules.url.message };
                }
                break;

            case 'date':
                const dateResult = this.validateDate(field, value);
                if (!dateResult.isValid) {
                    return dateResult;
                }
                break;
        }

        return { isValid: true };
    }

    validateByAttributes(field, value) {
        const num = parseFloat(value);

        // Min/Max validation for numbers
        if (field.type === 'number' && !isNaN(num)) {
            if (field.min && num < parseFloat(field.min)) {
                return {
                    isValid: false,
                    message: `Value must be at least ${field.min}`
                };
            }

            if (field.max && num > parseFloat(field.max)) {
                return {
                    isValid: false,
                    message: `Value must be no more than ${field.max}`
                };
            }
        }

        // Length validation for text fields
        if (field.type === 'text' || field.type === 'textarea') {
            if (field.minLength && value.length < parseInt(field.minLength)) {
                return {
                    isValid: false,
                    message: `Must be at least ${field.minLength} characters`
                };
            }

            if (field.maxLength && value.length > parseInt(field.maxLength)) {
                return {
                    isValid: false,
                    message: `Must be no more than ${field.maxLength} characters`
                };
            }
        }

        // Pattern validation
        if (field.pattern) {
            const pattern = new RegExp(field.pattern);
            if (!pattern.test(value)) {
                const title = field.title || 'Please match the required format';
                return { isValid: false, message: title };
            }
        }

        return { isValid: true };
    }

    validateCustomRules(field, value) {
        const className = field.className;
        const dataValidation = field.dataset.validation;

        // Check for custom validation classes
        if (className.includes('currency') && this.rules.currency) {
            if (!this.rules.currency.test(value)) {
                return { isValid: false, message: this.rules.currency.message };
            }
        }

        if (className.includes('percentage') && this.rules.percentage) {
            if (!this.rules.percentage.test(value)) {
                return { isValid: false, message: this.rules.percentage.message };
            }
        }

        // Check for data-validation attribute
        if (dataValidation && this.rules[dataValidation]) {
            if (!this.rules[dataValidation].test(value)) {
                return { isValid: false, message: this.rules[dataValidation].message };
            }
        }

        return { isValid: true };
    }

    validateDate(field, value) {
        const date = new Date(value);

        // Check if date is valid
        if (isNaN(date.getTime())) {
            return { isValid: false, message: 'Please enter a valid date' };
        }

        // Check min date
        if (field.min) {
            const minDate = new Date(field.min);
            if (date < minDate) {
                return {
                    isValid: false,
                    message: `Date must be after ${minDate.toLocaleDateString()}`
                };
            }
        }

        // Check max date
        if (field.max) {
            const maxDate = new Date(field.max);
            if (date > maxDate) {
                return {
                    isValid: false,
                    message: `Date must be before ${maxDate.toLocaleDateString()}`
                };
            }
        }

        return { isValid: true };
    }

    showFieldError(field, message) {
        let errorDiv = document.getElementById(field.name + '-error') ||
            field.parentNode.querySelector('.field-error');

        if (!errorDiv) {
            // Create error div if it doesn't exist
            errorDiv = document.createElement('div');
            errorDiv.className = 'field-error';
            errorDiv.id = field.name + '-error';

            // Insert after the field
            if (field.nextSibling) {
                field.parentNode.insertBefore(errorDiv, field.nextSibling);
            } else {
                field.parentNode.appendChild(errorDiv);
            }
        }

        errorDiv.innerHTML = '<span style="color: #e53e3e; font-size: 0.875rem;">⚠️ ' + message + '</span>';
        errorDiv.style.display = 'block';
        errorDiv.style.marginTop = '5px';

        // Add error styling to field
        field.classList.add('error');
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

    // Batch validation for forms
    validateForm(form) {
        let isValid = true;
        const errors = [];

        const fields = form.querySelectorAll('input, select, textarea');
        fields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
                errors.push({
                    field: field.name || field.id,
                    element: field,
                    message: field.parentNode.querySelector('.field-error')?.textContent || 'Invalid'
                });
            }
        });

        return {
            isValid,
            errors,
            errorCount: errors.length
        };
    }

    // Real-time validation setup
    setupRealTimeValidation(form) {
        const fields = form.querySelectorAll('input, select, textarea');

        fields.forEach(field => {
            // Debounced validation on input
            let timeout;
            field.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.validateField(field);
                }, 300);
            });

            // Immediate validation on blur
            field.addEventListener('blur', () => {
                this.validateField(field);
            });

            // Clear errors on focus
            field.addEventListener('focus', () => {
                this.clearFieldError(field);
            });
        });
    }

    // Sanitization methods
    sanitizeInput(value, type = 'text') {
        if (typeof value !== 'string') {
            value = String(value);
        }

        switch (type) {
            case 'number':
                return value.replace(/[^\d.-]/g, '');

            case 'currency':
                return value.replace(/[^\d.]/g, '');

            case 'phone':
                return value.replace(/[^\d+\-\s()]/g, '');

            case 'email':
                return value.toLowerCase().trim();

            case 'text':
            default:
                // Basic HTML sanitization
                return value
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/"/g, '&quot;')
                    .replace(/'/g, '&#x27;')
                    .trim();
        }
    }

    // Get validation summary
    getValidationSummary(form) {
        const result = this.validateForm(form);

        return {
            isValid: result.isValid,
            totalFields: form.querySelectorAll('input, select, textarea').length,
            errorCount: result.errorCount,
            errors: result.errors.map(error => ({
                field: error.field,
                message: error.message
            })),
            completionPercentage: Math.round(
                ((result.totalFields - result.errorCount) / result.totalFields) * 100
            )
        };
    }

    // Custom validation rule registration
    addCustomRule(name, testFunction, message) {
        this.rules[name] = {
            test: testFunction,
            message: message
        };
    }

    // Remove custom rule
    removeCustomRule(name) {
        delete this.rules[name];
    }

    // Get all available rules
    getAvailableRules() {
        return Object.keys(this.rules);
    }

    // Validate specific value against rule
    testRule(ruleName, value) {
        if (!this.rules[ruleName]) {
            return { isValid: false, message: 'Rule not found' };
        }

        const rule = this.rules[ruleName];
        const isValid = rule.test(value);

        return {
            isValid,
            message: isValid ? 'Valid' : rule.message
        };
    }
}

// Export for global access
window.CalculatorValidator = CalculatorValidator;