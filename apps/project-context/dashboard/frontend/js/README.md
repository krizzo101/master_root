# Real-Time Dashboard JavaScript Application

This directory contains the complete JavaScript application for the real-time orchestrator monitoring dashboard.

## Architecture Overview

The application is built using a modular architecture with the following core components:

### Core Modules

1. **dom-utils.js** - DOM manipulation utilities
2. **api-client.js** - REST API integration layer
3. **websocket-manager.js** - WebSocket connection management
4. **chart-manager.js** - Chart rendering with Chart.js
5. **notification-system.js** - Alert system and browser notifications
6. **dashboard.js** - Main application orchestrator

## Features

### Real-Time Updates
- WebSocket connection with automatic reconnection
- 5-second polling intervals for data refresh
- Live chart updates with real-time metrics

### Data Visualization
- Performance metrics charts (CPU, Memory)
- Task status distribution (pie/doughnut charts)
- Progress timeline visualization
- Real-time metrics with sliding window

### Interactive Features
- Task filtering by status (all, running, completed, failed, pending)
- Table sorting with visual indicators
- Search functionality with debounced input
- Theme toggle (light/dark mode)

### Notification System
- Toast notifications with different severity levels
- Browser notifications for critical alerts
- Progress notifications for long-running tasks
- Connection status indicators

### Error Handling
- Automatic retry logic for failed requests
- WebSocket reconnection with exponential backoff
- Graceful degradation when services are unavailable
- User-friendly error messages

## API Endpoints Integration

The application integrates with the following backend endpoints:

- `GET /api/status` - Overall system status
- `GET /api/tasks` - Task list and details
- `GET /api/performance` - System performance metrics
- `GET /api/quality-report` - Quality metrics
- `GET /api/analytics` - Analytics data
- `WebSocket /ws` - Real-time updates

## Usage

### Initialization

The dashboard automatically initializes when the DOM is ready:

```javascript
// Automatic initialization
window.dashboard = new Dashboard();
```

### Manual Control

```javascript
// Access dashboard instance
const dashboard = window.dashboard;

// Check status
console.log(dashboard.getStatus());

// Force refresh
await dashboard.refreshData();

// View task details
await dashboard.viewTaskDetails('task-123');
```

### Notifications

```javascript
// Show different types of notifications
notifications.success('Operation completed successfully');
notifications.warning('Connection unstable');
notifications.error('Failed to load data');
notifications.info('System update in progress');

// Progress notifications
const progress = notifications.progress('Processing...');
progress.update(50, 'Half way done');
progress.complete('Processing finished');
```

### Charts

```javascript
// Create custom charts
await chartManager.createPerformanceChart('my-chart', performanceData);

// Update existing charts
chartManager.updateChart('my-chart', newData);

// Add real-time data points
chartManager.addDataPoint('realtime-chart', timestamp, [value1, value2]);
```

## Configuration

### WebSocket Settings

```javascript
const wsManager = new WebSocketManager('ws://localhost:8000/ws', {
    maxReconnectAttempts: 5,
    reconnectDelay: 3000,
    heartbeatInterval: 30000
});
```

### API Client Settings

```javascript
const apiClient = new DashboardApiClient('http://localhost:8000', {
    timeout: 10000,
    retryAttempts: 3,
    cacheTimeout: 5000
});
```

## Browser Support

- Modern browsers with ES6+ support
- WebSocket support required
- Canvas support for charts
- Notification API (optional, graceful fallback)

## Dependencies

### External Libraries
- Chart.js (loaded dynamically via CDN)
- No other external dependencies required

### Browser APIs Used
- WebSocket API
- Fetch API
- Notification API
- Canvas API
- Local Storage API

## Performance Considerations

### Optimization Features
- Request caching with TTL
- Debounced search input
- Throttled DOM updates
- Batch DOM operations
- Canvas chart animations
- Memory cleanup on destroy

### Data Handling
- Efficient table updates with DocumentFragment
- Smart chart data updates (only changed data)
- Connection pooling and reuse
- Automatic cleanup of event listeners

## Error Boundaries

The application includes comprehensive error handling:

1. **Network Errors** - Automatic retry with exponential backoff
2. **WebSocket Errors** - Reconnection logic with status indicators
3. **Chart Errors** - Graceful fallbacks when Chart.js fails to load
4. **DOM Errors** - Safe element access with null checks
5. **Data Errors** - Validation and sanitization of API responses

## Accessibility Features

- ARIA labels and roles
- Keyboard navigation support
- Screen reader announcements
- High contrast theme support
- Focus management
- Semantic HTML structure

## Security Features

- XSS protection with HTML escaping
- Safe DOM manipulation
- Secure WebSocket connections (WSS in production)
- Content Security Policy compatible
- No inline scripts or eval usage

## Development

### Adding New Features

1. Create new module in appropriate category
2. Export classes/functions to window object
3. Add script tag to index.html
4. Update this documentation

### Debugging

```javascript
// Enable debug logging
window.dashboard.debug = true;

// Access internal state
console.log(window.dashboard.cache);
console.log(window.chartManager.getAllCharts());
console.log(window.notifications.getStats());
```

## Production Deployment

### Recommended Optimizations

1. **Minification** - Minify all JavaScript files
2. **Bundling** - Combine modules into single file
3. **Caching** - Set appropriate cache headers
4. **CDN** - Use CDN for Chart.js and other assets
5. **Compression** - Enable gzip/brotli compression

### Environment Variables

```javascript
// Configure for production
const config = {
    apiUrl: process.env.API_URL || 'http://localhost:8000',
    wsUrl: process.env.WS_URL || 'ws://localhost:8000/ws',
    environment: process.env.NODE_ENV || 'development'
};
```

## Monitoring

The application includes built-in monitoring:

- Performance timing
- Error tracking
- Connection status
- Chart render times
- API response times

## Troubleshooting

### Common Issues

1. **Charts not rendering** - Check Chart.js CDN availability
2. **WebSocket connection fails** - Verify backend is running
3. **Notifications not working** - Check browser permissions
4. **Slow performance** - Check network tab for API delays

### Debug Tools

```javascript
// Connection diagnostics
console.log(window.dashboard.wsManager.getConnectionState());

// API client status
console.log(window.dashboard.apiClient.checkHealth());

// Notification stats
console.log(window.notifications.getStats());
```
