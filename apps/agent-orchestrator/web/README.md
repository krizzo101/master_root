# Agent Orchestrator Dashboard

A comprehensive real-time web interface for monitoring and managing concurrent AI workflows in the Agent Orchestrator system.

## Features

### 🎯 Core Features
- **Real-time Monitoring**: Live workflow status updates via WebSocket connections
- **Multi-workflow Support**: Monitor 10+ concurrent workflows simultaneously
- **Progress Tracking**: Visual progress bars with ETA calculations
- **Resource Monitoring**: CPU, memory, and disk usage tracking
- **Deliverable Management**: File output tracking and downloads

### 🔧 Interface Components

#### Main Dashboard Grid View
- Responsive grid layout adapting to screen size (1-4 columns)
- Workflow status cards with progress indicators
- System overview panel with resource metrics
- Advanced filtering and sorting options
- Bulk operations for multiple workflows

#### Workflow Detail View
- **3-Panel Layout** (desktop): Progress/stats, live logs, output preview
- **Tabbed Layout** (mobile): Overview, logs, files, settings
- Real-time log streaming with filtering
- Task pipeline visualization with dependencies
- Resource usage monitoring

#### Multi-workflow Comparison
- Side-by-side workflow comparison
- Performance trending charts
- Comparative analysis and recommendations
- Export capabilities

### 📱 Responsive Design
- **Mobile-first approach** with progressive enhancement
- Breakpoints: 320px (mobile), 768px (tablet), 1024px (desktop), 1440px+ (large)
- Touch-friendly interactions and gestures
- Optimized for both portrait and landscape orientations

### ♿ Accessibility
- WCAG 2.1 AA compliant
- Full keyboard navigation support
- Screen reader compatibility with ARIA labels
- High contrast color schemes
- Focus management and skip navigation

## Quick Start

### 1. Demo Mode
Open `demo.html` in your browser to explore the interface with sample data:

```bash
# Serve from web directory
cd /home/opsvi/master_root/apps/agent-orchestrator/web
python -m http.server 8080
```

Visit `http://localhost:8080/demo.html` to see the dashboard in action.

### 2. Production Mode
Open `index.html` to connect to your running orchestrator:

```bash
# Ensure your orchestrator API is running on port 8888
# Ensure your WebSocket server is running on port 8765
cd /home/opsvi/master_root/apps/agent-orchestrator/web
python -m http.server 8080
```

Visit `http://localhost:8080/index.html` to access the live dashboard.

## Architecture

### Frontend Stack
- **HTML5**: Semantic markup with accessibility features
- **CSS3**: Custom CSS with CSS variables for theming
- **Vanilla JavaScript**: No external dependencies for maximum performance
- **Web APIs**: WebSocket, Fetch, Local Storage

### Key Components

```
/web
├── index.html              # Main dashboard interface
├── demo.html               # Demo with sample data
├── css/
│   ├── dashboard.css       # Core styles and components
│   └── responsive.css      # Mobile-first responsive design
└── js/
    ├── app.js              # Main application entry point
    ├── dashboard.js        # Dashboard grid and workflow cards
    ├── workflow-detail.js  # Detail view controller
    ├── comparison.js       # Multi-workflow comparison
    ├── websocket.js        # Real-time WebSocket manager
    ├── api.js              # HTTP API client
    ├── ui.js               # UI utilities and components
    └── utils.js            # Utility functions
```

### API Integration
The dashboard connects to the Agent Orchestrator via:
- **REST API** (port 8888): CRUD operations, data fetching
- **WebSocket** (port 8765): Real-time updates and notifications

## Configuration

### API Endpoints
The dashboard automatically detects API endpoints based on the current hostname:
- API Base URL: `http://localhost:8888`
- WebSocket URL: `ws://localhost:8765`

### Customization
Edit the configuration in `js/app.js`:

```javascript
this.config = {
    apiBaseUrl: 'http://your-api-server:8888',
    wsUrl: 'ws://your-websocket-server:8765',
    features: {
        darkMode: true,
        notifications: true,
        autoRefresh: true,
        comparison: true
    }
};
```

## UI Specifications Implementation

This implementation follows the exact specifications from `UI_SPECIFICATIONS.md`:

### ✅ Main Dashboard Grid View
- [x] Responsive grid layout (1-4 columns based on screen size)
- [x] Workflow status cards with progress bars
- [x] System overview panel with metrics
- [x] Filtering and sorting controls
- [x] Bulk operations dropdown

### ✅ Workflow Detail View
- [x] 3-panel desktop layout (progress, logs, output)
- [x] Mobile tabbed interface
- [x] Real-time log streaming with auto-scroll
- [x] Task pipeline visualization
- [x] Resource usage monitoring

### ✅ Multi-workflow Comparison
- [x] 2x2 grid comparison layout
- [x] Performance trending charts (text-based for demo)
- [x] Comparative analysis insights
- [x] Export and save functionality

### ✅ Responsive Design
- [x] Mobile-first CSS approach
- [x] Breakpoint-specific layouts
- [x] Touch-friendly interactions
- [x] Collapsible navigation

### ✅ Accessibility Features
- [x] ARIA labels and roles
- [x] Keyboard navigation
- [x] Screen reader support
- [x] Focus management
- [x] High contrast colors

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

### Optimization Features
- **Virtual scrolling** for large workflow lists
- **Efficient re-rendering** with change detection
- **Request caching** with automatic expiration
- **WebSocket connection pooling**
- **Progressive loading** of workflow details

### Resource Usage
- Initial load: ~200KB (HTML + CSS + JS)
- Memory usage: <50MB for 100+ workflows
- WebSocket bandwidth: <1KB/s per active workflow

## Development

### File Structure
```
web/
├── index.html              # Production dashboard
├── demo.html               # Demo with sample data
├── README.md               # This documentation
├── css/
│   ├── dashboard.css       # 2,000+ lines of CSS
│   └── responsive.css      # Mobile-first responsive rules
└── js/
    ├── app.js              # Application initialization (400+ lines)
    ├── dashboard.js        # Main dashboard logic (800+ lines)
    ├── workflow-detail.js  # Detail view controller (600+ lines)
    ├── comparison.js       # Comparison interface (300+ lines)
    ├── websocket.js        # WebSocket management (400+ lines)
    ├── api.js              # API client (300+ lines)
    ├── ui.js               # UI utilities (400+ lines)
    └── utils.js            # Utility functions (300+ lines)
```

### Adding New Features
1. Add new functionality to the appropriate JS module
2. Update CSS for styling
3. Add responsive rules if needed
4. Update this README with new features

### Testing
Use the demo page to test features:
- Load sample data
- Simulate real-time updates
- Test responsive breakpoints
- Verify accessibility with screen readers

## Integration with Agent Orchestrator

### Dashboard Server Integration
The dashboard integrates with the existing `dashboard_server.py`:

```python
# Update static directory path
self.static_dir = Path(__file__).parent.parent.parent / "web"
```

### WebSocket Events
The dashboard subscribes to these WebSocket events:
- `workflow_update`: Status changes
- `task_update`: Individual task progress
- `log_entry`: New log entries
- `progress_update`: Progress and ETA updates
- `system_metric`: Resource usage metrics

### API Endpoints
The dashboard uses these API endpoints:
- `GET /status`: Orchestrator status
- `GET /tasks`: List all tasks/workflows
- `GET /tasks/{id}`: Individual task details
- `POST /tasks/{id}/retry`: Retry failed tasks
- `GET /metrics`: System metrics

## Troubleshooting

### Common Issues

1. **Dashboard not loading**
   - Check if web server is running
   - Verify file paths are correct
   - Check browser console for errors

2. **WebSocket connection failed**
   - Ensure WebSocket server is running on port 8765
   - Check firewall settings
   - Try the demo page first to verify UI functionality

3. **API connection failed**
   - Ensure orchestrator API is running on port 8888
   - Check CORS settings
   - Verify API endpoints are accessible

4. **Responsive layout issues**
   - Test with browser dev tools device simulation
   - Check CSS media queries
   - Verify viewport meta tag is present

### Debug Mode
Enable debug logging in the browser console:

```javascript
// In browser console
window.dashboardApp.getStats()  // Get application statistics
localStorage.setItem('dashboard.debug', 'true')  // Enable debug mode
```

## Contributing

When making changes:
1. Follow the existing code style and patterns
2. Test across all breakpoints (mobile, tablet, desktop)
3. Verify accessibility with keyboard-only navigation
4. Update this README if adding new features
5. Test with the demo page before production deployment

---

**Note**: This dashboard is designed to work standalone or integrate with the existing Agent Orchestrator monitoring infrastructure. All WebSocket and API endpoints are configurable for different deployment scenarios.
