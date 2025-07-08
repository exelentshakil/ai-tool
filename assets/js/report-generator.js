// themes/hello-elements/tool-js/report-generator.js
// Report Generation Module

class ReportGenerator {
    constructor(config, chartManager) {
        this.config = config;
        this.chartManager = chartManager;
        this.isGenerating = false;
        this.reportFormats = ['png', 'pdf', 'html', 'json'];

        console.log('✅ Report Generator initialized');
    }

    showReportModal() {
        if (this.isGenerating) {
            console.log('Report generation already in progress');
            return;
        }

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
                    <h3>📊 Generate Professional Report</h3>
                    <button class="modal-close-btn">&times;</button>
                </div>
                
                <div class="modal-body">
                    <p>Choose your preferred format for this comprehensive report:</p>
                    
                    <div class="report-options-grid">
                        <button class="report-option-btn" data-format="png">
                            <div class="option-icon">🖼️</div>
                            <div class="option-title">High-Quality Image</div>
                            <div class="option-desc">Perfect for sharing on social media</div>
                            <div class="option-size">~2-5 MB</div>
                        </button>
                        
                        <button class="report-option-btn" data-format="pdf">
                            <div class="option-icon">📄</div>
                            <div class="option-title">Professional PDF</div>
                            <div class="option-desc">Great for printing and archiving</div>
                            <div class="option-size">~1-3 MB</div>
                        </button>
                        
                        <button class="report-option-btn" data-format="html">
                            <div class="option-icon">🌐</div>
                            <div class="option-title">Interactive HTML</div>
                            <div class="option-desc">Full interactive experience</div>
                            <div class="option-size">~500 KB</div>
                        </button>

                        <button class="report-option-btn" data-format="json">
                            <div class="option-icon">📋</div>
                            <div class="option-title">Data Export</div>
                            <div class="option-desc">Raw data for analysis</div>
                            <div class="option-size">~50 KB</div>
                        </button>
                    </div>
                    
                    <div class="report-options-section">
                        <h4>📋 Report Options</h4>
                        <div class="options-grid">
                            <label class="option-checkbox">
                                <input type="checkbox" id="include-charts" checked>
                                <span class="checkmark"></span>
                                Include Interactive Charts
                            </label>
                            <label class="option-checkbox">
                                <input type="checkbox" id="include-analysis" checked>
                                <span class="checkmark"></span>
                                Include AI Analysis
                            </label>
                            <label class="option-checkbox">
                                <input type="checkbox" id="include-roadmap" checked>
                                <span class="checkmark"></span>
                                Include Growth Roadmap
                            </label>
                            <label class="option-checkbox">
                                <input type="checkbox" id="include-actions" checked>
                                <span class="checkmark"></span>
                                Include Action Items
                            </label>
                        </div>
                    </div>

                    <div class="report-preview-section">
                        <h4>👁️ Preview:</h4>
                        <div class="report-preview-container">
                            <div class="preview-sample">
                                <div class="preview-header">
                                    <h5>${this.config.seo_data?.title || this.config.base_name} Report</h5>
                                    <div class="preview-date">${new Date().toLocaleDateString()}</div>
                                </div>
                                <div class="preview-content">
                                    <div class="preview-section">📊 Key Metrics Dashboard</div>
                                    <div class="preview-section">📈 Interactive Charts</div>
                                    <div class="preview-section">🤖 AI Strategic Insights</div>
                                    <div class="preview-section">🚀 Growth Roadmap</div>
                                    <div class="preview-section">📋 Action Items</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="modal-footer">
                    <div class="generation-status" id="generation-status"></div>
                </div>
            </div>
        `;

        this.addModalStyles(modal);
        this.addModalEventListeners(modal);

        return modal;
    }

    addModalStyles(modal) {
        if (document.getElementById('report-modal-styles')) return;

        const style = document.createElement('style');
        style.id = 'report-modal-styles';
        style.textContent = `
            .report-modal-enhanced {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 10001;
                display: flex;
                align-items: center;
                justify-content: center;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
            }

            .report-modal-enhanced.show {
                opacity: 1;
                visibility: visible;
            }

            .modal-backdrop {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(5px);
            }

            .modal-content-enhanced {
                background: white;
                border-radius: 16px;
                max-width: 800px;
                width: 90%;
                max-height: 90vh;
                overflow-y: auto;
                position: relative;
                z-index: 1;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                transform: translateY(-20px);
                transition: transform 0.3s ease;
            }

            .report-modal-enhanced.show .modal-content-enhanced {
                transform: translateY(0);
            }

            .modal-header {
                padding: 25px 30px;
                border-bottom: 1px solid #e2e8f0;
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                border-radius: 16px 16px 0 0;
            }

            .modal-header h3 {
                margin: 0;
                font-size: 1.5rem;
                font-weight: 700;
            }

            .modal-close-btn {
                background: none;
                border: none;
                font-size: 1.5rem;
                color: white;
                cursor: pointer;
                padding: 5px;
                border-radius: 50%;
                width: 35px;
                height: 35px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
            }

            .modal-close-btn:hover {
                background: rgba(255, 255, 255, 0.2);
            }

            .modal-body {
                padding: 30px;
            }

            .modal-body > p {
                margin-bottom: 25px;
                color: #4a5568;
                font-size: 1.1rem;
            }

            .report-options-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 15px;
                margin-bottom: 30px;
            }

            .report-option-btn {
                background: white;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 20px;
                cursor: pointer;
                transition: all 0.3s ease;
                text-align: center;
                position: relative;
                overflow: hidden;
            }

            .report-option-btn:hover {
                border-color: #667eea;
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.15);
            }

            .report-option-btn.generating {
                pointer-events: none;
                opacity: 0.7;
            }

            .option-icon {
                font-size: 2rem;
                margin-bottom: 10px;
            }

            .option-title {
                font-weight: 600;
                margin-bottom: 5px;
                color: #2d3748;
            }

            .option-desc {
                font-size: 0.9rem;
                color: #718096;
                margin-bottom: 8px;
            }

            .option-size {
                font-size: 0.8rem;
                color: #a0aec0;
                font-weight: 500;
            }

            .report-options-section {
                margin: 30px 0;
                padding: 20px;
                background: #f7fafc;
                border-radius: 12px;
            }

            .report-options-section h4 {
                margin: 0 0 15px 0;
                color: #2d3748;
                font-size: 1.1rem;
            }

            .options-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
            }

            .option-checkbox {
                display: flex;
                align-items: center;
                cursor: pointer;
                font-size: 0.95rem;
                color: #2d3748;
            }

            .option-checkbox input {
                margin-right: 10px;
                transform: scale(1.2);
            }

            .report-preview-section {
                margin-top: 25px;
            }

            .report-preview-section h4 {
                margin-bottom: 15px;
                color: #2d3748;
            }

            .preview-sample {
                border: 2px dashed #e2e8f0;
                border-radius: 8px;
                padding: 20px;
                background: #fafafa;
            }

            .preview-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 1px solid #e2e8f0;
            }

            .preview-header h5 {
                margin: 0;
                color: #2d3748;
            }

            .preview-date {
                color: #718096;
                font-size: 0.9rem;
            }

            .preview-section {
                padding: 8px 0;
                color: #4a5568;
                font-size: 0.9rem;
            }

            .modal-footer {
                padding: 20px 30px;
                border-top: 1px solid #e2e8f0;
                background: #f7fafc;
                border-radius: 0 0 16px 16px;
            }

            .generation-status {
                text-align: center;
                color: #4a5568;
                font-weight: 500;
            }

            @media (max-width: 768px) {
                .modal-content-enhanced {
                    width: 95%;
                    margin: 20px;
                }

                .modal-header, .modal-body, .modal-footer {
                    padding: 20px;
                }

                .report-options-grid {
                    grid-template-columns: 1fr;
                    gap: 12px;
                }

                .options-grid {
                    grid-template-columns: 1fr;
                }
            }
        `;

        document.head.appendChild(style);
    }

    addModalEventListeners(modal) {
        // Close button
        modal.querySelector('.modal-close-btn').addEventListener('click', () => {
            this.hideModal(modal);
        });

        // Backdrop click
        modal.querySelector('.modal-backdrop').addEventListener('click', () => {
            this.hideModal(modal);
        });

        // Report format buttons
        modal.querySelectorAll('.report-option-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const format = btn.dataset.format;
                this.generateReport(format, modal);
            });
        });

        // Escape key
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                this.hideModal(modal);
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);
    }

    hideModal(modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.remove();
        }, 300);
    }

    async generateReport(format, modal) {
        if (this.isGenerating) return;

        this.isGenerating = true;
        const btn = modal.querySelector(`[data-format="${format}"]`);
        const originalHTML = btn.innerHTML;
        const statusDiv = modal.querySelector('#generation-status');

        // Update button state
        btn.classList.add('generating');
        btn.innerHTML = `
            <div class="option-icon">⏳</div>
            <div class="option-title">Generating...</div>
            <div class="option-desc">Please wait</div>
        `;

        try {
            // Get report options
            const options = this.getReportOptions(modal);

            statusDiv.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; gap: 10px;">
                    <div class="spinner" style="width: 20px; height: 20px; border: 2px solid #e2e8f0; border-top: 2px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                    <span>Generating ${format.toUpperCase()} report...</span>
                </div>
                <style>
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                </style>
            `;

            // Generate report based on format
            let success = false;
            switch (format) {
                case 'png':
                    success = await this.generateImageReport(options);
                    break;
                case 'pdf':
                    success = await this.generatePDFReport(options);
                    break;
                case 'html':
                    success = await this.generateHTMLReport(options);
                    break;
                case 'json':
                    success = await this.generateJSONReport(options);
                    break;
                default:
                    throw new Error('Unsupported format: ' + format);
            }

            if (success) {
                statusDiv.innerHTML = `
                    <div style="color: #48bb78; font-weight: 600;">
                        ✅ ${format.toUpperCase()} report generated successfully!
                    </div>
                `;

                // Track analytics
                this.trackReportGeneration(format, 'success');

                // Auto-close modal after success
                setTimeout(() => {
                    this.hideModal(modal);
                }, 2000);
            }

        } catch (error) {
            console.error('Report generation error:', error);
            statusDiv.innerHTML = `
                <div style="color: #e53e3e; font-weight: 600;">
                    ❌ Failed to generate report: ${error.message}
                </div>
            `;
            this.trackReportGeneration(format, 'error', error.message);
        } finally {
            this.isGenerating = false;
            btn.classList.remove('generating');
            btn.innerHTML = originalHTML;
        }
    }

    getReportOptions(modal) {
        return {
            includeCharts: modal.querySelector('#include-charts')?.checked ?? true,
            includeAnalysis: modal.querySelector('#include-analysis')?.checked ?? true,
            includeRoadmap: modal.querySelector('#include-roadmap')?.checked ?? true,
            includeActions: modal.querySelector('#include-actions')?.checked ?? true,
            timestamp: new Date().toISOString()
        };
    }

    async generateImageReport(options) {
        const container = document.getElementById('tool-results');
        if (!container) throw new Error('No results to capture');

        // Check if html2canvas is available
        if (typeof html2canvas === 'undefined') {
            throw new Error('html2canvas library not loaded');
        }

        // Temporarily modify styles for better capture
        const originalStyle = container.style.cssText;
        container.style.background = 'white';
        container.style.padding = '40px';
        container.style.borderRadius = '0';
        container.style.boxShadow = 'none';

        // Hide copy buttons
        const copyBtns = container.querySelectorAll('.copy-section-btn');
        copyBtns.forEach(btn => btn.style.display = 'none');

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

            return true;

        } finally {
            // Restore original styles
            container.style.cssText = originalStyle;
            copyBtns.forEach(btn => btn.style.display = '');
        }
    }

    async generatePDFReport(options) {
        // Check if jsPDF is available
        if (typeof window.jspdf === 'undefined') {
            throw new Error('jsPDF library not loaded');
        }

        const { jsPDF } = window.jspdf;
        const container = document.getElementById('tool-results');
        if (!container) throw new Error('No results to capture');

        // Hide copy buttons temporarily
        const copyBtns = container.querySelectorAll('.copy-section-btn');
        copyBtns.forEach(btn => btn.style.display = 'none');

        try {
            // Check if html2canvas is available for PDF generation
            if (typeof html2canvas === 'undefined') {
                throw new Error('html2canvas library required for PDF generation');
            }

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

            // Add header
            pdf.setFontSize(20);
            pdf.setFont('helvetica', 'bold');
            const title = this.config.seo_data?.title || 'Calculator Report';
            pdf.text(title, pdfWidth / 2, 15, { align: 'center' });

            // Add main content
            pdf.addImage(imgData, 'PNG', imgX, imgY, imgWidth * ratio * 96 / 72, imgHeight * ratio * 96 / 72);

            // Add footer
            pdf.setFontSize(10);
            pdf.setFont('helvetica', 'normal');
            pdf.text(`Generated on ${new Date().toLocaleDateString()}`, pdfWidth / 2, pdfHeight - 15, { align: 'center' });
            pdf.text('Powered by AI Calculator System', pdfWidth / 2, pdfHeight - 8, { align: 'center' });

            // Save the PDF
            pdf.save(`${this.config.slug}-report-${new Date().toISOString().split('T')[0]}.pdf`);

            return true;

        } finally {
            // Restore copy buttons
            copyBtns.forEach(btn => btn.style.display = '');
        }
    }

    async generateHTMLReport(options) {
        const container = document.getElementById('tool-results');
        if (!container) throw new Error('No results to capture');

        const title = this.config.seo_data?.title || 'Calculator Report';
        const category = (this.config.category || '').toUpperCase();
        const toolName = this.config.base_name || '';
        const slug = this.config.slug || 'calculator-report';
        const today = new Date().toLocaleDateString();
        const filename = `${slug}-interactive-report-${new Date().toISOString().split('T')[0]}.html`;

        // Get container HTML and clean it
        let containerHtml = container.innerHTML;

        // Remove copy buttons from HTML
        containerHtml = containerHtml.replace(/<button[^>]*copy-section-btn[^>]*>.*?<\/button>/g, '');

        // Get chart data for reconstruction
        const chartData = this.getChartDataForExport();

        // Create CSS (condensed version)
        const safeCss = this.getExportCSS();

        // Create chart initialization script
        const safeChartJs = this.getChartExportScript(chartData);

        // Build the complete HTML
        const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.min.js"></script>
    <style>
        ${safeCss}
    </style>
</head>
<body>
    <div class="report-container">
        <header class="report-header">
            <h1>${title}</h1>
            <p>Generated on ${today}</p>
            <div class="report-meta">
                <span>Category: ${category}</span>
                <span>Tool: ${toolName}</span>
            </div>
        </header>
        ${containerHtml}
        <footer class="report-footer">
            <p>Powered by AI Calculator System</p>
            <p>This report contains interactive charts and analysis</p>
        </footer>
    </div>
    <script>
        // Re-initialize charts after DOM load
        setTimeout(() => {
            ${safeChartJs}
        }, 100);
    </script>
</body>
</html>`;

        // Create and download the file
        const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
        const link = document.createElement('a');
        link.download = filename;
        link.href = URL.createObjectURL(blob);

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);

        return true;
    }

    async generateJSONReport(options) {
        const container = document.getElementById('tool-results');
        if (!container) throw new Error('No results to capture');

        // Extract all data from the results
        const reportData = {
            metadata: {
                tool: this.config.slug,
                category: this.config.category,
                title: this.config.seo_data?.title || this.config.base_name,
                generatedAt: new Date().toISOString(),
                version: '1.0.0'
            },
            options: options,
            metrics: this.extractMetricsData(),
            charts: this.getChartDataForExport(),
            analysis: this.extractAnalysisData(),
            roadmap: this.extractRoadmapData(),
            actions: this.extractActionsData(),
            rawHTML: container.innerHTML
        };

        // Create and download JSON file
        const jsonString = JSON.stringify(reportData, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const link = document.createElement('a');
        link.download = `${this.config.slug}-data-${new Date().toISOString().split('T')[0]}.json`;
        link.href = URL.createObjectURL(blob);

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);

        return true;
    }

    getChartDataForExport() {
        if (!this.chartManager) return {};

        const chartData = {};
        Object.keys(this.chartManager.charts).forEach(chartName => {
            const data = this.chartManager.getChartData(chartName);
            if (data) {
                chartData[chartName] = {
                    type: data.type,
                    data: data.data,
                    options: data.options
                };
            }
        });

        return chartData;
    }

    getChartExportScript(chartData) {
        let script = `
            try {
                if (typeof Chart !== 'undefined') {
                    Chart.defaults.font.family = "'Inter', sans-serif";
        `;

        Object.keys(chartData).forEach(chartName => {
            const chart = chartData[chartName];
            script += `
                    const ${chartName}Ctx = document.getElementById('${chartName}');
                    if (${chartName}Ctx) {
                        new Chart(${chartName}Ctx, ${JSON.stringify({
                            type: chart.type,
                            data: chart.data,
                            options: chart.options
                        })});
                    }
            `;
        });

        script += `
                }
            } catch (error) {
                console.error('Chart initialization error:', error);
            }
        `;

        return script;
    }

    getExportCSS() {
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
                flex-wrap: wrap;
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
            .enhanced-results-container { animation: none; }
            @media (max-width: 768px) {
                .report-container { padding: 20px; }
                .report-header h1 { font-size: 2rem; }
                .report-meta { flex-direction: column; align-items: center; gap: 10px; }
            }
        `;
    }

    extractMetricsData() {
        const metrics = [];
        document.querySelectorAll('.metric-card-enhanced').forEach(card => {
            const icon = card.querySelector('.metric-icon')?.textContent || '';
            const label = card.querySelector('.metric-label')?.textContent || '';
            const value = card.querySelector('.metric-value')?.textContent || '';
            const change = card.querySelector('.metric-change')?.textContent || '';

            metrics.push({ icon, label, value, change });
        });
        return metrics;
    }

    extractAnalysisData() {
        const analysisSection = document.querySelector('.ai-analysis-section .ai-content-wrapper');
        return analysisSection ? analysisSection.textContent.trim() : '';
    }

    extractRoadmapData() {
        const roadmap = [];
        document.querySelectorAll('.ladder-step-enhanced').forEach(step => {
            const title = step.querySelector('.step-title')?.textContent || '';
            const description = step.querySelector('.step-description')?.textContent || '';
            const value = step.querySelector('.step-value')?.textContent || '';
            const timeline = step.querySelector('.step-timeline')?.textContent || '';
            const icon = step.querySelector('.step-icon')?.textContent || '';

            roadmap.push({ title, description, value, timeline, icon });
        });
        return roadmap;
    }

    extractActionsData() {
        const actions = [];
        document.querySelectorAll('.action-item-card').forEach(card => {
            const title = card.querySelector('.action-title')?.textContent || '';
            const description = card.querySelector('.action-description')?.textContent || '';
            const priority = card.dataset.priority || '';
            const timeline = card.querySelector('.action-timeline')?.textContent || '';
            const effort = card.querySelector('.action-effort')?.textContent || '';
            const icon = card.querySelector('.action-icon')?.textContent || '';

            actions.push({ title, description, priority, timeline, effort, icon });
        });
        return actions;
    }

    trackReportGeneration(format, status, error = null) {
        const eventData = {
            format: format,
            status: status,
            tool: this.config.slug,
            category: this.config.category,
            timestamp: new Date().toISOString()
        };

        if (error) {
            eventData.error = error;
        }

        // Track with analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'report_generated', eventData);
        }

        console.log('📊 Report generation:', eventData);
    }

    // Get report generation statistics
    getStats() {
        return {
            isGenerating: this.isGenerating,
            supportedFormats: this.reportFormats,
            lastGenerated: this.lastGeneratedTime || null
        };
    }
}

// Export for global access
window.ReportGenerator = ReportGenerator;