/**
 * Performance monitoring utilities
 * @module PerformanceMonitor
 */

export class PerformanceMonitor {
  static #metrics = new Map();
  static #observers = new Map();

  /**
   * Initialize performance monitoring
   */
  static init() {
    // Monitor page load performance
    if ('PerformanceObserver' in window) {
      this.#observeNavigationTiming();
      this.#observeLCP();
      this.#observeFID();
      this.#observeCLS();
    }

    // Monitor memory usage if available
    this.#monitorMemory();
  }

  /**
   * Measure function execution time
   * @param {string} name - Metric name
   * @param {Function} fn - Function to measure
   * @returns {*} Function result
   */
  static measure(name, fn) {
    const startTime = performance.now();
    const result = fn();
    const endTime = performance.now();
    const duration = endTime - startTime;

    this.#recordMetric(name, duration);
    return result;
  }

  /**
   * Measure async function execution time
   * @param {string} name - Metric name
   * @param {Function} fn - Async function to measure
   * @returns {Promise<*>} Function result
   */
  static async measureAsync(name, fn) {
    const startTime = performance.now();
    const result = await fn();
    const endTime = performance.now();
    const duration = endTime - startTime;

    this.#recordMetric(name, duration);
    return result;
  }

  /**
   * Record a metric value
   * @param {string} name - Metric name
   * @param {number} value - Metric value
   * @private
   */
  static #recordMetric(name, value) {
    if (!this.#metrics.has(name)) {
      this.#metrics.set(name, []);
    }
    
    const metrics = this.#metrics.get(name);
    metrics.push({
      value,
      timestamp: Date.now()
    });

    // Keep only last 100 measurements
    if (metrics.length > 100) {
      metrics.shift();
    }

    // Log slow operations
    if (value > 100 && import.meta.env.DEV) {
      console.warn(`⚡ Slow operation: ${name} took ${value.toFixed(2)}ms`);
    }
  }

  /**
   * Observe navigation timing
   * @private
   */
  static #observeNavigationTiming() {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'navigation') {
          this.#recordMetric('navigation.domContentLoaded', entry.domContentLoadedEventEnd);
          this.#recordMetric('navigation.loadComplete', entry.loadEventEnd);
        }
      }
    });

    observer.observe({ entryTypes: ['navigation'] });
    this.#observers.set('navigation', observer);
  }

  /**
   * Observe Largest Contentful Paint
   * @private
   */
  static #observeLCP() {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      this.#recordMetric('webvitals.lcp', lastEntry.renderTime || lastEntry.loadTime);
    });

    observer.observe({ entryTypes: ['largest-contentful-paint'] });
    this.#observers.set('lcp', observer);
  }

  /**
   * Observe First Input Delay
   * @private
   */
  static #observeFID() {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'first-input') {
          this.#recordMetric('webvitals.fid', entry.processingStart - entry.startTime);
        }
      }
    });

    observer.observe({ entryTypes: ['first-input'] });
    this.#observers.set('fid', observer);
  }

  /**
   * Observe Cumulative Layout Shift
   * @private
   */
  static #observeCLS() {
    let clsValue = 0;
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
          this.#recordMetric('webvitals.cls', clsValue);
        }
      }
    });

    observer.observe({ entryTypes: ['layout-shift'] });
    this.#observers.set('cls', observer);
  }

  /**
   * Monitor memory usage
   * @private
   */
  static #monitorMemory() {
    if ('memory' in performance) {
      setInterval(() => {
        const memory = performance.memory;
        this.#recordMetric('memory.used', memory.usedJSHeapSize / 1048576); // Convert to MB
        this.#recordMetric('memory.total', memory.totalJSHeapSize / 1048576);
      }, 10000); // Check every 10 seconds
    }
  }

  /**
   * Get metrics summary
   * @param {string} name - Metric name (optional)
   * @returns {Object} Metrics summary
   */
  static getMetrics(name = null) {
    if (name) {
      const metrics = this.#metrics.get(name);
      if (!metrics || metrics.length === 0) {
        return null;
      }

      const values = metrics.map(m => m.value);
      return {
        count: values.length,
        min: Math.min(...values),
        max: Math.max(...values),
        avg: values.reduce((a, b) => a + b, 0) / values.length,
        last: values[values.length - 1]
      };
    }

    const summary = {};
    for (const [key, metrics] of this.#metrics) {
      if (metrics.length > 0) {
        const values = metrics.map(m => m.value);
        summary[key] = {
          count: values.length,
          min: Math.min(...values),
          max: Math.max(...values),
          avg: values.reduce((a, b) => a + b, 0) / values.length,
          last: values[values.length - 1]
        };
      }
    }
    return summary;
  }

  /**
   * Clear all metrics
   */
  static clearMetrics() {
    this.#metrics.clear();
  }

  /**
   * Cleanup observers
   */
  static cleanup() {
    for (const observer of this.#observers.values()) {
      observer.disconnect();
    }
    this.#observers.clear();
  }
}

// Auto-initialize if in browser
if (typeof window !== 'undefined') {
  PerformanceMonitor.init();
}