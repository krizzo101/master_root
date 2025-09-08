/**
 * Workflow Comparison View Controller
 * Manages the multi-workflow comparison interface
 */

class WorkflowComparisonView {
    constructor(apiClient) {
        this.apiClient = apiClient;

        // DOM elements
        this.modal = document.getElementById('comparison-modal');
        this.selectedWorkflowsContainer = document.getElementById('selected-workflows');
        this.comparisonTable = document.getElementById('comparison-table');
        this.performanceChart = document.getElementById('performance-chart');

        // State
        this.selectedWorkflows = [];
        this.comparisonData = null;
        this.chart = null;

        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Back button
        document.getElementById('back-to-dashboard-compare')?.addEventListener('click', () => {
            this.hide();
        });

        // Export and save buttons
        document.getElementById('export-comparison')?.addEventListener('click', () => {
            this.exportComparison();
        });

        document.getElementById('save-comparison')?.addEventListener('click', () => {
            this.saveComparison();
        });

        // Add workflow button
        document.getElementById('add-workflow-compare')?.addEventListener('click', () => {
            this.showAddWorkflowDialog();
        });

        // Remove workflow tags
        EventUtils.delegate(this.modal, '.remove-tag', 'click', (e) => {
            const tag = e.target.closest('.workflow-tag');
            if (tag) {
                const workflowName = tag.textContent.replace('×', '').trim();
                this.removeWorkflow(workflowName);
            }
        });

        // Custom events
        document.addEventListener('show-workflow-comparison', (e) => {
            this.show(e.detail);
        });
    }

    show(workflows) {
        this.selectedWorkflows = workflows || [];
        this.loadComparisonData();
        UI.showModal('comparison-modal');
    }

    hide() {
        this.selectedWorkflows = [];
        this.comparisonData = null;
        UI.hideModal('comparison-modal');
    }

    async loadComparisonData() {
        if (this.selectedWorkflows.length === 0) return;

        try {
            UI.showLoading('Loading comparison data...');

            // Generate comparison data
            this.comparisonData = await this.generateComparisonData(this.selectedWorkflows);

            // Update UI
            this.updateSelectedWorkflowTags();
            this.updateComparisonTable();
            this.updatePerformanceChart();
            this.updateComparativeAnalysis();

            UI.hideLoading();
        } catch (error) {
            console.error('Failed to load comparison data:', error);
            UI.hideLoading();
            UI.showToast(`Failed to load comparison data: ${error.message}`, 'error');
        }
    }

    async generateComparisonData(workflows) {
        // In a real implementation, this would fetch detailed metrics from the API
        // For now, we'll generate realistic sample data

        const comparisonData = {
            workflows: workflows.map(workflow => ({
                ...workflow,
                metrics: this.generateMetrics(workflow),
                performanceHistory: this.generatePerformanceHistory(workflow)
            })),
            insights: this.generateInsights(workflows),
            recommendations: this.generateRecommendations(workflows)
        };

        return comparisonData;
    }

    generateMetrics(workflow) {
        const baseMetrics = {
            status: workflow.status,
            progress: workflow.progress,
            startedAt: workflow.startTime,
            duration: workflow.duration,
            eta: workflow.eta,
            cpuUsageAvg: workflow.resourceUsage?.cpu || Math.floor(Math.random() * 20) + 5,
            memoryPeak: workflow.resourceUsage?.memory || `${(Math.random() * 3 + 0.5).toFixed(1)}GB`,
            filesGenerated: workflow.deliverables?.length || Math.floor(Math.random() * 15) + 3,
            outputSize: DataUtils.formatBytes(Math.floor(Math.random() * 10000000) + 1000000),
            errors: Math.floor(Math.random() * 3),
            lastCheckpoint: TimeUtils.formatDateTime(new Date(Date.now() - Math.random() * 3600000))
        };

        return baseMetrics;
    }

    generatePerformanceHistory(workflow) {
        const points = 20;
        const history = [];
        const baseUsage = workflow.resourceUsage?.cpu || Math.floor(Math.random() * 20) + 5;

        for (let i = 0; i < points; i++) {
            const timestamp = Date.now() - (points - i) * 300000; // 5-minute intervals
            const variation = (Math.random() - 0.5) * 10;
            const usage = Math.max(0, Math.min(100, baseUsage + variation));

            history.push({
                timestamp,
                cpuUsage: usage,
                memoryUsage: Math.random() * 1000 + 500 // MB
            });
        }

        return history;
    }

    generateInsights(workflows) {
        const insights = [];

        // Find best performer
        const completed = workflows.filter(w => w.status === 'completed');
        if (completed.length > 0) {
            const best = completed.reduce((prev, curr) =>
                (prev.errors || 0) < (curr.errors || 0) ? prev : curr
            );
            insights.push({
                type: 'best',
                icon: '🏆',
                text: `Best Performer: ${best.name} (${best.status}, ${best.errors || 0} errors)`
            });
        }

        // Find issues
        const paused = workflows.filter(w => w.status === 'paused');
        if (paused.length > 0) {
            const pausedTime = TimeUtils.formatTimeAgo(paused[0].lastUpdated);
            insights.push({
                type: 'warning',
                icon: '⚠️',
                text: `Attention Needed: ${paused[0].name} (paused ${pausedTime})`
            });
        }

        // Find most efficient
        const running = workflows.filter(w => w.status === 'running');
        if (running.length > 0) {
            const efficient = running.reduce((prev, curr) => {
                const prevEfficiency = (prev.progress || 0) / ((prev.resourceUsage?.cpu || 10) / 100);
                const currEfficiency = (curr.progress || 0) / ((curr.resourceUsage?.cpu || 10) / 100);
                return currEfficiency > prevEfficiency ? curr : prev;
            });
            insights.push({
                type: 'efficient',
                icon: '📈',
                text: `Most Efficient: ${efficient.name} (lowest resource usage per progress)`
            });
        }

        // Resource intensive
        const resourceIntensive = workflows.reduce((prev, curr) => {
            const prevMem = parseFloat(prev.resourceUsage?.memory || '1GB');
            const currMem = parseFloat(curr.resourceUsage?.memory || '1GB');
            return currMem > prevMem ? curr : prev;
        });
        insights.push({
            type: 'resource',
            icon: '🔄',
            text: `Resource Intensive: ${resourceIntensive.name} (${resourceIntensive.resourceUsage?.memory || '2.5GB'} peak memory)`
        });

        return insights;
    }

    generateRecommendations(workflows) {
        const recommendations = [];

        // Check for paused workflows
        const paused = workflows.filter(w => w.status === 'paused');
        if (paused.length > 0) {
            recommendations.push(`Resume ${paused[0].name} - paused for extended period`);
        }

        // Check for high resource usage
        const highResource = workflows.filter(w => {
            const cpu = w.resourceUsage?.cpu || 0;
            return cpu > 15;
        });
        if (highResource.length > 0) {
            recommendations.push(`Monitor ${highResource[0].name} memory usage - trending upward`);
        }

        // Check for completed workflows
        const completed = workflows.filter(w => w.status === 'completed');
        if (completed.length > 0) {
            recommendations.push(`Archive ${completed[0].name} outputs to free disk space`);
        }

        return recommendations;
    }

    updateSelectedWorkflowTags() {
        if (!this.selectedWorkflowsContainer) return;

        this.selectedWorkflowsContainer.innerHTML = '';

        this.selectedWorkflows.forEach(workflow => {
            const tag = DomUtils.createElement('span', {
                className: 'workflow-tag'
            });

            tag.innerHTML = `
                ${workflow.name}
                <button class="remove-tag" aria-label="Remove ${workflow.name}">×</button>
            `;

            this.selectedWorkflowsContainer.appendChild(tag);
        });
    }

    updateComparisonTable() {
        if (!this.comparisonTable || !this.comparisonData) return;

        const table = this.createComparisonTable(this.comparisonData.workflows);
        this.comparisonTable.innerHTML = '';
        this.comparisonTable.appendChild(table);
    }

    createComparisonTable(workflows) {
        const table = DomUtils.createElement('table', {
            className: 'comparison-data-table',
            style: 'width: 100%; border-collapse: collapse;'
        });

        // Create header
        const thead = DomUtils.createElement('thead');
        const headerRow = DomUtils.createElement('tr');

        // Metric column
        const metricHeader = DomUtils.createElement('th', {
            style: 'text-align: left; padding: 1rem; border-bottom: 1px solid var(--border-color); background: var(--bg-secondary);'
        }, ['METRIC']);
        headerRow.appendChild(metricHeader);

        // Workflow columns
        workflows.forEach(workflow => {
            const workflowHeader = DomUtils.createElement('th', {
                style: 'text-align: center; padding: 1rem; border-bottom: 1px solid var(--border-color); background: var(--bg-secondary);'
            }, [workflow.name]);
            headerRow.appendChild(workflowHeader);
        });

        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Create body
        const tbody = DomUtils.createElement('tbody');

        const metrics = [
            {
                label: 'Status',
                getValue: (w) => StatusUtils.getStatusText(w.status),
                getStyle: (w) => `color: ${StatusUtils.getStatusColor(w.status)}`
            },
            {
                label: 'Progress',
                getValue: (w) => `${w.progress}%`,
                getStyle: () => ''
            },
            {
                label: 'Started',
                getValue: (w) => TimeUtils.formatDateTime(w.startTime),
                getStyle: () => ''
            },
            {
                label: 'Duration',
                getValue: (w) => {
                    if (w.status === 'paused') {
                        return `${TimeUtils.formatDuration(w.duration)} (paused)`;
                    }
                    return TimeUtils.formatDuration(w.duration);
                },
                getStyle: () => ''
            },
            {
                label: 'ETA',
                getValue: (w) => {
                    if (w.status === 'completed') return 'Completed';
                    if (w.eta) return TimeUtils.formatETA(w.eta);
                    return '~15 min';
                },
                getStyle: () => ''
            },
            {
                label: 'CPU Usage (avg)',
                getValue: (w) => `${w.metrics.cpuUsageAvg}%`,
                getStyle: () => ''
            },
            {
                label: 'Memory Peak',
                getValue: (w) => w.metrics.memoryPeak,
                getStyle: () => ''
            },
            {
                label: 'Files Generated',
                getValue: (w) => `${w.metrics.filesGenerated}/${w.metrics.filesGenerated + 2}`,
                getStyle: () => ''
            },
            {
                label: 'Output Size',
                getValue: (w) => w.metrics.outputSize,
                getStyle: () => ''
            },
            {
                label: 'Errors',
                getValue: (w) => {
                    const errors = w.metrics.errors;
                    if (errors === 0) return '0';
                    if (errors === 1) return '1 warning';
                    return `${errors} errors`;
                },
                getStyle: (w) => w.metrics.errors > 0 ? 'color: var(--status-failed)' : 'color: var(--status-running)'
            },
            {
                label: 'Last Checkpoint',
                getValue: (w) => w.metrics.lastCheckpoint,
                getStyle: () => ''
            }
        ];

        metrics.forEach(metric => {
            const row = DomUtils.createElement('tr');

            // Metric name
            const nameCell = DomUtils.createElement('td', {
                style: 'padding: 0.75rem 1rem; border-bottom: 1px solid var(--border-light); font-weight: 600; background: var(--bg-secondary);'
            }, [metric.label]);
            row.appendChild(nameCell);

            // Values for each workflow
            workflows.forEach(workflow => {
                const value = metric.getValue(workflow);
                const style = metric.getStyle(workflow);

                const valueCell = DomUtils.createElement('td', {
                    style: `padding: 0.75rem 1rem; border-bottom: 1px solid var(--border-light); text-align: center; ${style}`
                }, [value]);
                row.appendChild(valueCell);
            });

            tbody.appendChild(row);
        });

        table.appendChild(tbody);
        return table;
    }

    updatePerformanceChart() {
        if (!this.performanceChart || !this.comparisonData) return;

        // For this demo, we'll create a simple text-based chart
        // In a real implementation, you'd use Chart.js or similar
        this.createTextChart();
    }

    createTextChart() {
        if (!this.performanceChart) return;

        const chartContainer = DomUtils.createElement('div', {
            style: 'font-family: monospace; background: var(--bg-primary); padding: 1rem; border-radius: 0.5rem; overflow-x: auto;'
        });

        const chartText = `
CPU %  ┃
  20 ┃  ●●●
     ┃     ●
  15 ┃      ●●●
     ┃         ●
  10 ┃          ●●●●●●●●●●●●●●●●●●   ━━━━━━━━ (paused)
     ┃                              ●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●
   5 ┃
     ┃
   0 ┣━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┳━━━┫
     12:45  13:00  13:15  13:30  13:45  14:00  14:15  14:30         Time
        `;

        chartContainer.innerHTML = `<pre>${chartText.trim()}</pre>`;

        this.performanceChart.innerHTML = '';
        this.performanceChart.appendChild(chartContainer);
    }

    updateComparativeAnalysis() {
        if (!this.comparisonData) return;

        const analysisContainer = this.modal.querySelector('.analysis-insights');
        if (analysisContainer) {
            analysisContainer.innerHTML = '';

            this.comparisonData.insights.forEach(insight => {
                const insightEl = DomUtils.createElement('div', {
                    className: `insight ${insight.type}`
                }, [`${insight.icon} ${insight.text}`]);

                analysisContainer.appendChild(insightEl);
            });
        }

        const recommendationsContainer = this.modal.querySelector('.recommendations ul');
        if (recommendationsContainer) {
            recommendationsContainer.innerHTML = '';

            this.comparisonData.recommendations.forEach(recommendation => {
                const li = DomUtils.createElement('li', {}, [recommendation]);
                recommendationsContainer.appendChild(li);
            });
        }
    }

    removeWorkflow(workflowName) {
        this.selectedWorkflows = this.selectedWorkflows.filter(w => w.name !== workflowName);

        if (this.selectedWorkflows.length < 2) {
            UI.showToast('Comparison requires at least 2 workflows', 'warning');
            this.hide();
            return;
        }

        this.loadComparisonData();
    }

    showAddWorkflowDialog() {
        UI.showToast('Add workflow to comparison - Feature coming soon', 'info');
    }

    exportComparison() {
        if (!this.comparisonData) {
            UI.showToast('No comparison data to export', 'warning');
            return;
        }

        const exportData = {
            timestamp: new Date().toISOString(),
            workflows: this.selectedWorkflows.map(w => w.name),
            comparison: this.comparisonData,
            insights: this.comparisonData.insights,
            recommendations: this.comparisonData.recommendations
        };

        const data = JSON.stringify(exportData, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `workflow-comparison-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        UI.showToast('Comparison exported', 'success');
    }

    saveComparison() {
        if (!this.comparisonData) {
            UI.showToast('No comparison data to save', 'warning');
            return;
        }

        const comparisonId = DataUtils.generateId('comparison');
        const savedComparisons = StorageUtils.get('dashboard.savedComparisons') || [];

        const comparisonSave = {
            id: comparisonId,
            name: `Comparison ${savedComparisons.length + 1}`,
            workflows: this.selectedWorkflows.map(w => w.name),
            createdAt: new Date().toISOString(),
            data: this.comparisonData
        };

        savedComparisons.push(comparisonSave);
        StorageUtils.set('dashboard.savedComparisons', savedComparisons);

        UI.showToast('Comparison saved', 'success');
    }
}

// Export for global use
if (typeof window !== 'undefined') {
    window.WorkflowComparisonView = WorkflowComparisonView;
}
