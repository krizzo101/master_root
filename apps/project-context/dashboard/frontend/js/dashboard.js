/**
 * Main Dashboard Application
 * Orchestrates all dashboard functionality and real-time updates
 */
class Dashboard {
    constructor() {
        this.wsManager = null;
        this.apiClient = null;
        this.lastUpdate = null;
        this.updateInterval = 5000; // 5 seconds
        this.autoUpdateTimer = null;
        this.isInitialized = false;

        // Component states
        this.currentFilter = 'all';
        this.sortColumn = null;
        this.sortDirection = 'asc';
        this.searchQuery = '';

        // Data cache
        this.cache = {
            status: null,
            tasks: [],
            performance: null,
            lastFetchTime: 0
        };

        // Performance tracking
        this.startTime = Date.now();
        this.metricsHistory = [];

        this.init();
    }

    async init() {
        try {
            console.log('Initializing dashboard...');

            // Initialize API client - use current host instead of hardcoded port
            const currentHost = window.location.protocol + '//' + window.location.host;
            this.apiClient = new ApiClient(currentHost);

            // Initialize WebSocket manager - use current host
            const wsHost = window.location.host;
            this.wsManager = new WebSocketManager(`ws://${wsHost}/ws`);

            // Set up WebSocket event listeners
            this.setupWebSocketListeners();

            // Set up DOM event listeners
            this.setupDOMEventListeners();

            // Load initial data
            await this.loadInitialData();

            // Start auto-update
            this.startAutoUpdate();

            // Initialize charts
            await this.initializeCharts();

            this.isInitialized = true;
            console.log('Dashboard initialized successfully');

            // Show success notification
            domUtils.createNotification('Dashboard connected successfully', 'success', 3000);

        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            domUtils.createNotification('Failed to initialize dashboard: ' + error.message, 'danger', 0);
        }
    }

    setupWebSocketListeners() {
        // Connection events
        this.wsManager.on('connected', () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus('connected');
        });

        this.wsManager.on('disconnected', () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus('disconnected');
        });

        this.wsManager.on('error', (error) => {
            console.error('WebSocket error:', error);
            domUtils.createNotification('Connection error: ' + error.type, 'warning');
        });

        // Data update events
        this.wsManager.on('taskUpdate', (data) => {
            this.handleTaskUpdate(data);
        });

        this.wsManager.on('statusUpdate', (data) => {
            this.handleStatusUpdate(data);
        });

        this.wsManager.on('performanceUpdate', (data) => {
            this.handlePerformanceUpdate(data);
        });
    }

    setupDOMEventListeners() {
        // Theme toggle
        const themeToggle = domUtils.byId('theme-toggle');
        if (themeToggle) {
            domUtils.on(themeToggle, 'click', () => this.toggleTheme());
        }

        // Task filters
        const filterButtons = domUtils.$$('.filter-btn');
        filterButtons.forEach(btn => {
            domUtils.on(btn, 'click', (e) => this.handleFilterChange(e));
        });

        // Table sorting
        const sortableHeaders = domUtils.$$('th[data-sort]');
        sortableHeaders.forEach(header => {
            domUtils.on(header, 'click', (e) => this.handleSort(e));
        });

        // Search functionality
        this.setupSearchFunctionality();

        // Window events
        domUtils.on(window, 'beforeunload', () => this.cleanup());
        domUtils.on(window, 'focus', () => this.handleWindowFocus());
        domUtils.on(window, 'blur', () => this.handleWindowBlur());
    }

    setupSearchFunctionality() {
        // Create search input if it doesn't exist
        let searchInput = domUtils.byId('task-search');
        if (!searchInput) {
            const taskHeader = domUtils.$('.task-monitoring-header');
            if (taskHeader) {
                searchInput = domUtils.createElement('input', {
                    id: 'task-search',
                    type: 'search',
                    placeholder: 'Search tasks...',
                    className: 'search-input'
                });
                taskHeader.appendChild(searchInput);
            }
        }

        if (searchInput) {
            const debouncedSearch = domUtils.debounce((value) => {
                this.searchQuery = value;
                this.updateTaskTable();
            }, 300);

            domUtils.on(searchInput, 'input', (e) => {
                debouncedSearch(e.target.value);
            });
        }
    }

    async loadInitialData() {
        try {
            console.log('Loading initial dashboard data...');

            const data = await this.apiClient.getDashboardData();

            this.cache.status = data.status;
            this.cache.tasks = data.tasks || [];
            this.cache.performance = data.performance;
            this.cache.lastFetchTime = Date.now();

            // Update UI components
            this.updateExecutiveSummary();
            this.updateTaskTable();

            console.log('Initial data loaded successfully');

        } catch (error) {
            console.error('Failed to load initial data:', error);
            domUtils.createNotification('Failed to load dashboard data', 'danger');
        }
    }

    updateExecutiveSummary() {
        const status = this.cache.status || {};
        const tasks = this.cache.tasks || [];

        // Calculate metrics
        const totalTasks = tasks.length;
        const completedTasks = tasks.filter(t => t.status === 'completed').length;
        const activeTasks = tasks.filter(t => t.status === 'running').length;
        const failedTasks = tasks.filter(t => t.status === 'failed').length;
        const overallProgress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

        // Calculate elapsed time
        const elapsedTime = this.formatElapsedTime(Date.now() - this.startTime);

        // Update DOM elements with animation
        this.updateMetricCard('overall-progress', `${overallProgress}%`);
        this.updateMetricCard('current-phase', status.current_phase || 'Initializing');
        this.updateMetricCard('elapsed-time', elapsedTime);
        this.updateMetricCard('active-tasks', activeTasks.toString());
        this.updateMetricCard('completed-tasks', completedTasks.toString());
        this.updateMetricCard('failed-tasks', failedTasks.toString());

        // Update last update time
        this.updateLastUpdateTime();
    }

    updateMetricCard(elementId, newValue) {
        const element = domUtils.byId(elementId);
        if (element) {
            const currentValue = element.textContent;
            if (currentValue !== newValue) {
                // Animate value change
                domUtils.addClass(element.parentElement, 'updating');
                setTimeout(() => {
                    domUtils.updateText(element, newValue);
                    domUtils.removeClass(element.parentElement, 'updating');
                }, 150);
            }
        }
    }

    updateTaskTable() {
        const tableContainer = domUtils.$('.task-table-container');
        const table = domUtils.$('.task-table tbody');

        if (!table) {
            console.warn('Task table not found');
            return;
        }

        // Filter and sort tasks
        let filteredTasks = this.filterTasks(this.cache.tasks);
        filteredTasks = this.sortTasks(filteredTasks);

        // Define table columns
        const columns = [
            { key: 'task_id', render: (value) => this.truncateText(value, 20) },
            { key: 'type', render: (value) => value || 'Unknown' },
            {
                key: 'status',
                render: (value) => `<span class="status-badge ${value}">${value}</span>`,
                className: 'status-cell'
            },
            {
                key: 'progress',
                render: (value) => {
                    const progress = parseInt(value) || 0;
                    return `
                        <div class="progress-bar" role="progressbar" aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100">
                            <div class="progress-fill" style="width: ${progress}%"></div>
                            <span class="progress-text">${progress}%</span>
                        </div>
                    `;
                }
            },
            { key: 'start_time', render: (value) => this.formatTimestamp(value) },
            {
                key: 'execution_time',
                render: (value) => value ? domUtils.formatDuration(value) : '-'
            },
            {
                key: 'actions',
                render: (value, row) => `
                    <button class="btn-small" onclick="dashboard.viewTaskDetails('${row.task_id}')">
                        View
                    </button>
                `
            }
        ];

        // Update table
        domUtils.updateTable(table.parentElement, filteredTasks, columns);
    }

    filterTasks(tasks) {
        if (!Array.isArray(tasks)) return [];

        let filtered = tasks;

        // Apply status filter
        if (this.currentFilter !== 'all') {
            filtered = filtered.filter(task => task.status === this.currentFilter);
        }

        // Apply search filter
        if (this.searchQuery.trim()) {
            const query = this.searchQuery.toLowerCase();
            filtered = filtered.filter(task =>
                (task.task_id && task.task_id.toLowerCase().includes(query)) ||
                (task.type && task.type.toLowerCase().includes(query)) ||
                (task.status && task.status.toLowerCase().includes(query))
            );
        }

        return filtered;
    }

    sortTasks(tasks) {
        if (!this.sortColumn || !Array.isArray(tasks)) return tasks;

        return [...tasks].sort((a, b) => {
            const aValue = domUtils.getNestedValue(a, this.sortColumn);
            const bValue = domUtils.getNestedValue(b, this.sortColumn);

            let comparison = 0;
            if (aValue < bValue) comparison = -1;
            if (aValue > bValue) comparison = 1;

            return this.sortDirection === 'desc' ? -comparison : comparison;
        });
    }

    handleTaskUpdate(data) {
        console.log('Task update received:', data);

        // Update task in cache
        const taskIndex = this.cache.tasks.findIndex(t => t.task_id === data.task_id);
        if (taskIndex >= 0) {
            this.cache.tasks[taskIndex] = { ...this.cache.tasks[taskIndex], ...data };
        } else {
            this.cache.tasks.push(data);
        }

        // Update UI
        this.updateExecutiveSummary();
        this.updateTaskTable();

        // Update charts
        this.updateChartsWithNewData();

        // Show notification for important updates
        if (data.status === 'completed') {
            domUtils.createNotification(`Task ${data.task_id} completed`, 'success');
        } else if (data.status === 'failed') {
            domUtils.createNotification(`Task ${data.task_id} failed`, 'danger');
        }
    }

    handleStatusUpdate(data) {
        console.log('Status update received:', data);

        this.cache.status = { ...this.cache.status, ...data };
        this.updateExecutiveSummary();
    }

    handlePerformanceUpdate(data) {
        console.log('Performance update received:', data);

        this.cache.performance = data;

        // Update real-time charts
        const timestamp = new Date();
        chartManager.addDataPoint('realtime-chart', timestamp, [
            data.active_tasks || 0,
            data.completion_rate || 0
        ]);
    }

    async initializeCharts() {
        try {
            // Performance chart
            const performanceData = {
                timestamps: this.generateTimeLabels(24), // Last 24 hours
                cpu: this.generateSampleData(24, 0, 100),
                memory: this.generateSampleData(24, 0, 100)
            };
            await chartManager.createPerformanceChart('performance-chart', performanceData);

            // Task status chart
            await chartManager.createTaskStatusChart('task-status-chart', this.cache.tasks);

            // Progress timeline
            const progressData = {
                timestamps: this.generateTimeLabels(10),
                progress: this.generateProgressData(10)
            };
            await chartManager.createProgressChart('progress-chart', progressData);

            // Real-time metrics chart
            await chartManager.createRealTimeChart('realtime-chart', 50);

        } catch (error) {
            console.error('Failed to initialize charts:', error);
        }
    }

    updateChartsWithNewData() {
        // Update task status chart
        chartManager.updateChart('task-status-chart', {
            datasets: [{
                data: Object.values(chartManager.calculateStatusCounts(this.cache.tasks))
            }]
        });
    }

    handleFilterChange(event) {
        const filter = event.target.dataset.filter;
        this.currentFilter = filter;

        // Update button states
        domUtils.$$('.filter-btn').forEach(btn => {
            domUtils.removeClass(btn, 'active');
            btn.setAttribute('aria-selected', 'false');
        });

        domUtils.addClass(event.target, 'active');
        event.target.setAttribute('aria-selected', 'true');

        // Update table
        this.updateTaskTable();
    }

    handleSort(event) {
        const column = event.target.dataset.sort;

        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }

        // Update sort indicators
        domUtils.$$('th[data-sort]').forEach(th => {
            th.setAttribute('aria-sort', 'none');
            domUtils.removeClass(th, 'sort-asc');
            domUtils.removeClass(th, 'sort-desc');
        });

        event.target.setAttribute('aria-sort', this.sortDirection === 'asc' ? 'ascending' : 'descending');
        domUtils.addClass(event.target, `sort-${this.sortDirection}`);

        this.updateTaskTable();
    }

    startAutoUpdate() {
        this.stopAutoUpdate();

        this.autoUpdateTimer = setInterval(async () => {
            try {
                await this.refreshData();
            } catch (error) {
                console.error('Auto-update failed:', error);
            }
        }, this.updateInterval);

        console.log(`Auto-update started (${this.updateInterval}ms interval)`);
    }

    stopAutoUpdate() {
        if (this.autoUpdateTimer) {
            clearInterval(this.autoUpdateTimer);
            this.autoUpdateTimer = null;
        }
    }

    async refreshData() {
        try {
            // Use individual API endpoints instead of getDashboardData
            const [status, tasks, performance] = await Promise.all([
                this.apiClient.getStatus(),
                this.apiClient.getTasks(),
                this.apiClient.getPerformance()
            ]);

            this.cache.status = status;
            this.cache.tasks = tasks || [];
            this.cache.performance = performance;
            this.cache.lastFetchTime = Date.now();

            this.updateExecutiveSummary();
            this.updateTaskTable();
            this.updateConnectionStatus('connected');

        } catch (error) {
            console.warn('Failed to refresh data:', error);
            this.updateConnectionStatus('error');
        }
    }

    updateConnectionStatus(status) {
        domUtils.updateStatusIndicator(
            domUtils.byId('connection-status'),
            status,
            {
                text: this.getStatusText(status),
                ariaLabel: `Connection status: ${status}`
            }
        );

        domUtils.updateStatusIndicator(
            domUtils.$('.status-indicator'),
            status,
            {
                ariaLabel: `System status: ${status}`
            }
        );
    }

    getStatusText(status) {
        const statusTexts = {
            connected: 'Connected',
            disconnected: 'Disconnected',
            error: 'Connection Error',
            failed: 'Connection Failed'
        };
        return statusTexts[status] || status;
    }

    updateLastUpdateTime() {
        const lastUpdateElement = domUtils.byId('last-update');
        if (lastUpdateElement) {
            const now = new Date().toLocaleTimeString();
            lastUpdateElement.textContent = `Last updated: ${now}`;
        }
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('dashboard-theme', newTheme);

        // Update theme toggle icon
        const themeIcon = domUtils.$('.theme-icon');
        if (themeIcon) {
            themeIcon.textContent = newTheme === 'dark' ? '☀️' : '🌙';
        }
    }

    handleWindowFocus() {
        // Resume real-time updates when window gains focus
        if (!this.autoUpdateTimer) {
            this.startAutoUpdate();
        }
    }

    handleWindowBlur() {
        // Optionally pause updates when window loses focus to save resources
        // this.stopAutoUpdate();
    }

    // Utility methods
    formatElapsedTime(milliseconds) {
        return domUtils.formatDuration(milliseconds);
    }

    formatTimestamp(timestamp) {
        if (!timestamp) return '-';
        return new Date(timestamp).toLocaleString();
    }

    truncateText(text, maxLength) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    generateTimeLabels(count) {
        const labels = [];
        const now = new Date();
        for (let i = count - 1; i >= 0; i--) {
            const time = new Date(now.getTime() - (i * 60000)); // 1 minute intervals
            labels.push(time.toLocaleTimeString());
        }
        return labels;
    }

    generateSampleData(count, min, max) {
        const data = [];
        for (let i = 0; i < count; i++) {
            data.push(Math.floor(Math.random() * (max - min + 1)) + min);
        }
        return data;
    }

    generateProgressData(count) {
        const data = [];
        for (let i = 0; i < count; i++) {
            data.push(Math.min(100, (i / count) * 100 + Math.random() * 10));
        }
        return data;
    }

    // Public methods for external access
    async viewTaskDetails(taskId) {
        try {
            const task = await this.apiClient.getTask(taskId);
            // TODO: Implement task details modal
            console.log('Task details:', task);
            domUtils.createNotification(`Viewing details for task ${taskId}`, 'info');
        } catch (error) {
            console.error('Failed to load task details:', error);
            domUtils.createNotification('Failed to load task details', 'danger');
        }
    }

    // Cleanup
    cleanup() {
        console.log('Cleaning up dashboard...');

        this.stopAutoUpdate();

        if (this.apiClient) {
            this.apiClient.stopAllPolling();
        }

        if (this.wsManager) {
            this.wsManager.disconnect();
        }

        chartManager.destroyAllCharts();
    }

    // Getters
    getStatus() {
        return {
            isInitialized: this.isInitialized,
            wsConnected: this.wsManager ? this.wsManager.isConnected : false,
            lastUpdate: this.lastUpdate,
            taskCount: this.cache.tasks.length
        };
    }
}

// Initialize dashboard when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.dashboard = new Dashboard();
    });
} else {
    window.dashboard = new Dashboard();
}

// Export for external access
window.Dashboard = Dashboard;
