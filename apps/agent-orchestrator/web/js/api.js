/**
 * API Client for Agent Orchestrator Dashboard
 * Handles HTTP requests to the orchestrator backend
 */

class ApiClient {
    constructor(baseUrl = 'http://localhost:8888') {
        this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };

        // Request interceptors
        this.requestInterceptors = [];
        this.responseInterceptors = [];

        // Request cache for GET requests
        this.cache = new Map();
        this.cacheTimeout = 30000; // 30 seconds
    }

    /**
     * Add request interceptor
     */
    addRequestInterceptor(interceptor) {
        this.requestInterceptors.push(interceptor);
    }

    /**
     * Add response interceptor
     */
    addResponseInterceptor(interceptor) {
        this.responseInterceptors.push(interceptor);
    }

    /**
     * Apply request interceptors
     */
    async applyRequestInterceptors(config) {
        let modifiedConfig = { ...config };

        for (const interceptor of this.requestInterceptors) {
            try {
                modifiedConfig = await interceptor(modifiedConfig);
            } catch (error) {
                console.error('Request interceptor error:', error);
            }
        }

        return modifiedConfig;
    }

    /**
     * Apply response interceptors
     */
    async applyResponseInterceptors(response, request) {
        let modifiedResponse = response;

        for (const interceptor of this.responseInterceptors) {
            try {
                modifiedResponse = await interceptor(modifiedResponse, request);
            } catch (error) {
                console.error('Response interceptor error:', error);
            }
        }

        return modifiedResponse;
    }

    /**
     * Make HTTP request
     */
    async request(config) {
        // Apply request interceptors
        config = await this.applyRequestInterceptors(config);

        // Build URL
        const url = config.url.startsWith('http') ? config.url : `${this.baseUrl}${config.url}`;

        // Check cache for GET requests
        if (config.method === 'GET' && config.useCache !== false) {
            const cacheKey = this.getCacheKey(url, config.params);
            const cached = this.getFromCache(cacheKey);
            if (cached) {
                return cached;
            }
        }

        // Prepare request options
        const options = {
            method: config.method || 'GET',
            headers: { ...this.defaultHeaders, ...(config.headers || {}) }
        };

        // Add query parameters
        if (config.params) {
            const urlObj = new URL(url);
            Object.keys(config.params).forEach(key => {
                if (config.params[key] !== null && config.params[key] !== undefined) {
                    urlObj.searchParams.set(key, config.params[key]);
                }
            });
            url = urlObj.toString();
        }

        // Add request body
        if (config.data && ['POST', 'PUT', 'PATCH'].includes(options.method)) {
            options.body = JSON.stringify(config.data);
        }

        // Set timeout
        const controller = new AbortController();
        const timeout = config.timeout || 30000;
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        options.signal = controller.signal;

        try {
            const response = await fetch(url, options);
            clearTimeout(timeoutId);

            // Apply response interceptors
            const processedResponse = await this.applyResponseInterceptors(response, config);

            // Handle response
            if (!processedResponse.ok) {
                throw await this.createHttpError(processedResponse, config);
            }

            // Parse response
            const result = await this.parseResponse(processedResponse);

            // Cache GET requests
            if (config.method === 'GET' && config.useCache !== false) {
                const cacheKey = this.getCacheKey(url, config.params);
                this.setCache(cacheKey, result);
            }

            return result;

        } catch (error) {
            clearTimeout(timeoutId);

            if (error.name === 'AbortError') {
                throw new ApiError('Request timeout', 408, null, config);
            }

            if (error instanceof ApiError) {
                throw error;
            }

            throw new ApiError('Network error', 0, error.message, config);
        }
    }

    /**
     * Parse response based on content type
     */
    async parseResponse(response) {
        const contentType = response.headers.get('content-type');

        if (contentType && contentType.includes('application/json')) {
            try {
                return await response.json();
            } catch (error) {
                return null;
            }
        } else if (contentType && contentType.includes('text/')) {
            return await response.text();
        } else {
            return await response.blob();
        }
    }

    /**
     * Create HTTP error
     */
    async createHttpError(response, config) {
        let errorData = null;

        try {
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                errorData = await response.json();
            } else {
                errorData = { message: await response.text() };
            }
        } catch (e) {
            errorData = { message: response.statusText };
        }

        return new ApiError(
            errorData.message || response.statusText,
            response.status,
            errorData,
            config
        );
    }

    /**
     * Cache management
     */
    getCacheKey(url, params) {
        const paramsStr = params ? JSON.stringify(params) : '';
        return `${url}:${paramsStr}`;
    }

    getFromCache(key) {
        const cached = this.cache.get(key);
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            return cached.data;
        }
        this.cache.delete(key);
        return null;
    }

    setCache(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }

    clearCache() {
        this.cache.clear();
    }

    // HTTP method shortcuts
    get(url, config = {}) {
        return this.request({ ...config, method: 'GET', url });
    }

    post(url, data, config = {}) {
        return this.request({ ...config, method: 'POST', url, data });
    }

    put(url, data, config = {}) {
        return this.request({ ...config, method: 'PUT', url, data });
    }

    patch(url, data, config = {}) {
        return this.request({ ...config, method: 'PATCH', url, data });
    }

    delete(url, config = {}) {
        return this.request({ ...config, method: 'DELETE', url });
    }
}

/**
 * Custom API Error class
 */
class ApiError extends Error {
    constructor(message, status, data, config) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.data = data;
        this.config = config;
    }

    isNetworkError() {
        return this.status === 0;
    }

    isTimeout() {
        return this.status === 408;
    }

    isClientError() {
        return this.status >= 400 && this.status < 500;
    }

    isServerError() {
        return this.status >= 500;
    }
}

/**
 * Orchestrator API wrapper
 */
class OrchestratorAPI {
    constructor(baseUrl) {
        this.client = new ApiClient(baseUrl);
        this.setupInterceptors();
    }

    setupInterceptors() {
        // Add request logging
        this.client.addRequestInterceptor(async (config) => {
            console.log(`API Request: ${config.method || 'GET'} ${config.url}`);
            return config;
        });

        // Add response logging
        this.client.addResponseInterceptor(async (response, config) => {
            if (response.ok) {
                console.log(`API Response: ${config.method || 'GET'} ${config.url} - ${response.status}`);
            } else {
                console.error(`API Error: ${config.method || 'GET'} ${config.url} - ${response.status}`);
            }
            return response;
        });
    }

    // Orchestrator Management
    async getStatus() {
        return this.client.get('/status');
    }

    async getMetrics() {
        return this.client.get('/metrics');
    }

    async getHealthCheck() {
        return this.client.get('/metrics/health');
    }

    // Task Management
    async getTasks(params = {}) {
        return this.client.get('/tasks', { params });
    }

    async getTask(taskId) {
        return this.client.get(`/tasks/${taskId}`);
    }

    async retryTask(taskId, data = {}) {
        return this.client.post(`/tasks/${taskId}/retry`, data);
    }

    async cancelTask(taskId) {
        return this.client.delete(`/tasks/${taskId}`);
    }

    async injectTasks(tasks, options = {}) {
        const data = {
            tasks,
            priority: options.priority || 'normal',
            execution_mode: options.executionMode || 'parallel'
        };
        return this.client.post('/inject_tasks', data);
    }

    async updateDependencies(taskId, dependencies) {
        return this.client.post('/update_dependencies', {
            task_id: taskId,
            ...dependencies
        });
    }

    async triggerContinue(options = {}) {
        return this.client.post('/trigger_continue', options);
    }

    // Workflow Management (if supported)
    async getWorkflows(params = {}) {
        return this.client.get('/workflows', { params });
    }

    async getWorkflow(workflowId) {
        return this.client.get(`/workflows/${workflowId}`);
    }

    async pauseWorkflow(workflowId) {
        return this.client.post(`/workflows/${workflowId}/pause`);
    }

    async resumeWorkflow(workflowId) {
        return this.client.post(`/workflows/${workflowId}/resume`);
    }

    async cancelWorkflow(workflowId) {
        return this.client.delete(`/workflows/${workflowId}`);
    }

    async getWorkflowLogs(workflowId, params = {}) {
        return this.client.get(`/workflows/${workflowId}/logs`, { params });
    }

    async getWorkflowDeliverables(workflowId) {
        return this.client.get(`/workflows/${workflowId}/deliverables`);
    }

    async downloadDeliverable(workflowId, deliverableId) {
        return this.client.get(`/workflows/${workflowId}/deliverables/${deliverableId}/download`, {
            headers: { 'Accept': '*/*' }
        });
    }

    // Chat Integration
    async getChatStatus() {
        return this.client.get('/chat/status');
    }

    async getChatMessages(params = {}) {
        return this.client.get('/chat/messages', { params });
    }

    async sendChatMessage(content, messageType = 'chat') {
        return this.client.post('/chat/message', {
            content,
            sender_id: 'dashboard',
            message_type: messageType
        });
    }

    // System Operations
    async getSystemInfo() {
        return Promise.all([
            this.getStatus(),
            this.getMetrics(),
            this.getHealthCheck()
        ]).then(([status, metrics, health]) => ({
            status,
            metrics,
            health
        }));
    }

    // Batch Operations
    async getMultipleWorkflows(workflowIds) {
        return Promise.all(
            workflowIds.map(id => this.getWorkflow(id).catch(error => ({ id, error })))
        );
    }

    async batchOperation(operation, items) {
        return Promise.allSettled(
            items.map(item => operation(item))
        );
    }
}

/**
 * API response cache with automatic expiration
 */
class ResponseCache {
    constructor(defaultTtl = 30000) {
        this.cache = new Map();
        this.defaultTtl = defaultTtl;
        this.timers = new Map();
    }

    set(key, value, ttl = this.defaultTtl) {
        // Clear existing timer
        if (this.timers.has(key)) {
            clearTimeout(this.timers.get(key));
        }

        // Set cache entry
        this.cache.set(key, {
            value,
            timestamp: Date.now(),
            ttl
        });

        // Set expiration timer
        const timer = setTimeout(() => {
            this.delete(key);
        }, ttl);

        this.timers.set(key, timer);
    }

    get(key) {
        const entry = this.cache.get(key);
        if (!entry) return null;

        // Check if expired
        if (Date.now() - entry.timestamp > entry.ttl) {
            this.delete(key);
            return null;
        }

        return entry.value;
    }

    delete(key) {
        // Clear timer
        if (this.timers.has(key)) {
            clearTimeout(this.timers.get(key));
            this.timers.delete(key);
        }

        // Remove from cache
        return this.cache.delete(key);
    }

    clear() {
        // Clear all timers
        this.timers.forEach(timer => clearTimeout(timer));
        this.timers.clear();

        // Clear cache
        this.cache.clear();
    }

    size() {
        return this.cache.size;
    }

    keys() {
        return Array.from(this.cache.keys());
    }
}

// Export for global use
if (typeof window !== 'undefined') {
    window.ApiClient = ApiClient;
    window.ApiError = ApiError;
    window.OrchestratorAPI = OrchestratorAPI;
    window.ResponseCache = ResponseCache;
}
