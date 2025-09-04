#!/usr/bin/env python3
"""
Build Dashboard using GenericOrchestrator (Known Working Pattern)
Uses the same reliable pattern as execute_phase1_generic.py
"""
import asyncio
import os
import sys
from pathlib import Path

# Add paths for imports
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator")
sys.path.append("/home/opsvi/master_root/apps/project-context")

from src.generic_orchestrator import AgentTask, GenericOrchestrator
from src.token_loader import TokenLoader


def create_dashboard_agent_tasks():
    """
    Create dashboard development tasks as AgentTask objects
    Following the original working pattern from execute_phase1_generic.py
    """

    agent_tasks = []

    # Task 1: Backend Monitoring Service (no dependencies)
    backend_monitoring_prompt = """TASK: Build comprehensive monitoring service that aggregates data from orchestrator outputs.

SPECIALIST ROLE: You are acting as a development-specialist agent.

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context/dashboard/backend
- Data Source: *_output/tasks/*.json files from PracticalOrchestrator
- Integration: Must work with existing orchestrator task result format
- Real-time Support: WebSocket broadcasts for live updates

REQUIREMENTS:
1. Create MonitoringService class that:
   - Scans /home/opsvi/master_root/apps/project-context/*_output/tasks/*.json files
   - Provides real-time task status tracking
   - Calculates performance metrics and analytics
   - Supports WebSocket broadcasts for live updates

2. Key Features:
   - File system monitoring with caching
   - Task status aggregation (pending, running, completed, failed)
   - Performance metrics calculation (parallel utilization, tasks/hour, success rate)
   - Quality report generation
   - Log file access for task debugging

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are building a real-time monitoring dashboard for orchestrator processes that can track multiple agents simultaneously and provide performance insights.
"""

    agent_tasks.append(
        AgentTask(
            task_id="backend_monitoring_service",
            task_type="development-specialist",
            prompt=backend_monitoring_prompt,
            context={"phase": "backend_development", "priority": "high"},
        )
    )

    # Task 2: WebSocket Handler (depends on monitoring service)
    websocket_prompt = """TASK: Create WebSocket handler for real-time dashboard updates.

SPECIALIST ROLE: You are acting as an api-integration-specialist agent.

DEPENDENCIES: This task depends on completion of: backend_monitoring_service

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context/dashboard/backend
- Data Source: MonitoringService from backend_monitoring_service task
- Real-time Requirements: 5-10 second update intervals

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

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are building a real-time monitoring dashboard for orchestrator processes that can track multiple agents simultaneously and provide performance insights.
"""

    agent_tasks.append(
        AgentTask(
            task_id="websocket_handler",
            task_type="api-integration-specialist",
            prompt=websocket_prompt,
            dependencies=["backend_monitoring_service"],
            context={"phase": "backend_development", "priority": "high"},
        )
    )

    # Task 3: FastAPI Backend (depends on monitoring service and websocket)
    fastapi_prompt = """TASK: Create FastAPI backend server with REST API endpoints and WebSocket support.

SPECIALIST ROLE: You are acting as an api-integration-specialist agent.

DEPENDENCIES: This task depends on completion of: backend_monitoring_service, websocket_handler

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context/dashboard/backend
- Integration: MonitoringService and WebSocketManager from previous tasks
- Frontend Support: Static file serving and CORS configuration

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

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are building a real-time monitoring dashboard for orchestrator processes that can track multiple agents simultaneously and provide performance insights.
"""

    agent_tasks.append(
        AgentTask(
            task_id="fastapi_backend",
            task_type="api-integration-specialist",
            prompt=fastapi_prompt,
            dependencies=["backend_monitoring_service", "websocket_handler"],
            context={"phase": "backend_development", "priority": "high"},
        )
    )

    # Task 4: Dashboard HTML Structure (no dependencies)
    html_prompt = """TASK: Create responsive HTML structure for real-time monitoring dashboard.

SPECIALIST ROLE: You are acting as a development-specialist agent.

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context/dashboard/frontend
- Design Goal: Clean, modern dashboard aesthetic with real-time indicators
- Integration: Must work with FastAPI backend and WebSocket updates

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

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are building a real-time monitoring dashboard for orchestrator processes that can track multiple agents simultaneously and provide performance insights.
"""

    agent_tasks.append(
        AgentTask(
            task_id="dashboard_html_structure",
            task_type="development-specialist",
            prompt=html_prompt,
            context={"phase": "frontend_development", "priority": "high"},
        )
    )

    # Task 5: Dashboard CSS Styling (depends on HTML structure)
    css_prompt = """TASK: Create comprehensive CSS styling for monitoring dashboard.

SPECIALIST ROLE: You are acting as a development-specialist agent.

DEPENDENCIES: This task depends on completion of: dashboard_html_structure

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context/dashboard/frontend
- Design Requirements: Professional dashboard with status color coding
- Responsive: Mobile and desktop support

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

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are building a real-time monitoring dashboard for orchestrator processes that can track multiple agents simultaneously and provide performance insights.
"""

    agent_tasks.append(
        AgentTask(
            task_id="dashboard_css_styling",
            task_type="development-specialist",
            prompt=css_prompt,
            dependencies=["dashboard_html_structure"],
            context={"phase": "frontend_development", "priority": "normal"},
        )
    )

    # Task 6: Dashboard JavaScript Core (depends on HTML and FastAPI)
    javascript_prompt = """TASK: Create JavaScript application for real-time dashboard functionality.

SPECIALIST ROLE: You are acting as a development-specialist agent.

DEPENDENCIES: This task depends on completion of: dashboard_html_structure, fastapi_backend

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context/dashboard/frontend
- Backend Integration: FastAPI endpoints and WebSocket from previous tasks
- Real-time Updates: 5-second refresh intervals

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

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are building a real-time monitoring dashboard for orchestrator processes that can track multiple agents simultaneously and provide performance insights.
"""

    agent_tasks.append(
        AgentTask(
            task_id="dashboard_javascript_core",
            task_type="development-specialist",
            prompt=javascript_prompt,
            dependencies=["dashboard_html_structure", "fastapi_backend"],
            context={"phase": "frontend_development", "priority": "high"},
        )
    )

    # Task 7: Dashboard Integration Testing (depends on backend and frontend)
    testing_prompt = """TASK: Test dashboard integration with running orchestrator and validate functionality.

SPECIALIST ROLE: You are acting as a qa-testing-guru agent.

DEPENDENCIES: This task depends on completion of: fastapi_backend, dashboard_javascript_core

CONTEXT:
- Working Directory: /home/opsvi/master_root/apps/project-context/dashboard
- Integration Target: Complete dashboard with backend and frontend
- Test Data: Use real orchestrator output files from *_output/tasks/

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

DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.

PROJECT CONTEXT: You are building a real-time monitoring dashboard for orchestrator processes that can track multiple agents simultaneously and provide performance insights.
"""

    agent_tasks.append(
        AgentTask(
            task_id="dashboard_integration_testing",
            task_type="qa-testing-guru",
            prompt=testing_prompt,
            dependencies=["fastapi_backend", "dashboard_javascript_core"],
            context={"phase": "testing_validation", "priority": "normal"},
        )
    )

    return agent_tasks


async def main():
    """Execute dashboard build using the original GenericOrchestrator pattern"""

    print("🚀 DASHBOARD BUILD - GENERIC ORCHESTRATOR")
    print("=" * 60)
    print("✅ Foundation: Backend infrastructure + Frontend components")
    print("🎯 Architecture: FastAPI + WebSocket + HTML/CSS/JS dashboard")
    print(
        "⚡ Execution: Up to 6 parallel tasks using GenericOrchestrator + dashboard tokens"
    )
    print()

    # Create tasks using original pattern
    tasks = create_dashboard_agent_tasks()

    # Load dashboard tokens (should get 6 tokens from dashboard pool)
    loader = TokenLoader()
    loader._orchestrator_type = "dashboard"  # Set type for dashboard token pool
    tokens = loader.load_tokens()

    # Create orchestrator with dashboard coordination (like the original)
    orchestrator = GenericOrchestrator(
        output_dir=Path("./dashboard_output"),
        max_parallel=min(len(tokens), 6),  # Use dashboard tokens, up to 6
        tokens=tokens,
        use_optimizations=True,
    )

    print(f"🔧 Token count: {len(tokens)}")
    print(f"⚡ Max parallel: {orchestrator.max_parallel}")
    print()

    # Print task plan
    print("📋 EXECUTION PLAN")
    print("-" * 30)
    for task in tasks:
        deps = (
            f" → depends on: {', '.join(task.dependencies)}"
            if task.dependencies
            else ""
        )
        print(f"  {task.task_id} ({task.task_type}){deps}")
    print()

    # Execute tasks
    print("🎯 Starting dashboard build...")
    results = await orchestrator.execute_batch(tasks)

    # Analyze results
    successful = [r for r in results if r.get("status") == "completed"]
    failed = [r for r in results if r.get("status") == "failed"]

    print("\n✅ DASHBOARD BUILD COMPLETED!")
    print("=" * 50)
    print(f"✅ Successful tasks: {len(successful)}")
    print(f"❌ Failed tasks: {len(failed)}")

    if failed:
        print("\n❌ Failed Tasks:")
        for task in failed:
            print(f"   - {task['task_id']}: {task.get('error', 'Unknown error')}")

    if len(successful) >= 6:  # Backend + Frontend complete
        print(f"\n🎉 SUCCESS: Dashboard build complete!")
        print(f"🌐 Backend: cd dashboard/backend && python app.py")
        print(f"🌐 Frontend: Open dashboard/frontend/index.html")
    else:
        print(f"\n⚠️  Some tasks failed. Check results in ./dashboard_output/")

    print(f"\n📄 Full results saved to: ./dashboard_output/")
    print(f"📊 Quality metrics will be available after completion")

    return results


if __name__ == "__main__":
    print("🎨 Dashboard Development - GenericOrchestrator Pattern")
    print("=" * 60)
    print()

    asyncio.run(main())
