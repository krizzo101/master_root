/**
 * WebSocket Connection Manager
 * Handles real-time communication with the dashboard backend
 */
class WebSocketManager {
    constructor(url = 'ws://localhost:8004/ws', options = {}) {
        this.url = url;
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectDelay = options.reconnectDelay || 3000;
        this.heartbeatInterval = options.heartbeatInterval || 30000;
        this.heartbeatTimer = null;

        // Event listeners
        this.eventListeners = {
            connected: [],
            disconnected: [],
            message: [],
            error: [],
            taskUpdate: [],
            statusUpdate: [],
            performanceUpdate: []
        };

        // Initialize connection
        this.connect();
    }

    connect() {
        try {
            console.log('Attempting WebSocket connection to:', this.url);
            this.ws = new WebSocket(this.url);

            this.ws.onopen = (event) => {
                console.log('WebSocket connected successfully');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.startHeartbeat();
                this.emit('connected', event);
                this.updateConnectionStatus('connected');
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                    this.emit('error', { type: 'parse_error', error, data: event.data });
                }
            };

            this.ws.onclose = (event) => {
                console.log('WebSocket connection closed:', event.code, event.reason);
                this.isConnected = false;
                this.stopHeartbeat();
                this.emit('disconnected', event);
                this.updateConnectionStatus('disconnected');
                this.attemptReconnection();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.emit('error', { type: 'connection_error', error });
                this.updateConnectionStatus('error');
            };

        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.emit('error', { type: 'creation_error', error });
            this.updateConnectionStatus('error');
            this.attemptReconnection();
        }
    }

    handleMessage(data) {
        console.log('WebSocket message received:', data);

        // Emit generic message event
        this.emit('message', data);

        // Emit specific events based on message type
        switch (data.type) {
            case 'task_update':
                this.emit('taskUpdate', data);
                break;
            case 'status_update':
                this.emit('statusUpdate', data);
                break;
            case 'performance_update':
                this.emit('performanceUpdate', data);
                break;
            case 'heartbeat_response':
                // Handle heartbeat response
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    send(data) {
        if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
            try {
                const message = typeof data === 'string' ? data : JSON.stringify(data);
                this.ws.send(message);
                return true;
            } catch (error) {
                console.error('Error sending WebSocket message:', error);
                this.emit('error', { type: 'send_error', error });
                return false;
            }
        } else {
            console.warn('Cannot send message: WebSocket not connected');
            return false;
        }
    }

    startHeartbeat() {
        this.stopHeartbeat();
        this.heartbeatTimer = setInterval(() => {
            if (this.isConnected) {
                this.send({ type: 'heartbeat', timestamp: Date.now() });
            }
        }, this.heartbeatInterval);
    }

    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    attemptReconnection() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${this.reconnectDelay}ms`);

            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay);
        } else {
            console.error('Maximum reconnection attempts reached');
            this.updateConnectionStatus('failed');
        }
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        const statusIndicator = document.querySelector('.status-indicator');

        if (statusElement) {
            switch (status) {
                case 'connected':
                    statusElement.textContent = 'Connected';
                    statusElement.className = 'connection-status connected';
                    break;
                case 'disconnected':
                    statusElement.textContent = 'Disconnected';
                    statusElement.className = 'connection-status disconnected';
                    break;
                case 'error':
                    statusElement.textContent = 'Connection Error';
                    statusElement.className = 'connection-status error';
                    break;
                case 'failed':
                    statusElement.textContent = 'Connection Failed';
                    statusElement.className = 'connection-status failed';
                    break;
            }
        }

        if (statusIndicator) {
            statusIndicator.className = `status-indicator ${status}`;
            statusIndicator.setAttribute('aria-label', `System status: ${status}`);
        }

        // Update last update time
        this.updateLastUpdateTime();
    }

    updateLastUpdateTime() {
        const lastUpdateElement = document.getElementById('last-update');
        if (lastUpdateElement) {
            const now = new Date().toLocaleTimeString();
            lastUpdateElement.textContent = `Last updated: ${now}`;
        }
    }

    // Event system
    on(event, callback) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].push(callback);
        }
    }

    off(event, callback) {
        if (this.eventListeners[event]) {
            const index = this.eventListeners[event].indexOf(callback);
            if (index > -1) {
                this.eventListeners[event].splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    disconnect() {
        this.stopHeartbeat();
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
        }
        this.isConnected = false;
    }

    // Getters
    getConnectionState() {
        return {
            isConnected: this.isConnected,
            readyState: this.ws ? this.ws.readyState : WebSocket.CLOSED,
            url: this.url,
            reconnectAttempts: this.reconnectAttempts
        };
    }
}

// Export for use in other modules
window.WebSocketManager = WebSocketManager;
