#!/usr/bin/env python3
"""
Orchestrated Dashboard Development
Using PracticalOrchestrator to coordinate specialist agents for building the monitoring dashboard
"""

import asyncio
import sys
from pathlib import Path

# Add orchestrator path
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator/src")

from practical_orchestrator import PracticalAgentTask, PracticalOrchestrator


async def build_monitoring_dashboard():
    """Build real-time monitoring dashboard using orchestrated agents"""

    # Initialize orchestrator with dashboard token pool
    orchestrator = PracticalOrchestrator(
        output_dir="/home/opsvi/master_root/apps/project-context/dashboard_output",
        max_parallel=6,  # Match our 6 token allocation
        enable_monitoring=True,
        enable_quality_reports=True,
    )

    # Set orchestrator type for token coordination
    orchestrator._orchestrator_type = "dashboard"

    # Set up progress monitoring
    def progress_handler(event_type: str, data: dict):
        print(f"🔄 {event_type}: {data}")

    orchestrator.set_progress_callback(progress_handler)

    # Define dashboard development tasks
    tasks = [
        # Backend Infrastructure
        PracticalAgentTask(
            task_id="backend_monitoring_service",
            task_type="development-specialist",
            prompt="""
            TASK: Build a comprehensive monitoring service that aggregates data from PracticalOrchestrator and existing monitoring infrastructure

            REQUIREMENTS:
            1. Create MonitoringService class that:
               - Scans /home/opsvi/master_root/apps/project-context/*_output/tasks/*.json files
               - Integrates with existing ChatImportMonitor
               - Provides real-time task status tracking
               - Calculates performance metrics and analytics
               - Supports WebSocket broadcasts for live updates

            2. Key Features:
               - File system monitoring with caching
               - Task status aggregation (pending, running, completed, failed)
               - Performance metrics calculation (parallel utilization, tasks/hour, success rate)
               - Quality report generation
               - Log file access for task debugging

            WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context/dashboard/backend
            INTEGRATION: Must work with existing orchestrator task result format from PracticalOrchestrator
            """,
            phase_id="backend_development",
            priority="high",
            tags=["monitoring", "backend", "python"],
        ),
        PracticalAgentTask(
            task_id="websocket_handler",
            task_type="api-integration-specialist",
            prompt="""
            TASK: Create WebSocket handler for real-time dashboard updates

            REQUIREMENTS:
            1. WebSocketManager class that:
               - Manages multiple client connections
               - Broadcasts system status updates every 5-10 seconds
               - Handles client subscriptions (specific tasks, phases, etc.)
               - Provides connection management and error handling
               - Supports different update frequencies for different data types

            2. Features:
               - Connection pooling and cleanup
               - Selective broadcasting based on client subscriptions
               - Heartbeat/keepalive mechanism
               - Error recovery and reconnection support

            WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context/dashboard/backend
            DEPENDENCIES: backend_monitoring_service (for data source)
            """,
            dependencies=["backend_monitoring_service"],
            phase_id="backend_development",
            priority="high",
            tags=["websocket", "realtime", "backend"],
        ),
        PracticalAgentTask(
            task_id="fastapi_backend",
            task_type="api-integration-specialist",
            prompt="""
            TASK: Create FastAPI backend server with REST API endpoints and WebSocket support

            REQUIREMENTS:
            1. FastAPI application with endpoints:
               - GET /api/status - System overview
               - GET /api/tasks - All task details
               - GET /api/tasks/{task_id} - Specific task info
               - GET /api/performance - Performance metrics
               - GET /api/logs/{task_id} - Task logs
               - GET /api/quality-report - Quality analytics
               - WebSocket /ws - Real-time updates

            2. Features:
               - CORS configuration for frontend
               - Error handling and logging
               - Health check endpoint
               - Static file serving for frontend
               - Integration with MonitoringService and WebSocketManager

            WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context/dashboard/backend
            DEPENDENCIES: backend_monitoring_service, websocket_handler
            """,
            dependencies=["backend_monitoring_service", "websocket_handler"],
            phase_id="backend_development",
            priority="high",
            tags=["fastapi", "api", "backend"],
        ),
        # Frontend Development
        PracticalAgentTask(
            task_id="dashboard_html_structure",
            task_type="development-specialist",
            prompt="""
            TASK: Create responsive HTML structure for real-time monitoring dashboard

            REQUIREMENTS:
            1. Modern HTML5 dashboard with:
               - Executive summary section (overall progress, current phase, key metrics)
               - Task monitoring grid with sortable columns
               - Performance charts area
               - Alert notifications area
               - Real-time status indicators

            2. Features:
               - Responsive design (mobile-friendly)
               - Semantic HTML structure
               - Accessibility considerations
               - Clean, professional layout
               - Integration points for JavaScript functionality

            WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context/dashboard/frontend
            DESIGN: Clean, modern dashboard aesthetic with real-time indicators
            """,
            phase_id="frontend_development",
            priority="high",
            tags=["html", "frontend", "dashboard"],
        ),
        PracticalAgentTask(
            task_id="dashboard_css_styling",
            task_type="development-specialist",
            prompt="""
            TASK: Create comprehensive CSS styling for monitoring dashboard

            REQUIREMENTS:
            1. Professional dashboard styling:
               - Modern color scheme with status indicators
               - Responsive grid layout
               - Progress bars and status badges
               - Chart areas and data tables
               - Animation effects for real-time updates

            2. Features:
               - CSS Grid/Flexbox layouts
               - Status color coding (green/yellow/red)
               - Hover effects and transitions
               - Mobile responsive breakpoints
               - Print stylesheet considerations

            WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context/dashboard/frontend
            DEPENDENCIES: dashboard_html_structure
            """,
            dependencies=["dashboard_html_structure"],
            phase_id="frontend_development",
            priority="normal",
            tags=["css", "styling", "responsive"],
        ),
        PracticalAgentTask(
            task_id="dashboard_javascript_core",
            task_type="development-specialist",
            prompt="""
            TASK: Create JavaScript application for real-time dashboard functionality

            REQUIREMENTS:
            1. Dashboard JavaScript application:
               - WebSocket connection management for real-time updates
               - REST API integration for data fetching
               - DOM manipulation for status updates
               - Chart rendering (Chart.js or similar)
               - Error handling and connection retry logic

            2. Core Features:
               - Executive dashboard auto-updating every 5 seconds
               - Task grid with filtering, sorting, search
               - Performance metrics visualization
               - Alert system with browser notifications
               - Connection status indicator

            3. Data Handling:
               - Parse JSON responses from backend APIs
               - Handle WebSocket messages for live updates
               - Cache data efficiently
               - Update UI elements without full refresh

            WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context/dashboard/frontend
            DEPENDENCIES: dashboard_html_structure, fastapi_backend
            """,
            dependencies=["dashboard_html_structure", "fastapi_backend"],
            phase_id="frontend_development",
            priority="high",
            tags=["javascript", "websocket", "charts"],
        ),
        # Integration & Testing
        PracticalAgentTask(
            task_id="dashboard_integration_testing",
            task_type="qa-testing-guru",
            prompt="""
            TASK: Test dashboard integration with running orchestrator and validate functionality

            REQUIREMENTS:
            1. Integration Testing:
               - Test backend APIs with real orchestrator data
               - Validate WebSocket real-time updates
               - Test frontend with various data scenarios
               - Verify performance under load

            2. Functional Testing:
               - Test all dashboard features (executive view, task grid, charts)
               - Validate data accuracy against source files
               - Test error handling and recovery
               - Cross-browser compatibility testing

            3. Performance Testing:
               - Monitor memory usage during long sessions
               - Test WebSocket connection stability
               - Validate update frequencies and responsiveness

            WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context/dashboard
            DEPENDENCIES: fastapi_backend, dashboard_javascript_core
            """,
            dependencies=["fastapi_backend", "dashboard_javascript_core"],
            phase_id="testing_validation",
            priority="high",
            tags=["testing", "integration", "qa"],
        ),
        # Documentation & Deployment
        PracticalAgentTask(
            task_id="dashboard_documentation",
            task_type="technical-writer",
            prompt="""
            TASK: Create comprehensive documentation for the monitoring dashboard

            REQUIREMENTS:
            1. User Documentation:
               - Dashboard usage guide
               - Feature explanations
               - Troubleshooting guide
               - Configuration options

            2. Technical Documentation:
               - Architecture overview
               - API documentation
               - Installation and setup instructions
               - Development guide for extensions

            3. Deployment Documentation:
               - Production deployment guide
               - Security considerations
               - Monitoring and maintenance
               - Performance optimization tips

            WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context/dashboard
            DEPENDENCIES: dashboard_integration_testing
            """,
            dependencies=["dashboard_integration_testing"],
            phase_id="documentation",
            priority="normal",
            tags=["documentation", "user-guide", "technical-docs"],
        ),
    ]

    print(f"🚀 Starting orchestrated dashboard development with {len(tasks)} tasks")
    print(f"📊 Parallel execution: {orchestrator.max_parallel} agents")
    print(f"📁 Output directory: {orchestrator.output_dir}")
    print()

    # Execute all tasks
    results = await orchestrator.execute_batch(tasks)

    # Print session mapping for monitoring
    print("\n" + "=" * 60)
    orchestrator.print_session_map()

    # Summary
    completed = sum(
        1 for r in results if isinstance(r, dict) and r.get("status") == "completed"
    )
    failed = sum(
        1 for r in results if isinstance(r, dict) and r.get("status") == "failed"
    )

    print(f"\n✅ Dashboard development complete!")
    print(
        f"📈 Results: {completed} completed, {failed} failed out of {len(tasks)} total"
    )
    print(f"📄 Quality report: {orchestrator.output_dir}/quality_report.json")

    if completed == len(tasks):
        print("\n🎉 SUCCESS: Dashboard fully implemented and ready!")
        print("🌐 Start the dashboard: cd dashboard/backend && python app.py")
    else:
        print(
            f"\n⚠️  Some tasks failed. Check logs and results in {orchestrator.output_dir}"
        )

    return results


if __name__ == "__main__":
    print("🎯 Real-Time Orchestrator Monitoring Dashboard Builder")
    print("=" * 60)
    print("Using PracticalOrchestrator to coordinate specialist agents")
    print()

    asyncio.run(build_monitoring_dashboard())
