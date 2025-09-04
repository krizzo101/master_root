/**
 * Advanced Notification System
 * Handles browser notifications, toast messages, and alert management
 */
class NotificationSystem {
    constructor() {
        this.notifications = new Map();
        this.notificationCount = 0;
        this.maxNotifications = 5;
        this.defaultDuration = 5000;
        this.browserNotificationsEnabled = false;

        // Sound effects (optional)
        this.sounds = {
            success: null,
            warning: null,
            danger: null,
            info: null
        };

        this.init();
    }

    async init() {
        // Request browser notification permission
        await this.requestBrowserPermission();

        // Create notification container
        this.createNotificationContainer();

        // Set up keyboard shortcuts
        this.setupKeyboardShortcuts();

        console.log('Notification system initialized');
    }

    async requestBrowserPermission() {
        if ('Notification' in window) {
            if (Notification.permission === 'default') {
                try {
                    const permission = await Notification.requestPermission();
                    this.browserNotificationsEnabled = permission === 'granted';
                } catch (error) {
                    console.warn('Failed to request notification permission:', error);
                }
            } else {
                this.browserNotificationsEnabled = Notification.permission === 'granted';
            }
        }

        console.log('Browser notifications enabled:', this.browserNotificationsEnabled);
    }

    createNotificationContainer() {
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'notification-container';
            container.setAttribute('role', 'region');
            container.setAttribute('aria-label', 'Notifications');
            document.body.appendChild(container);
        }
        this.container = container;
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Shift + N to clear all notifications
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'N') {
                e.preventDefault();
                this.clearAll();
            }

            // Escape to dismiss latest notification
            if (e.key === 'Escape') {
                this.dismissLatest();
            }
        });
    }

    /**
     * Create and show a toast notification
     */
    show(message, type = 'info', options = {}) {
        const id = this.generateId();
        const notification = this.createToastNotification(id, message, type, options);

        // Add to container
        this.container.appendChild(notification);
        this.notifications.set(id, notification);

        // Limit number of notifications
        this.enforceLimit();

        // Auto-dismiss
        if (options.duration !== 0) {
            const duration = options.duration || this.defaultDuration;
            setTimeout(() => this.dismiss(id), duration);
        }

        // Animate in
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });

        // Show browser notification if enabled and important
        if (options.browser || type === 'danger') {
            this.showBrowserNotification(message, type);
        }

        // Play sound if configured
        this.playSound(type);

        return id;
    }

    createToastNotification(id, message, type, options) {
        const notification = document.createElement('div');
        notification.className = `notification toast ${type}`;
        notification.id = `notification-${id}`;
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', type === 'danger' ? 'assertive' : 'polite');

        // Icon based on type
        const icon = this.getTypeIcon(type);

        // Build notification content
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">${icon}</div>
                <div class="notification-body">
                    <div class="notification-message">${this.escapeHTML(message)}</div>
                    ${options.subtitle ? `<div class="notification-subtitle">${this.escapeHTML(options.subtitle)}</div>` : ''}
                </div>
                <div class="notification-actions">
                    ${options.actions ? this.renderActions(id, options.actions) : ''}
                    <button class="notification-close" aria-label="Close notification" data-id="${id}">×</button>
                </div>
            </div>
            ${options.progress ? '<div class="notification-progress"><div class="progress-bar"></div></div>' : ''}
        `;

        // Add event listeners
        this.addNotificationListeners(notification, id);

        return notification;
    }

    renderActions(id, actions) {
        return actions.map(action =>
            `<button class="notification-action" data-id="${id}" data-action="${action.id}">
                ${this.escapeHTML(action.label)}
            </button>`
        ).join('');
    }

    addNotificationListeners(notification, id) {
        // Close button
        const closeBtn = notification.querySelector('.notification-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.dismiss(id));
        }

        // Action buttons
        const actionBtns = notification.querySelectorAll('.notification-action');
        actionBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const actionId = e.target.dataset.action;
                this.handleAction(id, actionId);
            });
        });

        // Click to dismiss (optional)
        notification.addEventListener('click', (e) => {
            if (e.target === notification) {
                this.dismiss(id);
            }
        });
    }

    /**
     * Show success notification
     */
    success(message, options = {}) {
        return this.show(message, 'success', { ...options, duration: options.duration || 3000 });
    }

    /**
     * Show warning notification
     */
    warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }

    /**
     * Show error notification
     */
    error(message, options = {}) {
        return this.show(message, 'danger', { ...options, duration: options.duration || 10000, browser: true });
    }

    /**
     * Show info notification
     */
    info(message, options = {}) {
        return this.show(message, 'info', options);
    }

    /**
     * Show progress notification
     */
    progress(message, options = {}) {
        const id = this.show(message, 'info', {
            ...options,
            duration: 0,
            progress: true
        });
        return {
            id,
            update: (progress, newMessage) => this.updateProgress(id, progress, newMessage),
            complete: (message) => this.completeProgress(id, message),
            error: (message) => this.errorProgress(id, message)
        };
    }

    updateProgress(id, progress, message) {
        const notification = this.notifications.get(id);
        if (!notification) return;

        const progressBar = notification.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${Math.max(0, Math.min(100, progress))}%`;
        }

        if (message) {
            const messageEl = notification.querySelector('.notification-message');
            if (messageEl) {
                messageEl.textContent = message;
            }
        }
    }

    completeProgress(id, message) {
        const notification = this.notifications.get(id);
        if (!notification) return;

        // Update to success state
        notification.className = notification.className.replace(/\binfo\b/, 'success');

        // Update message
        if (message) {
            const messageEl = notification.querySelector('.notification-message');
            if (messageEl) {
                messageEl.textContent = message;
            }
        }

        // Update icon
        const iconEl = notification.querySelector('.notification-icon');
        if (iconEl) {
            iconEl.innerHTML = this.getTypeIcon('success');
        }

        // Remove progress bar
        const progressContainer = notification.querySelector('.notification-progress');
        if (progressContainer) {
            progressContainer.remove();
        }

        // Auto-dismiss after delay
        setTimeout(() => this.dismiss(id), 3000);
    }

    errorProgress(id, message) {
        const notification = this.notifications.get(id);
        if (!notification) return;

        // Update to error state
        notification.className = notification.className.replace(/\binfo\b/, 'danger');

        // Update message
        if (message) {
            const messageEl = notification.querySelector('.notification-message');
            if (messageEl) {
                messageEl.textContent = message;
            }
        }

        // Update icon
        const iconEl = notification.querySelector('.notification-icon');
        if (iconEl) {
            iconEl.innerHTML = this.getTypeIcon('danger');
        }

        // Remove progress bar
        const progressContainer = notification.querySelector('.notification-progress');
        if (progressContainer) {
            progressContainer.remove();
        }

        // Auto-dismiss after longer delay
        setTimeout(() => this.dismiss(id), 8000);
    }

    /**
     * Dismiss a specific notification
     */
    dismiss(id) {
        const notification = this.notifications.get(id);
        if (!notification) return;

        notification.classList.add('hide');

        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            this.notifications.delete(id);
        }, 300);
    }

    /**
     * Dismiss the latest notification
     */
    dismissLatest() {
        const notifications = Array.from(this.notifications.keys());
        if (notifications.length > 0) {
            this.dismiss(notifications[notifications.length - 1]);
        }
    }

    /**
     * Clear all notifications
     */
    clearAll() {
        const ids = Array.from(this.notifications.keys());
        ids.forEach(id => this.dismiss(id));
    }

    /**
     * Show browser notification
     */
    showBrowserNotification(message, type) {
        if (!this.browserNotificationsEnabled || !('Notification' in window)) return;

        const options = {
            body: message,
            icon: this.getNotificationIcon(type),
            badge: '/favicon.ico',
            tag: 'dashboard-notification',
            requireInteraction: type === 'danger'
        };

        try {
            const notification = new Notification('Orchestrator Dashboard', options);

            notification.onclick = () => {
                window.focus();
                notification.close();
            };

            // Auto-close after 5 seconds for non-critical notifications
            if (type !== 'danger') {
                setTimeout(() => notification.close(), 5000);
            }

        } catch (error) {
            console.warn('Failed to show browser notification:', error);
        }
    }

    /**
     * Handle notification actions
     */
    handleAction(notificationId, actionId) {
        const notification = this.notifications.get(notificationId);
        if (!notification) return;

        // Emit custom event for action handling
        const event = new CustomEvent('notificationAction', {
            detail: { notificationId, actionId }
        });
        document.dispatchEvent(event);

        // Dismiss the notification after action
        this.dismiss(notificationId);
    }

    /**
     * Show alert notification for critical issues
     */
    alert(message, options = {}) {
        const alertOptions = {
            ...options,
            duration: 0, // Don't auto-dismiss alerts
            browser: true,
            actions: [
                { id: 'acknowledge', label: 'Acknowledge' }
            ]
        };

        return this.show(message, 'danger', alertOptions);
    }

    /**
     * Show connection status notifications
     */
    connectionStatus(status, message) {
        const statusMessages = {
            connected: 'Connection restored',
            disconnected: 'Connection lost',
            error: 'Connection error occurred',
            failed: 'Connection failed'
        };

        const finalMessage = message || statusMessages[status] || 'Connection status changed';

        const types = {
            connected: 'success',
            disconnected: 'warning',
            error: 'danger',
            failed: 'danger'
        };

        return this.show(finalMessage, types[status] || 'info', {
            browser: status !== 'connected'
        });
    }

    // Utility methods
    generateId() {
        return ++this.notificationCount;
    }

    enforceLimit() {
        const current = Array.from(this.notifications.keys());
        if (current.length > this.maxNotifications) {
            const toRemove = current.slice(0, current.length - this.maxNotifications);
            toRemove.forEach(id => this.dismiss(id));
        }
    }

    getTypeIcon(type) {
        const icons = {
            success: '✅',
            warning: '⚠️',
            danger: '❌',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }

    getNotificationIcon(type) {
        // Could return different icon URLs based on type
        return '/favicon.ico';
    }

    escapeHTML(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    playSound(type) {
        const sound = this.sounds[type];
        if (sound && sound.play) {
            sound.play().catch(() => {
                // Ignore audio play errors
            });
        }
    }

    // Configuration methods
    setMaxNotifications(max) {
        this.maxNotifications = max;
    }

    setDefaultDuration(duration) {
        this.defaultDuration = duration;
    }

    setBrowserNotifications(enabled) {
        this.browserNotificationsEnabled = enabled;
    }

    // Get notification status
    getStats() {
        return {
            active: this.notifications.size,
            total: this.notificationCount,
            browserEnabled: this.browserNotificationsEnabled
        };
    }
}

// Create CSS for notifications if not exists
const notificationCSS = `
.notification-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 10000;
    pointer-events: none;
}

.notification {
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    margin-bottom: 10px;
    max-width: 400px;
    opacity: 0;
    transform: translateX(100%);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    pointer-events: auto;
    border-left: 4px solid;
}

.notification.show {
    opacity: 1;
    transform: translateX(0);
}

.notification.hide {
    opacity: 0;
    transform: translateX(100%);
}

.notification.success { border-left-color: #10b981; }
.notification.warning { border-left-color: #f59e0b; }
.notification.danger { border-left-color: #ef4444; }
.notification.info { border-left-color: #3b82f6; }

.notification-content {
    display: flex;
    align-items: flex-start;
    padding: 16px;
    gap: 12px;
}

.notification-icon {
    font-size: 18px;
    flex-shrink: 0;
}

.notification-body {
    flex: 1;
    min-width: 0;
}

.notification-message {
    font-weight: 500;
    color: #374151;
    margin-bottom: 4px;
    word-break: break-word;
}

.notification-subtitle {
    font-size: 14px;
    color: #6b7280;
    word-break: break-word;
}

.notification-actions {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    flex-shrink: 0;
}

.notification-action {
    background: none;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
    cursor: pointer;
    color: #374151;
    transition: all 0.2s;
}

.notification-action:hover {
    background: #f3f4f6;
    border-color: #9ca3af;
}

.notification-close {
    background: none;
    border: none;
    font-size: 20px;
    cursor: pointer;
    color: #9ca3af;
    padding: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    transition: all 0.2s;
}

.notification-close:hover {
    background: #f3f4f6;
    color: #374151;
}

.notification-progress {
    height: 3px;
    background: #f3f4f6;
    overflow: hidden;
}

.notification-progress .progress-bar {
    height: 100%;
    background: #3b82f6;
    width: 0%;
    transition: width 0.3s ease;
}

@keyframes slideIn {
    from { opacity: 0; transform: translateX(100%); }
    to { opacity: 1; transform: translateX(0); }
}

@keyframes slideOut {
    from { opacity: 1; transform: translateX(0); }
    to { opacity: 0; transform: translateX(100%); }
}

[data-theme="dark"] .notification {
    background: #1f2937;
    color: #f9fafb;
}

[data-theme="dark"] .notification-message {
    color: #f9fafb;
}

[data-theme="dark"] .notification-subtitle {
    color: #9ca3af;
}
`;

// Inject CSS if it doesn't exist
if (!document.querySelector('#notification-styles')) {
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = notificationCSS;
    document.head.appendChild(style);
}

// Export singleton instance
window.notifications = new NotificationSystem();
window.NotificationSystem = NotificationSystem;
