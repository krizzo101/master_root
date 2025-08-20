/**
 * Interactive Pipeline Flow Diagram
 * Real-time visualization of pipeline stages and their status
 */

class PipelineVisualization {
    constructor(containerId, runId) {
        this.containerId = containerId;
        this.runId = runId;
        this.container = document.getElementById(containerId);
        this.svg = null;
        this.stages = [];
        this.dependencies = [];
        this.currentStage = null;
        this.websocket = null;
        this.updateInterval = null;

        this.colors = {
            pending: '#6B7280',
            running: '#F59E0B',
            completed: '#10B981',
            failed: '#EF4444',
            current: '#3B82F6'
        };

        this.init();
    }

    async init() {
        await this.loadPipelineData();
        this.createSVG();
        this.renderPipeline();
        this.setupWebSocket();
        this.setupAutoRefresh();
    }

    async loadPipelineData() {
        try {
            const response = await fetch(`/api/runs/${this.runId}/pipeline-visualization`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            this.stages = data.stages;
            this.dependencies = data.dependencies;
            this.currentStage = this.stages.find(s => s.status === 'running');
        } catch (error) {
            console.error('Failed to load pipeline data:', error);
            this.showError('Failed to load pipeline data');
        }
    }

    createSVG() {
        // Clear container
        this.container.innerHTML = '';

        // Create SVG
        this.svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        this.svg.setAttribute('width', '100%');
        this.svg.setAttribute('height', '600');
        this.svg.setAttribute('viewBox', '0 0 1800 400');
        this.svg.style.background = '#1a1a1a';
        this.svg.style.borderRadius = '8px';

        // Add definitions for markers and filters
        this.addSVGDefinitions();

        this.container.appendChild(this.svg);
    }

    addSVGDefinitions() {
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');

        // Arrow marker for dependency lines
        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
        marker.setAttribute('id', 'arrowhead');
        marker.setAttribute('markerWidth', '10');
        marker.setAttribute('markerHeight', '7');
        marker.setAttribute('refX', '9');
        marker.setAttribute('refY', '3.5');
        marker.setAttribute('orient', 'auto');

        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', '0 0, 10 3.5, 0 7');
        polygon.setAttribute('fill', '#9CA3AF');

        marker.appendChild(polygon);
        defs.appendChild(marker);

        // Glow filter for current stage
        const filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        filter.setAttribute('id', 'glow');

        const feGaussianBlur = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGaussianBlur.setAttribute('stdDeviation', '3');
        feGaussianBlur.setAttribute('result', 'coloredBlur');

        const feMerge = document.createElementNS('http://www.w3.org/2000/svg', 'feMerge');
        const feMergeNode1 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        feMergeNode1.setAttribute('in', 'coloredBlur');
        const feMergeNode2 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        feMergeNode2.setAttribute('in', 'SourceGraphic');

        feMerge.appendChild(feMergeNode1);
        feMerge.appendChild(feMergeNode2);
        filter.appendChild(feGaussianBlur);
        filter.appendChild(feMerge);
        defs.appendChild(filter);

        this.svg.appendChild(defs);
    }

    renderPipeline() {
        this.renderDependencies();
        this.renderStages();
        this.renderLegend();
    }

    renderDependencies() {
        this.dependencies.forEach(dep => {
            const fromStage = this.stages.find(s => s.id === dep.from);
            const toStage = this.stages.find(s => s.id === dep.to);

            if (fromStage && toStage) {
                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line.setAttribute('x1', fromStage.position.x + 50);
                line.setAttribute('y1', fromStage.position.y + 25);
                line.setAttribute('x2', toStage.position.x + 50);
                line.setAttribute('y2', toStage.position.y + 25);
                line.setAttribute('stroke', '#9CA3AF');
                line.setAttribute('stroke-width', '2');
                line.setAttribute('marker-end', 'url(#arrowhead)');
                line.setAttribute('opacity', '0.6');

                this.svg.appendChild(line);
            }
        });
    }

    renderStages() {
        this.stages.forEach(stage => {
            const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            group.setAttribute('transform', `translate(${stage.position.x}, ${stage.position.y})`);
            group.setAttribute('class', `stage-group stage-${stage.status}`);
            group.setAttribute('data-stage-id', stage.id);

            // Stage rectangle
            const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            rect.setAttribute('width', '100');
            rect.setAttribute('height', '50');
            rect.setAttribute('rx', '8');
            rect.setAttribute('fill', this.colors[stage.status]);
            rect.setAttribute('stroke', stage.status === 'running' ? this.colors.current : 'none');
            rect.setAttribute('stroke-width', '3');

            if (stage.status === 'running') {
                rect.setAttribute('filter', 'url(#glow)');
                rect.setAttribute('class', 'stage-rect running');
            }

            group.appendChild(rect);

            // Stage name
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', '50');
            text.setAttribute('y', '20');
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('fill', '#ffffff');
            text.setAttribute('font-size', '10');
            text.setAttribute('font-weight', 'bold');
            text.textContent = stage.name;

            group.appendChild(text);

            // Agent type
            const agentText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            agentText.setAttribute('x', '50');
            agentText.setAttribute('y', '35');
            agentText.setAttribute('text-anchor', 'middle');
            agentText.setAttribute('fill', '#ffffff');
            agentText.setAttribute('font-size', '8');
            agentText.setAttribute('opacity', '0.8');
            agentText.textContent = stage.agent;

            group.appendChild(agentText);

            // Status indicator
            if (stage.status === 'running') {
                const indicator = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                indicator.setAttribute('cx', '85');
                indicator.setAttribute('cy', '15');
                indicator.setAttribute('r', '4');
                indicator.setAttribute('fill', '#ffffff');
                indicator.setAttribute('class', 'status-indicator');
                group.appendChild(indicator);
            }

            // Add click handler for stage details
            group.addEventListener('click', () => this.showStageDetails(stage));
            group.style.cursor = 'pointer';

            this.svg.appendChild(group);
        });
    }

    renderLegend() {
        const legend = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        legend.setAttribute('transform', 'translate(20, 350)');

        const legendItems = [
            { status: 'pending', label: 'Pending' },
            { status: 'running', label: 'Running' },
            { status: 'completed', label: 'Completed' },
            { status: 'failed', label: 'Failed' }
        ];

        legendItems.forEach((item, index) => {
            const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            group.setAttribute('transform', `translate(${index * 150}, 0)`);

            const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            rect.setAttribute('width', '15');
            rect.setAttribute('height', '15');
            rect.setAttribute('fill', this.colors[item.status]);
            rect.setAttribute('rx', '3');

            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', '25');
            text.setAttribute('y', '12');
            text.setAttribute('fill', '#ffffff');
            text.setAttribute('font-size', '12');
            text.textContent = item.label;

            group.appendChild(rect);
            group.appendChild(text);
            legend.appendChild(group);
        });

        this.svg.appendChild(legend);
    }

    showStageDetails(stage) {
        const modal = document.createElement('div');
        modal.className = 'stage-modal';
        modal.innerHTML = `
            <div class="stage-modal-content">
                <div class="stage-modal-header">
                    <h3>${stage.name}</h3>
                    <span class="stage-modal-close">&times;</span>
                </div>
                <div class="stage-modal-body">
                    <p><strong>Description:</strong> ${stage.description}</p>
                    <p><strong>Agent:</strong> ${stage.agent}</p>
                    <p><strong>Status:</strong> <span class="status-${stage.status}">${stage.status}</span></p>
                    ${stage.start_time ? `<p><strong>Started:</strong> ${new Date(stage.start_time).toLocaleString()}</p>` : ''}
                    ${stage.end_time ? `<p><strong>Completed:</strong> ${new Date(stage.end_time).toLocaleString()}</p>` : ''}
                    ${stage.duration ? `<p><strong>Duration:</strong> ${stage.duration}s</p>` : ''}
                    ${stage.task_id ? `<p><strong>Task ID:</strong> ${stage.task_id}</p>` : ''}
                </div>
            </div>
        `;

        modal.addEventListener('click', (e) => {
            if (e.target === modal || e.target.classList.contains('stage-modal-close')) {
                document.body.removeChild(modal);
            }
        });

        document.body.appendChild(modal);
    }

    setupWebSocket() {
        try {
            this.websocket = new WebSocket(`ws://${window.location.host}/api/ws?run_id=${this.runId}`);

            this.websocket.onopen = () => {
                console.log('WebSocket connected for pipeline updates');
            };

            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'task_update' || data.type === 'run_update') {
                    this.handleUpdate(data);
                }
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                // Attempt to reconnect after 5 seconds
                setTimeout(() => this.setupWebSocket(), 5000);
            };
        } catch (error) {
            console.error('Failed to setup WebSocket:', error);
        }
    }

    handleUpdate(data) {
        // Update stage status based on WebSocket message
        if (data.data && data.data.task_id) {
            this.updateStageStatus(data.data);
        }
    }

    updateStageStatus(taskData) {
        // Find and update the corresponding stage
        const stage = this.stages.find(s => s.task_id === taskData.task_id);
        if (stage) {
            stage.status = taskData.status;
            stage.start_time = taskData.start_time;
            stage.end_time = taskData.end_time;
            stage.duration = taskData.duration;

            // Re-render the pipeline
            this.svg.innerHTML = '';
            this.addSVGDefinitions();
            this.renderPipeline();
        }
    }

    setupAutoRefresh() {
        // Refresh pipeline data every 10 seconds as fallback
        this.updateInterval = setInterval(async () => {
            await this.loadPipelineData();
            this.svg.innerHTML = '';
            this.addSVGDefinitions();
            this.renderPipeline();
        }, 10000);
    }

    showError(message) {
        this.container.innerHTML = `
            <div class="pipeline-error">
                <h3>Pipeline Visualization Error</h3>
                <p>${message}</p>
                <button onclick="location.reload()">Retry</button>
            </div>
        `;
    }

    destroy() {
        if (this.websocket) {
            this.websocket.close();
        }
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// CSS styles for the pipeline visualization
const pipelineStyles = `
<style>
.pipeline-container {
    background: #1a1a1a;
    border-radius: 8px;
    padding: 20px;
    margin: 20px 0;
    overflow: hidden;
}

.pipeline-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #00ff88;
}

.pipeline-title {
    color: #00ff88;
    font-size: 1.5rem;
    font-weight: bold;
}

.pipeline-stats {
    display: flex;
    gap: 20px;
}

.pipeline-stat {
    text-align: center;
}

.pipeline-stat-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: #00ff88;
}

.pipeline-stat-label {
    font-size: 0.8rem;
    color: #cccccc;
}

.stage-rect.running {
    animation: pulse 2s infinite;
}

.status-indicator {
    animation: blink 1s infinite;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.7; }
    100% { opacity: 1; }
}

@keyframes blink {
    0% { opacity: 1; }
    50% { opacity: 0.3; }
    100% { opacity: 1; }
}

.stage-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.stage-modal-content {
    background: #2d2d2d;
    border-radius: 8px;
    padding: 20px;
    max-width: 500px;
    width: 90%;
    color: #ffffff;
}

.stage-modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 1px solid #444;
}

.stage-modal-close {
    font-size: 1.5rem;
    cursor: pointer;
    color: #cccccc;
}

.stage-modal-close:hover {
    color: #ffffff;
}

.stage-modal-body p {
    margin: 8px 0;
    line-height: 1.4;
}

.status-pending { color: #6B7280; }
.status-running { color: #F59E0B; }
.status-completed { color: #10B981; }
.status-failed { color: #EF4444; }

.pipeline-error {
    text-align: center;
    padding: 40px;
    color: #ffffff;
}

.pipeline-error h3 {
    color: #EF4444;
    margin-bottom: 15px;
}

.pipeline-error button {
    background: #00ff88;
    color: #1a1a1a;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
    margin-top: 15px;
}

.pipeline-error button:hover {
    background: #00cc6a;
}

@media (max-width: 768px) {
    .pipeline-stats {
        flex-direction: column;
        gap: 10px;
    }

    .pipeline-header {
        flex-direction: column;
        gap: 10px;
        text-align: center;
    }
}
</style>
`;

// Add styles to document
document.head.insertAdjacentHTML('beforeend', pipelineStyles);
