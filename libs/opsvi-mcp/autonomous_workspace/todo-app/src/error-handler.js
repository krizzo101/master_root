/**
 * Error handling utilities
 * @module ErrorHandler
 */

export class ErrorHandler {
  static #errorLog = [];
  static #maxLogSize = 100;

  /**
   * Log an error with context
   * @param {Error} error - The error object
   * @param {string} context - Context where error occurred
   * @param {object} metadata - Additional metadata
   */
  static logError(error, context = 'Unknown', metadata = {}) {
    const errorEntry = {
      timestamp: new Date().toISOString(),
      context,
      message: error.message,
      stack: error.stack,
      metadata,
      userAgent: navigator.userAgent
    };

    // Add to internal log
    this.#errorLog.unshift(errorEntry);
    if (this.#errorLog.length > this.#maxLogSize) {
      this.#errorLog.pop();
    }

    // Console logging in development
    if (import.meta.env.DEV) {
      console.group(`🔴 Error in ${context}`);
      console.error('Message:', error.message);
      console.error('Stack:', error.stack);
      console.table(metadata);
      console.groupEnd();
    }

    // Send to monitoring service in production
    if (import.meta.env.PROD && typeof window.reportError === 'function') {
      window.reportError(errorEntry);
    }
  }

  /**
   * Handle async errors gracefully
   * @param {Function} fn - Async function to wrap
   * @param {string} context - Context for error logging
   * @returns {Function} Wrapped function
   */
  static wrapAsync(fn, context = 'AsyncOperation') {
    return async (...args) => {
      try {
        return await fn(...args);
      } catch (error) {
        this.logError(error, context, { args });
        throw error;
      }
    };
  }

  /**
   * Get error log for debugging
   * @returns {Array} Error log entries
   */
  static getErrorLog() {
    return [...this.#errorLog];
  }

  /**
   * Clear error log
   */
  static clearErrorLog() {
    this.#errorLog = [];
  }

  /**
   * Export error log as JSON
   * @returns {string} JSON string of error log
   */
  static exportErrorLog() {
    return JSON.stringify(this.#errorLog, null, 2);
  }
}

// Global error handlers
window.addEventListener('error', (event) => {
  ErrorHandler.logError(
    new Error(event.message),
    'GlobalError',
    {
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno
    }
  );
});

window.addEventListener('unhandledrejection', (event) => {
  ErrorHandler.logError(
    new Error(event.reason?.message || 'Unhandled Promise Rejection'),
    'UnhandledRejection',
    { reason: event.reason }
  );
});