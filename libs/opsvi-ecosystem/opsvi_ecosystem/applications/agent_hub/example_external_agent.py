#!/usr/bin/env python3
"""
Example External AI Agent
Demonstrates how another AI agent would discover and use our Agent Hub.
"""

import asyncio
from typing import Dict

import httpx


class ExternalAIAgent:
    """
    Example external AI agent that discovers and uses our Agent Hub
    """

    def __init__(self, name: str = "ExternalAgent"):
        self.name = name
        self.discovered_agents = {}
        self.agent_hub_url = None

    async def discover_agent_hub(self, base_url: str = "http://localhost:8003"):
        """Step 1: Discover agent hub capabilities"""
        print(f"🔍 [{self.name}] Discovering agents at {base_url}...")

        try:
            async with httpx.AsyncClient() as client:
                # Get agent manifest
                response = await client.get(f"{base_url}/discovery/manifest")

                if response.status_code == 200:
                    manifest = response.json()
                    self.agent_hub_url = base_url
                    self.discovered_agents[manifest["agent_id"]] = manifest

                    print(f"✅ Discovered Agent Hub: {manifest['name']}")
                    print(f"   Provider: {manifest['provider']}")
                    print(f"   Version: {manifest['version']}")
                    print(f"   Capabilities: {len(manifest['capabilities'])}")

                    return True
                else:
                    print(f"❌ Failed to discover agents: {response.status_code}")
                    return False

        except Exception as e:
            print(f"❌ Discovery failed: {e}")
            return False

    async def resolve_ans_name(self, ans_name: str):
        """Step 2: Use ANS (Agent Name Service) to resolve specific capabilities"""
        print(f"🔍 [{self.name}] Resolving ANS name: {ans_name}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.agent_hub_url}/ans/resolve/{ans_name}"
                )

                if response.status_code == 200:
                    resolution = response.json()
                    print("✅ ANS Resolution successful:")
                    print(f"   Agent ID: {resolution['agent_id']}")
                    print(f"   Verified: {resolution['verified']}")
                    return resolution
                else:
                    print(f"❌ ANS resolution failed: {response.status_code}")
                    return None

        except Exception as e:
            print(f"❌ ANS resolution error: {e}")
            return None

    async def use_agent_protocol(
        self, task_description: str, additional_params: Dict = None
    ):
        """Step 3: Use standardized Agent Protocol for communication"""
        print(f"🤖 [{self.name}] Using Agent Protocol for task: {task_description}")

        try:
            async with httpx.AsyncClient() as client:
                # Create task
                task_response = await client.post(
                    f"{self.agent_hub_url}/ap/v1/agent/tasks",
                    json={
                        "input": task_description,
                        "additional_input": additional_params or {},
                    },
                )

                if task_response.status_code != 200:
                    print(f"❌ Task creation failed: {task_response.status_code}")
                    return None

                task = task_response.json()
                task_id = task["task_id"]
                print(f"✅ Task created: {task_id}")

                # Execute step
                step_response = await client.post(
                    f"{self.agent_hub_url}/ap/v1/agent/tasks/{task_id}/steps",
                    json={"input": "execute"},
                )

                if step_response.status_code != 200:
                    print(f"❌ Step execution failed: {step_response.status_code}")
                    return None

                step = step_response.json()
                print(f"✅ Step completed: {step['status']}")
                print(f"📄 Output preview: {step['output'][:200]}...")

                return {"task": task, "step": step, "success": True}

        except Exception as e:
            print(f"❌ Agent Protocol error: {e}")
            return None

    async def use_direct_rpc(self, method: str, params: Dict):
        """Step 4: Use direct JSON-RPC for specific agent methods"""
        print(f"🎯 [{self.name}] Direct RPC call: {method}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.agent_hub_url}/rpc",
                    json={
                        "jsonrpc": "2.0",
                        "method": method,
                        "params": params,
                        "id": 1,
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    print("✅ RPC call successful")
                    print(f"📄 Result preview: {str(result.get('result', {}))[:200]}...")
                    return result
                else:
                    print(f"❌ RPC call failed: {response.status_code}")
                    return None

        except Exception as e:
            print(f"❌ RPC error: {e}")
            return None

    async def multi_agent_workflow(self, user_request: str):
        """Step 5: Orchestrate multiple agents for complex task"""
        print(f"🌐 [{self.name}] Multi-agent workflow for: {user_request}")

        results = {}

        # 1. Code Generation
        print("\n--- Phase 1: Code Generation ---")
        code_result = await self.use_agent_protocol(
            f"Generate code for: {user_request}",
            {"requirements": "production-ready, well-documented"},
        )
        results["code_generation"] = code_result

        # 2. Security Audit (if code was generated)
        if code_result and code_result.get("success"):
            print("\n--- Phase 2: Security Audit ---")
            audit_result = await self.use_direct_rpc(
                "sentinel.audit_patch",
                {
                    "diff": "# Generated code would be here",
                    "rule_ids": ["security_baseline"],
                },
            )
            results["security_audit"] = audit_result

        # 3. Knowledge Extraction
        print("\n--- Phase 3: Knowledge Extraction ---")
        knowledge_result = await self.use_direct_rpc(
            "kb_updater.digest_research", {"doc_ids": ["synthetic_doc_1"]}
        )
        results["knowledge_extraction"] = knowledge_result

        print("\n🎉 Multi-agent workflow completed!")
        return results

    async def demonstrate_full_discovery_workflow(self):
        """Complete demonstration of agent discovery and usage"""
        print(f"\n{'='*60}")
        print(f"🚀 [{self.name}] Starting Agent Discovery Workflow")
        print(f"{'='*60}")

        # Step 1: Discover Agent Hub
        discovered = await self.discover_agent_hub()
        if not discovered:
            print("❌ Cannot proceed without discovering agents")
            return

        # Step 2: Test ANS Resolution
        print(f"\n{'-'*40}")
        print("Step 2: Testing ANS Resolution")
        print(f"{'-'*40}")

        ans_names = [
            "agent-protocol://codeGeneration.AgentHub.v1.0",
            "agent-protocol://securityAudit.AgentHub.v1.0",
            "agent-protocol://knowledgeExtraction.AgentHub.v1.0",
        ]

        for ans_name in ans_names:
            await self.resolve_ans_name(ans_name)
            await asyncio.sleep(0.5)  # Be nice to the server

        # Step 3: Test Agent Protocol
        print(f"\n{'-'*40}")
        print("Step 3: Testing Agent Protocol")
        print(f"{'-'*40}")

        await self.use_agent_protocol(
            "Create a simple REST API for user management",
            {"requirements": "FastAPI, basic CRUD operations"},
        )

        # Step 4: Test Direct RPC
        print(f"\n{'-'*40}")
        print("Step 4: Testing Direct RPC")
        print(f"{'-'*40}")

        await self.use_direct_rpc(
            "quality_curator.vector_healthcheck",
            {"collection": "research_docs", "threshold": 0.8},
        )

        # Step 5: Multi-Agent Workflow
        print(f"\n{'-'*40}")
        print("Step 5: Multi-Agent Workflow")
        print(f"{'-'*40}")

        await self.multi_agent_workflow("user authentication system")

        print(f"\n{'='*60}")
        print(f"✅ [{self.name}] Discovery Workflow Complete!")
        print(f"{'='*60}")


async def main():
    """Run the external agent demonstration"""

    # Create external agent
    external_agent = ExternalAIAgent("DemoExternalAgent")

    # Run full demonstration
    await external_agent.demonstrate_full_discovery_workflow()

    print("\n📋 Summary:")
    print("   ✅ Agent discovery via service manifest")
    print("   ✅ ANS (Agent Name Service) resolution")
    print("   ✅ Agent Protocol communication")
    print("   ✅ Direct JSON-RPC calls")
    print("   ✅ Multi-agent workflow orchestration")
    print("\n🎯 This demonstrates how any AI agent can:")
    print("   • Discover our agent hub automatically")
    print("   • Choose appropriate communication protocols")
    print("   • Leverage multiple specialized agents")
    print("   • Orchestrate complex multi-step workflows")


if __name__ == "__main__":
    asyncio.run(main())
