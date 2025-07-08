// themes/hello-elements/tool-js/chart-manager.js
// Chart Management Module

class ChartManager {
    constructor(config) {
        this.config = config;
        this.charts = {};
        this.chartDefaults = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        font: {
                            family: "'Inter', sans-serif",
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    cornerRadius: 8,
                    padding: 12,
                    displayColors: false,
                    titleFont: {
                        family: "'Inter', sans-serif",
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        family: "'Inter', sans-serif",
                        size: 12
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        };

        this.colors = {
            primary: ['#667eea', '#764ba2', '#f093fb', '#f5576c'],
            secondary: ['#4facfe', '#00f2fe', '#43e97b', '#38f9d7'],
            success: ['#48bb78', '#38a169', '#68d391', '#9ae6b4'],
            warning: ['#ed8936', '#dd6b20', '#f6ad55', '#fbd38d'],
            error: ['#e53e3e', '#c53030', '#fc8181', '#feb2b2'],
            info: ['#4299e1', '#3182ce', '#63b3ed', '#90cdf4']
        };

        this.setupChartDefaults();
        console.log('✅ Chart Manager initialized');
    }

    setupChartDefaults() {
        if (typeof Chart !== 'undefined') {
            Chart.defaults.font.family = "'Inter', sans-serif";
            Chart.defaults.font.size = 12;
            Chart.defaults.color = '#2d3748';
        }
    }

    initializeCharts(output) {
        try {
            this.createPrimaryChart(output);
            this.createSecondaryChart(output);
            console.log('✅ Charts initialized successfully');
        } catch (error) {
            console.error('❌ Chart initialization failed:', error);
        }
    }

    createPrimaryChart(output) {
        const ctx = document.getElementById('primary-chart');
        if (!ctx) {
            console.warn('Primary chart canvas not found');
            return;
        }

        // Destroy existing chart
        if (this.charts.primary) {
            this.charts.primary.destroy();
        }

        const config = this.getPrimaryChartConfig(output);

        try {
            this.charts.primary = new Chart(ctx, config);
        } catch (error) {
            console.error('Failed to create primary chart:', error);
            this.showChartError(ctx, 'Primary Chart');
        }
    }

    createSecondaryChart(output) {
        const ctx = document.getElementById('secondary-chart');
        if (!ctx) {
            console.warn('Secondary chart canvas not found');
            return;
        }

        // Destroy existing chart
        if (this.charts.secondary) {
            this.charts.secondary.destroy();
        }

        const config = this.getSecondaryChartConfig(output);

        try {
            this.charts.secondary = new Chart(ctx, config);
        } catch (error) {
            console.error('Failed to create secondary chart:', error);
            this.showChartError(ctx, 'Secondary Chart');
        }
    }

    getPrimaryChartConfig(output) {
        const category = this.config.category;

        switch (category) {
            case 'finance':
            case 'business':
                return this.getFinancePrimaryChart(output);
            case 'legal':
                return this.getLegalPrimaryChart(output);
            case 'health':
                return this.getHealthPrimaryChart(output);
            default:
                return this.getDefaultPrimaryChart(output);
        }
    }

    getSecondaryChartConfig(output) {
        const category = this.config.category;

        switch (category) {
            case 'finance':
            case 'business':
                return this.getFinanceSecondaryChart(output);
            case 'legal':
                return this.getLegalSecondaryChart(output);
            case 'health':
                return this.getHealthSecondaryChart(output);
            default:
                return this.getDefaultSecondaryChart(output);
        }
    }

    // Finance Charts
    getFinancePrimaryChart(output) {
        return {
            type: 'doughnut',
            data: {
                labels: ['Investments', 'Returns', 'Fees', 'Taxes'],
                datasets: [{
                    data: [70, 20, 5, 5],
                    backgroundColor: this.colors.primary,
                    borderWidth: 0,
                    hoverOffset: 8,
                    borderRadius: 4
                }]
            },
            options: {
                ...this.chartDefaults,
                plugins: {
                    ...this.chartDefaults.plugins,
                    title: {
                        display: true,
                        text: 'Portfolio Breakdown',
                        font: { size: 16, weight: 'bold' },
                        padding: 20
                    }
                }
            }
        };
    }

    getFinanceSecondaryChart(output) {
        const years = ['Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5'];
        const values = [100000, 107000, 114490, 122504, 131079];

        return {
            type: 'line',
            data: {
                labels: years,
                datasets: [{
                    label: 'Portfolio Value',
                    data: values,
                    borderColor: this.colors.secondary[0],
                    backgroundColor: this.colors.secondary[0] + '20',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: this.colors.secondary[0],
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                ...this.chartDefaults,
                plugins: {
                    ...this.chartDefaults.plugins,
                    title: {
                        display: true,
                        text: 'Growth Projection',
                        font: { size: 16, weight: 'bold' },
                        padding: 20
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return ' + value.toLocaleString();
                            }
                        },
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    }
                }
            }
        };
    }

    // Legal Charts
    getLegalPrimaryChart(output) {
        return {
            type: 'bar',
            data: {
                labels: ['Medical Bills', 'Lost Wages', 'Pain & Suffering', 'Legal Fees'],
                datasets: [{
                    data: [45000, 25000, 75000, 15000],
                    backgroundColor: this.colors.primary,
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                ...this.chartDefaults,
                plugins: {
                    ...this.chartDefaults.plugins,
                    title: {
                        display: true,
                        text: 'Settlement Breakdown',
                        font: { size: 16, weight: 'bold' },
                        padding: 20
                    },
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return ' + value.toLocaleString();
                            }
                        },
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        };
    }

    getLegalSecondaryChart(output) {
        return {
            type: 'radar',
            data: {
                labels: ['Evidence Strength', 'Legal Precedent', 'Damages Clarity', 'Liability', 'Settlement Likelihood'],
                datasets: [{
                    label: 'Case Strength',
                    data: [8, 7, 9, 8, 8],
                    borderColor: this.colors.secondary[0],
                    backgroundColor: this.colors.secondary[0] + '30',
                    pointBackgroundColor: this.colors.secondary[0],
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6
                }]
            },
            options: {
                ...this.chartDefaults,
                plugins: {
                    ...this.chartDefaults.plugins,
                    title: {
                        display: true,
                        text: 'Case Analysis',
                        font: { size: 16, weight: 'bold' },
                        padding: 20
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 10,
                        ticks: {
                            stepSize: 2
                        },
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        },
                        angleLines: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    }
                }
            }
        };
    }

    // Health Charts
    getHealthPrimaryChart(output) {
        return {
            type: 'line',
            data: {
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
                datasets: [{
                    label: 'Weight (lbs)',
                    data: [180, 178, 176, 174, 172, 170],
                    borderColor: this.colors.primary[0],
                    backgroundColor: this.colors.primary[0] + '20',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: this.colors.primary[0],
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                ...this.chartDefaults,
                plugins: {
                    ...this.chartDefaults.plugins,
                    title: {
                        display: true,
                        text: 'Weight Progress',
                        font: { size: 16, weight: 'bold' },
                        padding: 20
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return value + ' lbs';
                            }
                        },
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    }
                }
            }
        };
    }

    getHealthSecondaryChart(output) {
        return {
            type: 'polarArea',
            data: {
                labels: ['Cardio', 'Strength', 'Flexibility', 'Nutrition', 'Sleep'],
                datasets: [{
                    data: [85, 70, 60, 90, 75],
                    backgroundColor: this.colors.secondary.map(color => color + '80'),
                    borderColor: this.colors.secondary,
                    borderWidth: 2
                }]
            },
            options: {
                ...this.chartDefaults,
                plugins: {
                    ...this.chartDefaults.plugins,
                    title: {
                        display: true,
                        text: 'Health Metrics',
                        font: { size: 16, weight: 'bold' },
                        padding: 20
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20,
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        };
    }

    // Default Charts
    getDefaultPrimaryChart(output) {
        return {
            type: 'bar',
            data: {
                labels: ['Result A', 'Result B', 'Result C', 'Result D'],
                datasets: [{
                    data: [65, 75, 80, 70],
                    backgroundColor: this.colors.primary,
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                ...this.chartDefaults,
                plugins: {
                    ...this.chartDefaults.plugins,
                    title: {
                        display: true,
                        text: 'Analysis Results',
                        font: { size: 16, weight: 'bold' },
                        padding: 20
                    },
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        };
    }

    getDefaultSecondaryChart(output) {
        return {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Progress',
                    data: [30, 45, 60, 70, 85, 95],
                    borderColor: this.colors.secondary[0],
                    backgroundColor: this.colors.secondary[0] + '20',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: this.colors.secondary[0],
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                ...this.chartDefaults,
                plugins: {
                    ...this.chartDefaults.plugins,
                    title: {
                        display: true,
                        text: 'Progress Over Time',
                        font: { size: 16, weight: 'bold' },
                        padding: 20
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    }
                }
            }
        };
    }

    showChartError(canvas, chartName) {
        const container = canvas.parentElement;
        container.innerHTML = `
            <div class="chart-error" style="
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 300px;
                background: #f7fafc;
                border-radius: 8px;
                border: 2px dashed #e2e8f0;
                color: #718096;
            ">
                <div style="font-size: 2rem; margin-bottom: 10px;">📊</div>
                <div style="font-weight: 600; margin-bottom: 5px;">${chartName} Unavailable</div>
                <div style="font-size: 0.9rem; text-align: center;">
                    Chart could not be loaded.<br>
                    Please check your browser compatibility.
                </div>
            </div>
        `;
    }

    // Utility methods
    updateChartData(chartName, newData) {
        const chart = this.charts[chartName];
        if (!chart) return false;

        try {
            chart.data = newData;
            chart.update('animate');
            return true;
        } catch (error) {
            console.error(`Failed to update ${chartName} chart:`, error);
            return false;
        }
    }

    resizeCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.resize === 'function') {
                chart.resize();
            }
        });
    }

    destroyChart(chartName) {
        if (this.charts[chartName]) {
            this.charts[chartName].destroy();
            delete this.charts[chartName];
        }
    }

    destroyAllCharts() {
        Object.keys(this.charts).forEach(chartName => {
            this.destroyChart(chartName);
        });
        console.log('🧹 All charts destroyed');
    }

    // Export chart as image
    exportChart(chartName, format = 'png') {
        const chart = this.charts[chartName];
        if (!chart) return null;

        try {
            const url = chart.toBase64Image(format, 1);
            return url;
        } catch (error) {
            console.error(`Failed to export ${chartName} chart:`, error);
            return null;
        }
    }

    // Download chart as image
    downloadChart(chartName, filename) {
        const dataUrl = this.exportChart(chartName);
        if (!dataUrl) return false;

        const link = document.createElement('a');
        link.download = filename || `${chartName}-chart.png`;
        link.href = dataUrl;

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        return true;
    }

    // Get chart data for reports
    getChartData(chartName) {
        const chart = this.charts[chartName];
        if (!chart) return null;

        return {
            data: chart.data,
            options: chart.options,
            type: chart.config.type,
            image: this.exportChart(chartName)
        };
    }

    // Handle responsive behavior
    handleResize() {
        // Debounce resize events
        clearTimeout(this.resizeTimeout);
        this.resizeTimeout = setTimeout(() => {
            this.resizeCharts();
        }, 250);
    }

    // Animation helpers
    animateChartAppearance(chartName, delay = 0) {
        const chart = this.charts[chartName];
        if (!chart) return;

        setTimeout(() => {
            chart.update('animate');
        }, delay);
    }

    // Color theme management
    setColorTheme(themeName) {
        const themes = {
            default: {
                primary: ['#667eea', '#764ba2', '#f093fb', '#f5576c'],
                secondary: ['#4facfe', '#00f2fe', '#43e97b', '#38f9d7']
            },
            dark: {
                primary: ['#4facfe', '#00f2fe', '#43e97b', '#38f9d7'],
                secondary: ['#667eea', '#764ba2', '#f093fb', '#f5576c']
            },
            monochrome: {
                primary: ['#2d3748', '#4a5568', '#718096', '#a0aec0'],
                secondary: ['#1a202c', '#2d3748', '#4a5568', '#718096']
            }
        };

        if (themes[themeName]) {
            this.colors = { ...this.colors, ...themes[themeName] };

            // Update existing charts
            Object.keys(this.charts).forEach(chartName => {
                this.updateChartColors(chartName);
            });
        }
    }

    updateChartColors(chartName) {
        const chart = this.charts[chartName];
        if (!chart) return;

        // Update colors based on chart type
        const datasets = chart.data.datasets;
        datasets.forEach((dataset, index) => {
            if (dataset.backgroundColor && Array.isArray(dataset.backgroundColor)) {
                dataset.backgroundColor = this.colors.primary;
            } else if (dataset.backgroundColor) {
                dataset.backgroundColor = this.colors.primary[index % this.colors.primary.length];
            }

            if (dataset.borderColor) {
                dataset.borderColor = this.colors.secondary[index % this.colors.secondary.length];
            }
        });

        chart.update();
    }

    // Get chart statistics
    getChartStats() {
        return {
            totalCharts: Object.keys(this.charts).length,
            activeCharts: Object.keys(this.charts),
            chartTypes: Object.values(this.charts).map(chart => chart.config.type),
            memoryUsage: this.estimateMemoryUsage()
        };
    }

    estimateMemoryUsage() {
        // Rough estimation of memory usage
        const chartCount = Object.keys(this.charts).length;
        const avgDataPoints = 50; // Estimate
        const bytesPerDataPoint = 8; // Estimate

        return chartCount * avgDataPoints * bytesPerDataPoint;
    }
}

// Export for global access
window.ChartManager = ChartManager;