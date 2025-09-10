/**
 * REST API Client
 * Handles all HTTP requests to the dashboard backend
 */
class ApiClient {
    constructor(baseUrl = window.location.origin, options = {}) {
        this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
        this.timeout = options.timeout || 10000;
        this.retryAttempts = options.retryAttempts || 3;
        this.retryDelay = options.retryDelay || 1000;

        // Request interceptors
        this.requestInterceptors = [];
        this.responseInterceptors = [];

        // Cache for GET requests
        this.cache = new Map();
        this.cacheTimeout = options.cacheTimeout || 5000;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            timeout: this.timeout,
            ...options
        };

        // Check cache for GET requests
        if (config.method === 'GET' && this.shouldUseCache(url, options)) {
            const cached = this.getFromCache(url);
            if (cached) {
                return cached;
            }
        }

        // Apply request interceptors
        for (const interceptor of this.requestInterceptors) {
            await interceptor(config);
        }

        let lastError;
        for (let attempt = 0; attempt <= this.retryAttempts; attempt++) {
            try {
                const response = await this.executeRequest(url, config);

                // Apply response interceptors
                for (const interceptor of this.responseInterceptors) {
                    await interceptor(response);
                }

                const result = await this.processResponse(response);

                // Cache GET requests
                if (config.method === 'GET' && this.shouldUseCache(url, options)) {
                    this.setCache(url, result);
                }

                return result;
            } catch (error) {
                lastError = error;
                console.warn(`Request attempt ${attempt + 1} failed:`, error.message);

                // Don't retry on client errors (4xx) or if it's the last attempt
                if (error.status >= 400 && error.status < 500 || attempt === this.retryAttempts) {
                    throw error;
                }

                // Wait before retrying
                if (attempt < this.retryAttempts) {
                    await this.sleep(this.retryDelay * Math.pow(2, attempt));
                }
            }
        }

        throw lastError;
    }

    async executeRequest(url, config) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), config.timeout);

        try {
            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error(`Request timeout after ${config.timeout}ms`);
            }
            throw error;
        }
    }

    async processResponse(response) {
        if (!response.ok) {
            const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
            error.status = response.status;
            error.statusText = response.statusText;

            try {
                const errorBody = await response.json();
                error.data = errorBody;
            } catch {
                // Ignore JSON parsing errors for error responses
            }

            throw error;
        }

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }

        return await response.text();
    }

    // Cache management
    shouldUseCache(url, options) {
        return !options.noCache && !options.cache === false;
    }

    getFromCache(url) {
        const cached = this.cache.get(url);
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            console.log('Using cached response for:', url);
            return cached.data;
        }
        return null;
    }

    setCache(url, data) {
        this.cache.set(url, {
            data: data,
            timestamp: Date.now()
        });
    }

    clearCache() {
        this.cache.clear();
    }

    // Utility methods
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Interceptor methods
    addRequestInterceptor(interceptor) {
        this.requestInterceptors.push(interceptor);
    }

    addResponseInterceptor(interceptor) {
        this.responseInterceptors.push(interceptor);
    }

    // API endpoints
    async getStatus() {
        return await this.request('/api/status');
    }

    async getTasks() {
        return await this.request('/api/tasks');
    }

    async getTask(taskId) {
        return await this.request(`/api/tasks/${taskId}`);
    }

    async getPerformance() {
        return await this.request('/api/performance');
    }

    async getTaskLogs(taskId) {
        return await this.request(`/api/logs/${taskId}`);
    }

    async getQualityReport() {
        return await this.request('/api/quality-report');
    }

    async getHealth() {
        return await this.request('/api/health');
    }

    async getAnalytics() {
        return await this.request('/api/analytics');
    }

    async getLiveData() {
        return await this.request('/api/live-data');
    }

    async getDirectories() {
        return await this.request('/api/directories');
    }

    async getWebSocketStats() {
        return await this.request('/api/websocket-stats');
    }

    async simulateProgress() {
        return await this.request('/api/simulate-progress');
    }
}

/**
 * Enhanced API Client with dashboard-specific methods
 */
class DashboardApiClient extends ApiClient {
    constructor(baseUrl, options = {}) {
        super(baseUrl, options);
        this.pollingIntervals = new Map();
    }

    // Dashboard-specific data fetching
    async getDashboardData() {
        try {
            const [status, tasks, performance] = await Promise.all([
                this.getStatus(),
                this.getTasks(),
                this.getPerformance()
            ]);

            return {
                status,
                tasks,
                performance,
                timestamp: Date.now()
            };
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
            throw error;
        }
    }

    // Polling mechanism for real-time updates
    startPolling(endpoint, callback, interval = 5000) {
        if (this.pollingIntervals.has(endpoint)) {
            this.stopPolling(endpoint);
        }

        const poll = async () => {
            try {
                const data = await this.request(endpoint, { noCache: true });
                callback(null, data);
            } catch (error) {
                callback(error, null);
            }
        };

        // Initial call
        poll();

        // Set up interval
        const intervalId = setInterval(poll, interval);
        this.pollingIntervals.set(endpoint, intervalId);

        console.log(`Started polling ${endpoint} every ${interval}ms`);
    }

    stopPolling(endpoint) {
        const intervalId = this.pollingIntervals.get(endpoint);
        if (intervalId) {
            clearInterval(intervalId);
            this.pollingIntervals.delete(endpoint);
            console.log(`Stopped polling ${endpoint}`);
        }
    }

    stopAllPolling() {
        for (const [endpoint, intervalId] of this.pollingIntervals) {
            clearInterval(intervalId);
            console.log(`Stopped polling ${endpoint}`);
        }
        this.pollingIntervals.clear();
    }

    // Batch requests for efficiency
    async batchRequests(requests) {
        try {
            const promises = requests.map(req =>
                this.request(req.endpoint, req.options)
                    .catch(error => ({ error, endpoint: req.endpoint }))
            );

            const results = await Promise.all(promises);

            return results.map((result, index) => ({
                endpoint: requests[index].endpoint,
                data: result.error ? null : result,
                error: result.error || null
            }));
        } catch (error) {
            console.error('Batch request failed:', error);
            throw error;
        }
    }

    // Health monitoring
    async checkHealth() {
        try {
            const startTime = Date.now();
            const health = await this.getHealth();
            const responseTime = Date.now() - startTime;

            return {
                ...health,
                responseTime,
                healthy: true
            };
        } catch (error) {
            return {
                healthy: false,
                error: error.message,
                responseTime: null
            };
        }
    }
}

// Export for use in other modules
window.ApiClient = ApiClient;
window.DashboardApiClient = DashboardApiClient;
