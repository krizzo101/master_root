/**
 * Modern TODO App with ES2024+ features
 * @module TodoApp
 */

import { ErrorHandler } from './error-handler.js';
import { PerformanceMonitor } from './performance-monitor.js';

// TypeScript-style type annotations in JSDoc
/**
 * @typedef {'low' | 'medium' | 'high'} Priority
 * @typedef {'all' | 'active' | 'completed'} FilterType
 * 
 * @typedef {Object} Todo
 * @property {string} id - Unique identifier
 * @property {string} text - Task description
 * @property {boolean} completed - Completion status
 * @property {Priority} priority - Task priority
 * @property {number} createdAt - Creation timestamp
 * @property {number} completedAt - Completion timestamp (nullable)
 */

class TodoApp {
  #todos = new Map();
  #currentFilter = 'all';
  #searchQuery = '';
  #storageKey = 'modernTodoApp_v1';
  
  // DOM element cache using Private fields (ES2022)
  #elements = {};
  
  constructor() {
    this.#initializeElements();
    this.#loadFromStorage();
    this.#attachEventListeners();
    this.#render();
  }
  
  /**
   * Initialize and cache DOM elements
   * @private
   */
  #initializeElements() {
    this.#elements = {
      form: document.getElementById('todo-form'),
      input: document.getElementById('todo-input'),
      prioritySelect: document.getElementById('priority-select'),
      todoList: document.getElementById('todo-list'),
      taskCount: document.getElementById('task-count'),
      completedCount: document.getElementById('completed-count'),
      clearButton: document.getElementById('clear-completed'),
      searchInput: document.getElementById('search-input'),
      emptyState: document.getElementById('empty-state'),
      filterButtons: document.querySelectorAll('.filter-btn')
    };
  }
  
  /**
   * Attach event listeners using modern event handling
   * @private
   */
  #attachEventListeners() {
    // Form submission
    this.#elements.form.addEventListener('submit', this.#handleSubmit.bind(this));
    
    // Filter buttons using event delegation
    document.querySelector('.filter-buttons').addEventListener('click', (e) => {
      if (e.target.matches('.filter-btn')) {
        this.#setFilter(e.target.dataset.filter);
      }
    });
    
    // Search input with debouncing
    let searchTimeout;
    this.#elements.searchInput.addEventListener('input', (e) => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        this.#searchQuery = e.target.value.toLowerCase();
        this.#render();
      }, 300);
    });
    
    // Clear completed button
    this.#elements.clearButton.addEventListener('click', () => {
      this.#clearCompleted();
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', this.#handleKeyboard.bind(this));
    
    // Auto-save on window unload
    window.addEventListener('beforeunload', () => {
      this.#saveToStorage();
    });
  }
  
  /**
   * Handle form submission
   * @param {Event} e - Submit event
   * @private
   */
  #handleSubmit(e) {
    e.preventDefault();
    
    const text = this.#elements.input.value.trim();
    if (!text) return;
    
    const priority = this.#elements.prioritySelect.value;
    this.#addTodo(text, priority);
    
    // Reset form
    this.#elements.form.reset();
    this.#elements.input.focus();
  }
  
  /**
   * Add a new todo item
   * @param {string} text - Task description
   * @param {Priority} priority - Task priority
   * @private
   */
  #addTodo(text, priority = 'medium') {
    const todo = {
      id: crypto.randomUUID(), // ES2024 crypto.randomUUID()
      text,
      completed: false,
      priority,
      createdAt: Date.now(),
      completedAt: null
    };
    
    this.#todos.set(todo.id, todo);
    this.#saveToStorage();
    this.#render();
    
    // Announce to screen readers
    this.#announce(`Task "${text}" added`);
  }
  
  /**
   * Toggle todo completion status
   * @param {string} id - Todo ID
   * @private
   */
  #toggleTodo(id) {
    const todo = this.#todos.get(id);
    if (!todo) return;
    
    todo.completed = !todo.completed;
    todo.completedAt = todo.completed ? Date.now() : null;
    
    this.#saveToStorage();
    this.#render();
    
    const status = todo.completed ? 'completed' : 'uncompleted';
    this.#announce(`Task "${todo.text}" ${status}`);
  }
  
  /**
   * Delete a todo item
   * @param {string} id - Todo ID
   * @private
   */
  #deleteTodo(id) {
    const todo = this.#todos.get(id);
    if (!todo) return;
    
    this.#todos.delete(id);
    this.#saveToStorage();
    this.#render();
    
    this.#announce(`Task "${todo.text}" deleted`);
  }
  
  /**
   * Clear all completed todos
   * @private
   */
  #clearCompleted() {
    const completed = Array.from(this.#todos.values())
      .filter(todo => todo.completed);
    
    for (const todo of completed) {
      this.#todos.delete(todo.id);
    }
    
    this.#saveToStorage();
    this.#render();
    
    this.#announce(`${completed.length} completed tasks cleared`);
  }
  
  /**
   * Set the current filter
   * @param {FilterType} filter - Filter type
   * @private
   */
  #setFilter(filter) {
    this.#currentFilter = filter;
    
    // Update button states
    this.#elements.filterButtons.forEach(btn => {
      const isActive = btn.dataset.filter === filter;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-pressed', isActive);
    });
    
    this.#render();
  }
  
  /**
   * Get filtered todos based on current filter and search
   * @returns {Todo[]} Filtered todos
   * @private
   */
  #getFilteredTodos() {
    let todos = Array.from(this.#todos.values());
    
    // Apply filter
    switch (this.#currentFilter) {
      case 'active':
        todos = todos.filter(todo => !todo.completed);
        break;
      case 'completed':
        todos = todos.filter(todo => todo.completed);
        break;
    }
    
    // Apply search
    if (this.#searchQuery) {
      todos = todos.filter(todo => 
        todo.text.toLowerCase().includes(this.#searchQuery)
      );
    }
    
    // Sort by priority and creation time
    const priorityOrder = { high: 0, medium: 1, low: 2 };
    todos.sort((a, b) => {
      if (a.completed !== b.completed) {
        return a.completed ? 1 : -1;
      }
      const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
      if (priorityDiff !== 0) return priorityDiff;
      return b.createdAt - a.createdAt;
    });
    
    return todos;
  }
  
  /**
   * Render the todo list
   * @private
   */
  #render() {
    const todos = this.#getFilteredTodos();
    const allTodos = Array.from(this.#todos.values());
    
    // Update stats
    const activeTodos = allTodos.filter(t => !t.completed);
    const completedTodos = allTodos.filter(t => t.completed);
    
    this.#elements.taskCount.textContent = 
      `${activeTodos.length} ${activeTodos.length === 1 ? 'task' : 'tasks'}`;
    this.#elements.completedCount.textContent = 
      `${completedTodos.length} completed`;
    
    // Enable/disable clear button
    this.#elements.clearButton.disabled = completedTodos.length === 0;
    
    // Show/hide empty state
    const isEmpty = todos.length === 0;
    this.#elements.emptyState.classList.toggle('show', isEmpty);
    
    // Render todo list
    if (!isEmpty) {
      // Using template literals with Array.map (ES6+)
      this.#elements.todoList.innerHTML = todos.map(todo => this.#createTodoHTML(todo)).join('');
      
      // Attach todo item event listeners
      this.#attachTodoListeners();
    } else {
      this.#elements.todoList.innerHTML = '';
    }
  }
  
  /**
   * Create HTML for a todo item
   * @param {Todo} todo - Todo object
   * @returns {string} HTML string
   * @private
   */
  #createTodoHTML(todo) {
    const { id, text, completed, priority } = todo;
    const escapedText = this.#escapeHtml(text);
    
    return `
      <li class="todo-item ${completed ? 'completed' : ''}" data-id="${id}">
        <input 
          type="checkbox" 
          class="todo-checkbox"
          ${completed ? 'checked' : ''}
          aria-label="Mark ${escapedText} as ${completed ? 'incomplete' : 'complete'}"
        >
        <span class="todo-text">${escapedText}</span>
        <span class="priority-badge ${priority}">${priority}</span>
        <button class="delete-btn" aria-label="Delete ${escapedText}">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
          </svg>
        </button>
      </li>
    `;
  }
  
  /**
   * Attach event listeners to todo items
   * @private
   */
  #attachTodoListeners() {
    // Using event delegation for better performance
    this.#elements.todoList.addEventListener('click', (e) => {
      const todoItem = e.target.closest('.todo-item');
      if (!todoItem) return;
      
      const id = todoItem.dataset.id;
      
      if (e.target.matches('.todo-checkbox')) {
        this.#toggleTodo(id);
      } else if (e.target.closest('.delete-btn')) {
        this.#deleteTodo(id);
      }
    }, { once: true }); // Re-attach on next render
  }
  
  /**
   * Handle keyboard shortcuts
   * @param {KeyboardEvent} e - Keyboard event
   * @private
   */
  #handleKeyboard(e) {
    // Ctrl/Cmd + Enter to add todo
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      this.#elements.input.focus();
    }
    
    // Escape to clear search
    if (e.key === 'Escape' && this.#searchQuery) {
      this.#elements.searchInput.value = '';
      this.#searchQuery = '';
      this.#render();
    }
    
    // Alt + 1/2/3 for filters
    if (e.altKey) {
      switch (e.key) {
        case '1':
          this.#setFilter('all');
          break;
        case '2':
          this.#setFilter('active');
          break;
        case '3':
          this.#setFilter('completed');
          break;
      }
    }
  }
  
  /**
   * Save todos to localStorage
   * @private
   */
  #saveToStorage() {
    try {
      const data = {
        todos: Array.from(this.#todos.entries()),
        filter: this.#currentFilter,
        version: 1
      };
      localStorage.setItem(this.#storageKey, JSON.stringify(data));
    } catch (e) {
      console.error('Failed to save to localStorage:', e);
    }
  }
  
  /**
   * Load todos from localStorage
   * @private
   */
  #loadFromStorage() {
    try {
      const stored = localStorage.getItem(this.#storageKey);
      if (!stored) return;
      
      const data = JSON.parse(stored);
      if (data.version !== 1) return; // Handle version mismatch
      
      // Restore todos using Map constructor
      this.#todos = new Map(data.todos);
      
      // Restore filter if valid
      if (['all', 'active', 'completed'].includes(data.filter)) {
        this.#setFilter(data.filter);
      }
    } catch (e) {
      console.error('Failed to load from localStorage:', e);
    }
  }
  
  /**
   * Escape HTML to prevent XSS
   * @param {string} text - Text to escape
   * @returns {string} Escaped text
   * @private
   */
  #escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  /**
   * Announce to screen readers
   * @param {string} message - Message to announce
   * @private
   */
  #announce(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.classList.add('sr-only');
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    setTimeout(() => announcement.remove(), 1000);
  }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => new TodoApp());
} else {
  new TodoApp();
}

// Service Worker registration for offline support (optional)
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(() => {
    // Service worker registration failed, app still works
  });
}