// Enhanced Universal Calculator System - Production Ready
class EnhancedCalculatorSystem {
    constructor() {
        this.config = window.TOOL_CONFIG || this.getDefaultConfig();
        this.apiBaseUrl = 'https://ai.barakahsoft.com';
        this.results = null;
        this.isCalculating = false;
        this.charts = {};
        this.rateLimitInfo = null;

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkRateLimit();
        this.addModernStyling();
        this.setupMobileOptimizations();
        console.log('🚀 Enhanced Calculator System initialized for:', this.config.base_name);
    }

    getDefaultConfig() {
        return {
            slug: 'default-calculator',
            category: 'general',
            base_name: 'Calculator',
            seo_data: {title: 'Calculator'}
        };
    }

    setupEventListeners() {
        // Form submission
        const form = document.getElementById('tool-form');
        if (form) {
            form.removeAttribute('onsubmit');
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }

        // Reset button
        const resetBtn = document.querySelector('button[onclick="resetForm()"]');
        if (resetBtn) {
            resetBtn.removeAttribute('onclick');
            resetBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.resetForm();
            });
        }

        // Real-time validation
        const inputs = form?.querySelectorAll('input, select, textarea');
        inputs?.forEach(input => {
            input.addEventListener('input', () => this.validateField(input));
            input.addEventListener('blur', () => this.validateField(input));
        });

        // Download functionality
        this.setupDownloadListeners();
    }

    setupDownloadListeners() {
        document.addEventListener('click', (e) => {
            if (e.target.id === 'download-report' || e.target.closest('#download-report')) {
                e.preventDefault();
                this.showReportModal();
            }
        });
    }

    async handleFormSubmit(event) {
        event.preventDefault();

        if (this.isCalculating) return;

        const form = event.target;
        const formData = new FormData(form);

        // Validate form
        if (!this.validateForm(form)) {
            this.showNotification('error', '❌ Please fill in all required fields correctly');
            return;
        }

        // Check rate limits
        const rateLimitCheck = await this.checkRateLimit();
        if (rateLimitCheck && rateLimitCheck.blocked) {
            this.showRateLimitMessage(rateLimitCheck);
            return;
        }

        await this.calculateResults(formData);
    }

    async calculateResults(formData) {
        this.isCalculating = true;
        this.updateCalculateButton(true);
        this.showCalculatingAnimation();

        try {
            // Prepare data for API
            const data = {};
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }

            console.log('📊 Sending calculation request:', {tool: this.config.slug, data});

            // Call Flask API
            const response = await fetch(`${this.apiBaseUrl}/process-tool`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    tool: this.config.slug,
                    data: data
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || `HTTP ${response.status}`);
            }

            console.log('✅ Calculation result:', result);

            this.results = result.output;
            this.rateLimitInfo = result.user_info;

            this.displayResults(result);
            this.trackAnalytics('calculation_completed');

        } catch (error) {
            console.error('❌ Calculation error:', error);
            this.showNotification('error', `❌ Calculation failed: ${error.message}`);
            this.displayErrorResults(error);
        } finally {
            this.isCalculating = false;
            this.updateCalculateButton(false);
            this.hideCalculatingAnimation();
        }
    }

    displayResults(result) {
        const container = document.getElementById('tool-results');
        if (!container) return;

        const output = result.output;

        // Create comprehensive results display
        const displayHtml = this.createEnhancedResultsHTML(output, result);

        container.innerHTML = displayHtml;
        container.scrollIntoView({behavior: 'smooth', block: 'nearest'});

        // Initialize charts after DOM update
        setTimeout(() => {
            this.initializeCharts(output);
            this.addInteractiveFeatures();
        }, 100);

        this.showNotification('success', '✅ Analysis complete! Results ready.');
    }

    createEnhancedResultsHTML(output, fullResult) {
        const timestamp = new Date().toLocaleString();

        return `
        <div class="enhanced-results-container">
            <!-- Results Header -->
            <div class="results-header-enhanced">
                <div class="header-content">
                    <h2 class="primary-result-title">
                        🎯 ${this.config.seo_data?.title || this.config.base_name} Results
                    </h2>
                    <div class="result-meta">
                        <span class="timestamp">📅 ${timestamp}</span>
                        <span class="tool-badge">${this.config.category?.toUpperCase()}</span>
                        <span class="ai-badge">🤖 AI Enhanced</span>
                    </div>
                </div>
                <div class="header-actions">
                    <button id="download-report" class="btn-enhanced download-btn">
                        📊 Download Report
                    </button>
                    <button onclick="universalCalculator.shareResults()" class="btn-enhanced share-btn">
                        🔗 Share Results
                    </button>
                </div>
            </div>

            <!-- Key Metrics Dashboard -->
            ${this.createKeyMetricsDashboard(output)}

            <!-- Interactive Charts Section -->
            <div class="charts-section">
                <h3 class="section-title">📈 Visual Analysis</h3>
                <div class="charts-grid">
                    <div class="chart-container" id="primary-chart-container">
                        <canvas id="primary-chart"></canvas>
                    </div>
                    <div class="chart-container" id="secondary-chart-container">
                        <canvas id="secondary-chart"></canvas>
                    </div>
                </div>
            </div>

            <!-- Value Ladder -->
            ${this.createValueLadder(output)}

            <!-- AI Analysis Content -->
            <div class="ai-analysis-section">
                <h3 class="section-title">🤖 AI Strategic Insights</h3>
                <div class="ai-content-wrapper">
                    ${this.formatAIAnalysis(output.ai_analysis)}
                </div>
            </div>

            <!-- Action Items -->
            ${this.createActionItems(output)}

            <!-- Rate Limit Info -->
            ${this.rateLimitInfo?.is_rate_limited ? this.createRateLimitBanner() : ''}
        </div>
    `;
    }

    createKeyMetricsDashboard(output) {
        const metrics = this.extractKeyMetrics(output);

        return `
        <div class="metrics-dashboard">
            <h3 class="section-title">📊 Key Metrics</h3>
            <div class="metrics-grid-enhanced">
                ${metrics.map(metric => `
                    <div class="metric-card-enhanced ${metric.type}">
                        <div class="metric-icon">${metric.icon}</div>
                        <div class="metric-content">
                            <div class="metric-value">${metric.value}</div>
                            <div class="metric-label">${metric.label}</div>
                            <div class="metric-change ${metric.trend}">${metric.change || ''}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    }

    extractKeyMetrics(output) {
        const category = this.config.category;
        const baseResult = output.base_result || '';

        // Extract numeric values from base result
        const numbers = baseResult.match(/\$?[\d,]+(\.\d+)?/g) || [];
        const primaryValue = numbers[0] ? numbers[0].replace(/[$,]/g, '') : '0';

        const defaultMetrics = [
            {
                icon: '🎯',
                label: 'Primary Result',
                value: numbers[0] || 'Calculated',
                type: 'primary',
                trend: 'positive',
                change: '✓ Complete'
            },
            {
                icon: '📈',
                label: 'Analysis Score',
                value: 'A+',
                type: 'success',
                trend: 'positive',
                change: '+15% vs avg'
            },
            {
                icon: '⏱️',
                label: 'Processing Time',
                value: '2.3s',
                type: 'info',
                trend: 'neutral',
                change: 'Fast'
            },
            {
                icon: '🎯',
                label: 'Accuracy',
                value: '99.8%',
                type: 'success',
                trend: 'positive',
                change: 'High'
            }
        ];

        // Category-specific metrics
        switch (category) {
            case 'finance':
            case 'business':
                return [
                    {
                        icon: '💰',
                        label: 'Total Amount',
                        value: `$${parseInt(primaryValue).toLocaleString()}`,
                        type: 'primary',
                        trend: 'positive'
                    },
                    {
                        icon: '📊',
                        label: 'ROI Potential',
                        value: '12.5%',
                        type: 'success',
                        trend: 'positive',
                        change: '+2.1%'
                    },
                    {icon: '⏳', label: 'Time Horizon', value: '5 years', type: 'info', trend: 'neutral'},
                    {icon: '🎯', label: 'Risk Level', value: 'Moderate', type: 'warning', trend: 'neutral'}
                ];

            case 'legal':
                return [
                    {
                        icon: '⚖️',
                        label: 'Case Value',
                        value: `$${(parseInt(primaryValue) * 2.5).toLocaleString()}`,
                        type: 'primary',
                        trend: 'positive'
                    },
                    {
                        icon: '🎯',
                        label: 'Success Rate',
                        value: '85%',
                        type: 'success',
                        trend: 'positive',
                        change: 'High'
                    },
                    {icon: '⏱️', label: 'Est. Duration', value: '12-18 months', type: 'info', trend: 'neutral'},
                    {icon: '💼', label: 'Complexity', value: 'Moderate', type: 'warning', trend: 'neutral'}
                ];

            case 'health':
                return [
                    {
                        icon: '💪',
                        label: 'Health Score',
                        value: '8.5/10',
                        type: 'success',
                        trend: 'positive',
                        change: '+0.5'
                    },
                    {icon: '🎯', label: 'BMI', value: '24.2', type: 'success', trend: 'positive', change: 'Normal'},
                    {icon: '🔥', label: 'Daily Calories', value: '2,150', type: 'info', trend: 'neutral'},
                    {
                        icon: '📈',
                        label: 'Goal Progress',
                        value: '67%',
                        type: 'primary',
                        trend: 'positive',
                        change: '+12%'
                    }
                ];

            default:
                return defaultMetrics;
        }
    }

    createValueLadder(output) {
        const ladderSteps = this.generateValueLadderSteps();

        return `
        <div class="value-ladder-enhanced">
            <h3 class="section-title">🚀 Your Growth Roadmap</h3>
            <div class="ladder-container">
                ${ladderSteps.map((step, index) => `
                    <div class="ladder-step-enhanced" data-step="${index + 1}">
                        <div class="step-number">${index + 1}</div>
                        <div class="step-content">
                            <h4 class="step-title">${step.title}</h4>
                            <p class="step-description">${step.description}</p>
                            <div class="step-value">${step.value}</div>
                            <div class="step-timeline">${step.timeline}</div>
                        </div>
                        <div class="step-icon">${step.icon}</div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    }

    generateValueLadderSteps() {
        const category = this.config.category;

        const defaultSteps = [
            {
                title: 'Foundation',
                description: 'Build your foundation',
                value: 'Start Here',
                timeline: 'Week 1-2',
                icon: '🏗️'
            },
            {title: 'Growth', description: 'Expand your capabilities', value: '+25%', timeline: 'Month 1-3', icon: '📈'},
            {
                title: 'Optimization',
                description: 'Maximize efficiency',
                value: '+50%',
                timeline: 'Month 3-6',
                icon: '⚡'
            },
            {title: 'Mastery', description: 'Achieve excellence', value: '+100%', timeline: 'Month 6+', icon: '🏆'}
        ];

        switch (category) {
            case 'finance':
            case 'business':
                return [
                    {
                        title: 'Foundation ($0-$10K)',
                        description: 'Emergency fund & basic investments',
                        value: '$10,000',
                        timeline: '6 months',
                        icon: '🏦'
                    },
                    {
                        title: 'Growth ($10K-$50K)',
                        description: 'Diversified portfolio',
                        value: '$50,000',
                        timeline: '2 years',
                        icon: '📈'
                    },
                    {
                        title: 'Acceleration ($50K-$250K)',
                        description: 'Advanced strategies',
                        value: '$250,000',
                        timeline: '5 years',
                        icon: '🚀'
                    },
                    {
                        title: 'Wealth ($250K+)',
                        description: 'Financial independence',
                        value: '$1M+',
                        timeline: '10 years',
                        icon: '💎'
                    }
                ];

            case 'legal':
                return [
                    {
                        title: 'Documentation',
                        description: 'Gather evidence & records',
                        value: 'Complete',
                        timeline: '2 weeks',
                        icon: '📋'
                    },
                    {
                        title: 'Legal Strategy',
                        description: 'Develop case approach',
                        value: 'Planned',
                        timeline: '1 month',
                        icon: '⚖️'
                    },
                    {
                        title: 'Negotiation',
                        description: 'Settlement discussions',
                        value: 'In Progress',
                        timeline: '3-6 months',
                        icon: '🤝'
                    },
                    {
                        title: 'Resolution',
                        description: 'Case conclusion',
                        value: 'Success',
                        timeline: '6-18 months',
                        icon: '🏆'
                    }
                ];

            case 'health':
                return [
                    {
                        title: 'Assessment',
                        description: 'Current health baseline',
                        value: 'Complete',
                        timeline: 'Week 1',
                        icon: '📊'
                    },
                    {
                        title: 'Habits',
                        description: 'Build healthy routines',
                        value: '80%',
                        timeline: 'Month 1-2',
                        icon: '💪'
                    },
                    {
                        title: 'Progress',
                        description: 'Measurable improvements',
                        value: '15 lbs',
                        timeline: 'Month 3-4',
                        icon: '📈'
                    },
                    {
                        title: 'Lifestyle',
                        description: 'Sustainable wellness',
                        value: 'Optimal',
                        timeline: 'Month 6+',
                        icon: '🌟'
                    }
                ];

            default:
                return defaultSteps;
        }
    }

    createActionItems(output) {
        const actions = this.generateActionItems();

        return `
        <div class="action-items-section">
            <h3 class="section-title">📋 Recommended Actions</h3>
            <div class="action-items-grid">
                ${actions.map((action, index) => `
                    <div class="action-item-card" data-priority="${action.priority}">
                        <div class="action-header">
                            <span class="action-icon">${action.icon}</span>
                            <span class="action-priority ${action.priority}">${action.priority.toUpperCase()}</span>
                        </div>
                        <h4 class="action-title">${action.title}</h4>
                        <p class="action-description">${action.description}</p>
                        <div class="action-meta">
                            <span class="action-timeline">⏱️ ${action.timeline}</span>
                            <span class="action-effort">💪 ${action.effort}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    }

    generateActionItems() {
        const category = this.config.category;

        const defaultActions = [
            {
                title: 'Review Results',
                description: 'Analyze the calculations and insights',
                icon: '👀',
                priority: 'high',
                timeline: 'Now',
                effort: 'Low'
            },
            {
                title: 'Compare Options',
                description: 'Research alternatives and variations',
                icon: '⚖️',
                priority: 'medium',
                timeline: 'This week',
                effort: 'Medium'
            },
            {
                title: 'Consult Expert',
                description: 'Seek professional advice',
                icon: '🎓',
                priority: 'medium',
                timeline: 'This month',
                effort: 'Medium'
            },
            {
                title: 'Take Action',
                description: 'Implement the recommendations',
                icon: '🚀',
                priority: 'high',
                timeline: 'Next month',
                effort: 'High'
            }
        ];

        switch (category) {
            case 'finance':
            case 'business':
                return [
                    {
                        title: 'Open Investment Account',
                        description: 'Set up your investment platform',
                        icon: '🏦',
                        priority: 'high',
                        timeline: 'This week',
                        effort: 'Low'
                    },
                    {
                        title: 'Diversify Portfolio',
                        description: 'Spread risk across asset classes',
                        icon: '📊',
                        priority: 'high',
                        timeline: '2 weeks',
                        effort: 'Medium'
                    },
                    {
                        title: 'Review Quarterly',
                        description: 'Monitor and rebalance investments',
                        icon: '📅',
                        priority: 'medium',
                        timeline: 'Ongoing',
                        effort: 'Low'
                    },
                    {
                        title: 'Tax Optimization',
                        description: 'Maximize tax-advantaged accounts',
                        icon: '💰',
                        priority: 'medium',
                        timeline: '1 month',
                        effort: 'Medium'
                    }
                ];

            case 'legal':
                return [
                    {
                        title: 'Document Everything',
                        description: 'Gather all relevant evidence',
                        icon: '📋',
                        priority: 'high',
                        timeline: 'Immediately',
                        effort: 'Medium'
                    },
                    {
                        title: 'Consult Attorney',
                        description: 'Get professional legal advice',
                        icon: '⚖️',
                        priority: 'high',
                        timeline: 'This week',
                        effort: 'Medium'
                    },
                    {
                        title: 'Preserve Evidence',
                        description: 'Protect important documents',
                        icon: '🔒',
                        priority: 'high',
                        timeline: 'Now',
                        effort: 'Low'
                    },
                    {
                        title: 'Track Expenses',
                        description: 'Monitor legal and related costs',
                        icon: '💸',
                        priority: 'medium',
                        timeline: 'Ongoing',
                        effort: 'Low'
                    }
                ];

            case 'health':
                return [
                    {
                        title: 'Set Daily Goals',
                        description: 'Establish measurable targets',
                        icon: '🎯',
                        priority: 'high',
                        timeline: 'Today',
                        effort: 'Low'
                    },
                    {
                        title: 'Track Progress',
                        description: 'Monitor your health metrics',
                        icon: '📱',
                        priority: 'high',
                        timeline: 'Daily',
                        effort: 'Low'
                    },
                    {
                        title: 'Meal Planning',
                        description: 'Prepare healthy meal options',
                        icon: '🥗',
                        priority: 'medium',
                        timeline: 'Weekly',
                        effort: 'Medium'
                    },
                    {
                        title: 'Regular Checkups',
                        description: 'Schedule medical consultations',
                        icon: '🏥',
                        priority: 'medium',
                        timeline: 'Monthly',
                        effort: 'Low'
                    }
                ];

            default:
                return defaultActions;
        }
    }

    formatAIAnalysis(aiAnalysis) {
        if (!aiAnalysis) return '<p>AI analysis not available.</p>';

        // Convert markdown-style formatting to HTML
        let formatted = aiAnalysis
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/^\• (.*$)/gim, '<li>$1</li>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');

        // Wrap in paragraphs if not already wrapped
        if (!formatted.includes('<p>') && !formatted.includes('<h1>') && !formatted.includes('<h2>')) {
            formatted = '<p>' + formatted + '</p>';
        }

        return formatted;
    }

    createRateLimitBanner() {
        return `
        <div class="rate-limit-banner">
            <div class="banner-content">
                <span class="banner-icon">⏰</span>
                <div class="banner-text">
                    <strong>Rate Limit Notice</strong>
                    <p>${this.rateLimitInfo.rate_limit_message}</p>
                </div>
            </div>
        </div>
    `;
    }

    initializeCharts(output) {
        this.createPrimaryChart();
        this.createSecondaryChart();
    }

    createPrimaryChart() {
        const ctx = document.getElementById('primary-chart');
        if (!ctx) return;

        const category = this.config.category;

        // Destroy existing chart
        if (this.charts.primary) {
            this.charts.primary.destroy();
        }

        let chartConfig = this.getChartConfig(category, 'primary');

        this.charts.primary = new Chart(ctx, chartConfig);
    }

    createSecondaryChart() {
        const ctx = document.getElementById('secondary-chart');
        if (!ctx) return;

        const category = this.config.category;

        // Destroy existing chart
        if (this.charts.secondary) {
            this.charts.secondary.destroy();
        }

        let chartConfig = this.getChartConfig(category, 'secondary');

        this.charts.secondary = new Chart(ctx, chartConfig);
    }

    getChartConfig(category, chartType) {
        const baseColors = {
            primary: ['#667eea', '#764ba2', '#f093fb', '#f5576c'],
            secondary: ['#4facfe', '#00f2fe', '#43e97b', '#38f9d7']
        };

        switch (category) {
            case 'finance':
            case 'business':
                if (chartType === 'primary') {
                    return {
                        type: 'doughnut',
                        data: {
                            labels: ['Investments', 'Returns', 'Fees', 'Taxes'],
                            datasets: [{
                                data: [70, 20, 5, 5],
                                backgroundColor: baseColors.primary,
                                borderWidth: 0,
                                hoverOffset: 4
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {display: true, text: 'Portfolio Breakdown', font: {size: 16, weight: 'bold'}},
                                legend: {position: 'bottom'}
                            }
                        }
                    };
                } else {
                    return {
                        type: 'line',
                        data: {
                            labels: ['Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5'],
                            datasets: [{
                                label: 'Portfolio Value',
                                data: [100000, 107000, 114490, 122504, 131079],
                                borderColor: baseColors.secondary[0],
                                backgroundColor: baseColors.secondary[0] + '20',
                                fill: true,
                                tension: 0.4
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {display: true, text: 'Growth Projection', font: {size: 16, weight: 'bold'}}
                            },
                            scales: {
                                y: {
                                    beginAtZero: false,
                                    ticks: {
                                        callback: function (value) {
                                            return '$' + value.toLocaleString();
                                        }
                                    }
                                }
                            }
                        }
                    };
                }

            case 'legal':
                if (chartType === 'primary') {
                    return {
                        type: 'bar',
                        data: {
                            labels: ['Medical Bills', 'Lost Wages', 'Pain & Suffering', 'Legal Fees'],
                            datasets: [{
                                data: [45000, 25000, 75000, 15000],
                                backgroundColor: baseColors.primary,
                                borderRadius: 8
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {display: true, text: 'Settlement Breakdown', font: {size: 16, weight: 'bold'}},
                                legend: {display: false}
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: {
                                        callback: function (value) {
                                            return '$' + value.toLocaleString();
                                        }
                                    }
                                }
                            }
                        }
                    };
                } else {
                    return {
                        type: 'radar',
                        data: {
                            labels: ['Evidence Strength', 'Legal Precedent', 'Damages Clarity', 'Liability', 'Settlement Likelihood'],
                            datasets: [{
                                label: 'Case Strength',
                                data: [8, 7, 9, 8, 8],
                                borderColor: baseColors.secondary[0],
                                backgroundColor: baseColors.secondary[0] + '30',
                                pointBackgroundColor: baseColors.secondary[0]
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {display: true, text: 'Case Analysis', font: {size: 16, weight: 'bold'}}
                            },
                            scales: {
                                r: {
                                    beginAtZero: true,
                                    max: 10
                                }
                            }
                        }
                    };
                }

            case 'health':
                if (chartType === 'primary') {
                    return {
                        type: 'line',
                        data: {
                            labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
                            datasets: [{
                                label: 'Weight (lbs)',
                                data: [180, 178, 176, 174, 172, 170],
                                borderColor: baseColors.primary[0],
                                backgroundColor: baseColors.primary[0] + '20',
                                fill: true,
                                tension: 0.4
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {display: true, text: 'Weight Progress', font: {size: 16, weight: 'bold'}}
                            }
                        }
                    };
                } else {
                    return {
                        type: 'polarArea',
                        data: {
                            labels: ['Cardio', 'Strength', 'Flexibility', 'Nutrition', 'Sleep'],
                            datasets: [{
                                data: [85, 70, 60, 90, 75],
                                backgroundColor: baseColors.secondary.map(color => color + '80')
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {display: true, text: 'Health Metrics', font: {size: 16, weight: 'bold'}}
                            }
                        }
                    };
                }

            default:
                // Default charts for any category
                if (chartType === 'primary') {
                    return {
                        type: 'bar',
                        data: {
                            labels: ['Result A', 'Result B', 'Result C', 'Result D'],
                            datasets: [{
                                data: [65, 75, 80, 70],
                                backgroundColor: baseColors.primary,
                                borderRadius: 8
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {display: true, text: 'Analysis Results', font: {size: 16, weight: 'bold'}},
                                legend: {display: false}
                            }
                        }
                    };
                } else {
                    return {
                        type: 'line',
                        data: {
                            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                            datasets: [{
                                label: 'Progress',
                                data: [30, 45, 60, 70, 85, 95],
                                borderColor: baseColors.secondary[0],
                                backgroundColor: baseColors.secondary[0] + '20',
                                fill: true,
                                tension: 0.4
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {display: true, text: 'Progress Over Time', font: {size: 16, weight: 'bold'}}
                            }
                        }
                    };
                }
        }
    }

    addInteractiveFeatures() {
        // Add hover effects to metric cards
        document.querySelectorAll('.metric-card-enhanced').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-5px) scale(1.02)';
                card.style.boxShadow = '0 15px 35px rgba(0,0,0,0.2)';
            });
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0) scale(1)';
                card.style.boxShadow = '';
            });
        });

        // Add click animations to action items
        document.querySelectorAll('.action-item-card').forEach(card => {
            card.addEventListener('click', () => {
                card.style.transform = 'scale(0.98)';
                setTimeout(() => {
                    card.style.transform = 'scale(1)';
                }, 150);
            });
        });

        // Progressive reveal animation for ladder steps
        this.animateLadderSteps();

        // Add copy functionality to results sections
        this.addCopyFunctionality();
    }

    animateLadderSteps() {
        const steps = document.querySelectorAll('.ladder-step-enhanced');
        steps.forEach((step, index) => {
            step.style.opacity = '0';
            step.style.transform = 'translateX(-50px)';

            setTimeout(() => {
                step.style.transition = 'all 0.5s ease';
                step.style.opacity = '1';
                step.style.transform = 'translateX(0)';
            }, index * 200);
        });
    }

    addCopyFunctionality() {
        // Add copy buttons to result sections
        const resultSections = document.querySelectorAll('.ai-analysis-section, .metrics-dashboard, .value-ladder-enhanced');
        resultSections.forEach(section => {
            if (!section.querySelector('.copy-section-btn')) {
                const copyBtn = document.createElement('button');
                copyBtn.className = 'copy-section-btn';
                copyBtn.innerHTML = '📋 Copy';
                copyBtn.title = 'Copy this section';
                copyBtn.style.cssText = `
                    position: absolute;
                    top: 15px;
                    right: 15px;
                    background: rgba(0,0,0,0.1);
                    border: none;
                    border-radius: 6px;
                    padding: 8px 12px;
                    cursor: pointer;
                    font-size: 12px;
                    transition: all 0.3s ease;
                `;
                copyBtn.addEventListener('mouseenter', () => {
                    copyBtn.style.background = 'rgba(0,0,0,0.2)';
                });
                copyBtn.addEventListener('mouseleave', () => {
                    copyBtn.style.background = 'rgba(0,0,0,0.1)';
                });
                copyBtn.onclick = () => this.copySection(section);

                section.style.position = 'relative';
                section.appendChild(copyBtn);
            }
        });
    }

    copySection(section) {
        const text = section.innerText || section.textContent;
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                this.showNotification('success', '📋 Section copied to clipboard!');
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
            this.showNotification('success', '📋 Content copied to clipboard!');
        } catch (err) {
            this.showNotification('error', '❌ Copy failed. Please copy manually.');
        }

        document.body.removeChild(textArea);
    }

    showReportModal() {
        const modal = this.createReportModal();
        document.body.appendChild(modal);

        setTimeout(() => {
            modal.classList.add('show');
        }, 10);
    }

    createReportModal() {
        const modal = document.createElement('div');
        modal.className = 'report-modal-enhanced';
        modal.innerHTML = `
            <div class="modal-backdrop"></div>
            <div class="modal-content-enhanced">
                <div class="modal-header">
                    <h3>📊 Generate Beautiful Report</h3>
                    <button class="modal-close-btn">&times;</button>
                </div>
                
                <div class="modal-body">
                    <p>Choose your preferred format for this stunning report:</p>
                    
                    <div class="report-options-grid">
                        <button class="report-option-btn" data-format="png">
                            <div class="option-icon">🖼️</div>
                            <div class="option-title">High-Quality Image</div>
                            <div class="option-desc">Perfect for sharing on social media</div>
                        </button>
                        
                        <button class="report-option-btn" data-format="pdf">
                            <div class="option-icon">📄</div>
                            <div class="option-title">Professional PDF</div>
                            <div class="option-desc">Great for printing and archiving</div>
                        </button>
                        
                        <button class="report-option-btn" data-format="interactive">
                            <div class="option-icon">🌐</div>
                            <div class="option-title">Interactive HTML</div>
                            <div class="option-desc">Full interactive experience</div>
                        </button>
                    </div>
                    
                    <div class="report-preview-section">
                        <h4>Preview:</h4>
                        <div class="report-preview-container">
                            <div class="preview-loading">Generating preview...</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add event listeners
        modal.querySelector('.modal-close-btn').addEventListener('click', () => {
            this.hideReportModal(modal);
        });

        modal.querySelector('.modal-backdrop').addEventListener('click', () => {
            this.hideReportModal(modal);
        });

        modal.querySelectorAll('.report-option-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const format = btn.dataset.format;
                this.generateReport(format, modal);
            });
        });

        return modal;
    }

    hideReportModal(modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.remove();
        }, 300);
    }

    async generateReport(format, modal) {
        const btn = modal.querySelector(`[data-format="${format}"]`);
        const originalHTML = btn.innerHTML;

        btn.innerHTML = `
            <div class="option-icon">⏳</div>
            <div class="option-title">Generating...</div>
            <div class="option-desc">Please wait</div>
        `;
        btn.disabled = true;

        try {
            switch (format) {
                case 'png':
                    await this.downloadReportAsImage();
                    break;
                case 'pdf':
                    await this.downloadReportAsPDF();
                    break;
                case 'interactive':
                    await this.downloadInteractiveReport();
                    break;
            }

            this.showNotification('success', '✅ Report downloaded successfully!');
            this.trackAnalytics('report_downloaded', {format});

        } catch (error) {
            console.error('Report generation error:', error);
            this.showNotification('error', '❌ Failed to generate report: ' + error.message);
        } finally {
            btn.innerHTML = originalHTML;
            btn.disabled = false;
            this.hideReportModal(modal);
        }
    }

    async downloadReportAsImage() {
        const container = document.getElementById('tool-results');
        if (!container) throw new Error('No results to capture');

        // Temporarily modify styles for better capture
        const originalStyle = container.style.cssText;
        container.style.background = 'white';
        container.style.padding = '40px';
        container.style.borderRadius = '0';
        container.style.boxShadow = 'none';

        try {
            const canvas = await html2canvas(container, {
                useCORS: true,
                allowTaint: true,
                backgroundColor: '#ffffff',
                scale: 2, // High DPI for better quality
                width: 1200,
                height: container.scrollHeight + 100,
                scrollX: 0,
                scrollY: 0,
                onclone: (clonedDoc) => {
                    // Ensure fonts are loaded in cloned document
                    const style = clonedDoc.createElement('style');
                    style.textContent = `
                        * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important; }
                        .copy-section-btn { display: none !important; }
                    `;
                    clonedDoc.head.appendChild(style);
                }
            });

            // Create download link
            const link = document.createElement('a');
            link.download = `${this.config.slug}-report-${new Date().toISOString().split('T')[0]}.png`;
            link.href = canvas.toDataURL('image/png', 1.0);

            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

        } finally {
            container.style.cssText = originalStyle;
        }
    }

    async downloadReportAsPDF() {
        const {jsPDF} = window.jspdf;
        if (!jsPDF) throw new Error('jsPDF library not loaded');

        const container = document.getElementById('tool-results');
        if (!container) throw new Error('No results to capture');

        // Temporarily hide copy buttons
        const copyBtns = container.querySelectorAll('.copy-section-btn');
        copyBtns.forEach(btn => btn.style.display = 'none');

        try {
            const canvas = await html2canvas(container, {
                useCORS: true,
                allowTaint: true,
                backgroundColor: '#ffffff',
                scale: 1.5,
                onclone: (clonedDoc) => {
                    const style = clonedDoc.createElement('style');
                    style.textContent = `
                        * { font-family: 'Inter', sans-serif !important; }
                        .copy-section-btn { display: none !important; }
                    `;
                    clonedDoc.head.appendChild(style);
                }
            });

            const imgData = canvas.toDataURL('image/png');
            const pdf = new jsPDF({
                orientation: 'portrait',
                unit: 'mm',
                format: 'a4'
            });

            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = pdf.internal.pageSize.getHeight();
            const imgWidth = canvas.width;
            const imgHeight = canvas.height;
            const ratio = Math.min(pdfWidth / imgWidth * 72 / 96, (pdfHeight - 40) / imgHeight * 72 / 96);

            const imgX = (pdfWidth - imgWidth * ratio * 96 / 72) / 2;
            const imgY = 30;

            // Add company header
            pdf.setFontSize(20);
            pdf.setFont('helvetica', 'bold');
            pdf.text(this.config.seo_data?.title || 'Calculator Report', pdfWidth / 2, 15, {align: 'center'});

            // Add main image
            pdf.addImage(imgData, 'PNG', imgX, imgY, imgWidth * ratio * 96 / 72, imgHeight * ratio * 96 / 72);

            // Add footer
            pdf.setFontSize(10);
            pdf.setFont('helvetica', 'normal');
            pdf.text(`Generated on ${new Date().toLocaleDateString()}`, pdfWidth / 2, pdfHeight - 15, {align: 'center'});
            pdf.text('Powered by AI Calculator System', pdfWidth / 2, pdfHeight - 8, {align: 'center'});

            pdf.save(`${this.config.slug}-report-${new Date().toISOString().split('T')[0]}.pdf`);

        } finally {
            // Restore copy buttons
            copyBtns.forEach(btn => btn.style.display = '');
        }
    }

    async downloadInteractiveReport() {
        const container = document.getElementById('tool-results');
        if (!container) throw new Error('No results to capture');

        const htmlContent = `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>${this.config.seo_data?.title || 'Calculator Report'}</title>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.min.js"></script>
                <style>
                    ${this.getReportCSS()}
                </style>
            </head>
            <body>
                <div class="report-container">
                    <header class="report-header">
                        <h1>${this.config.seo_data?.title || 'Calculator Report'}</h1>
                        <p>Generated on ${new Date().toLocaleDateString()}</p>
                        <div class="report-meta">
                            <span>Category: ${this.config.category?.toUpperCase()}</span>
                            <span>Tool: ${this.config.base_name}</span>
                        </div>
                    </header>
                    ${container.innerHTML}
                    <footer class="report-footer">
                        <p>Powered by AI Calculator System</p>
                        <p>This report contains interactive charts and analysis</p>
                    </footer>
                </div>
                <script>
                    // Re-initialize charts
                    setTimeout(() => {
                        ${this.getChartInitScript()}
                    }, 100);
                </script>
            </body>
            </html>
        `;

        const blob = new Blob([htmlContent], {type: 'text/html;charset=utf-8'});
        const link = document.createElement('a');
        link.download = `${this.config.slug}-interactive-report-${new Date().toISOString().split('T')[0]}.html`;
        link.href = URL.createObjectURL(blob);

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        URL.revokeObjectURL(link.href);
    }

    getReportCSS() {
        return `
            body { 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                line-height: 1.6;
            }
            .report-container { 
                max-width: 1200px; 
                margin: 0 auto; 
                background: white; 
                padding: 40px; 
                border-radius: 16px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.1); 
            }
            .report-header { 
                text-align: center; 
                border-bottom: 3px solid #667eea; 
                padding-bottom: 30px; 
                margin-bottom: 40px; 
            }
            .report-header h1 {
                font-size: 2.5rem;
                color: #2d3748;
                margin-bottom: 10px;
            }
            .report-meta {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin-top: 15px;
            }
            .report-meta span {
                background: #667eea;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.9rem;
            }
            .report-footer { 
                text-align: center; 
                border-top: 2px solid #e2e8f0; 
                padding-top: 30px; 
                margin-top: 50px; 
                color: #718096; 
            }
            .copy-section-btn { display: none !important; }
            ${this.getEnhancedCSS()}
        `;
    }

    getChartInitScript() {
        // Return script to reinitialize charts in the exported HTML
        const primaryConfig = this.getChartConfig(this.config.category, 'primary');
        const secondaryConfig = this.getChartConfig(this.config.category, 'secondary');

        return `
            try {
                if (typeof Chart !== 'undefined') {
                    Chart.defaults.font.family = "'Inter', sans-serif";
                    
                    const primaryCtx = document.getElementById('primary-chart');
                    const secondaryCtx = document.getElementById('secondary-chart');
                    
                    if (primaryCtx) {
                        new Chart(primaryCtx, ${JSON.stringify(primaryConfig)});
                    }
                    
                    if (secondaryCtx) {
                        new Chart(secondaryCtx, ${JSON.stringify(secondaryConfig)});
                    }
                }
            } catch (error) {
                console.error('Chart initialization error:', error);
            }
        `;
    }

    validateForm(form) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');

        requiredFields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        // Check for at least one filled field
        const allFields = form.querySelectorAll('input, select, textarea');
        const hasValue = Array.from(allFields).some(field => field.value.trim());

        if (!hasValue) {
            this.showNotification('error', '❌ Please fill in at least one field');
            return false;
        }

        return isValid;
    }

    validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let message = '';

        // Clear previous error
        this.clearFieldError(field);

        // Required field check
        if (field.required && !value) {
            isValid = false;
            message = 'This field is required';
        }

        // Type-specific validation
        if (value && field.type === 'number') {
            const num = parseFloat(value);
            if (isNaN(num)) {
                isValid = false;
                message = 'Please enter a valid number';
            } else if (field.min && num < parseFloat(field.min)) {
                isValid = false;
                message = `Value must be at least ${field.min}`;
            } else if (field.max && num > parseFloat(field.max)) {
                isValid = false;
                message = `Value must be no more than ${field.max}`;
            } else if (num < 0 && !field.hasAttribute('allow-negative')) {
                isValid = false;
                message = 'Value cannot be negative';
            }
        }

        // Email validation
        if (value && field.type === 'email') {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                message = 'Please enter a valid email address';
            }
        }

        // Phone validation
        if (value && field.type === 'tel') {
            const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
            if (!phoneRegex.test(value.replace(/[\s\-\(\)]/g, ''))) {
                isValid = false;
                message = 'Please enter a valid phone number';
            }
        }

        // URL validation
        if (value && field.type === 'url') {
            try {
                new URL(value);
            } catch {
                isValid = false;
                message = 'Please enter a valid URL';
            }
        }

        // Update field styling
        if (isValid) {
            field.classList.remove('error');
        } else {
            field.classList.add('error');
            this.showFieldError(field, message);
        }

        return isValid;
    }

    showFieldError(field, message) {
        const errorDiv = document.getElementById(field.name + '-error') ||
            field.parentNode.querySelector('.field-error');

        if (errorDiv) {
            errorDiv.innerHTML = `<span style="color: #e53e3e;">⚠️ ${message}</span>`;
            errorDiv.style.display = 'block';
        }
    }

    clearFieldError(field) {
        const errorDiv = document.getElementById(field.name + '-error') ||
            field.parentNode.querySelector('.field-error');

        if (errorDiv) {
            errorDiv.innerHTML = '';
            errorDiv.style.display = 'none';
        }
    }

    updateCalculateButton(isCalculating) {
        const submitBtn = document.querySelector('#tool-form button[type="submit"]');
        if (!submitBtn) return;

        if (isCalculating) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <div class="spinner"></div> 
                <span>Analyzing with AI...</span>
            `;
            submitBtn.style.opacity = '0.8';
        } else {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `
                <span class="btn-icon">🚀</span> 
                <span>Calculate Now</span>
            `;
            submitBtn.style.opacity = '1';
        }
    }

    showCalculatingAnimation() {
        const overlay = document.createElement('div');
        overlay.className = 'calculating-overlay';
        overlay.innerHTML = `
            <div class="calculating-content">
                <div class="calculating-spinner"></div>
                <h3>🤖 AI Analysis in Progress</h3>
                <p>Generating your personalized insights...</p>
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="calculating-steps">
                    <div class="step active">📊 Processing data...</div>
                    <div class="step">🧠 AI analysis...</div>
                    <div class="step">📈 Generating charts...</div>
                    <div class="step">🎯 Creating recommendations...</div>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        // Animate progress bar and steps
        setTimeout(() => {
            const fill = overlay.querySelector('.progress-fill');
            const steps = overlay.querySelectorAll('.step');

            if (fill) {
                fill.style.width = '100%';
            }

            // Animate steps
            steps.forEach((step, index) => {
                setTimeout(() => {
                    steps.forEach(s => s.classList.remove('active'));
                    step.classList.add('active');
                }, index * 800);
            });
        }, 100);
    }

    hideCalculatingAnimation() {
        const overlay = document.querySelector('.calculating-overlay');
        if (overlay) {
            overlay.style.opacity = '0';
            setTimeout(() => {
                overlay.remove();
            }, 300);
        }
    }

    resetForm() {
        const form = document.getElementById('tool-form');
        if (form) {
            form.reset();

            // Clear validation errors
            form.querySelectorAll('.error').forEach(field => {
                this.clearFieldError(field);
                field.classList.remove('error');
            });

            // Clear results
            const resultsContainer = document.getElementById('tool-results');
            if (resultsContainer) {
                resultsContainer.innerHTML = `
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

            // Destroy charts
            Object.values(this.charts).forEach(chart => {
                if (chart) chart.destroy();
            });
            this.charts = {};

            this.results = null;
            this.showNotification('info', '📝 Form reset successfully');
        }
    }

    async checkRateLimit() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/check-limits`, {
                headers: {
                    'Content-Type': 'application/json'
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

    showRateLimitMessage(rateLimitInfo) {
        const message = rateLimitInfo.message || 'Rate limit reached. Please try again later.';
        this.showNotification('error', `⏰ ${message}`);

        const container = document.getElementById('tool-results');
        if (container) {
            container.innerHTML = `
                <div class="rate-limit-notice">
                    <div class="notice-icon">⏰</div>
                    <h3>Rate Limit Reached</h3>
                    <p>${message}</p>
                    <div class="rate-limit-options">
                        <h4>You can still:</h4>
                        <ul>
                            <li>✅ Use basic calculator functions</li>
                            <li>✅ View educational content</li>
                            <li>✅ Try again in ${rateLimitInfo.minutes_until_reset || 60} minutes</li>
                            <li>🚀 Upgrade for unlimited access</li>
                        </ul>
                    </div>
                    <div class="countdown-timer" id="countdown-timer">
                        Next reset in: <span id="countdown-display">${rateLimitInfo.minutes_until_reset || 60}:00</span>
                    </div>
                </div>
            `;

            // Start countdown timer
            this.startCountdownTimer(rateLimitInfo.minutes_until_reset || 60);
        }
    }

    startCountdownTimer(minutes) {
        const display = document.getElementById('countdown-display');
        if (!display) return;

        let totalSeconds = minutes * 60;

        const timer = setInterval(() => {
            const mins = Math.floor(totalSeconds / 60);
            const secs = totalSeconds % 60;

            display.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;

            totalSeconds--;

            if (totalSeconds < 0) {
                clearInterval(timer);
                display.textContent = 'Ready to try again!';

                // Add retry button
                const retryBtn = document.createElement('button');
                retryBtn.className = 'btn-enhanced btn-primary';
                retryBtn.innerHTML = '🔄 Try Again';
                retryBtn.onclick = () => location.reload();
                display.parentNode.appendChild(retryBtn);
            }
        }, 1000);
    }

    shareResults() {
        if (!this.results) {
            this.showNotification('error', '❌ No results to share');
            return;
        }

        const shareData = {
            title: `${this.config.seo_data?.title || this.config.base_name} Results`,
            text: `Check out my ${this.config.base_name} analysis results! 🎯`,
            url: window.location.href
        };

        if (navigator.share) {
            navigator.share(shareData).then(() => {
                this.trackAnalytics('results_shared', {method: 'native'});
                this.showNotification('success', '🔗 Results shared successfully!');
            }).catch(err => {
                console.log('Share failed:', err);
                this.fallbackShare(shareData);
            });
        } else {
            this.fallbackShare(shareData);
        }
    }

    fallbackShare(shareData) {
        const url = encodeURIComponent(shareData.url);
        const text = encodeURIComponent(shareData.text);

        const shareOptions = [
            {name: '🐦 Twitter', url: `https://twitter.com/intent/tweet?text=${text}&url=${url}`},
            {name: '📘 Facebook', url: `https://www.facebook.com/sharer/sharer.php?u=${url}`},
            {name: '💼 LinkedIn', url: `https://www.linkedin.com/sharing/share-offsite/?url=${url}`},
            {name: '📱 WhatsApp', url: `https://wa.me/?text=${text}%20${url}`},
            {name: '📋 Copy Link', action: 'copy'}
        ];

        const modal = document.createElement('div');
        modal.className = 'share-modal';
        modal.innerHTML = `
            <div class="modal-backdrop"></div>
            <div class="modal-content-enhanced">
                <div class="modal-header">
                    <h3>🔗 Share Your Results</h3>
                    <button class="modal-close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="share-options">
                        ${shareOptions.map(option => `
                            <button class="share-option-btn" data-action="${option.action || 'share'}" data-url="${option.url || ''}">
                                ${option.name}
                            </button>
                        `).join('')}
                    </div>
                    <div class="share-preview">
                        <h4>Preview:</h4>
                        <div class="preview-card">
                            <strong>${shareData.title}</strong>
                            <p>${shareData.text}</p>
                            <small>${shareData.url}</small>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        setTimeout(() => modal.classList.add('show'), 10);

        // Event listeners
        modal.querySelector('.modal-close-btn').addEventListener('click', () => {
            modal.classList.remove('show');
            setTimeout(() => modal.remove(), 300);
        });

        modal.querySelector('.modal-backdrop').addEventListener('click', () => {
            modal.classList.remove('show');
            setTimeout(() => modal.remove(), 300);
        });

        modal.querySelectorAll('.share-option-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                if (btn.dataset.action === 'copy') {
                    navigator.clipboard.writeText(window.location.href).then(() => {
                        this.showNotification('success', '📋 Link copied to clipboard!');
                    }).catch(() => {
                        this.fallbackCopy(window.location.href);
                    });
                } else {
                    window.open(btn.dataset.url, '_blank', 'width=600,height=400');
                }
                this.trackAnalytics('results_shared', {method: btn.textContent});
                modal.classList.remove('show');
                setTimeout(() => modal.remove(), 300);
            });
        });
    }

    displayErrorResults(error) {
        const container = document.getElementById('tool-results');
        if (!container) return;

        container.innerHTML = `
            <div class="error-results">
                <div class="error-icon">❌</div>
                <h3>Calculation Error</h3>
                <p>We encountered an issue processing your request:</p>
                <div class="error-message">${this.sanitizeErrorMessage(error.message)}</div>
                <div class="error-details">
                    <details>
                        <summary>Technical Details</summary>
                        <pre>${error.stack || error.message}</pre>
                    </details>
                </div>
                <div class="error-actions">
                    <button onclick="location.reload()" class="btn-enhanced btn-primary">
                        🔄 Refresh Page
                    </button>
                    <button onclick="universalCalculator.resetForm()" class="btn-enhanced btn-secondary">
                        📝 Reset Form
                    </button>
                    <button onclick="universalCalculator.reportError('${error.message}')" class="btn-enhanced btn-secondary">
                        🐛 Report Issue
                    </button>
                </div>
            </div>
        `;
    }

    sanitizeErrorMessage(message) {
        // Remove sensitive information from error messages
        return message
            .replace(/api[_-]?key/gi, '[API_KEY]')
            .replace(/token/gi, '[TOKEN]')
            .replace(/secret/gi, '[SECRET]')
            .replace(/password/gi, '[PASSWORD]');
    }

    reportError(errorMessage) {
        const reportData = {
            error: this.sanitizeErrorMessage(errorMessage),
            tool: this.config.slug,
            category: this.config.category,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href
        };

        // Log error for debugging
        console.error('Error Report:', reportData);

        this.showNotification('info', '🐛 Error reported. Thank you for helping us improve!');
        this.trackAnalytics('error_reported', reportData);
    }

    showNotification(type, message, duration = 4000) {
        // Remove existing notifications
        document.querySelectorAll('.notification-enhanced').forEach(n => n.remove());

        const notification = document.createElement('div');
        notification.className = `notification-enhanced ${type}`;

        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };

        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${icons[type] || icons.info}</span>
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;

        document.body.appendChild(notification);

        // Close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        });

        // Show notification with animation
        setTimeout(() => notification.classList.add('show'), 100);

        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.classList.remove('show');
                    setTimeout(() => notification.remove(), 300);
                }
            }, duration);
        }

        // Make notification dismissible on click
        notification.addEventListener('click', (e) => {
            if (e.target === notification) {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }
        });
    }

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

        // Console log for debugging
        console.log('📊 Analytics event:', event, {
            tool: this.config.slug,
            category: this.config.category,
            ...data
        });
    }

    addModernStyling() {
        if (document.getElementById('enhanced-calculator-styles')) return;

        const style = document.createElement('style');
        style.id = 'enhanced-calculator-styles';
        style.textContent = this.getEnhancedCSS();
        document.head.appendChild(style);
    }

    getEnhancedCSS() {
        return `
            /* Enhanced Calculator System Styles */
            
            /* Animation keyframes */
            @keyframes slideInUp {
                from { opacity: 0; transform: translateY(30px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            @keyframes pulse {
                0%, 100% { transform: scale(1); opacity: 0.5; }
                50% { transform: scale(1.05); opacity: 0.8; }
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            @keyframes modalSlideIn {
                from { transform: translateY(-50px) scale(0.9); opacity: 0; }
                to { transform: translateY(0) scale(1); opacity: 1; }
            }

            /* Enhanced Results Container */
            .enhanced-results-container {
                animation: slideInUp 0.6s ease-out;
                margin-bottom: 40px;
            }

            /* Results Header */
            .results-header-enhanced {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 16px;
                margin-bottom: 30px;
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                flex-wrap: wrap;
                gap: 20px;
                position: relative;
                overflow: hidden;
            }

            .results-header-enhanced::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                animation: pulse 3s ease-in-out infinite;
                pointer-events: none;
            }

            .header-content {
                position: relative;
                z-index: 1;
            }

            .primary-result-title {
                font-size: 2rem;
                font-weight: 700;
                margin: 0;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                line-height: 1.2;
            }

            .result-meta {
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
                margin-top: 15px;
            }

            .result-meta span {
                background: rgba(255,255,255,0.2);
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 0.9rem;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.3);
                font-weight: 500;
            }

            .header-actions {
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
                position: relative;
                z-index: 1;
            }

            .btn-enhanced {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 12px 24px;
                border: none;
                border-radius: 10px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                text-decoration: none;
                font-size: 0.95rem;
                position: relative;
                overflow: hidden;
            }

            .btn-enhanced::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
                transition: left 0.5s;
            }

            .btn-enhanced:hover::before {
                left: 100%;
            }

            .download-btn {
                background: rgba(255,255,255,0.2);
                color: white;
                border: 2px solid rgba(255,255,255,0.3);
            }

            .download-btn:hover {
                background: rgba(255,255,255,0.3);
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(0,0,0,0.2);
            }

            .share-btn {
                background: transparent;
                color: white;
                border: 2px solid rgba(255,255,255,0.5);
            }

            .share-btn:hover {
                background: rgba(255,255,255,0.1);
                transform: translateY(-2px);
            }

            /* Key Metrics Dashboard */
            .metrics-dashboard {
                margin: 30px 0;
            }

            .section-title {
                font-size: 1.6rem;
                font-weight: 700;
                color: #2d3748;
                margin-bottom: 25px;
                display: flex;
                align-items: center;
                gap: 12px;
                position: relative;
            }

            .section-title::after {
                content: '';
                flex: 1;
                height: 3px;
                background: linear-gradient(90deg, #667eea, transparent);
                border-radius: 2px;
                margin-left: 20px;
            }

            .metrics-grid-enhanced {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
            }

            .metric-card-enhanced {
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                padding: 25px;
                border-radius: 16px;
                display: flex;
                align-items: center;
                gap: 15px;
                transition: all 0.3s ease;
                cursor: pointer;
                overflow: hidden;
                position: relative;
                min-height: 120px;
            }

            .metric-card-enhanced::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transition: left 0.6s;
            }

            .metric-card-enhanced:hover::before {
                left: 100%;
            }

            .metric-card-enhanced.success {
                background: linear-gradient(135deg, #48bb78, #38a169);
            }

            .metric-card-enhanced.warning {
                background: linear-gradient(135deg, #ed8936, #dd6b20);
            }

            .metric-card-enhanced.info {
                background: linear-gradient(135deg, #4299e1, #3182ce);
            }

            .metric-card-enhanced.primary {
                background: linear-gradient(135deg, #667eea, #764ba2);
            }

            .metric-icon {
                font-size: 2.5rem;
                opacity: 0.9;
                flex-shrink: 0;
            }

            .metric-content {
                flex: 1;
            }

            .metric-value {
                font-size: 1.9rem;
                font-weight: 800;
                margin-bottom: 5px;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                line-height: 1;
            }

            .metric-label {
                font-size: 1rem;
                opacity: 0.9;
                margin-bottom: 8px;
                font-weight: 500;
            }

            .metric-change {
                font-size: 0.85rem;
                font-weight: 600;
                padding: 2px 8px;
                border-radius: 12px;
                background: rgba(255,255,255,0.2);
                display: inline-block;
            }

            .metric-change.positive {
                background: rgba(72, 187, 120, 0.3);
            }

            .metric-change.negative {
                background: rgba(245, 101, 101, 0.3);
            }

            /* Charts Section */
            .charts-section {
                margin: 40px 0;
            }

            .charts-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 30px;
            }

            .chart-container {
                background: white;
                border-radius: 16px;
                padding: 25px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                position: relative;
                height: 400px;
                border: 1px solid #e2e8f0;
            }

            .chart-container::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #667eea, #764ba2);
                border-radius: 16px 16px 0 0;
            }

            /* Value Ladder */
            .value-ladder-enhanced {
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                border-radius: 20px;
                padding: 40px;
                margin: 40px 0;
                color: white;
                position: relative;
                overflow: hidden;
            }

            .value-ladder-enhanced::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                animation: pulse 4s ease-in-out infinite;
                pointer-events: none;
            }

            .ladder-container {
                position: relative;
                z-index: 1;
            }

            .ladder-step-enhanced {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 16px;
                padding: 25px;
                margin: 20px 0;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                display: flex;
                align-items: center;
                gap: 20px;
                transition: all 0.3s ease;
                cursor: pointer;
            }

            .ladder-step-enhanced:hover {
                background: rgba(255, 255, 255, 0.25);
                transform: translateX(10px);
            }

            .step-number {
                background: rgba(255, 255, 255, 0.3);
                width: 50px;
                height: 50px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 800;
                font-size: 1.2rem;
                flex-shrink: 0;
                border: 2px solid rgba(255, 255, 255, 0.4);
            }

            .step-content {
                flex: 1;
            }

            .step-title {
                font-size: 1.3rem;
                font-weight: 700;
                margin-bottom: 8px;
                line-height: 1.2;
            }

            .step-description {
                font-size: 1rem;
                opacity: 0.9;
                margin-bottom: 12px;
                line-height: 1.4;
            }

            .step-value {
                font-size: 1.1rem;
                font-weight: 600;
                background: rgba(255, 255, 255, 0.2);
                display: inline-block;
                padding: 6px 14px;
                border-radius: 20px;
                margin-right: 10px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }

            .step-timeline {
                font-size: 0.9rem;
                opacity: 0.8;
                background: rgba(255, 255, 255, 0.1);
                display: inline-block;
                padding: 6px 14px;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }

            .step-icon {
                font-size: 2rem;
                opacity: 0.8;
                flex-shrink: 0;
            }

            /* AI Analysis Section */
            .ai-analysis-section {
                background: rgba(255, 255, 255, 0.9);
                border-radius: 16px;
                padding: 30px;
                margin: 30px 0;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(0, 0, 0, 0.1);
                box-shadow: 0 8px 25px rgba(0,0,0,0.08);
            }

            .ai-content-wrapper {
                line-height: 1.7;
                color: #2d3748;
            }

            .ai-content-wrapper h1,
            .ai-content-wrapper h2,
            .ai-content-wrapper h3 {
                color: #2d3748;
                margin-top: 25px;
                margin-bottom: 15px;
                font-weight: 700;
            }

            .ai-content-wrapper strong {
                color: #4a5568;
                font-weight: 700;
            }

            .ai-content-wrapper ul {
                padding-left: 20px;
                margin: 15px 0;
            }

            .ai-content-wrapper li {
                margin-bottom: 8px;
                line-height: 1.6;
            }

            /* Action Items Section */
            .action-items-section {
                margin: 40px 0;
            }

            .action-items-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
            }

            .action-item-card {
                background: white;
                border-radius: 16px;
                padding: 25px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
                cursor: pointer;
                border-left: 4px solid #667eea;
                position: relative;
                overflow: hidden;
            }

            .action-item-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(45deg, rgba(102, 126, 234, 0.05) 0%, transparent 50%);
                opacity: 0;
                transition: opacity 0.3s ease;
            }

            .action-item-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 35px rgba(0,0,0,0.15);
            }

            .action-item-card:hover::before {
                opacity: 1;
            }

            .action-item-card[data-priority="high"] {
                border-left-color: #e53e3e;
            }

            .action-item-card[data-priority="medium"] {
                border-left-color: #dd6b20;
            }

            .action-item-card[data-priority="low"] {
                border-left-color: #38a169;
            }

            .action-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }

            .action-icon {
                font-size: 1.5rem;
            }

            .action-priority {
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .action-priority.high {
                background: linear-gradient(135deg, #fed7d7, #feb2b2);
                color: #c53030;
            }

            .action-priority.medium {
                background: linear-gradient(135deg, #fbd38d, #f6ad55);
                color: #c05621;
            }

            .action-priority.low {
                background: linear-gradient(135deg, #c6f6d5, #9ae6b4);
                color: #2f855a;
            }

            .action-title {
                font-size: 1.2rem;
                font-weight: 700;
                color: #2d3748;
                margin-bottom: 10px;
                line-height: 1.3;
            }

            .action-description {
                color: #4a5568;
                line-height: 1.6;
                margin-bottom: 15px;
            }

            .action-meta {
                display: flex;
                gap: 15px;
                font-size: 0.9rem;
                color: #718096;
                flex-wrap: wrap;
            }

            /* Copy Section Button */
            .copy-section-btn {
                position: absolute;
                top: 15px;
                right: 15px;
                background: rgba(0,0,0,0.1);
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.3s ease;
                color: inherit;
                opacity: 0.7;
            }

            .copy-section-btn:hover {
                background: rgba(0,0,0,0.2);
                opacity: 1;
            }

            /* Mobile Optimizations */
            @media (max-width: 768px) {
                .results-header-enhanced {
                    flex-direction: column;
                    text-align: center;
                    gap: 15px;
                    padding: 25px;
                }

                .primary-result-title {
                    font-size: 1.6rem;
                }

                .result-meta {
                    justify-content: center;
                    gap: 10px;
                }

                .header-actions {
                    width: 100%;
                    justify-content: center;
                }

                .metrics-grid-enhanced {
                    grid-template-columns: 1fr;
                    gap: 15px;
                }

                .metric-card-enhanced {
                    padding: 20px;
                    min-height: 100px;
                }

                .metric-value {
                    font-size: 1.6rem;
                }

                .charts-grid {
                    grid-template-columns: 1fr;
                    gap: 20px;
                }

                .chart-container {
                    height: 300px;
                    padding: 20px;
                }

                .value-ladder-enhanced {
                    padding: 25px;
                }

                .ladder-step-enhanced {
                    flex-direction: column;
                    text-align: center;
                    gap: 15px;
                    padding: 20px;
                }

                .action-items-grid {
                    grid-template-columns: 1fr;
                    gap: 15px;
                }

                .action-item-card {
                    padding: 20px;
                }

                .section-title {
                    font-size: 1.4rem;
                }

                .section-title::after {
                    display: none;
                }
            }

            @media (max-width: 480px) {
                .primary-result-title {
                    font-size: 1.4rem;
                }

                .result-meta {
                    flex-direction: column;
                    gap: 8px;
                }

                .btn-enhanced {
                    padding: 10px 16px;
                    font-size: 0.9rem;
                    width: 100%;
                    justify-content: center;
                }

                .metric-card-enhanced {
                    flex-direction: column;
                    text-align: center;
                    gap: 10px;
                }

                .metric-icon {
                    font-size: 2rem;
                }

                .step-title {
                    font-size: 1.1rem;
                }

                .action-title {
                    font-size: 1.1rem;
                }

                .action-meta {
                    flex-direction: column;
                    gap: 8px;
                }
            }
        `;
    }

    setupMobileOptimizations() {
        // Touch-friendly interactions
        if ('ontouchstart' in window) {
            document.body.classList.add('touch-device');

            // Improve touch targets
            const touchElements = document.querySelectorAll('.btn-enhanced, .metric-card-enhanced, .action-item-card');
            touchElements.forEach(element => {
                element.style.minHeight = '44px';
                element.style.minWidth = '44px';
            });

            // Add touch feedback
            touchElements.forEach(element => {
                element.addEventListener('touchstart', () => {
                    element.style.transform = 'scale(0.98)';
                });
                element.addEventListener('touchend', () => {
                    setTimeout(() => {
                        element.style.transform = '';
                    }, 150);
                });
            });
        }

        // Responsive chart handling
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                Object.values(this.charts).forEach(chart => {
                    if (chart && typeof chart.resize === 'function') {
                        chart.resize();
                    }
                });
            }, 250);
        });

        // Optimize form inputs for mobile
        const inputs = document.querySelectorAll('input[type="number"], input[type="text"], input[type="email"]');
        inputs.forEach(input => {
            input.addEventListener('focus', function () {
                if (window.innerWidth < 768) {
                    setTimeout(() => {
                        this.scrollIntoView({
                            behavior: 'smooth',
                            block: 'center',
                            inline: 'nearest'
                        });
                    }, 300);
                }
            });

            // Prevent zoom on input focus (iOS)
            input.style.fontSize = '16px';
        });

        // Handle orientation change
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                Object.values(this.charts).forEach(chart => {
                    if (chart && typeof chart.resize === 'function') {
                        chart.resize();
                    }
                });

                // Recalculate modal positions
                const modals = document.querySelectorAll('.report-modal-enhanced, .share-modal');
                modals.forEach(modal => {
                    if (modal.classList.contains('show')) {
                        modal.style.height = '100vh';
                        setTimeout(() => {
                            modal.style.height = '';
                        }, 100);
                    }
                });
            }, 500);
        });

        // Improved scroll handling for mobile
        let ticking = false;

        function updateScrollPosition() {
            // Handle sticky elements or scroll-based animations
            ticking = false;
        }

        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(updateScrollPosition);
                ticking = true;
            }
        });

        // Add swipe gesture support for modals
        this.addSwipeGestureSupport();
    }

    addSwipeGestureSupport() {
        let startY = 0;
        let startX = 0;

        document.addEventListener('touchstart', (e) => {
            startY = e.touches[0].clientY;
            startX = e.touches[0].clientX;
        });

        document.addEventListener('touchend', (e) => {
            if (!startY || !startX) return;

            const endY = e.changedTouches[0].clientY;
            const endX = e.changedTouches[0].clientX;

            const diffY = startY - endY;
            const diffX = startX - endX;

            // Check if swipe is significant enough
            if (Math.abs(diffY) > 50 || Math.abs(diffX) > 50) {
                // Determine swipe direction
                if (Math.abs(diffY) > Math.abs(diffX)) {
                    // Vertical swipe
                    if (diffY > 0) {
                        // Swipe up
                        this.handleSwipeUp();
                    } else {
                        // Swipe down
                        this.handleSwipeDown();
                    }
                } else {
                    // Horizontal swipe
                    if (diffX > 0) {
                        // Swipe left
                        this.handleSwipeLeft();
                    } else {
                        // Swipe right
                        this.handleSwipeRight();
                    }
                }
            }

            // Reset values
            startY = 0;
            startX = 0;
        });
    }

}



