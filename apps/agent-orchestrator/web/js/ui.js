/**
 * UI Utilities and Components
 * Provides common UI functionality across the dashboard
 */

class UI {
    static toastContainer = null;
    static modalStack = [];
    static dropdownManager = new DropdownManager();

    /**
     * Initialize UI components
     */
    static init() {
        this.createToastContainer();
        this.setupGlobalEventHandlers();
        this.setupKeyboardShortcuts();
        this.setupAccessibility();
    }

    /**
     * Create toast notification container
     */
    static createToastContainer() {
        if (!this.toastContainer) {
            this.toastContainer = document.getElementById('toast-container');
            if (!this.toastContainer) {
                this.toastContainer = DomUtils.createElement('div', {
                    id: 'toast-container',
                    className: 'toast-container'
                });
                document.body.appendChild(this.toastContainer);
            }
        }
    }

    /**
     * Show toast notification
     */
    static showToast(message, type = 'info', options = {}) {
        const {
            duration = 5000,
            closeable = true,
            actions = []
        } = options;

        const toastId = DataUtils.generateId('toast');

        const toast = DomUtils.createElement('div', {
            className: `toast ${type}`,
            id: toastId,
            role: 'alert',
            'aria-live': 'polite'
        });

        const header = DomUtils.createElement('div', {
            className: 'toast-header'
        });

        const title = DomUtils.createElement('div', {
            className: 'toast-title'
        }, [this.getToastTitle(type)]);

        header.appendChild(title);

        if (closeable) {
            const closeBtn = DomUtils.createElement('button', {
                className: 'toast-close',
                'aria-label': 'Close notification'
            }, ['×']);

            closeBtn.addEventListener('click', () => {
                this.hideToast(toastId);
            });

            header.appendChild(closeBtn);
        }

        const body = DomUtils.createElement('div', {
            className: 'toast-body'
        }, [message]);

        toast.appendChild(header);
        toast.appendChild(body);

        // Add actions if provided
        if (actions.length > 0) {
            const actionsContainer = DomUtils.createElement('div', {
                className: 'toast-actions'
            });

            actions.forEach(action => {
                const actionBtn = DomUtils.createElement('button', {
                    className: `small-btn ${action.className || ''}`
                }, [action.text]);

                actionBtn.addEventListener('click', () => {
                    action.handler();
                    if (action.closeOnClick !== false) {
                        this.hideToast(toastId);
                    }
                });

                actionsContainer.appendChild(actionBtn);
            });

            toast.appendChild(actionsContainer);
        }

        this.toastContainer.appendChild(toast);

        // Trigger animation
        setTimeout(() => {
            DomUtils.addClass(toast, 'show');
        }, 10);

        // Auto-hide
        if (duration > 0) {
            setTimeout(() => {
                this.hideToast(toastId);
            }, duration);
        }

        return toastId;
    }

    /**
     * Hide toast notification
     */
    static hideToast(toastId) {
        const toast = document.getElementById(toastId);
        if (toast) {
            DomUtils.removeClass(toast, 'show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }
    }

    /**
     * Get toast title by type
     */
    static getToastTitle(type) {
        const titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Information'
        };
        return titles[type] || 'Notification';
    }

    /**
     * Show modal
     */
    static showModal(modalId, options = {}) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`Modal not found: ${modalId}`);
            return null;
        }

        const {
            backdrop = true,
            keyboard = true,
            focus = true
        } = options;

        // Add to modal stack
        this.modalStack.push(modalId);

        // Show modal
        modal.style.display = 'flex';
        DomUtils.addClass(modal, 'show');

        // Focus management
        if (focus) {
            const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (firstFocusable) {
                firstFocusable.focus();
            }
        }

        // Backdrop click handler
        if (backdrop) {
            const backdropEl = modal.querySelector('.modal-backdrop');
            if (backdropEl) {
                const clickHandler = (e) => {
                    if (e.target === backdropEl) {
                        this.hideModal(modalId);
                    }
                };
                backdropEl.addEventListener('click', clickHandler);
                modal.dataset.backdropHandler = 'true';
            }
        }

        // Keyboard handler
        if (keyboard) {
            const keyHandler = (e) => {
                if (e.key === 'Escape') {
                    this.hideModal(modalId);
                }
            };
            document.addEventListener('keydown', keyHandler);
            modal.dataset.keyHandler = 'true';
        }

        // Prevent body scroll
        DomUtils.addClass(document.body, 'modal-open');

        // Emit event
        EventUtils.emit(modal, 'modal-shown');

        return modal;
    }

    /**
     * Hide modal
     */
    static hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        // Remove from modal stack
        const index = this.modalStack.indexOf(modalId);
        if (index > -1) {
            this.modalStack.splice(index, 1);
        }

        // Hide modal
        DomUtils.removeClass(modal, 'show');

        setTimeout(() => {
            modal.style.display = 'none';

            // Clean up event handlers
            if (modal.dataset.backdropHandler) {
                delete modal.dataset.backdropHandler;
            }
            if (modal.dataset.keyHandler) {
                delete modal.dataset.keyHandler;
            }

            // Restore body scroll if no modals are open
            if (this.modalStack.length === 0) {
                DomUtils.removeClass(document.body, 'modal-open');
            }

            // Emit event
            EventUtils.emit(modal, 'modal-hidden');
        }, 300);
    }

    /**
     * Toggle dropdown
     */
    static toggleDropdown(dropdownId) {
        this.dropdownManager.toggle(dropdownId);
    }

    /**
     * Show loading overlay
     */
    static showLoading(message = 'Loading...') {
        let overlay = document.getElementById('loading-overlay');

        if (!overlay) {
            overlay = DomUtils.createElement('div', {
                id: 'loading-overlay',
                className: 'loading-overlay',
                style: `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 9999;
                    backdrop-filter: blur(4px);
                `
            });

            const content = DomUtils.createElement('div', {
                className: 'loading-content',
                style: `
                    background: white;
                    padding: 2rem;
                    border-radius: 0.5rem;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 1rem;
                    box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
                `
            });

            const spinner = DomUtils.createElement('div', {
                className: 'spinner'
            });

            const text = DomUtils.createElement('div', {
                className: 'loading-text',
                style: 'color: #6c757d;'
            }, [message]);

            content.appendChild(spinner);
            content.appendChild(text);
            overlay.appendChild(content);
            document.body.appendChild(overlay);
        }

        overlay.style.display = 'flex';
    }

    /**
     * Hide loading overlay
     */
    static hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    /**
     * Show confirmation dialog
     */
    static showConfirm(message, options = {}) {
        return new Promise((resolve) => {
            const {
                title = 'Confirm',
                confirmText = 'Confirm',
                cancelText = 'Cancel',
                type = 'warning'
            } = options;

            const dialogId = DataUtils.generateId('confirm-dialog');

            const dialog = DomUtils.createElement('div', {
                id: dialogId,
                className: 'modal',
                style: 'display: flex;'
            });

            const backdrop = DomUtils.createElement('div', {
                className: 'modal-backdrop'
            });

            const content = DomUtils.createElement('div', {
                className: 'modal-content',
                style: 'max-width: 400px;'
            });

            const header = DomUtils.createElement('div', {
                className: 'modal-header'
            });

            const titleEl = DomUtils.createElement('h3', {}, [title]);
            header.appendChild(titleEl);

            const body = DomUtils.createElement('div', {
                className: 'modal-body',
                style: 'padding: 1rem;'
            }, [message]);

            const footer = DomUtils.createElement('div', {
                className: 'modal-footer',
                style: 'padding: 1rem; display: flex; gap: 0.5rem; justify-content: flex-end;'
            });

            const cancelBtn = DomUtils.createElement('button', {
                className: 'btn secondary-btn'
            }, [cancelText]);

            const confirmBtn = DomUtils.createElement('button', {
                className: `btn ${type === 'danger' ? 'danger-btn' : 'primary-btn'}`
            }, [confirmText]);

            cancelBtn.addEventListener('click', () => {
                document.body.removeChild(dialog);
                resolve(false);
            });

            confirmBtn.addEventListener('click', () => {
                document.body.removeChild(dialog);
                resolve(true);
            });

            backdrop.addEventListener('click', (e) => {
                if (e.target === backdrop) {
                    document.body.removeChild(dialog);
                    resolve(false);
                }
            });

            footer.appendChild(cancelBtn);
            footer.appendChild(confirmBtn);

            content.appendChild(header);
            content.appendChild(body);
            content.appendChild(footer);

            dialog.appendChild(backdrop);
            dialog.appendChild(content);

            document.body.appendChild(dialog);

            // Focus confirm button
            confirmBtn.focus();
        });
    }

    /**
     * Setup global event handlers
     */
    static setupGlobalEventHandlers() {
        // Close dropdowns on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.dropdown')) {
                this.dropdownManager.closeAll();
            }
        });

        // Handle dropdown toggles
        EventUtils.delegate(document, '.dropdown-toggle', 'click', (e) => {
            e.stopPropagation();
            const dropdown = e.target.closest('.dropdown');
            if (dropdown) {
                this.dropdownManager.toggle(dropdown.id || DataUtils.generateId('dropdown'));
            }
        });

        // Handle modal close buttons
        EventUtils.delegate(document, '.modal .back-btn, .modal .close-btn', 'click', (e) => {
            const modal = e.target.closest('.modal');
            if (modal) {
                this.hideModal(modal.id);
            }
        });
    }

    /**
     * Setup keyboard shortcuts
     */
    static setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+N: New workflow
            if (e.ctrlKey && e.key === 'n') {
                e.preventDefault();
                EventUtils.emit(document, 'keyboard-shortcut', { action: 'new-workflow' });
            }

            // Ctrl+R: Refresh
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                EventUtils.emit(document, 'keyboard-shortcut', { action: 'refresh' });
            }

            // Escape: Close modals/dropdowns
            if (e.key === 'Escape') {
                if (this.modalStack.length > 0) {
                    const lastModal = this.modalStack[this.modalStack.length - 1];
                    this.hideModal(lastModal);
                } else {
                    this.dropdownManager.closeAll();
                }
            }
        });
    }

    /**
     * Setup accessibility features
     */
    static setupAccessibility() {
        // Announce dynamic content changes
        const announcer = DomUtils.createElement('div', {
            id: 'aria-announcer',
            'aria-live': 'polite',
            'aria-atomic': 'true',
            style: `
                position: absolute;
                left: -10000px;
                width: 1px;
                height: 1px;
                overflow: hidden;
            `
        });
        document.body.appendChild(announcer);

        // Focus management for dynamic content
        this.setupFocusManagement();
    }

    /**
     * Setup focus management
     */
    static setupFocusManagement() {
        // Track last focused element before modal
        let lastFocusedElement = null;

        document.addEventListener('modal-shown', (e) => {
            lastFocusedElement = document.activeElement;
        });

        document.addEventListener('modal-hidden', (e) => {
            if (lastFocusedElement && this.modalStack.length === 0) {
                lastFocusedElement.focus();
                lastFocusedElement = null;
            }
        });

        // Tab trapping in modals
        EventUtils.delegate(document, '.modal', 'keydown', (e) => {
            if (e.key === 'Tab') {
                this.trapFocus(e, e.currentTarget);
            }
        });
    }

    /**
     * Trap focus within element
     */
    static trapFocus(e, container) {
        const focusableElements = container.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
            if (document.activeElement === firstElement) {
                e.preventDefault();
                lastElement.focus();
            }
        } else {
            if (document.activeElement === lastElement) {
                e.preventDefault();
                firstElement.focus();
            }
        }
    }

    /**
     * Announce to screen readers
     */
    static announce(message) {
        const announcer = document.getElementById('aria-announcer');
        if (announcer) {
            announcer.textContent = message;
        }
    }

    /**
     * Format file size for display
     */
    static formatFileSize(bytes) {
        return DataUtils.formatBytes(bytes);
    }

    /**
     * Format date for display
     */
    static formatDate(date, options = {}) {
        return TimeUtils.formatDateTime(date, options);
    }

    /**
     * Create progress indicator
     */
    static createProgressIndicator(progress, options = {}) {
        const {
            showText = true,
            showBar = true,
            animated = false,
            size = 'normal'
        } = options;

        const container = DomUtils.createElement('div', {
            className: `progress-indicator ${size} ${animated ? 'animated' : ''}`
        });

        if (showText) {
            const text = DomUtils.createElement('div', {
                className: 'progress-text'
            }, [`${Math.round(progress)}%`]);
            container.appendChild(text);
        }

        if (showBar) {
            const bar = ProgressUtils.createProgressBar(progress);
            container.appendChild(bar);
        }

        return container;
    }

    /**
     * Create status badge
     */
    static createStatusBadge(status, options = {}) {
        const {
            showIcon = true,
            size = 'normal'
        } = options;

        const badge = DomUtils.createElement('span', {
            className: `status-badge ${status} ${size}`
        });

        if (showIcon) {
            const icon = DomUtils.createElement('span', {
                className: 'status-icon'
            }, [StatusUtils.getStatusIcon(status)]);
            badge.appendChild(icon);
        }

        const text = DomUtils.createElement('span', {
            className: 'status-text'
        }, [StatusUtils.getStatusText(status)]);
        badge.appendChild(text);

        return badge;
    }
}

/**
 * Dropdown Manager
 */
class DropdownManager {
    constructor() {
        this.openDropdowns = new Set();
    }

    toggle(dropdownId) {
        const dropdown = document.getElementById(dropdownId) ||
                        document.querySelector(`[data-dropdown-id="${dropdownId}"]`);

        if (!dropdown) return;

        const isOpen = DomUtils.hasClass(dropdown, 'open');

        if (isOpen) {
            this.close(dropdownId);
        } else {
            this.closeAll();
            this.open(dropdownId);
        }
    }

    open(dropdownId) {
        const dropdown = document.getElementById(dropdownId) ||
                        document.querySelector(`[data-dropdown-id="${dropdownId}"]`);

        if (dropdown) {
            DomUtils.addClass(dropdown, 'open');
            this.openDropdowns.add(dropdownId);

            // Focus first menu item
            const firstItem = dropdown.querySelector('.dropdown-item');
            if (firstItem) {
                firstItem.focus();
            }
        }
    }

    close(dropdownId) {
        const dropdown = document.getElementById(dropdownId) ||
                        document.querySelector(`[data-dropdown-id="${dropdownId}"]`);

        if (dropdown) {
            DomUtils.removeClass(dropdown, 'open');
            this.openDropdowns.delete(dropdownId);
        }
    }

    closeAll() {
        this.openDropdowns.forEach(id => this.close(id));
        this.openDropdowns.clear();
    }
}

/**
 * Theme Manager
 */
class ThemeManager {
    constructor() {
        this.currentTheme = StorageUtils.get('dashboard.theme') || 'light';
        this.applyTheme(this.currentTheme);
    }

    setTheme(theme) {
        this.currentTheme = theme;
        this.applyTheme(theme);
        StorageUtils.set('dashboard.theme', theme);
        EventUtils.emit(document, 'theme-changed', { theme });
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
    }

    getCurrentTheme() {
        return this.currentTheme;
    }
}

// Export for global use
if (typeof window !== 'undefined') {
    window.UI = UI;
    window.DropdownManager = DropdownManager;
    window.ThemeManager = ThemeManager;
}
