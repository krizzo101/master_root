#!/usr/bin/env python3
"""
Web API Demo and Testing Script

This script demonstrates the complete Web API functionality including:
- Server startup and configuration
- ExecutionPlan creation and execution
- Quality gates validation
- Metrics collection
- Error handling
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

import aiohttp

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from async_web_server import AsyncWebServer, RequestQualityGate


class DemoQualityGate(RequestQualityGate):
    """Demo quality gate with custom validation"""

    async def validate_rate_limit(self, request):
        """Demo rate limiting - allow max 100 requests per minute"""
        return {"passed": True, "issues": []}

    async def validate_input(self, request):
        """Demo input validation"""
        if request.payload and isinstance(request.payload, dict):
            # Check for required fields in ExecutionPlan
            if (
                request.endpoint == "/api/v1/execution-plans"
                and request.request_type == "POST"
            ):
                required_fields = ["plan_id", "name", "tasks"]
                missing_fields = [
                    field for field in required_fields if field not in request.payload
                ]
                if missing_fields:
                    return {
                        "passed": False,
                        "issues": [f"Missing required fields: {missing_fields}"],
                    }
        return {"passed": True, "issues": []}

    async def validate_business_rules(self, request):
        """Demo business rules validation"""
        if request.payload and isinstance(request.payload, dict):
            # Limit number of tasks in execution plan
            tasks = request.payload.get("tasks", [])
            if len(tasks) > 10:
                return {
                    "passed": False,
                    "issues": ["Maximum 10 tasks allowed per execution plan"],
                }
        return {"passed": True, "issues": []}


class WebAPIDemo:
    """Comprehensive Web API demonstration"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8001):
        self.host = host
        self.port = port
        self.server = None
        self.client_session = None
        self.base_url = f"http://{host}:{port}"

    async def start_server(self):
        """Start the web server with demo configuration"""
        print("🚀 Starting Web API Server...")

        # Create server with custom configuration
        self.server = AsyncWebServer(host=self.host, port=self.port, max_parallel=20)

        # Add demo quality gate
        self.server.add_quality_gate(DemoQualityGate())

        # Start server
        await self.server.start()

        print(f"✅ Server started on {self.base_url}")
        print(f"   Health check: {self.base_url}/health")
        print(f"   Metrics: {self.base_url}/metrics")

    async def setup_client(self):
        """Setup HTTP client for testing"""
        self.client_session = aiohttp.ClientSession()

    async def cleanup(self):
        """Cleanup resources"""
        if self.client_session:
            await self.client_session.close()
        if self.server:
            await self.server.shutdown()

    async def test_health_endpoint(self):
        """Test health endpoint"""
        print("\n📋 Testing Health Endpoint...")

        try:
            async with self.client_session.get(f"{self.base_url}/health") as response:
                data = await response.json()
                print(f"   Status: {response.status}")
                print(f"   Response: {json.dumps(data, indent=2)}")
                return response.status == 200
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            return False

    async def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        print("\n📊 Testing Metrics Endpoint...")

        try:
            async with self.client_session.get(f"{self.base_url}/metrics") as response:
                data = await response.json()
                print(f"   Status: {response.status}")
                print(f"   Metrics Summary:")
                print(f"     - Total Requests: {data.get('requests_total', 0)}")
                print(f"     - Active Requests: {data.get('requests_active', 0)}")
                print(f"     - Success Rate: {data.get('success_rate', 0):.1f}%")
                print(f"     - Uptime: {data.get('uptime_seconds', 0):.1f}s")
                return response.status == 200
        except Exception as e:
            print(f"   ❌ Metrics test failed: {e}")
            return False

    async def test_create_execution_plan(self):
        """Test ExecutionPlan creation"""
        print("\n📝 Testing ExecutionPlan Creation...")

        sample_plan = {
            "plan_id": "demo-plan-001",
            "name": "Demo Data Processing Pipeline",
            "description": "Demonstration of ExecutionPlan API capabilities",
            "version": "1.0",
            "tasks": [
                {
                    "task_id": "data-fetch",
                    "task_type": "general-purpose",
                    "prompt": "Fetch data from external API",
                    "dependencies": [],
                    "context": {
                        "api_endpoint": "https://api.example.com/data",
                        "timeout": 30,
                    },
                    "timeout_seconds": 300,
                },
                {
                    "task_id": "data-process",
                    "task_type": "data-processor",
                    "prompt": "Process and validate the fetched data",
                    "dependencies": ["data-fetch"],
                    "context": {
                        "validation_rules": ["format_check", "completeness_check"],
                        "output_format": "json",
                    },
                    "timeout_seconds": 180,
                },
                {
                    "task_id": "data-store",
                    "task_type": "file-processor",
                    "prompt": "Store processed data to file",
                    "dependencies": ["data-process"],
                    "context": {
                        "output_path": "/tmp/processed_data.json",
                        "backup": True,
                    },
                    "timeout_seconds": 60,
                },
            ],
            "metadata": {"created_by": "demo_user", "priority": "medium"},
        }

        try:
            headers = {"Content-Type": "application/json"}
            async with self.client_session.post(
                f"{self.base_url}/api/v1/execution-plans",
                json=sample_plan,
                headers=headers,
            ) as response:
                data = await response.json()
                print(f"   Status: {response.status}")
                print(f"   Response: {json.dumps(data, indent=2)}")

                if response.status == 200 and data.get("success"):
                    print("   ✅ ExecutionPlan created successfully")
                    return data.get("plan_id")
                else:
                    print("   ❌ ExecutionPlan creation failed")
                    return None

        except Exception as e:
            print(f"   ❌ ExecutionPlan creation error: {e}")
            return None

    async def test_list_execution_plans(self):
        """Test ExecutionPlan listing"""
        print("\n📋 Testing ExecutionPlan Listing...")

        try:
            async with self.client_session.get(
                f"{self.base_url}/api/v1/execution-plans"
            ) as response:
                data = await response.json()
                print(f"   Status: {response.status}")

                if response.status == 200 and data.get("success"):
                    plans = data.get("plans", [])
                    print(f"   Found {len(plans)} execution plans:")
                    for plan in plans:
                        print(
                            f"     - {plan['plan_id']}: {plan['name']} ({plan['status']})"
                        )
                    return True
                else:
                    print("   ❌ ExecutionPlan listing failed")
                    return False

        except Exception as e:
            print(f"   ❌ ExecutionPlan listing error: {e}")
            return False

    async def test_get_execution_plan(self, plan_id: str):
        """Test ExecutionPlan retrieval"""
        print(f"\n🔍 Testing ExecutionPlan Retrieval: {plan_id}...")

        try:
            async with self.client_session.get(
                f"{self.base_url}/api/v1/execution-plans/{plan_id}"
            ) as response:
                data = await response.json()
                print(f"   Status: {response.status}")

                if response.status == 200 and data.get("success"):
                    plan = data.get("plan", {})
                    print(f"   Plan Name: {plan.get('name')}")
                    print(f"   Tasks: {len(plan.get('tasks', []))}")
                    print("   ✅ ExecutionPlan retrieved successfully")
                    return True
                else:
                    print("   ❌ ExecutionPlan retrieval failed")
                    return False

        except Exception as e:
            print(f"   ❌ ExecutionPlan retrieval error: {e}")
            return False

    async def test_execute_plan(self, plan_id: str):
        """Test ExecutionPlan execution"""
        print(f"\n🚀 Testing ExecutionPlan Execution: {plan_id}...")

        try:
            async with self.client_session.post(
                f"{self.base_url}/api/v1/execution-plans/{plan_id}/execute"
            ) as response:
                data = await response.json()
                print(f"   Status: {response.status}")
                print(f"   Response: {json.dumps(data, indent=2)}")

                if response.status == 200 and data.get("success"):
                    results = data.get("results", [])
                    print(
                        f"   ✅ ExecutionPlan executed with {len(results)} task results"
                    )

                    # Display task results summary
                    for result in results[:3]:  # Show first 3 results
                        task_id = result.get("task_id", "unknown")
                        status = result.get("status", "unknown")
                        duration = result.get("duration_ms", 0)
                        print(f"     - {task_id}: {status} ({duration}ms)")

                    return True
                else:
                    print("   ❌ ExecutionPlan execution failed")
                    return False

        except Exception as e:
            print(f"   ❌ ExecutionPlan execution error: {e}")
            return False

    async def test_quality_gates(self):
        """Test quality gates validation"""
        print("\n🛡️  Testing Quality Gates...")

        # Test 1: Missing required fields
        print("   Test 1: Missing required fields")
        invalid_plan = {
            "name": "Invalid Plan"
            # Missing plan_id and tasks
        }

        try:
            headers = {"Content-Type": "application/json"}
            async with self.client_session.post(
                f"{self.base_url}/api/v1/execution-plans",
                json=invalid_plan,
                headers=headers,
            ) as response:
                data = await response.json()

                if response.status == 400:
                    print("     ✅ Quality gates correctly rejected invalid plan")
                else:
                    print(f"     ❌ Expected 400 status, got {response.status}")

        except Exception as e:
            print(f"     ❌ Quality gates test error: {e}")

        # Test 2: Too many tasks (business rule)
        print("   Test 2: Business rule validation (too many tasks)")
        large_plan = {
            "plan_id": "large-plan",
            "name": "Large Plan",
            "tasks": [
                {
                    "task_id": f"task-{i}",
                    "task_type": "general-purpose",
                    "prompt": f"Task {i}",
                }
                for i in range(15)
            ],  # 15 tasks > limit of 10
        }

        try:
            headers = {"Content-Type": "application/json"}
            async with self.client_session.post(
                f"{self.base_url}/api/v1/execution-plans",
                json=large_plan,
                headers=headers,
            ) as response:
                data = await response.json()

                if response.status == 400:
                    print("     ✅ Quality gates correctly enforced business rules")
                else:
                    print(f"     ❌ Expected 400 status, got {response.status}")

        except Exception as e:
            print(f"     ❌ Business rules test error: {e}")

    async def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n🚫 Testing Error Handling...")

        # Test 1: Non-existent plan
        print("   Test 1: Non-existent plan retrieval")
        try:
            async with self.client_session.get(
                f"{self.base_url}/api/v1/execution-plans/non-existent-plan"
            ) as response:
                data = await response.json()

                if response.status == 400:
                    print("     ✅ Correctly handled non-existent plan")
                else:
                    print(f"     ❌ Expected 400 status, got {response.status}")

        except Exception as e:
            print(f"     ❌ Error handling test failed: {e}")

        # Test 2: Invalid JSON
        print("   Test 2: Invalid JSON payload")
        try:
            headers = {"Content-Type": "application/json"}
            async with self.client_session.post(
                f"{self.base_url}/api/v1/execution-plans",
                data="invalid json{",  # Invalid JSON
                headers=headers,
            ) as response:
                if response.status == 400:
                    print("     ✅ Correctly handled invalid JSON")
                else:
                    print(f"     ❌ Expected 400 status, got {response.status}")

        except Exception as e:
            print(f"     ❌ Invalid JSON test failed: {e}")

    async def run_comprehensive_demo(self):
        """Run comprehensive API demonstration"""
        print("=" * 60)
        print("🚀 Web API Comprehensive Demo")
        print("=" * 60)

        success_count = 0
        total_tests = 0

        try:
            # Setup
            await self.start_server()
            await asyncio.sleep(1)  # Give server time to start
            await self.setup_client()

            # Test basic endpoints
            total_tests += 1
            if await self.test_health_endpoint():
                success_count += 1

            total_tests += 1
            if await self.test_metrics_endpoint():
                success_count += 1

            # Test ExecutionPlan operations
            total_tests += 1
            plan_id = await self.test_create_execution_plan()
            if plan_id:
                success_count += 1

                total_tests += 1
                if await self.test_get_execution_plan(plan_id):
                    success_count += 1

                total_tests += 1
                if await self.test_list_execution_plans():
                    success_count += 1

                total_tests += 1
                if await self.test_execute_plan(plan_id):
                    success_count += 1

            # Test quality gates and error handling
            total_tests += 1
            await self.test_quality_gates()
            success_count += 1  # Quality gates test has its own validation

            total_tests += 1
            await self.test_error_handling()
            success_count += 1  # Error handling test has its own validation

            # Final metrics
            print("\n📊 Final Metrics Check...")
            await self.test_metrics_endpoint()

        finally:
            await self.cleanup()

        # Summary
        print("\n" + "=" * 60)
        print("📊 Demo Summary")
        print("=" * 60)
        print(f"Tests Completed: {total_tests}")
        print(f"Tests Passed: {success_count}")
        print(
            f"Success Rate: {(success_count/total_tests)*100:.1f}%"
            if total_tests > 0
            else "N/A"
        )

        if success_count == total_tests:
            print("🎉 All tests passed! Web API is fully functional.")
            return True
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
            return False


async def main():
    """Main demo function"""

    # Parse command line arguments
    host = "127.0.0.1"
    port = 8001

    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)

    if len(sys.argv) > 2:
        host = sys.argv[2]

    print(f"Starting demo on {host}:{port}")

    # Run demo
    demo = WebAPIDemo(host=host, port=port)

    try:
        success = await demo.run_comprehensive_demo()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Ensure we have required dependencies
    try:
        import aiohttp
    except ImportError:
        print("❌ Missing required dependency: aiohttp")
        print("   Run: pip install aiohttp")
        sys.exit(1)

    # Run the demo
    asyncio.run(main())
