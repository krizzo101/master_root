/**
 * Workflow Detail View Controller
 * Manages the detailed workflow view with 3-panel layout and mobile tabs
 */

class WorkflowDetailView {
    constructor(apiClient, wsManager) {
        this.apiClient = apiClient;
        this.wsManager = wsManager;

        // DOM elements
        this.modal = document.getElementById('workflow-detail-modal');
        this.workflowTitle = document.getElementById('workflow-title');
        this.statusBadge = document.getElementById('workflow-status-badge');

        // Detail elements
        this.detailStatus = document.getElementById('detail-status');
        this.detailStarted = document.getElementById('detail-started');
        this.detailEta = document.getElementById('detail-eta');
        this.detailCpu = document.getElementById('detail-cpu');

        // Progress elements
        this.detailProgress = document.getElementById('detail-progress');
        this.detailProgressFill = document.getElementById('detail-progress-fill');
        this.detailCurrentTask = document.getElementById('detail-current-task');
        this.detailFilesList = document.getElementById('detail-files-list');
        this.detailCpuAvg = document.getElementById('detail-cpu-avg');
        this.detailMemory = document.getElementById('detail-memory');
        this.detailDiskIo = document.getElementById('detail-disk-io');

        // Task pipeline
        this.taskPipeline = document.getElementById('task-pipeline');

        // Log stream
        this.logStream = document.getElementById('log-stream');
        this.mobileLogStream = document.getElementById('mobile-log-stream');
        this.logAutoScroll = true;
        this.logFilter = 'all';

        // Output content
        this.outputContent = document.getElementById('output-content');
        this.currentOutputFile = 'README.md';

        // State
        this.currentWorkflow = null;
        this.logEntries = [];
        this.maxLogEntries = 1000;
        this.updateInterval = null;

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupWebSocketHandlers();
    }

    setupEventListeners() {
        // Modal controls
        document.getElementById('back-to-dashboard')?.addEventListener('click', () => {
            this.hide();
        });

        document.getElementById('clone-workflow')?.addEventListener('click', () => {
            this.cloneWorkflow();
        });

        document.getElementById('export-workflow')?.addEventListener('click', () => {
            this.exportWorkflow();
        });

        // Workflow controls
        document.getElementById('pause-workflow')?.addEventListener('click', () => {
            this.toggleWorkflow();
        });

        document.getElementById('view-config')?.addEventListener('click', () => {
            this.showConfiguration();
        });

        document.getElementById('download-progress')?.addEventListener('click', () => {
            this.downloadProgress();
        });

        // Log controls
        document.getElementById('auto-scroll-toggle')?.addEventListener('click', (e) => {
            this.toggleAutoScroll(e.target);
        });

        document.getElementById('pause-logs')?.addEventListener('click', (e) => {
            this.toggleLogPause(e.target);
        });

        document.getElementById('download-logs')?.addEventListener('click', () => {
            this.downloadLogs();
        });

        document.getElementById('log-filter')?.addEventListener('change', (e) => {
            this.setLogFilter(e.target.value);
        });

        // Output tabs
        EventUtils.delegate(this.modal, '.tab-btn', 'click', (e) => {
            const fileName = e.target.dataset.file;
            if (fileName) {
                this.switchOutputFile(fileName);
            }
        });

        // Mobile tab navigation
        EventUtils.delegate(this.modal, '.tab-nav-btn', 'click', (e) => {
            const tabName = e.target.dataset.tab;
            if (tabName) {
                this.switchMobileTab(tabName);
            }
        });

        // Custom events
        document.addEventListener('show-workflow-detail', (e) => {
            this.show(e.detail);
        });
    }

    setupWebSocketHandlers() {
        document.addEventListener('workflow-update', (e) => {
            if (this.currentWorkflow && e.detail.workflow_id === this.currentWorkflow.id) {
                this.handleWorkflowUpdate(e.detail);
            }
        });

        document.addEventListener('task-update', (e) => {
            if (this.currentWorkflow && e.detail.workflow_id === this.currentWorkflow.id) {
                this.handleTaskUpdate(e.detail);
            }
        });

        document.addEventListener('log-entry', (e) => {
            if (this.currentWorkflow && e.detail.workflow_id === this.currentWorkflow.id) {
                this.handleLogEntry(e.detail);
            }
        });

        document.addEventListener('progress-update', (e) => {
            if (this.currentWorkflow && e.detail.workflow_id === this.currentWorkflow.id) {
                this.handleProgressUpdate(e.detail);
            }
        });
    }

    show(workflow) {
        this.currentWorkflow = workflow;
        this.loadWorkflowDetails(workflow);
        UI.showModal('workflow-detail-modal');

        // Subscribe to real-time updates
        if (this.wsManager) {
            this.wsManager.subscribeToWorkflow(workflow.id);
        }

        // Start periodic updates
        this.startUpdates();
    }

    hide() {
        // Unsubscribe from updates
        if (this.currentWorkflow && this.wsManager) {
            this.wsManager.unsubscribeFromWorkflow(this.currentWorkflow.id);
        }

        // Stop periodic updates
        this.stopUpdates();

        this.currentWorkflow = null;
        UI.hideModal('workflow-detail-modal');
    }

    async loadWorkflowDetails(workflow) {
        try {
            // Update basic info
            this.updateBasicInfo(workflow);

            // Load detailed data in parallel
            const [tasks, logs, deliverables] = await Promise.all([
                this.loadWorkflowTasks(workflow.id).catch(() => []),
                this.loadWorkflowLogs(workflow.id).catch(() => []),
                this.loadWorkflowDeliverables(workflow.id).catch(() => [])
            ]);

            // Update UI sections
            this.updateTaskPipeline(tasks);
            this.updateLogStream(logs);
            this.updateOutputPreview(deliverables);
            this.updateProgressInfo(workflow, tasks);
            this.updateResourceUsage(workflow);

        } catch (error) {
            console.error('Failed to load workflow details:', error);
            UI.showToast(`Failed to load workflow details: ${error.message}`, 'error');
        }
    }

    updateBasicInfo(workflow) {
        if (this.workflowTitle) {
            this.workflowTitle.textContent = workflow.name;
        }

        if (this.statusBadge) {
            this.statusBadge.textContent = StatusUtils.getStatusText(workflow.status);
            this.statusBadge.className = `workflow-status-badge ${workflow.status}`;
        }

        if (this.detailStatus) {
            this.detailStatus.textContent = StatusUtils.getStatusText(workflow.status);
        }

        if (this.detailStarted && workflow.startTime) {
            this.detailStarted.textContent = TimeUtils.formatDateTime(workflow.startTime);
        }

        if (this.detailEta && workflow.eta) {
            this.detailEta.textContent = TimeUtils.formatETA(workflow.eta);
        }

        if (this.detailCpu && workflow.resourceUsage) {
            this.detailCpu.textContent = `${workflow.resourceUsage.cpu}%`;
        }
    }

    async loadWorkflowTasks(workflowId) {
        try {
            const response = await this.apiClient.getTasks({
                workflow_id: workflowId
            });
            return response.tasks || [];
        } catch (error) {
            console.error('Failed to load workflow tasks:', error);
            return [];
        }
    }

    async loadWorkflowLogs(workflowId) {
        try {
            const response = await this.apiClient.getWorkflowLogs(workflowId, {
                limit: 100
            });
            return response.logs || [];
        } catch (error) {
            console.error('Failed to load workflow logs:', error);
            return [];
        }
    }

    async loadWorkflowDeliverables(workflowId) {
        try {
            const response = await this.apiClient.getWorkflowDeliverables(workflowId);
            return response.deliverables || [];
        } catch (error) {
            console.error('Failed to load workflow deliverables:', error);
            return [];
        }
    }

    updateTaskPipeline(tasks) {
        if (!this.taskPipeline) return;

        this.taskPipeline.innerHTML = '';

        tasks.forEach((task, index) => {
            const taskItem = this.createTaskItem(task, index);
            this.taskPipeline.appendChild(taskItem);
        });
    }

    createTaskItem(task, index) {
        const status = task.status || 'pending';
        let statusIcon = '○';
        let statusClass = 'pending';

        switch (status) {
            case 'completed':
                statusIcon = '✓';
                statusClass = 'completed';
                break;
            case 'running':
                statusIcon = '●';
                statusClass = 'running';
                break;
            case 'failed':
                statusIcon = '⚠';
                statusClass = 'failed';
                break;
            case 'queued':
                statusIcon = '⏳';
                statusClass = 'pending';
                break;
        }

        const taskItem = DomUtils.createElement('div', {
            className: `task-item ${statusClass}`
        });

        const statusEl = DomUtils.createElement('div', {
            className: `task-status ${statusClass}`
        }, [statusIcon]);

        const taskInfo = DomUtils.createElement('div', {
            className: 'task-info'
        });

        const taskName = DomUtils.createElement('h4', {}, [
            task.task_type || `Task ${index + 1}`
        ]);

        const taskDetails = DomUtils.createElement('p', {});

        if (status === 'completed' && task.duration) {
            taskDetails.textContent = `Duration: ${TimeUtils.formatDuration(task.duration)}`;
        } else if (status === 'running') {
            const progress = this.calculateTaskProgress(task);
            const eta = this.calculateTaskETA(task, progress);
            taskDetails.textContent = `Progress: ${progress}% • ETA: ${eta}`;
        } else if (status === 'queued') {
            taskDetails.textContent = `Queue position: ${index + 1}`;
        } else if (status === 'failed' && task.error) {
            taskDetails.textContent = `Error: ${task.error}`;
        }

        taskInfo.appendChild(taskName);
        taskInfo.appendChild(taskDetails);

        taskItem.appendChild(statusEl);
        taskItem.appendChild(taskInfo);

        return taskItem;
    }

    calculateTaskProgress(task) {
        if (task.progress) return task.progress;
        if (task.start_time) {
            const elapsed = Date.now() / 1000 - task.start_time;
            return Math.min(Math.floor(elapsed / 30) * 10, 90); // Estimate
        }
        return 0;
    }

    calculateTaskETA(task, progress) {
        if (progress > 0 && task.start_time) {
            const elapsed = Date.now() / 1000 - task.start_time;
            const estimated = elapsed / (progress / 100);
            const remaining = estimated - elapsed;
            return TimeUtils.formatDuration(Math.max(0, remaining));
        }
        return 'Unknown';
    }

    updateLogStream(logs) {
        this.logEntries = logs.slice(-this.maxLogEntries);
        this.renderLogEntries();
    }

    renderLogEntries() {
        const filteredLogs = this.filterLogEntries(this.logEntries);

        if (this.logStream) {
            this.renderLogsInContainer(this.logStream, filteredLogs);
        }

        if (this.mobileLogStream) {
            this.renderLogsInContainer(this.mobileLogStream, filteredLogs);
        }
    }

    filterLogEntries(logs) {
        if (this.logFilter === 'all') {
            return logs;
        }

        return logs.filter(log => {
            const level = log.level?.toLowerCase() || 'info';
            return level === this.logFilter.toLowerCase();
        });
    }

    renderLogsInContainer(container, logs) {
        const shouldScrollToBottom = this.logAutoScroll &&
            (container.scrollTop + container.clientHeight >= container.scrollHeight - 10);

        container.innerHTML = '';

        logs.forEach(log => {
            const logEntry = this.createLogEntry(log);
            container.appendChild(logEntry);
        });

        if (shouldScrollToBottom) {
            container.scrollTop = container.scrollHeight;
        }
    }

    createLogEntry(log) {
        const entry = DomUtils.createElement('div', {
            className: `log-entry ${log.level?.toLowerCase() || 'info'}`
        });

        const time = DomUtils.createElement('span', {
            className: 'log-time'
        }, [this.formatLogTime(log.timestamp)]);

        const level = DomUtils.createElement('span', {
            className: 'log-level'
        }, [`${(log.level || 'INFO').toUpperCase()}:`]);

        const message = DomUtils.createElement('span', {
            className: 'log-message'
        }, [log.message || '']);

        entry.appendChild(time);
        entry.appendChild(level);
        entry.appendChild(message);

        return entry;
    }

    formatLogTime(timestamp) {
        if (!timestamp) return '[--:--:--]';

        const date = new Date(timestamp);
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        const seconds = date.getSeconds().toString().padStart(2, '0');

        return `[${hours}:${minutes}:${seconds}]`;
    }

    updateOutputPreview(deliverables) {
        if (!deliverables || deliverables.length === 0) {
            if (this.outputContent) {
                this.outputContent.innerHTML = '<p>No output files available yet.</p>';
            }
            return;
        }

        // Update output tabs
        this.updateOutputTabs(deliverables);

        // Load first deliverable content
        if (deliverables.length > 0) {
            this.loadDeliverableContent(deliverables[0]);
        }
    }

    updateOutputTabs(deliverables) {
        const tabsContainer = this.modal.querySelector('.output-tabs');
        if (!tabsContainer) return;

        // Clear existing tabs (except "More" button)
        const moreBtn = tabsContainer.querySelector('.more-tabs');
        tabsContainer.innerHTML = '';

        // Add deliverable tabs
        deliverables.slice(0, 3).forEach((deliverable, index) => {
            const tab = DomUtils.createElement('button', {
                className: `tab-btn ${index === 0 ? 'active' : ''}`,
                'data-file': deliverable.name
            }, [deliverable.name]);

            tabsContainer.appendChild(tab);
        });

        // Add "More" button if needed
        if (deliverables.length > 3 && moreBtn) {
            tabsContainer.appendChild(moreBtn);
        }
    }

    async loadDeliverableContent(deliverable) {
        if (!this.outputContent) return;

        try {
            // For demo purposes, show sample content
            const sampleContent = this.getSampleContent(deliverable.name);
            this.outputContent.innerHTML = `<pre><code>${DataUtils.sanitizeHtml(sampleContent)}</code></pre>`;
        } catch (error) {
            console.error('Failed to load deliverable content:', error);
            this.outputContent.innerHTML = '<p>Failed to load file content.</p>';
        }
    }

    getSampleContent(fileName) {
        const samples = {
            'README.md': `# Agent Orchestrator

A sophisticated multi-agent workflow orchestration system for managing concurrent AI tasks with advanced resource management and intelligent load balancing.

## Quick Start

\`\`\`bash
# Install dependencies
pip install -r requirements.txt

# Run orchestrator
python main.py --mode dashboard
\`\`\`

## Features

- Multi-agent task orchestration
- Real-time monitoring dashboard
- WebSocket-based communication
- Advanced resource management
- Intelligent load balancing
`,
            'ARCHITECTURE.md': `# System Architecture

## Overview

The Agent Orchestrator consists of several key components:

1. **Task Manager** - Handles task distribution and dependencies
2. **Resource Pool** - Manages computational resources
3. **Communication Hub** - WebSocket-based real-time updates
4. **Monitoring System** - Tracks performance and health metrics

## Component Diagram

\`\`\`
┌─────────────┐    ┌─────────────┐
│ Task Manager│◄──►│Resource Pool│
└─────────────┘    └─────────────┘
       │                  │
       ▼                  ▼
┌─────────────┐    ┌─────────────┐
│ Comm Hub    │◄──►│ Monitoring  │
└─────────────┘    └─────────────┘
\`\`\`
`,
            'API_REFERENCE.md': `# API Reference

## Endpoints

### GET /status
Get current orchestrator status.

**Response:**
\`\`\`json
{
  "status": "running",
  "active_tasks": 5,
  "queue_size": 2
}
\`\`\`

### POST /tasks
Create a new task.

**Request:**
\`\`\`json
{
  "task_type": "analysis",
  "prompt": "Analyze the codebase",
  "priority": "high"
}
\`\`\`
`
        };

        return samples[fileName] || `Content of ${fileName} would be displayed here.`;
    }

    updateProgressInfo(workflow, tasks) {
        if (this.detailProgress) {
            this.detailProgress.textContent = `${workflow.progress}%`;
        }

        if (this.detailProgressFill) {
            this.detailProgressFill.style.width = `${workflow.progress}%`;
        }

        // Update current task
        if (this.detailCurrentTask && tasks.length > 0) {
            const currentTask = tasks.find(t => t.status === 'running');
            if (currentTask) {
                this.detailCurrentTask.textContent = `"${currentTask.task_type || 'Current Task'}"`;
            }
        }

        // Update files list
        if (this.detailFilesList) {
            this.updateFilesList(workflow, tasks);
        }
    }

    updateFilesList(workflow, tasks) {
        if (!this.detailFilesList) return;

        this.detailFilesList.innerHTML = '';

        const files = [
            { name: 'README.md', status: 'completed' },
            { name: 'ARCHITECTURE.md', status: 'completed' },
            { name: 'API_REFERENCE.md', status: 'in-progress', progress: workflow.progress },
            { name: 'USER_GUIDE.md', status: 'pending' },
            { name: 'DEPLOYMENT.md', status: 'pending' }
        ];

        files.forEach(file => {
            const li = DomUtils.createElement('li', {
                className: `file-${file.status}`
            });

            if (file.status === 'completed') {
                li.textContent = `${file.name} ✓`;
            } else if (file.status === 'in-progress') {
                li.innerHTML = `${file.name} <span>(${file.progress}% complete)</span>`;
            } else {
                li.textContent = file.name;
            }

            this.detailFilesList.appendChild(li);
        });
    }

    updateResourceUsage(workflow) {
        if (workflow.resourceUsage) {
            if (this.detailCpuAvg) {
                this.detailCpuAvg.textContent = `${workflow.resourceUsage.cpu}%`;
            }
            if (this.detailMemory) {
                this.detailMemory.textContent = workflow.resourceUsage.memory;
            }
            if (this.detailDiskIo) {
                this.detailDiskIo.textContent = workflow.resourceUsage.diskIO;
            }
        }
    }

    switchOutputFile(fileName) {
        // Update active tab
        this.modal.querySelectorAll('.tab-btn').forEach(tab => {
            DomUtils.removeClass(tab, 'active');
            if (tab.dataset.file === fileName) {
                DomUtils.addClass(tab, 'active');
            }
        });

        // Load file content
        this.loadDeliverableContent({ name: fileName });
        this.currentOutputFile = fileName;
    }

    switchMobileTab(tabName) {
        // Update active tab button
        this.modal.querySelectorAll('.tab-nav-btn').forEach(btn => {
            DomUtils.removeClass(btn, 'active');
            if (btn.dataset.tab === tabName) {
                DomUtils.addClass(btn, 'active');
            }
        });

        // Show/hide tab content
        this.modal.querySelectorAll('.tab-content').forEach(content => {
            if (content.dataset.tab === tabName) {
                content.style.display = 'block';
            } else {
                content.style.display = 'none';
            }
        });
    }

    toggleAutoScroll(button) {
        this.logAutoScroll = !this.logAutoScroll;

        if (this.logAutoScroll) {
            DomUtils.addClass(button, 'active');
            button.textContent = 'Auto-scroll';

            // Scroll to bottom
            if (this.logStream) {
                this.logStream.scrollTop = this.logStream.scrollHeight;
            }
        } else {
            DomUtils.removeClass(button, 'active');
            button.textContent = 'Manual';
        }
    }

    toggleLogPause(button) {
        const isPaused = DomUtils.hasClass(button, 'active');

        if (isPaused) {
            DomUtils.removeClass(button, 'active');
            button.textContent = 'Pause';
            this.startUpdates();
        } else {
            DomUtils.addClass(button, 'active');
            button.textContent = 'Resume';
            this.stopUpdates();
        }
    }

    setLogFilter(filter) {
        this.logFilter = filter;
        this.renderLogEntries();
    }

    startUpdates() {
        if (this.updateInterval) return;

        this.updateInterval = setInterval(() => {
            if (this.currentWorkflow) {
                this.refreshWorkflowData();
            }
        }, 5000); // Update every 5 seconds
    }

    stopUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    async refreshWorkflowData() {
        if (!this.currentWorkflow) return;

        try {
            // Refresh logs if not paused
            const logs = await this.loadWorkflowLogs(this.currentWorkflow.id);
            if (logs.length > this.logEntries.length) {
                this.updateLogStream(logs);
            }
        } catch (error) {
            console.error('Failed to refresh workflow data:', error);
        }
    }

    // Event handlers for real-time updates
    handleWorkflowUpdate(data) {
        if (this.currentWorkflow) {
            Object.assign(this.currentWorkflow, {
                status: data.status || this.currentWorkflow.status,
                progress: data.progress || this.currentWorkflow.progress,
                lastUpdated: new Date()
            });

            this.updateBasicInfo(this.currentWorkflow);
            this.updateProgressInfo(this.currentWorkflow, []);
        }
    }

    handleTaskUpdate(data) {
        // Update task pipeline if needed
        this.loadWorkflowTasks(this.currentWorkflow.id).then(tasks => {
            this.updateTaskPipeline(tasks);
        });
    }

    handleLogEntry(data) {
        // Add new log entry
        this.logEntries.push({
            timestamp: data.timestamp,
            level: data.level || 'INFO',
            message: data.message || ''
        });

        // Trim old entries
        if (this.logEntries.length > this.maxLogEntries) {
            this.logEntries = this.logEntries.slice(-this.maxLogEntries);
        }

        // Re-render logs
        this.renderLogEntries();
    }

    handleProgressUpdate(data) {
        if (this.currentWorkflow && data.progress !== undefined) {
            this.currentWorkflow.progress = Math.max(0, Math.min(100, data.progress));

            if (data.eta) {
                this.currentWorkflow.eta = new Date(data.eta);
            }

            this.updateProgressInfo(this.currentWorkflow, []);
        }
    }

    // Action handlers
    async toggleWorkflow() {
        if (!this.currentWorkflow) return;

        try {
            if (this.currentWorkflow.status === 'running') {
                await this.apiClient.pauseWorkflow(this.currentWorkflow.id);
                UI.showToast('Workflow paused', 'success');
            } else if (this.currentWorkflow.status === 'paused') {
                await this.apiClient.resumeWorkflow(this.currentWorkflow.id);
                UI.showToast('Workflow resumed', 'success');
            }
        } catch (error) {
            UI.showToast(`Failed to toggle workflow: ${error.message}`, 'error');
        }
    }

    cloneWorkflow() {
        if (this.currentWorkflow) {
            UI.showToast('Clone workflow - Feature coming soon', 'info');
        }
    }

    exportWorkflow() {
        if (this.currentWorkflow) {
            const data = JSON.stringify(this.currentWorkflow, null, 2);
            const blob = new Blob([data], { type: 'application/json' });
            const url = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = `${this.currentWorkflow.name}-export.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            UI.showToast('Workflow exported', 'success');
        }
    }

    showConfiguration() {
        UI.showToast('Configuration view - Feature coming soon', 'info');
    }

    downloadProgress() {
        if (this.currentWorkflow) {
            const progressData = {
                name: this.currentWorkflow.name,
                progress: this.currentWorkflow.progress,
                status: this.currentWorkflow.status,
                startTime: this.currentWorkflow.startTime,
                duration: this.currentWorkflow.duration,
                tasks: [] // Would include task details
            };

            const data = JSON.stringify(progressData, null, 2);
            const blob = new Blob([data], { type: 'application/json' });
            const url = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = `${this.currentWorkflow.name}-progress.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            UI.showToast('Progress downloaded', 'success');
        }
    }

    downloadLogs() {
        if (this.logEntries.length === 0) {
            UI.showToast('No logs available', 'warning');
            return;
        }

        const logText = this.logEntries.map(log => {
            return `${this.formatLogTime(log.timestamp)} ${log.level}: ${log.message}`;
        }).join('\n');

        const blob = new Blob([logText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.currentWorkflow?.name || 'workflow'}-logs.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        UI.showToast('Logs downloaded', 'success');
    }
}

// Export for global use
if (typeof window !== 'undefined') {
    window.WorkflowDetailView = WorkflowDetailView;
}
