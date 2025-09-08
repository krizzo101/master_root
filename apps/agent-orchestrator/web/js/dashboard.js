/**
 * Main Dashboard Controller
 * Manages the workflow grid, system overview, and dashboard interactions
 */

class Dashboard {
    constructor(apiClient, wsManager) {
        this.apiClient = apiClient;
        this.wsManager = wsManager;

        // DOM elements
        this.workflowsGrid = document.getElementById('workflows-grid');
        this.systemOverview = document.getElementById('system-overview');
        this.loadingState = document.getElementById('loading-state');
        this.emptyState = document.getElementById('empty-state');
        this.errorState = document.getElementById('error-state');
        this.loadMoreBtn = document.getElementById('load-more');

        // State
        this.workflows = new Map();
        this.selectedWorkflows = new Set();
        this.currentFilter = 'all';
        this.currentSort = 'recent';
        this.isLoading = false;
        this.autoRefreshEnabled = true;
        this.autoRefreshInterval = null;

        // Settings
        this.refreshInterval = 30000; // 30 seconds
        this.maxWorkflows = 100;

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupWebSocketHandlers();
        this.setupAutoRefresh();
        this.loadInitialData();
    }

    setupEventListeners() {
        // Filter and sort controls
        document.getElementById('status-filter')?.addEventListener('change', (e) => {
            this.currentFilter = e.target.value;
            this.applyFilters();
        });

        document.getElementById('sort-select')?.addEventListener('change', (e) => {
            this.currentSort = e.target.value;
            this.applySorting();
        });

        // Auto-refresh toggle
        document.getElementById('auto-refresh-toggle')?.addEventListener('click', () => {
            this.toggleAutoRefresh();
        });

        // New workflow button
        document.getElementById('new-workflow-btn')?.addEventListener('click', () => {
            this.showNewWorkflowDialog();
        });

        // Bulk actions
        document.getElementById('bulk-actions-dropdown')?.addEventListener('click', (e) => {
            if (e.target.classList.contains('dropdown-item')) {
                this.handleBulkAction(e.target.dataset.action);
            }
        });

        // Compare button
        document.getElementById('compare-btn')?.addEventListener('click', () => {
            this.showComparisonView();
        });

        // System overview actions
        document.getElementById('refresh-overview')?.addEventListener('click', () => {
            this.refreshSystemOverview();
        });

        // Error state retry
        document.getElementById('retry-btn')?.addEventListener('click', () => {
            this.loadInitialData();
        });

        // Workflow grid delegation
        EventUtils.delegate(this.workflowsGrid, '.workflow-card', 'click', (e) => {
            const card = e.target.closest('.workflow-card');
            if (card && !e.target.closest('.workflow-card-actions')) {
                this.handleWorkflowClick(card);
            }
        });

        EventUtils.delegate(this.workflowsGrid, '.workflow-checkbox', 'change', (e) => {
            const card = e.target.closest('.workflow-card');
            this.handleWorkflowSelection(card, e.target.checked);
        });

        EventUtils.delegate(this.workflowsGrid, '.workflow-action', 'click', (e) => {
            e.stopPropagation();
            const card = e.target.closest('.workflow-card');
            const action = e.target.dataset.action;
            this.handleWorkflowAction(card, action);
        });
    }

    setupWebSocketHandlers() {
        // Listen for real-time updates
        document.addEventListener('workflow-update', (e) => {
            this.handleWorkflowUpdate(e.detail);
        });

        document.addEventListener('task-update', (e) => {
            this.handleTaskUpdate(e.detail);
        });

        document.addEventListener('progress-update', (e) => {
            this.handleProgressUpdate(e.detail);
        });

        document.addEventListener('system-metric', (e) => {
            this.handleSystemMetric(e.detail);
        });

        document.addEventListener('websocket-connected', () => {
            // Subscribe to orchestrator updates
            this.wsManager.subscribeToOrchestrator();
        });
    }

    setupAutoRefresh() {
        if (this.autoRefreshEnabled) {
            this.autoRefreshInterval = setInterval(() => {
                if (!document.hidden) {
                    this.refreshWorkflows();
                }
            }, this.refreshInterval);
        }
    }

    toggleAutoRefresh() {
        const toggleBtn = document.getElementById('auto-refresh-toggle');

        this.autoRefreshEnabled = !this.autoRefreshEnabled;

        if (this.autoRefreshEnabled) {
            this.setupAutoRefresh();
            DomUtils.addClass(toggleBtn, 'active');
        } else {
            if (this.autoRefreshInterval) {
                clearInterval(this.autoRefreshInterval);
                this.autoRefreshInterval = null;
            }
            DomUtils.removeClass(toggleBtn, 'active');
        }

        StorageUtils.set('dashboard.autoRefresh', this.autoRefreshEnabled);
    }

    async loadInitialData() {
        this.showLoading();

        try {
            // Load workflows and system data in parallel
            const [workflowsData, systemData] = await Promise.all([
                this.loadWorkflows(),
                this.loadSystemOverview()
            ]);

            this.hideLoading();

            if (this.workflows.size === 0) {
                this.showEmptyState();
            } else {
                this.showWorkflowGrid();
            }
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError(error.message || 'Failed to load dashboard data');
        }
    }

    async loadWorkflows() {
        try {
            // Try to load from tasks endpoint first
            const response = await this.apiClient.getTasks({
                limit: this.maxWorkflows,
                status: this.currentFilter === 'all' ? undefined : this.currentFilter
            });

            if (response && response.tasks) {
                this.processWorkflows(response.tasks);
            }
        } catch (error) {
            console.error('Failed to load workflows:', error);
            throw error;
        }
    }

    async loadSystemOverview() {
        try {
            const systemInfo = await this.apiClient.getSystemInfo();
            this.updateSystemOverview(systemInfo);
        } catch (error) {
            console.error('Failed to load system overview:', error);
            // Don't throw - system overview is not critical
        }
    }

    processWorkflows(workflowData) {
        // Convert task data to workflow format
        workflowData.forEach(task => {
            const workflowId = task.task_id || DataUtils.generateId('workflow');

            const workflow = {
                id: workflowId,
                name: this.generateWorkflowName(task),
                status: task.status || 'pending',
                progress: this.calculateProgress(task),
                startTime: task.start_time ? new Date(task.start_time * 1000) : null,
                endTime: task.end_time ? new Date(task.end_time * 1000) : null,
                duration: this.calculateDuration(task),
                eta: this.calculateETA(task),
                taskType: task.task_type || 'unknown',
                error: task.error,
                resourceUsage: this.extractResourceUsage(task),
                deliverables: this.extractDeliverables(task),
                lastUpdated: new Date()
            };

            this.workflows.set(workflowId, workflow);
        });

        this.renderWorkflows();
        this.updateCompareButton();
    }

    generateWorkflowName(task) {
        // Generate friendly name from task data
        if (task.prompt) {
            const words = task.prompt.split(' ').slice(0, 3);
            return words.join(' ').toLowerCase().replace(/[^a-z0-9\s]/g, '');
        }
        return `${task.task_type || 'workflow'}-${Date.now()}`;
    }

    calculateProgress(task) {
        if (task.status === 'completed') return 100;
        if (task.status === 'failed' || task.status === 'cancelled') return 0;

        // Estimate progress based on duration if available
        if (task.start_time && task.end_time) {
            return 100; // Completed
        } else if (task.start_time) {
            // Running - estimate based on elapsed time
            const elapsed = Date.now() / 1000 - task.start_time;
            return Math.min(Math.floor(elapsed / 60) * 10, 90); // 10% per minute, max 90%
        }

        return 0;
    }

    calculateDuration(task) {
        if (task.start_time && task.end_time) {
            return task.end_time - task.start_time;
        } else if (task.start_time) {
            return Date.now() / 1000 - task.start_time;
        }
        return 0;
    }

    calculateETA(task) {
        if (task.status === 'completed' || task.status === 'failed') {
            return null;
        }

        if (task.start_time) {
            const progress = this.calculateProgress(task);
            const eta = ProgressUtils.calculateETA(new Date(task.start_time * 1000), progress);
            return eta;
        }

        return null;
    }

    extractResourceUsage(task) {
        // Extract resource usage from task data
        return {
            cpu: Math.floor(Math.random() * 20) + 5, // Mock data
            memory: `${(Math.random() * 2 + 0.5).toFixed(1)}GB`,
            diskIO: `${Math.floor(Math.random() * 50) + 10}MB/s`
        };
    }

    extractDeliverables(task) {
        // Extract deliverable info from task result
        const deliverables = [];
        if (task.result && typeof task.result === 'object') {
            Object.keys(task.result).forEach(key => {
                if (key.includes('file') || key.includes('path')) {
                    deliverables.push({
                        name: key,
                        path: task.result[key],
                        size: Math.floor(Math.random() * 5000000) + 100000 // Mock size
                    });
                }
            });
        }
        return deliverables;
    }

    renderWorkflows() {
        const filteredWorkflows = this.getFilteredWorkflows();
        const sortedWorkflows = this.getSortedWorkflows(filteredWorkflows);

        this.workflowsGrid.innerHTML = '';

        sortedWorkflows.forEach(workflow => {
            const card = this.createWorkflowCard(workflow);
            this.workflowsGrid.appendChild(card);
        });

        // Update empty state
        if (sortedWorkflows.length === 0) {
            this.showEmptyState();
        } else {
            this.showWorkflowGrid();
        }
    }

    createWorkflowCard(workflow) {
        const card = DomUtils.createElement('div', {
            className: `workflow-card ${workflow.status}`,
            'data-workflow-id': workflow.id,
            'data-status': workflow.status,
            role: 'article',
            'aria-labelledby': `workflow-title-${workflow.id}`,
            tabindex: '0'
        });

        // Selection checkbox
        const checkbox = DomUtils.createElement('input', {
            type: 'checkbox',
            className: 'checkbox-input workflow-checkbox',
            'aria-label': `Select ${workflow.name}`
        });

        const checkboxCustom = DomUtils.createElement('div', {
            className: 'checkbox-custom'
        });

        // Workflow header
        const header = DomUtils.createElement('div', {
            className: 'workflow-header'
        });

        const statusIndicator = DomUtils.createElement('div', {
            className: 'workflow-status',
            'aria-label': `Status: ${StatusUtils.getStatusText(workflow.status)}`
        }, [
            DomUtils.createElement('span', {
                className: `status-dot ${workflow.status}`
            }),
            StatusUtils.getStatusText(workflow.status).toUpperCase()
        ]);

        const actions = DomUtils.createElement('div', {
            className: 'workflow-actions'
        });

        header.appendChild(statusIndicator);
        header.appendChild(actions);

        // Workflow name
        const name = DomUtils.createElement('h3', {
            className: 'workflow-name',
            id: `workflow-title-${workflow.id}`
        }, [workflow.name]);

        // Progress section
        const progressSection = DomUtils.createElement('div', {
            className: 'workflow-progress'
        });

        const progressLabel = DomUtils.createElement('div', {
            className: 'progress-label'
        }, [
            DomUtils.createElement('span', {
                className: 'progress-text'
            }, ['Progress']),
            DomUtils.createElement('span', {
                className: 'progress-percent'
            }, [`${workflow.progress}%`])
        ]);

        const progressBar = ProgressUtils.createProgressBar(workflow.progress, workflow.status);
        progressBar.setAttribute('role', 'progressbar');
        progressBar.setAttribute('aria-valuenow', workflow.progress);
        progressBar.setAttribute('aria-valuemin', '0');
        progressBar.setAttribute('aria-valuemax', '100');
        progressBar.setAttribute('aria-label', `Progress: ${workflow.progress}%`);

        const progressVisual = DomUtils.createElement('div', {
            className: 'progress-visual'
        }, [ProgressUtils.generateProgressVisual(workflow.progress)]);

        progressSection.appendChild(progressLabel);
        progressSection.appendChild(progressBar);
        progressSection.appendChild(progressVisual);

        // Workflow info
        const info = this.createWorkflowInfo(workflow);

        // Card actions
        const cardActions = this.createWorkflowCardActions(workflow);

        // Assemble card
        card.appendChild(checkbox);
        card.appendChild(checkboxCustom);
        card.appendChild(header);
        card.appendChild(name);
        card.appendChild(progressSection);
        card.appendChild(info);
        card.appendChild(cardActions);

        // Add keyboard support
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.handleWorkflowClick(card);
            }
        });

        return card;
    }

    createWorkflowInfo(workflow) {
        const info = DomUtils.createElement('div', {
            className: 'workflow-info'
        });

        // ETA or duration
        const leftInfo = DomUtils.createElement('div', {
            className: 'info-item'
        });

        if (workflow.status === 'running' && workflow.eta) {
            leftInfo.appendChild(DomUtils.createElement('div', {
                className: 'info-label'
            }, ['ETA']));
            leftInfo.appendChild(DomUtils.createElement('div', {
                className: 'info-value'
            }, [TimeUtils.formatETA(workflow.eta)]));
        } else if (workflow.duration > 0) {
            leftInfo.appendChild(DomUtils.createElement('div', {
                className: 'info-label'
            }, ['Duration']));
            leftInfo.appendChild(DomUtils.createElement('div', {
                className: 'info-value'
            }, [TimeUtils.formatDuration(workflow.duration)]));
        } else {
            leftInfo.appendChild(DomUtils.createElement('div', {
                className: 'info-label'
            }, ['Created']));
            leftInfo.appendChild(DomUtils.createElement('div', {
                className: 'info-value'
            }, [TimeUtils.formatTimeAgo(workflow.lastUpdated)]));
        }

        // Resource usage or deliverables
        const rightInfo = DomUtils.createElement('div', {
            className: 'info-item'
        });

        if (workflow.status === 'running' && workflow.resourceUsage) {
            rightInfo.appendChild(DomUtils.createElement('div', {
                className: 'info-label'
            }, ['CPU']));
            rightInfo.appendChild(DomUtils.createElement('div', {
                className: 'info-value'
            }, [`${workflow.resourceUsage.cpu}%`]));
        } else if (workflow.deliverables.length > 0) {
            rightInfo.appendChild(DomUtils.createElement('div', {
                className: 'info-label'
            }, ['Files']));
            rightInfo.appendChild(DomUtils.createElement('div', {
                className: 'info-value'
            }, [`${workflow.deliverables.length}`]));
        }

        info.appendChild(leftInfo);
        info.appendChild(rightInfo);

        return info;
    }

    createWorkflowCardActions(workflow) {
        const actions = DomUtils.createElement('div', {
            className: 'workflow-card-actions'
        });

        if (workflow.status === 'running') {
            actions.appendChild(DomUtils.createElement('button', {
                className: 'btn secondary-btn small-btn workflow-action',
                'data-action': 'view'
            }, ['View']));
            actions.appendChild(DomUtils.createElement('button', {
                className: 'btn secondary-btn small-btn workflow-action',
                'data-action': 'pause'
            }, ['Pause']));
        } else if (workflow.status === 'paused') {
            actions.appendChild(DomUtils.createElement('button', {
                className: 'btn secondary-btn small-btn workflow-action',
                'data-action': 'resume'
            }, ['Resume']));
            actions.appendChild(DomUtils.createElement('button', {
                className: 'btn secondary-btn small-btn workflow-action',
                'data-action': 'cancel'
            }, ['Cancel']));
        } else if (workflow.status === 'completed') {
            actions.appendChild(DomUtils.createElement('button', {
                className: 'btn secondary-btn small-btn workflow-action',
                'data-action': 'download'
            }, ['Download']));
            actions.appendChild(DomUtils.createElement('button', {
                className: 'btn secondary-btn small-btn workflow-action',
                'data-action': 'view'
            }, ['▶']));
        } else if (workflow.status === 'failed') {
            actions.appendChild(DomUtils.createElement('button', {
                className: 'btn danger-btn small-btn workflow-action',
                'data-action': 'retry'
            }, ['Retry']));
            actions.appendChild(DomUtils.createElement('button', {
                className: 'btn secondary-btn small-btn workflow-action',
                'data-action': 'logs'
            }, ['Logs']));
        } else if (workflow.status === 'queued') {
            actions.appendChild(DomUtils.createElement('button', {
                className: 'btn secondary-btn small-btn workflow-action',
                'data-action': 'priority'
            }, ['Priority']));
            actions.appendChild(DomUtils.createElement('button', {
                className: 'btn secondary-btn small-btn workflow-action',
                'data-action': 'view'
            }, ['▶']));
        }

        return actions;
    }

    getFilteredWorkflows() {
        const workflowArray = Array.from(this.workflows.values());

        if (this.currentFilter === 'all') {
            return workflowArray;
        }

        return workflowArray.filter(workflow => {
            return workflow.status === this.currentFilter;
        });
    }

    getSortedWorkflows(workflows) {
        return workflows.sort((a, b) => {
            switch (this.currentSort) {
                case 'name':
                    return a.name.localeCompare(b.name);
                case 'progress':
                    return b.progress - a.progress;
                case 'duration':
                    return b.duration - a.duration;
                case 'recent':
                default:
                    return b.lastUpdated - a.lastUpdated;
            }
        });
    }

    applyFilters() {
        this.renderWorkflows();
    }

    applySorting() {
        this.renderWorkflows();
    }

    // Event handlers
    handleWorkflowClick(card) {
        const workflowId = card.dataset.workflowId;
        const workflow = this.workflows.get(workflowId);

        if (workflow) {
            EventUtils.emit(document, 'show-workflow-detail', workflow);
        }
    }

    handleWorkflowSelection(card, selected) {
        const workflowId = card.dataset.workflowId;

        if (selected) {
            this.selectedWorkflows.add(workflowId);
            DomUtils.addClass(card, 'selected');
        } else {
            this.selectedWorkflows.delete(workflowId);
            DomUtils.removeClass(card, 'selected');
        }

        this.updateCompareButton();
        this.updateBulkActions();
    }

    handleWorkflowAction(card, action) {
        const workflowId = card.dataset.workflowId;
        const workflow = this.workflows.get(workflowId);

        if (!workflow) return;

        switch (action) {
            case 'view':
                EventUtils.emit(document, 'show-workflow-detail', workflow);
                break;
            case 'pause':
                this.pauseWorkflow(workflowId);
                break;
            case 'resume':
                this.resumeWorkflow(workflowId);
                break;
            case 'cancel':
                this.cancelWorkflow(workflowId);
                break;
            case 'retry':
                this.retryWorkflow(workflowId);
                break;
            case 'download':
                this.downloadWorkflow(workflowId);
                break;
            case 'logs':
                this.showWorkflowLogs(workflowId);
                break;
        }
    }

    // WebSocket event handlers
    handleWorkflowUpdate(data) {
        const workflowId = data.workflow_id || data.task_id;
        const workflow = this.workflows.get(workflowId);

        if (workflow) {
            // Update workflow data
            Object.assign(workflow, {
                status: data.status || workflow.status,
                lastUpdated: new Date()
            });

            // Re-render the specific workflow card
            this.updateWorkflowCard(workflowId);
        }
    }

    handleTaskUpdate(data) {
        this.handleWorkflowUpdate(data);
    }

    handleProgressUpdate(data) {
        const workflowId = data.workflow_id || data.task_id;
        const workflow = this.workflows.get(workflowId);

        if (workflow && data.progress !== undefined) {
            workflow.progress = Math.max(0, Math.min(100, data.progress));
            workflow.lastUpdated = new Date();

            if (data.eta) {
                workflow.eta = new Date(data.eta);
            }

            this.updateWorkflowCard(workflowId);
        }
    }

    handleSystemMetric(data) {
        this.updateSystemMetrics(data);
    }

    updateWorkflowCard(workflowId) {
        const card = this.workflowsGrid.querySelector(`[data-workflow-id="${workflowId}"]`);
        if (card) {
            const workflow = this.workflows.get(workflowId);
            const newCard = this.createWorkflowCard(workflow);

            // Preserve selection state
            const wasSelected = DomUtils.hasClass(card, 'selected');
            if (wasSelected) {
                const checkbox = newCard.querySelector('.workflow-checkbox');
                if (checkbox) {
                    checkbox.checked = true;
                    DomUtils.addClass(newCard, 'selected');
                }
            }

            card.replaceWith(newCard);
        }
    }

    updateSystemOverview(systemData) {
        if (!this.systemOverview) return;

        const activeCount = document.getElementById('active-count');
        const queuedCount = document.getElementById('queued-count');
        const cpuUsage = document.getElementById('cpu-usage');
        const memoryUsage = document.getElementById('memory-usage');
        const diskUsage = document.getElementById('disk-usage');

        if (systemData.status) {
            if (activeCount) activeCount.textContent = systemData.status.running || 0;
            if (queuedCount) queuedCount.textContent = systemData.status.queued || 0;
        }

        if (systemData.metrics && systemData.metrics.system) {
            if (cpuUsage) cpuUsage.textContent = `${systemData.metrics.system.cpu_usage || 0}%`;
            if (memoryUsage) memoryUsage.textContent = `${systemData.metrics.system.memory_usage || 0}GB / 16GB`;
            if (diskUsage) diskUsage.textContent = `127GB / 500GB`;
        }
    }

    updateSystemMetrics(metricData) {
        // Update individual metrics as they come in
        if (metricData.metric_type === 'cpu' && document.getElementById('cpu-usage')) {
            document.getElementById('cpu-usage').textContent = `${Math.round(metricData.value)}%`;
        } else if (metricData.metric_type === 'memory' && document.getElementById('memory-usage')) {
            document.getElementById('memory-usage').textContent = `${(metricData.value / 1e9).toFixed(1)}GB / 16GB`;
        }
    }

    updateCompareButton() {
        const compareBtn = document.getElementById('compare-btn');
        if (compareBtn) {
            compareBtn.disabled = this.selectedWorkflows.size < 2;

            if (this.selectedWorkflows.size > 0) {
                compareBtn.innerHTML = `
                    <span class="btn-icon">📊</span>
                    <span class="btn-text">Compare (${this.selectedWorkflows.size})</span>
                `;
            } else {
                compareBtn.innerHTML = `
                    <span class="btn-icon">📊</span>
                    <span class="btn-text">Compare</span>
                `;
            }
        }
    }

    updateBulkActions() {
        const dropdown = document.getElementById('bulk-actions-dropdown');
        if (dropdown) {
            const hasSelection = this.selectedWorkflows.size > 0;
            const items = dropdown.querySelectorAll('.dropdown-item');
            items.forEach(item => {
                item.disabled = !hasSelection;
            });
        }
    }

    // Workflow operations
    async pauseWorkflow(workflowId) {
        try {
            await this.apiClient.pauseWorkflow(workflowId);
            UI.showToast('Workflow paused', 'success');
        } catch (error) {
            UI.showToast(`Failed to pause workflow: ${error.message}`, 'error');
        }
    }

    async resumeWorkflow(workflowId) {
        try {
            await this.apiClient.resumeWorkflow(workflowId);
            UI.showToast('Workflow resumed', 'success');
        } catch (error) {
            UI.showToast(`Failed to resume workflow: ${error.message}`, 'error');
        }
    }

    async cancelWorkflow(workflowId) {
        if (confirm('Are you sure you want to cancel this workflow?')) {
            try {
                await this.apiClient.cancelWorkflow(workflowId);
                UI.showToast('Workflow cancelled', 'success');
            } catch (error) {
                UI.showToast(`Failed to cancel workflow: ${error.message}`, 'error');
            }
        }
    }

    async retryWorkflow(workflowId) {
        try {
            await this.apiClient.retryTask(workflowId);
            UI.showToast('Workflow retry initiated', 'success');
        } catch (error) {
            UI.showToast(`Failed to retry workflow: ${error.message}`, 'error');
        }
    }

    async downloadWorkflow(workflowId) {
        try {
            const workflow = this.workflows.get(workflowId);
            if (workflow && workflow.deliverables.length > 0) {
                // Download first deliverable as example
                const deliverable = workflow.deliverables[0];
                const blob = await this.apiClient.downloadDeliverable(workflowId, deliverable.name);

                // Create download link
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = deliverable.name;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

                UI.showToast('Download started', 'success');
            } else {
                UI.showToast('No deliverables available', 'warning');
            }
        } catch (error) {
            UI.showToast(`Failed to download: ${error.message}`, 'error');
        }
    }

    showWorkflowLogs(workflowId) {
        EventUtils.emit(document, 'show-workflow-logs', { workflowId });
    }

    async refreshWorkflows() {
        if (this.isLoading) return;

        try {
            await this.loadWorkflows();
        } catch (error) {
            console.error('Failed to refresh workflows:', error);
        }
    }

    async refreshSystemOverview() {
        try {
            const systemData = await this.apiClient.getSystemInfo();
            this.updateSystemOverview(systemData);
        } catch (error) {
            console.error('Failed to refresh system overview:', error);
        }
    }

    // UI state management
    showLoading() {
        this.isLoading = true;
        this.loadingState.style.display = 'flex';
        this.workflowsGrid.style.display = 'none';
        this.emptyState.style.display = 'none';
        this.errorState.style.display = 'none';
    }

    hideLoading() {
        this.isLoading = false;
        this.loadingState.style.display = 'none';
    }

    showWorkflowGrid() {
        this.workflowsGrid.style.display = 'grid';
        this.emptyState.style.display = 'none';
        this.errorState.style.display = 'none';
    }

    showEmptyState() {
        this.workflowsGrid.style.display = 'none';
        this.emptyState.style.display = 'block';
        this.errorState.style.display = 'none';
    }

    showError(message) {
        this.hideLoading();
        this.workflowsGrid.style.display = 'none';
        this.emptyState.style.display = 'none';
        this.errorState.style.display = 'block';

        const errorMessage = document.getElementById('error-message');
        if (errorMessage) {
            errorMessage.textContent = message;
        }
    }

    // Dialog handlers
    showNewWorkflowDialog() {
        UI.showToast('New workflow dialog - Feature coming soon', 'info');
    }

    showComparisonView() {
        if (this.selectedWorkflows.size < 2) {
            UI.showToast('Select at least 2 workflows to compare', 'warning');
            return;
        }

        const selectedWorkflowData = Array.from(this.selectedWorkflows)
            .map(id => this.workflows.get(id))
            .filter(Boolean);

        EventUtils.emit(document, 'show-workflow-comparison', selectedWorkflowData);
    }

    handleBulkAction(action) {
        if (this.selectedWorkflows.size === 0) {
            UI.showToast('No workflows selected', 'warning');
            return;
        }

        switch (action) {
            case 'pause-all':
                this.bulkPauseWorkflows();
                break;
            case 'resume-all':
                this.bulkResumeWorkflows();
                break;
            case 'cancel-selected':
                this.bulkCancelWorkflows();
                break;
            case 'export-selected':
                this.bulkExportWorkflows();
                break;
        }
    }

    async bulkPauseWorkflows() {
        const results = await Promise.allSettled(
            Array.from(this.selectedWorkflows).map(id => this.pauseWorkflow(id))
        );

        const successful = results.filter(r => r.status === 'fulfilled').length;
        UI.showToast(`${successful} workflows paused`, 'success');
    }

    async bulkResumeWorkflows() {
        const results = await Promise.allSettled(
            Array.from(this.selectedWorkflows).map(id => this.resumeWorkflow(id))
        );

        const successful = results.filter(r => r.status === 'fulfilled').length;
        UI.showToast(`${successful} workflows resumed`, 'success');
    }

    async bulkCancelWorkflows() {
        if (!confirm(`Cancel ${this.selectedWorkflows.size} selected workflows?`)) {
            return;
        }

        const results = await Promise.allSettled(
            Array.from(this.selectedWorkflows).map(id => this.cancelWorkflow(id))
        );

        const successful = results.filter(r => r.status === 'fulfilled').length;
        UI.showToast(`${successful} workflows cancelled`, 'success');
    }

    bulkExportWorkflows() {
        UI.showToast('Bulk export - Feature coming soon', 'info');
    }
}

// Export for global use
if (typeof window !== 'undefined') {
    window.Dashboard = Dashboard;
}
