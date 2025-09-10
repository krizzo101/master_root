/**
 * Main Application Entry Point
 * Initializes and coordinates all dashboard components
 */

class DashboardApp {
    constructor() {
        // Configuration
        this.config = {
            apiBaseUrl: this.getApiBaseUrl(),
            wsUrl: this.getWebSocketUrl(),
            features: {
                darkMode: true,
                notifications: true,
                autoRefresh: true,
                comparison: true,
                chat: false // Disabled for now
            }
        };

        // Core components
        this.apiClient = null;
        this.wsManager = null;
        this.dashboard = null;
        this.workflowDetailView = null;
        this.comparisonView = null;

        // UI components
        this.connectionStatusIndicator = null;
        this.eventDispatcher = null;
        this.themeManager = null;

        // State
        this.isInitialized = false;
        this.initializationError = null;
    }

    /**
     * Initialize the application
     */
    async init() {
        try {
            console.log('Initializing Agent Orchestrator Dashboard...');

            // Check prerequisites
            this.checkPrerequisites();

            // Initialize UI utilities
            UI.init();

            // Initialize theme manager
            this.themeManager = new ThemeManager();

            // Initialize API client
            this.initializeApiClient();

            // Initialize WebSocket manager
            this.initializeWebSocketManager();

            // Initialize core components
            this.initializeComponents();

            // Setup global event handlers
            this.setupGlobalEventHandlers();

            // Setup keyboard shortcuts
            this.setupKeyboardShortcuts();

            // Setup error handling
            this.setupErrorHandling();

            // Load user preferences
            this.loadUserPreferences();

            // Mark as initialized
            this.isInitialized = true;

            console.log('Dashboard initialization complete');

            // Show welcome message
            this.showWelcomeMessage();

        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            this.initializationError = error;
            this.showInitializationError(error);
        }
    }

    /**
     * Check if all prerequisites are met
     */
    checkPrerequisites() {
        // Check for required DOM elements
        const requiredElements = [
            'dashboard-container',
            'workflows-grid',
            'workflow-detail-modal',
            'comparison-modal'
        ];

        const missingElements = requiredElements.filter(id => !document.getElementById(id));
        if (missingElements.length > 0) {
            throw new Error(`Missing required DOM elements: ${missingElements.join(', ')}`);
        }

        // Check for required browser features
        if (!window.WebSocket) {
            throw new Error('WebSocket support is required');
        }

        if (!window.fetch) {
            throw new Error('Fetch API support is required');
        }

        if (!window.localStorage) {
            console.warn('LocalStorage not available - some features may be limited');
        }
    }

    /**
     * Initialize API client
     */
    initializeApiClient() {
        this.apiClient = new OrchestratorAPI(this.config.apiBaseUrl);

        // Add global error interceptor
        this.apiClient.client.addResponseInterceptor(async (response, config) => {
            if (!response.ok && response.status >= 500) {
                UI.showToast('Server error occurred', 'error');
            }
            return response;
        });

        console.log('API client initialized:', this.config.apiBaseUrl);
    }

    /**
     * Initialize WebSocket manager
     */
    initializeWebSocketManager() {
        this.wsManager = new WebSocketManager(this.config.wsUrl);

        // Initialize connection status indicator
        this.connectionStatusIndicator = new ConnectionStatusIndicator(this.wsManager);

        // Initialize event dispatcher
        this.eventDispatcher = new EventDispatcher(this.wsManager);

        // Add connection event handlers
        this.wsManager.on('open', () => {
            console.log('WebSocket connected');
            UI.announce('Connected to server');
        });

        this.wsManager.on('close', () => {
            console.log('WebSocket disconnected');
            UI.announce('Disconnected from server');
        });

        this.wsManager.on('maxReconnectReached', () => {
            UI.showToast('Unable to connect to server. Please check your connection.', 'error', {
                duration: 0,
                actions: [
                    {
                        text: 'Retry',
                        handler: () => {
                            this.wsManager.reconnect();
                        }
                    },
                    {
                        text: 'Offline Mode',
                        handler: () => {
                            this.enableOfflineMode();
                        }
                    }
                ]
            });
        });

        console.log('WebSocket manager initialized:', this.config.wsUrl);
    }

    /**
     * Initialize core components
     */
    initializeComponents() {
        // Initialize main dashboard
        this.dashboard = new Dashboard(this.apiClient, this.wsManager);
        console.log('Dashboard component initialized');

        // Initialize workflow detail view
        this.workflowDetailView = new WorkflowDetailView(this.apiClient, this.wsManager);
        console.log('Workflow detail view initialized');

        // Initialize comparison view
        this.comparisonView = new WorkflowComparisonView(this.apiClient);
        console.log('Comparison view initialized');
    }

    /**
     * Setup global event handlers
     */
    setupGlobalEventHandlers() {
        // Handle window events
        window.addEventListener('beforeunload', () => {
            this.handleBeforeUnload();
        });

        window.addEventListener('online', () => {
            UI.showToast('Connection restored', 'success');
            if (this.wsManager && this.wsManager.getConnectionState() === 'disconnected') {
                this.wsManager.reconnect();
            }
        });

        window.addEventListener('offline', () => {
            UI.showToast('Connection lost', 'warning');
        });

        // Handle document visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.dashboard) {
                // Refresh data when tab becomes visible
                this.dashboard.refreshWorkflows();
            }
        });

        // Handle resize events
        window.addEventListener('resize', DataUtils.debounce(() => {
            this.handleResize();
        }, 250));

        // Handle keyboard shortcut events
        document.addEventListener('keyboard-shortcut', (e) => {
            this.handleKeyboardShortcut(e.detail.action);
        });

        // Handle global alert events
        document.addEventListener('alert', (e) => {
            const { level, message } = e.detail;
            UI.showToast(message, level);
        });
    }

    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        const shortcuts = [
            {
                key: 'F1',
                description: 'Show help',
                handler: () => this.showHelp()
            },
            {
                key: 'Ctrl+/',
                description: 'Show keyboard shortcuts',
                handler: () => this.showKeyboardShortcuts()
            },
            {
                key: 'Ctrl+Shift+D',
                description: 'Toggle dark mode',
                handler: () => this.themeManager.toggleTheme()
            },
            {
                key: 'Alt+N',
                description: 'Toggle notifications',
                handler: () => this.toggleNotifications()
            }
        ];

        // Store shortcuts for help display
        this.keyboardShortcuts = shortcuts;

        // Additional shortcuts handled in UI.js
        console.log('Keyboard shortcuts initialized');
    }

    /**
     * Setup error handling
     */
    setupErrorHandling() {
        // Global error handler
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);

            if (this.isInitialized) {
                UI.showToast('An unexpected error occurred', 'error');
            }
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);

            if (this.isInitialized) {
                UI.showToast('An error occurred while processing your request', 'error');
            }
        });
    }

    /**
     * Load user preferences
     */
    loadUserPreferences() {
        // Load saved preferences from localStorage
        const preferences = {
            theme: StorageUtils.get('dashboard.theme') || 'light',
            autoRefresh: StorageUtils.get('dashboard.autoRefresh') !== false,
            notifications: StorageUtils.get('dashboard.notifications') !== false,
            gridSize: StorageUtils.get('dashboard.gridSize') || 'normal',
            comparisonSaved: StorageUtils.get('dashboard.savedComparisons') || []
        };

        // Apply preferences
        if (preferences.theme) {
            this.themeManager.setTheme(preferences.theme);
        }

        this.config.features.autoRefresh = preferences.autoRefresh;
        this.config.features.notifications = preferences.notifications;

        console.log('User preferences loaded:', preferences);
    }

    /**
     * Save user preferences
     */
    saveUserPreferences() {
        const preferences = {
            theme: this.themeManager.getCurrentTheme(),
            autoRefresh: this.config.features.autoRefresh,
            notifications: this.config.features.notifications,
            gridSize: this.config.gridSize || 'normal'
        };

        Object.entries(preferences).forEach(([key, value]) => {
            StorageUtils.set(`dashboard.${key}`, value);
        });
    }

    /**
     * Get API base URL
     */
    getApiBaseUrl() {
        // Try to detect from current location
        const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
        const hostname = window.location.hostname;
        const port = '8888'; // Default API port

        return `${protocol}//${hostname}:${port}`;
    }

    /**
     * Get WebSocket URL
     */
    getWebSocketUrl() {
        // Try to detect from current location
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const hostname = window.location.hostname;
        const port = '8765'; // Default WebSocket port

        return `${protocol}//${hostname}:${port}`;
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcut(action) {
        switch (action) {
            case 'new-workflow':
                if (this.dashboard) {
                    this.dashboard.showNewWorkflowDialog();
                }
                break;
            case 'refresh':
                if (this.dashboard) {
                    this.dashboard.refreshWorkflows();
                }
                break;
        }
    }

    /**
     * Handle before unload
     */
    handleBeforeUnload() {
        // Save user preferences
        this.saveUserPreferences();

        // Close WebSocket connection
        if (this.wsManager) {
            this.wsManager.close();
        }
    }

    /**
     * Handle window resize
     */
    handleResize() {
        // Update any responsive components
        console.log('Window resized:', window.innerWidth, 'x', window.innerHeight);

        // Could trigger responsive chart updates, grid recalculations, etc.
    }

    /**
     * Show welcome message
     */
    showWelcomeMessage() {
        const isFirstVisit = !StorageUtils.get('dashboard.visited');

        if (isFirstVisit) {
            setTimeout(() => {
                UI.showToast('Welcome to Agent Orchestrator Dashboard!', 'info', {
                    duration: 7000,
                    actions: [
                        {
                            text: 'Take Tour',
                            handler: () => this.startTour()
                        }
                    ]
                });
            }, 1000);

            StorageUtils.set('dashboard.visited', true);
        }
    }

    /**
     * Show initialization error
     */
    showInitializationError(error) {
        const errorContainer = document.createElement('div');
        errorContainer.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: #f8f9fa;
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
            ">
                <div style="
                    background: white;
                    padding: 2rem;
                    border-radius: 0.5rem;
                    box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
                    max-width: 400px;
                    text-align: center;
                ">
                    <h2 style="color: #dc3545; margin-bottom: 1rem;">
                        ⚠️ Initialization Error
                    </h2>
                    <p style="color: #6c757d; margin-bottom: 1rem;">
                        ${error.message}
                    </p>
                    <button onclick="location.reload()" style="
                        background: #007bff;
                        color: white;
                        border: none;
                        padding: 0.5rem 1rem;
                        border-radius: 0.25rem;
                        cursor: pointer;
                    ">
                        Reload Page
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(errorContainer);
    }

    /**
     * Enable offline mode
     */
    enableOfflineMode() {
        console.log('Enabling offline mode');

        // Disable real-time features
        if (this.dashboard) {
            this.dashboard.autoRefreshEnabled = false;
        }

        // Show offline indicator
        UI.showToast('Running in offline mode', 'info', {
            duration: 0,
            actions: [
                {
                    text: 'Try Reconnect',
                    handler: () => {
                        this.wsManager.reconnect();
                    }
                }
            ]
        });
    }

    /**
     * Show help dialog
     */
    showHelp() {
        UI.showToast('Help system - Feature coming soon', 'info');
    }

    /**
     * Show keyboard shortcuts
     */
    showKeyboardShortcuts() {
        const shortcutsList = this.keyboardShortcuts.map(s =>
            `${s.key}: ${s.description}`
        ).join('\n');

        UI.showToast(`Keyboard Shortcuts:\n${shortcutsList}`, 'info', {
            duration: 10000
        });
    }

    /**
     * Toggle notifications
     */
    toggleNotifications() {
        this.config.features.notifications = !this.config.features.notifications;

        const status = this.config.features.notifications ? 'enabled' : 'disabled';
        UI.showToast(`Notifications ${status}`, 'info');

        StorageUtils.set('dashboard.notifications', this.config.features.notifications);
    }

    /**
     * Start application tour
     */
    startTour() {
        UI.showToast('Interactive tour - Feature coming soon', 'info');
    }

    /**
     * Get application statistics
     */
    getStats() {
        return {
            initialized: this.isInitialized,
            initializationError: this.initializationError?.message,
            config: this.config,
            wsStats: this.wsManager?.getStats(),
            components: {
                dashboard: !!this.dashboard,
                workflowDetailView: !!this.workflowDetailView,
                comparisonView: !!this.comparisonView
            }
        };
    }

    /**
     * Cleanup and destroy the application
     */
    destroy() {
        console.log('Destroying dashboard application');

        // Save preferences
        this.saveUserPreferences();

        // Close WebSocket connection
        if (this.wsManager) {
            this.wsManager.close();
        }

        // Clean up components
        if (this.dashboard?.autoRefreshInterval) {
            clearInterval(this.dashboard.autoRefreshInterval);
        }

        // Mark as not initialized
        this.isInitialized = false;
    }
}

// Initialize application when DOM is ready
let app;

function initializeApp() {
    app = new DashboardApp();
    app.init();

    // Make app available globally for debugging
    if (window.console && console.log) {
        window.dashboardApp = app;
        console.log('Dashboard app available as window.dashboardApp');
    }
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    // DOM is already ready
    initializeApp();
}

// Export for potential module use
if (typeof window !== 'undefined') {
    window.DashboardApp = DashboardApp;
}
