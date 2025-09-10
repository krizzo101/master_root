/**
 * WebSocket Manager for Agent Orchestrator Dashboard
 * Handles real-time communication with the orchestrator backend
 */

class WebSocketManager {
    constructor(url = 'ws://localhost:8765') {
        this.url = url;
        this.ws = null;
        this.reconnectInterval = 5000;
        this.maxReconnectAttempts = 10;
        this.reconnectAttempts = 0;
        this.isConnecting = false;
        this.isIntentionallyClosed = false;
        this.sessionId = this.generateSessionId();
        this.subscriptions = new Set();

        // Event handlers
        this.eventHandlers = {
            open: [],
            close: [],
            error: [],
            message: [],
            reconnect: [],
            maxReconnectReached: []
        };

        // Message queue for offline messages
        this.messageQueue = [];

        // Heartbeat
        this.heartbeatInterval = null;
        this.heartbeatTimeout = 30000; // 30 seconds
        this.lastHeartbeat = null;

        this.connect();
    }

    /**
     * Generate unique session ID
     */
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.CONNECTING)) {
            return;
        }

        this.isConnecting = true;
        this.isIntentionallyClosed = false;

        try {
            console.log('Connecting to WebSocket:', this.url);
            this.ws = new WebSocket(this.url);
            this.setupEventHandlers();
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.handleConnectionError(error);
        }
    }

    /**
     * Setup WebSocket event handlers
     */
    setupEventHandlers() {
        this.ws.onopen = (event) => {
            console.log('WebSocket connected');
            this.isConnecting = false;
            this.reconnectAttempts = 0;

            // Send connection initialization
            this.sendMessage({
                type: 'connection_init',
                session_id: this.sessionId,
                timestamp: new Date().toISOString()
            });

            // Subscribe to previously subscribed channels
            if (this.subscriptions.size > 0) {
                this.sendMessage({
                    type: 'subscribe',
                    channels: Array.from(this.subscriptions),
                    session_id: this.sessionId
                });
            }

            // Process queued messages
            this.processMessageQueue();

            // Start heartbeat
            this.startHeartbeat();

            this.emit('open', event);
        };

        this.ws.onclose = (event) => {
            console.log('WebSocket closed:', event.code, event.reason);
            this.isConnecting = false;
            this.stopHeartbeat();

            this.emit('close', event);

            if (!this.isIntentionallyClosed) {
                this.handleReconnection();
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.isConnecting = false;
            this.emit('error', error);
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };
    }

    /**
     * Handle incoming messages
     */
    handleMessage(data) {
        // Update last heartbeat time for heartbeat messages
        if (data.type === 'heartbeat' || data.type === 'pong') {
            this.lastHeartbeat = Date.now();
            return;
        }

        // Emit message event
        this.emit('message', data);

        // Handle specific message types
        switch (data.type) {
            case 'workflow_update':
                this.emit('workflowUpdate', data);
                break;
            case 'task_update':
                this.emit('taskUpdate', data);
                break;
            case 'log_entry':
                this.emit('logEntry', data);
                break;
            case 'progress_update':
                this.emit('progressUpdate', data);
                break;
            case 'system_metric':
                this.emit('systemMetric', data);
                break;
            case 'agent_status':
                this.emit('agentStatus', data);
                break;
            case 'alert':
                this.emit('alert', data);
                break;
            case 'connection_established':
                console.log('Connection established with session ID:', data.session_id);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    /**
     * Send message to server
     */
    sendMessage(message) {
        if (this.isConnected()) {
            try {
                this.ws.send(JSON.stringify(message));
                return true;
            } catch (error) {
                console.error('Failed to send message:', error);
                return false;
            }
        } else {
            // Queue message for later
            this.messageQueue.push(message);
            console.log('Message queued (not connected):', message.type);
            return false;
        }
    }

    /**
     * Process queued messages
     */
    processMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.sendMessage(message);
        }
    }

    /**
     * Subscribe to workflow updates
     */
    subscribeToWorkflow(workflowId) {
        this.subscriptions.add(`workflow:${workflowId}`);

        return this.sendMessage({
            type: 'subscribe',
            channels: [`workflow:${workflowId}`],
            session_id: this.sessionId
        });
    }

    /**
     * Unsubscribe from workflow updates
     */
    unsubscribeFromWorkflow(workflowId) {
        this.subscriptions.delete(`workflow:${workflowId}`);

        return this.sendMessage({
            type: 'unsubscribe',
            channels: [`workflow:${workflowId}`],
            session_id: this.sessionId
        });
    }

    /**
     * Subscribe to general orchestrator updates
     */
    subscribeToOrchestrator() {
        this.subscriptions.add('orchestrator');
        this.subscriptions.add('system_metrics');

        return this.sendMessage({
            type: 'subscribe',
            channels: ['orchestrator', 'system_metrics'],
            session_id: this.sessionId
        });
    }

    /**
     * Send chat message
     */
    sendChatMessage(content, targetAgentId = null) {
        return this.sendMessage({
            type: 'chat_message',
            content: content,
            sender_id: this.sessionId,
            target: targetAgentId || 'all',
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Execute command
     */
    executeCommand(command, parameters = {}) {
        return this.sendMessage({
            type: 'command',
            command: command,
            parameters: parameters,
            sender_id: this.sessionId,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Start heartbeat mechanism
     */
    startHeartbeat() {
        this.stopHeartbeat(); // Clear any existing heartbeat

        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected()) {
                this.sendMessage({
                    type: 'ping',
                    timestamp: new Date().toISOString()
                });

                // Check if we've received a recent heartbeat response
                if (this.lastHeartbeat && (Date.now() - this.lastHeartbeat) > this.heartbeatTimeout) {
                    console.warn('Heartbeat timeout detected, reconnecting...');
                    this.reconnect();
                }
            }
        }, this.heartbeatTimeout / 2);

        this.lastHeartbeat = Date.now();
    }

    /**
     * Stop heartbeat mechanism
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    /**
     * Handle reconnection logic
     */
    handleReconnection() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.emit('maxReconnectReached');
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1), 30000);

        console.log(`Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);

        setTimeout(() => {
            if (!this.isIntentionallyClosed) {
                this.emit('reconnect', this.reconnectAttempts);
                this.connect();
            }
        }, delay);
    }

    /**
     * Handle connection error
     */
    handleConnectionError(error) {
        this.isConnecting = false;
        console.error('Connection error:', error);

        if (!this.isIntentionallyClosed) {
            this.handleReconnection();
        }
    }

    /**
     * Manually reconnect
     */
    reconnect() {
        if (this.ws) {
            this.ws.close();
        }
        this.connect();
    }

    /**
     * Close connection
     */
    close() {
        this.isIntentionallyClosed = true;
        this.stopHeartbeat();

        if (this.ws) {
            this.ws.close();
        }
    }

    /**
     * Check if connected
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    /**
     * Get connection state
     */
    getConnectionState() {
        if (!this.ws) return 'disconnected';

        switch (this.ws.readyState) {
            case WebSocket.CONNECTING:
                return 'connecting';
            case WebSocket.OPEN:
                return 'connected';
            case WebSocket.CLOSING:
                return 'closing';
            case WebSocket.CLOSED:
                return 'disconnected';
            default:
                return 'unknown';
        }
    }

    /**
     * Add event listener
     */
    on(event, handler) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].push(handler);
        }
    }

    /**
     * Remove event listener
     */
    off(event, handler) {
        if (this.eventHandlers[event]) {
            const index = this.eventHandlers[event].indexOf(handler);
            if (index > -1) {
                this.eventHandlers[event].splice(index, 1);
            }
        }
    }

    /**
     * Emit event
     */
    emit(event, data) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error('Error in event handler:', error);
                }
            });
        }
    }

    /**
     * Get connection statistics
     */
    getStats() {
        return {
            sessionId: this.sessionId,
            connectionState: this.getConnectionState(),
            reconnectAttempts: this.reconnectAttempts,
            subscriptions: Array.from(this.subscriptions),
            queuedMessages: this.messageQueue.length,
            lastHeartbeat: this.lastHeartbeat ? new Date(this.lastHeartbeat).toISOString() : null
        };
    }
}

/**
 * Connection status indicator UI controller
 */
class ConnectionStatusIndicator {
    constructor(wsManager) {
        this.wsManager = wsManager;
        this.statusIndicator = document.getElementById('status-indicator');
        this.statusText = document.getElementById('status-text');

        this.setupEventListeners();
        this.updateStatus('connecting');
    }

    setupEventListeners() {
        this.wsManager.on('open', () => {
            this.updateStatus('connected');
        });

        this.wsManager.on('close', () => {
            this.updateStatus('disconnected');
        });

        this.wsManager.on('error', () => {
            this.updateStatus('error');
        });

        this.wsManager.on('reconnect', (attempt) => {
            this.updateStatus('reconnecting', `Reconnecting (${attempt})...`);
        });

        this.wsManager.on('maxReconnectReached', () => {
            this.updateStatus('failed', 'Connection failed');
        });
    }

    updateStatus(state, customText = null) {
        // Update indicator class
        this.statusIndicator.className = `status-indicator ${state}`;

        // Update status text
        const statusMessages = {
            connecting: 'Connecting...',
            connected: 'Connected',
            disconnected: 'Disconnected',
            reconnecting: 'Reconnecting...',
            error: 'Connection error',
            failed: 'Connection failed'
        };

        this.statusText.textContent = customText || statusMessages[state] || 'Unknown';
    }
}

/**
 * WebSocket event dispatcher for dashboard components
 */
class EventDispatcher {
    constructor(wsManager) {
        this.wsManager = wsManager;
        this.setupEventForwarding();
    }

    setupEventForwarding() {
        // Forward WebSocket events to custom events on document
        this.wsManager.on('workflowUpdate', (data) => {
            document.dispatchEvent(new CustomEvent('workflow-update', { detail: data }));
        });

        this.wsManager.on('taskUpdate', (data) => {
            document.dispatchEvent(new CustomEvent('task-update', { detail: data }));
        });

        this.wsManager.on('logEntry', (data) => {
            document.dispatchEvent(new CustomEvent('log-entry', { detail: data }));
        });

        this.wsManager.on('progressUpdate', (data) => {
            document.dispatchEvent(new CustomEvent('progress-update', { detail: data }));
        });

        this.wsManager.on('systemMetric', (data) => {
            document.dispatchEvent(new CustomEvent('system-metric', { detail: data }));
        });

        this.wsManager.on('agentStatus', (data) => {
            document.dispatchEvent(new CustomEvent('agent-status', { detail: data }));
        });

        this.wsManager.on('alert', (data) => {
            document.dispatchEvent(new CustomEvent('alert', { detail: data }));
        });

        this.wsManager.on('open', () => {
            document.dispatchEvent(new CustomEvent('websocket-connected'));
        });

        this.wsManager.on('close', () => {
            document.dispatchEvent(new CustomEvent('websocket-disconnected'));
        });
    }
}

// Export for global use
if (typeof window !== 'undefined') {
    window.WebSocketManager = WebSocketManager;
    window.ConnectionStatusIndicator = ConnectionStatusIndicator;
    window.EventDispatcher = EventDispatcher;
}
