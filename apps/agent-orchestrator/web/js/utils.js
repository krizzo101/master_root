/**
 * Utility functions for Agent Orchestrator Dashboard
 */

/**
 * Time utilities
 */
class TimeUtils {
    static formatDuration(seconds) {
        if (!seconds || seconds < 0) return '0s';

        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);

        if (hours > 0) {
            return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
        } else if (minutes > 0) {
            return secs > 0 ? `${minutes}m ${secs}s` : `${minutes}m`;
        } else {
            return `${secs}s`;
        }
    }

    static formatTimeAgo(timestamp) {
        if (!timestamp) return 'Unknown';

        const now = new Date();
        const past = new Date(timestamp);
        const diffMs = now - past;
        const diffSecs = Math.floor(diffMs / 1000);
        const diffMins = Math.floor(diffSecs / 60);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffDays > 0) {
            return `${diffDays}d ago`;
        } else if (diffHours > 0) {
            return `${diffHours}h ago`;
        } else if (diffMins > 0) {
            return `${diffMins}m ago`;
        } else {
            return 'Just now';
        }
    }

    static formatDateTime(timestamp, options = {}) {
        if (!timestamp) return 'Unknown';

        const date = new Date(timestamp);
        const defaultOptions = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        };

        return date.toLocaleDateString('en-US', { ...defaultOptions, ...options });
    }

    static estimateCompletion(startTime, progress) {
        if (!startTime || !progress || progress === 0) return null;

        const now = new Date();
        const start = new Date(startTime);
        const elapsed = now - start;
        const estimated = elapsed / (progress / 100);
        const remaining = estimated - elapsed;

        if (remaining <= 0) return null;

        return new Date(now.getTime() + remaining);
    }

    static formatETA(etaTimestamp) {
        if (!etaTimestamp) return 'Unknown';

        const now = new Date();
        const eta = new Date(etaTimestamp);
        const diffMs = eta - now;

        if (diffMs <= 0) return 'Complete';

        return this.formatDuration(Math.floor(diffMs / 1000));
    }
}

/**
 * Data utilities
 */
class DataUtils {
    static formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    static formatPercentage(value, total, decimals = 0) {
        if (!total || total === 0) return '0%';

        const percentage = (value / total) * 100;
        return percentage.toFixed(decimals) + '%';
    }

    static clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    static deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj);
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (typeof obj === 'object') {
            const cloned = {};
            Object.keys(obj).forEach(key => {
                cloned[key] = this.deepClone(obj[key]);
            });
            return cloned;
        }
    }

    static debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    }

    static throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    static generateId(prefix = 'id') {
        return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    static sanitizeHtml(str) {
        const temp = document.createElement('div');
        temp.textContent = str;
        return temp.innerHTML;
    }
}

/**
 * DOM utilities
 */
class DomUtils {
    static createElement(tag, attributes = {}, children = []) {
        const element = document.createElement(tag);

        Object.keys(attributes).forEach(key => {
            if (key === 'className') {
                element.className = attributes[key];
            } else if (key === 'innerHTML') {
                element.innerHTML = attributes[key];
            } else if (key.startsWith('data-')) {
                element.setAttribute(key, attributes[key]);
            } else {
                element[key] = attributes[key];
            }
        });

        children.forEach(child => {
            if (typeof child === 'string') {
                element.appendChild(document.createTextNode(child));
            } else if (child instanceof Element) {
                element.appendChild(child);
            }
        });

        return element;
    }

    static addClass(element, className) {
        if (element && className) {
            element.classList.add(className);
        }
    }

    static removeClass(element, className) {
        if (element && className) {
            element.classList.remove(className);
        }
    }

    static toggleClass(element, className) {
        if (element && className) {
            element.classList.toggle(className);
        }
    }

    static hasClass(element, className) {
        return element && className && element.classList.contains(className);
    }

    static setAttributes(element, attributes) {
        Object.keys(attributes).forEach(key => {
            element.setAttribute(key, attributes[key]);
        });
    }

    static getScrollPosition(element = window) {
        if (element === window) {
            return {
                x: window.pageXOffset || document.documentElement.scrollLeft,
                y: window.pageYOffset || document.documentElement.scrollTop
            };
        } else {
            return {
                x: element.scrollLeft,
                y: element.scrollTop
            };
        }
    }

    static scrollToTop(element = window, smooth = true) {
        if (element === window) {
            window.scrollTo({
                top: 0,
                behavior: smooth ? 'smooth' : 'auto'
            });
        } else {
            element.scrollTo({
                top: 0,
                behavior: smooth ? 'smooth' : 'auto'
            });
        }
    }

    static isElementVisible(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }

    static getElementPosition(element) {
        const rect = element.getBoundingClientRect();
        return {
            top: rect.top + window.pageYOffset,
            left: rect.left + window.pageXOffset,
            width: rect.width,
            height: rect.height
        };
    }
}

/**
 * Status utilities
 */
class StatusUtils {
    static getStatusColor(status) {
        const colors = {
            running: '#28a745',
            pending: '#6c757d',
            queued: '#6c757d',
            paused: '#ffc107',
            completed: '#007bff',
            success: '#28a745',
            failed: '#dc3545',
            error: '#dc3545',
            cancelled: '#6c757d',
            timeout: '#dc3545'
        };

        return colors[status?.toLowerCase()] || colors.pending;
    }

    static getStatusIcon(status) {
        const icons = {
            running: '●',
            pending: '○',
            queued: '⏳',
            paused: '⏸',
            completed: '✓',
            success: '✓',
            failed: '⚠',
            error: '⚠',
            cancelled: '✗',
            timeout: '⏰'
        };

        return icons[status?.toLowerCase()] || icons.pending;
    }

    static getStatusText(status) {
        const texts = {
            running: 'Running',
            pending: 'Pending',
            queued: 'Queued',
            paused: 'Paused',
            completed: 'Completed',
            success: 'Success',
            failed: 'Failed',
            error: 'Error',
            cancelled: 'Cancelled',
            timeout: 'Timeout'
        };

        return texts[status?.toLowerCase()] || 'Unknown';
    }

    static isActiveStatus(status) {
        const activeStatuses = ['running', 'pending', 'queued'];
        return activeStatuses.includes(status?.toLowerCase());
    }

    static isCompletedStatus(status) {
        const completedStatuses = ['completed', 'success', 'failed', 'error', 'cancelled', 'timeout'];
        return completedStatuses.includes(status?.toLowerCase());
    }
}

/**
 * Progress utilities
 */
class ProgressUtils {
    static createProgressBar(progress, className = '') {
        const percentage = Math.max(0, Math.min(100, progress));

        const progressBar = DomUtils.createElement('div', {
            className: `progress-bar ${className}`
        });

        const progressFill = DomUtils.createElement('div', {
            className: 'progress-fill',
            style: `width: ${percentage}%`
        });

        progressBar.appendChild(progressFill);

        return progressBar;
    }

    static generateProgressVisual(progress, width = 11) {
        const percentage = Math.max(0, Math.min(100, progress));
        const filledChars = Math.round((percentage / 100) * width);
        const emptyChars = width - filledChars;

        return '█'.repeat(filledChars) + '░'.repeat(emptyChars);
    }

    static calculateETA(startTime, progress) {
        if (!startTime || progress <= 0) return null;

        const now = new Date();
        const elapsed = now - new Date(startTime);
        const rate = progress / elapsed; // progress per millisecond
        const remaining = (100 - progress) / rate;

        return new Date(now.getTime() + remaining);
    }
}

/**
 * Local storage utilities
 */
class StorageUtils {
    static set(key, value, expiration = null) {
        const data = {
            value: value,
            timestamp: Date.now(),
            expiration: expiration
        };

        try {
            localStorage.setItem(key, JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Failed to save to localStorage:', error);
            return false;
        }
    }

    static get(key) {
        try {
            const data = JSON.parse(localStorage.getItem(key));
            if (!data) return null;

            // Check expiration
            if (data.expiration && Date.now() > data.expiration) {
                this.remove(key);
                return null;
            }

            return data.value;
        } catch (error) {
            console.error('Failed to read from localStorage:', error);
            return null;
        }
    }

    static remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Failed to remove from localStorage:', error);
            return false;
        }
    }

    static clear() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('Failed to clear localStorage:', error);
            return false;
        }
    }

    static getKeys() {
        return Object.keys(localStorage);
    }
}

/**
 * Event utilities
 */
class EventUtils {
    static on(element, event, handler, options = {}) {
        element.addEventListener(event, handler, options);
    }

    static off(element, event, handler, options = {}) {
        element.removeEventListener(event, handler, options);
    }

    static once(element, event, handler, options = {}) {
        const wrappedHandler = (e) => {
            handler(e);
            element.removeEventListener(event, wrappedHandler, options);
        };
        element.addEventListener(event, wrappedHandler, options);
    }

    static emit(element, event, data = null) {
        const customEvent = new CustomEvent(event, {
            detail: data,
            bubbles: true,
            cancelable: true
        });
        element.dispatchEvent(customEvent);
    }

    static delegate(container, selector, event, handler) {
        container.addEventListener(event, (e) => {
            if (e.target.matches(selector)) {
                handler(e);
            }
        });
    }

    static preventDefault(e) {
        e.preventDefault();
    }

    static stopPropagation(e) {
        e.stopPropagation();
    }
}

/**
 * Validation utilities
 */
class ValidationUtils {
    static isEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    static isUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }

    static isRequired(value) {
        return value !== null && value !== undefined && value.toString().trim() !== '';
    }

    static minLength(value, min) {
        return value && value.toString().length >= min;
    }

    static maxLength(value, max) {
        return !value || value.toString().length <= max;
    }

    static isNumber(value) {
        return !isNaN(value) && !isNaN(parseFloat(value));
    }

    static isInteger(value) {
        return Number.isInteger(Number(value));
    }

    static inRange(value, min, max) {
        const num = Number(value);
        return num >= min && num <= max;
    }
}

/**
 * Export utilities to global scope
 */
if (typeof window !== 'undefined') {
    window.TimeUtils = TimeUtils;
    window.DataUtils = DataUtils;
    window.DomUtils = DomUtils;
    window.StatusUtils = StatusUtils;
    window.ProgressUtils = ProgressUtils;
    window.StorageUtils = StorageUtils;
    window.EventUtils = EventUtils;
    window.ValidationUtils = ValidationUtils;
}
