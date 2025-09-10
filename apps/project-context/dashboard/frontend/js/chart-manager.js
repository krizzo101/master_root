/**
 * Chart Manager
 * Handles all chart rendering and updates using Chart.js
 */
class ChartManager {
    constructor() {
        this.charts = new Map();
        this.defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 750,
                easing: 'easeOutQuart'
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                }
            }
        };

        // Color palettes
        this.colors = {
            primary: '#3b82f6',
            success: '#10b981',
            warning: '#f59e0b',
            danger: '#ef4444',
            info: '#06b6d4',
            secondary: '#6b7280',

            // Status colors
            running: '#3b82f6',
            completed: '#10b981',
            failed: '#ef4444',
            pending: '#6b7280',

            // Chart color palette
            palette: [
                '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
                '#06b6d4', '#8b5cf6', '#ec4899', '#14b8a6'
            ]
        };
    }

    // Initialize Chart.js if not already loaded
    async ensureChartJS() {
        if (typeof Chart === 'undefined') {
            console.log('Loading Chart.js...');
            await this.loadScript('https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js');
            console.log('Chart.js loaded successfully');
        }
    }

    // Load external script
    loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    // Create or update a chart
    async createChart(canvasId, type, data, options = {}) {
        await this.ensureChartJS();

        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.error(`Canvas element with ID '${canvasId}' not found`);
            return null;
        }

        const ctx = canvas.getContext('2d');

        // Destroy existing chart if it exists
        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }

        // Merge options with defaults
        const chartOptions = this.mergeOptions(this.defaultOptions, options);

        // Create new chart
        const chart = new Chart(ctx, {
            type: type,
            data: data,
            options: chartOptions
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    // Update existing chart data
    updateChart(canvasId, newData, animate = true) {
        const chart = this.charts.get(canvasId);
        if (!chart) {
            console.warn(`Chart with ID '${canvasId}' not found`);
            return;
        }

        // Update data
        if (newData.labels) {
            chart.data.labels = newData.labels;
        }

        if (newData.datasets) {
            chart.data.datasets = newData.datasets;
        }

        // Update with or without animation
        chart.update(animate ? undefined : 'none');
    }

    // Create performance metrics chart
    async createPerformanceChart(canvasId, performanceData) {
        const data = {
            labels: performanceData.timestamps || [],
            datasets: [
                {
                    label: 'CPU Usage (%)',
                    data: performanceData.cpu || [],
                    borderColor: this.colors.primary,
                    backgroundColor: this.addAlpha(this.colors.primary, 0.1),
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Memory Usage (%)',
                    data: performanceData.memory || [],
                    borderColor: this.colors.success,
                    backgroundColor: this.addAlpha(this.colors.success, 0.1),
                    fill: true,
                    tension: 0.4
                }
            ]
        };

        const options = {
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: (value) => value + '%'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'System Performance Metrics'
                }
            }
        };

        return await this.createChart(canvasId, 'line', data, options);
    }

    // Create task status distribution chart
    async createTaskStatusChart(canvasId, taskData) {
        const statusCounts = this.calculateStatusCounts(taskData);

        const data = {
            labels: Object.keys(statusCounts),
            datasets: [{
                data: Object.values(statusCounts),
                backgroundColor: [
                    this.colors.running,
                    this.colors.completed,
                    this.colors.failed,
                    this.colors.pending
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        };

        const options = {
            plugins: {
                title: {
                    display: true,
                    text: 'Task Status Distribution'
                },
                legend: {
                    position: 'right'
                }
            }
        };

        return await this.createChart(canvasId, 'doughnut', data, options);
    }

    // Create progress timeline chart
    async createProgressChart(canvasId, progressData) {
        const data = {
            labels: progressData.timestamps || [],
            datasets: [{
                label: 'Progress %',
                data: progressData.progress || [],
                borderColor: this.colors.primary,
                backgroundColor: this.addAlpha(this.colors.primary, 0.2),
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 6
            }]
        };

        const options = {
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: (value) => value + '%'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Overall Progress Timeline'
                }
            }
        };

        return await this.createChart(canvasId, 'line', data, options);
    }

    // Create execution time comparison chart
    async createExecutionTimeChart(canvasId, taskData) {
        const executionTimes = this.calculateExecutionTimes(taskData);

        const data = {
            labels: executionTimes.map(item => item.name),
            datasets: [{
                label: 'Execution Time (seconds)',
                data: executionTimes.map(item => item.time),
                backgroundColor: this.colors.palette.slice(0, executionTimes.length),
                borderColor: this.colors.palette.slice(0, executionTimes.length),
                borderWidth: 1
            }]
        };

        const options = {
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: (value) => value + 's'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Task Execution Times'
                }
            }
        };

        return await this.createChart(canvasId, 'bar', data, options);
    }

    // Create real-time metrics chart
    async createRealTimeChart(canvasId, maxDataPoints = 50) {
        const data = {
            labels: [],
            datasets: [
                {
                    label: 'Active Tasks',
                    data: [],
                    borderColor: this.colors.primary,
                    backgroundColor: this.addAlpha(this.colors.primary, 0.1),
                    fill: false,
                    tension: 0.4
                },
                {
                    label: 'Completed/Min',
                    data: [],
                    borderColor: this.colors.success,
                    backgroundColor: this.addAlpha(this.colors.success, 0.1),
                    fill: false,
                    tension: 0.4
                }
            ]
        };

        const options = {
            scales: {
                x: {
                    type: 'time',
                    time: {
                        displayFormats: {
                            second: 'HH:mm:ss'
                        }
                    },
                    ticks: {
                        maxTicksLimit: 10
                    }
                },
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Real-time Metrics'
                }
            },
            animation: {
                duration: 0 // Disable animation for real-time updates
            }
        };

        const chart = await this.createChart(canvasId, 'line', data, options);

        // Store max data points for this chart
        if (chart) {
            chart.maxDataPoints = maxDataPoints;
        }

        return chart;
    }

    // Add data point to real-time chart
    addDataPoint(canvasId, timestamp, values) {
        const chart = this.charts.get(canvasId);
        if (!chart) return;

        const maxPoints = chart.maxDataPoints || 50;

        // Add new data point
        chart.data.labels.push(timestamp);
        values.forEach((value, index) => {
            if (chart.data.datasets[index]) {
                chart.data.datasets[index].data.push(value);
            }
        });

        // Remove old data points if exceeding max
        if (chart.data.labels.length > maxPoints) {
            chart.data.labels.shift();
            chart.data.datasets.forEach(dataset => {
                dataset.data.shift();
            });
        }

        chart.update('none'); // Update without animation for real-time feel
    }

    // Utility methods
    calculateStatusCounts(tasks) {
        const counts = { running: 0, completed: 0, failed: 0, pending: 0 };

        if (Array.isArray(tasks)) {
            tasks.forEach(task => {
                const status = task.status?.toLowerCase() || 'pending';
                if (counts.hasOwnProperty(status)) {
                    counts[status]++;
                }
            });
        }

        return counts;
    }

    calculateExecutionTimes(tasks) {
        if (!Array.isArray(tasks)) return [];

        return tasks
            .filter(task => task.execution_time && task.task_id)
            .map(task => ({
                name: task.task_id.substring(0, 20) + '...',
                time: task.execution_time / 1000 // Convert to seconds
            }))
            .sort((a, b) => b.time - a.time)
            .slice(0, 10); // Top 10 longest running tasks
    }

    addAlpha(color, alpha) {
        const hex = color.replace('#', '');
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    mergeOptions(defaults, overrides) {
        const merged = JSON.parse(JSON.stringify(defaults));
        return this.deepMerge(merged, overrides);
    }

    deepMerge(target, source) {
        for (const key in source) {
            if (source.hasOwnProperty(key)) {
                if (typeof source[key] === 'object' && source[key] !== null && !Array.isArray(source[key])) {
                    target[key] = target[key] || {};
                    this.deepMerge(target[key], source[key]);
                } else {
                    target[key] = source[key];
                }
            }
        }
        return target;
    }

    // Cleanup
    destroyChart(canvasId) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.destroy();
            this.charts.delete(canvasId);
        }
    }

    destroyAllCharts() {
        this.charts.forEach((chart, canvasId) => {
            chart.destroy();
        });
        this.charts.clear();
    }

    // Get chart instance
    getChart(canvasId) {
        return this.charts.get(canvasId);
    }

    // Get all chart instances
    getAllCharts() {
        return Array.from(this.charts.values());
    }
}

// Export singleton instance
window.chartManager = new ChartManager();
window.ChartManager = ChartManager;
