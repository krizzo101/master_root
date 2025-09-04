/**
 * DOM Manipulation Utilities
 * Helper functions for efficient DOM updates and interactions
 */
class DOMUtils {
    constructor() {
        this.animationQueue = [];
        this.isAnimating = false;
    }

    // Element selection utilities
    $(selector) {
        return document.querySelector(selector);
    }

    $$(selector) {
        return document.querySelectorAll(selector);
    }

    byId(id) {
        return document.getElementById(id);
    }

    // Element creation
    createElement(tag, attributes = {}, children = []) {
        const element = document.createElement(tag);

        // Set attributes
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'innerHTML') {
                element.innerHTML = value;
            } else if (key === 'textContent') {
                element.textContent = value;
            } else if (key.startsWith('data-')) {
                element.setAttribute(key, value);
            } else {
                element[key] = value;
            }
        });

        // Add children
        children.forEach(child => {
            if (typeof child === 'string') {
                element.appendChild(document.createTextNode(child));
            } else if (child instanceof HTMLElement) {
                element.appendChild(child);
            }
        });

        return element;
    }

    // Safe text updates (prevents XSS)
    updateText(element, text) {
        if (element) {
            element.textContent = text;
        }
    }

    updateHTML(element, html) {
        if (element) {
            // Basic XSS protection - remove script tags
            const cleanHTML = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
            element.innerHTML = cleanHTML;
        }
    }

    // Class manipulation
    addClass(element, className) {
        if (element && className) {
            element.classList.add(className);
        }
    }

    removeClass(element, className) {
        if (element && className) {
            element.classList.remove(className);
        }
    }

    toggleClass(element, className) {
        if (element && className) {
            element.classList.toggle(className);
        }
    }

    hasClass(element, className) {
        return element ? element.classList.contains(className) : false;
    }

    // Attribute manipulation
    setAttribute(element, name, value) {
        if (element) {
            element.setAttribute(name, value);
        }
    }

    getAttribute(element, name) {
        return element ? element.getAttribute(name) : null;
    }

    removeAttribute(element, name) {
        if (element) {
            element.removeAttribute(name);
        }
    }

    // Event handling
    on(element, event, handler, options = {}) {
        if (element) {
            element.addEventListener(event, handler, options);
        }
    }

    off(element, event, handler) {
        if (element) {
            element.removeEventListener(event, handler);
        }
    }

    // Efficient table updates
    updateTable(tableElement, data, columns) {
        if (!tableElement || !data || !Array.isArray(data)) return;

        const tbody = tableElement.querySelector('tbody') || tableElement;

        // Clear existing rows efficiently
        while (tbody.firstChild) {
            tbody.removeChild(tbody.firstChild);
        }

        // Create document fragment for batch DOM insertion
        const fragment = document.createDocumentFragment();

        data.forEach(row => {
            const tr = this.createElement('tr');

            columns.forEach(column => {
                const td = this.createElement('td');
                const value = this.getNestedValue(row, column.key);

                if (column.render) {
                    const rendered = column.render(value, row);
                    if (typeof rendered === 'string') {
                        td.innerHTML = rendered;
                    } else {
                        td.appendChild(rendered);
                    }
                } else {
                    td.textContent = value || '';
                }

                if (column.className) {
                    td.className = column.className;
                }

                tr.appendChild(td);
            });

            fragment.appendChild(tr);
        });

        tbody.appendChild(fragment);
    }

    // Get nested object values safely
    getNestedValue(obj, path) {
        return path.split('.').reduce((current, key) =>
            current && current[key] !== undefined ? current[key] : '', obj);
    }

    // Efficient list updates
    updateList(listElement, items, renderItem) {
        if (!listElement || !Array.isArray(items)) return;

        // Clear existing items
        while (listElement.firstChild) {
            listElement.removeChild(listElement.firstChild);
        }

        const fragment = document.createDocumentFragment();

        items.forEach(item => {
            const listItem = renderItem(item);
            if (listItem) {
                fragment.appendChild(listItem);
            }
        });

        listElement.appendChild(fragment);
    }

    // Animated value updates
    animateValue(element, start, end, duration = 1000, formatter = null) {
        if (!element) return;

        const startTime = performance.now();
        const startValue = parseFloat(start) || 0;
        const endValue = parseFloat(end) || 0;
        const difference = endValue - startValue;

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function (ease-out)
            const easeOut = 1 - Math.pow(1 - progress, 3);

            const currentValue = startValue + (difference * easeOut);

            const displayValue = formatter ?
                formatter(currentValue) :
                Math.round(currentValue * 100) / 100;

            element.textContent = displayValue;

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    // Progress bar updates
    updateProgressBar(element, percentage, animated = true) {
        if (!element) return;

        const progressBar = element.querySelector('.progress-fill') || element;
        const percentageText = element.querySelector('.progress-text');

        const clampedPercentage = Math.max(0, Math.min(100, percentage));

        if (animated) {
            progressBar.style.transition = 'width 0.3s ease-out';
        }

        progressBar.style.width = `${clampedPercentage}%`;

        if (percentageText) {
            percentageText.textContent = `${Math.round(clampedPercentage)}%`;
        }

        // Update ARIA attributes for accessibility
        element.setAttribute('aria-valuenow', clampedPercentage);
        element.setAttribute('aria-valuetext', `${Math.round(clampedPercentage)} percent`);
    }

    // Status indicator updates
    updateStatusIndicator(element, status, options = {}) {
        if (!element) return;

        const { text, className, ariaLabel } = options;

        // Remove existing status classes
        element.className = element.className.replace(/\b(connected|disconnected|error|failed|pending|running|completed)\b/g, '');

        // Add new status class
        this.addClass(element, status);

        if (text) {
            this.updateText(element, text);
        }

        if (ariaLabel) {
            this.setAttribute(element, 'aria-label', ariaLabel);
        }

        if (className) {
            this.addClass(element, className);
        }
    }

    // Notification creation
    createNotification(message, type = 'info', duration = 5000) {
        const notification = this.createElement('div', {
            className: `notification ${type}`,
            innerHTML: `
                <span class="notification-message">${this.escapeHTML(message)}</span>
                <button class="notification-close" aria-label="Close notification">&times;</button>
            `
        });

        // Add to notification container
        let container = this.$('#notification-container');
        if (!container) {
            container = this.createElement('div', {
                id: 'notification-container',
                className: 'notification-container'
            });
            document.body.appendChild(container);
        }

        container.appendChild(notification);

        // Add event listeners
        const closeBtn = notification.querySelector('.notification-close');
        const closeNotification = () => {
            notification.style.animation = 'slideOut 0.3s ease-out forwards';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        };

        this.on(closeBtn, 'click', closeNotification);

        // Auto-close after duration
        if (duration > 0) {
            setTimeout(closeNotification, duration);
        }

        // Animate in
        notification.style.animation = 'slideIn 0.3s ease-out forwards';

        return notification;
    }

    // Utility functions
    escapeHTML(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatDuration(milliseconds) {
        const seconds = Math.floor(milliseconds / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);

        if (hours > 0) {
            return `${hours}h ${minutes % 60}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${seconds % 60}s`;
        } else {
            return `${seconds}s`;
        }
    }

    formatTimestamp(timestamp) {
        return new Date(timestamp).toLocaleString();
    }

    // Debounce utility
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Throttle utility
    throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // Batch DOM updates
    batchUpdate(callback) {
        requestAnimationFrame(() => {
            callback();
        });
    }
}

// Export singleton instance
window.domUtils = new DOMUtils();
window.DOMUtils = DOMUtils;
