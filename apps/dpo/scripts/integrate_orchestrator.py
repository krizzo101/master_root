#!/usr/bin/env python3
"""
Integration script for connecting DPO with the existing agent-orchestrator system.

This script establishes the necessary connections and configurations to enable
seamless integration between DPO and the master_root ecosystem.
"""

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_orchestrator_installation() -> bool:
    """Check if agent-orchestrator is installed and accessible."""
    orchestrator_path = Path("/home/opsvi/master_root/apps/agent-orchestrator")

    if not orchestrator_path.exists():
        print("❌ Agent-orchestrator not found at expected location")
        return False

    # Check for key files
    required_files = [
        "src/generic_orchestrator.py",
        "src/websocket_server.py",
        "src/agent_factory.py",
    ]

    for file in required_files:
        if not (orchestrator_path / file).exists():
            print(f"❌ Missing required file: {file}")
            return False

    print("✅ Agent-orchestrator found and verified")
    return True


def create_integration_config() -> Dict[str, Any]:
    """Create integration configuration for DPO-Orchestrator connection."""
    config = {
        "integration": {
            "orchestrator": {
                "base_path": "/home/opsvi/master_root/apps/agent-orchestrator",
                "python_path": "/home/opsvi/miniconda/bin/python",
                "websocket_url": "ws://localhost:8765",
                "message_bus_url": "ws://localhost:8767",
                "enabled": True,
            },
            "knowledge_base": {
                "enabled": True,
                "mcp_server": "knowledge",
                "storage_path": "~/.dpo/knowledge",
            },
            "session_optimizer": {
                "enabled": True,
                "base_path": "/home/opsvi/master_root/apps/session-optimizer",
                "optimization_threshold": 0.7,
            },
            "mcp_tools": {
                "enabled": True,
                "servers": [
                    "firecrawl",
                    "web_search",
                    "tech_docs",
                    "time",
                    "thinking",
                    "knowledge",
                    "shell_exec",
                ],
            },
        },
        "agent_mappings": {
            "requirements_analyst": "requirements_analysis_agent",
            "system_architect": "system_design_agent",
            "backend_developer": "backend_development_agent",
            "frontend_developer": "frontend_development_agent",
            "database_designer": "database_design_agent",
            "test_engineer": "testing_specialist_agent",
            "qa_specialist": "quality_assurance_agent",
            "devops_engineer": "devops_specialist_agent",
            "technical_writer": "documentation_specialist_agent",
            "api_specialist": "api_development_agent",
            "ui_specialist": "ui_ux_specialist_agent",
            "integration_specialist": "integration_testing_agent",
            "performance_tester": "performance_optimization_agent",
            "security_specialist": "security_specialist_agent",
            "cloud_specialist": "cloud_deployment_agent",
        },
        "shared_resources": {
            "output_directory": "/home/opsvi/master_root/apps/agent-orchestrator/output",
            "checkpoint_directory": "/home/opsvi/master_root/apps/agent-orchestrator/checkpoints",
            "logs_directory": "/home/opsvi/master_root/apps/agent-orchestrator/logs",
            "templates_directory": "/home/opsvi/master_root/apps/agent-orchestrator/templates",
        },
    }

    return config


def setup_symbolic_links():
    """Create symbolic links for shared resources."""
    dpo_home = Path.home() / ".dpo"
    orchestrator_path = Path("/home/opsvi/master_root/apps/agent-orchestrator")

    links = [
        (orchestrator_path / "src", dpo_home / "orchestrator_src"),
        (orchestrator_path / "templates", dpo_home / "shared_templates"),
        (orchestrator_path / "output", dpo_home / "shared_output"),
    ]

    for source, target in links:
        if source.exists() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(source)
            print(f"✅ Created symlink: {target} -> {source}")


def update_python_path():
    """Update Python path to include necessary modules."""
    paths_to_add = [
        "/home/opsvi/master_root/apps/agent-orchestrator/src",
        "/home/opsvi/master_root/apps/dpo/src",
        "/home/opsvi/master_root/.claude/knowledge/scripts",
    ]

    pythonpath = os.environ.get("PYTHONPATH", "")
    new_paths = []

    for path in paths_to_add:
        if Path(path).exists() and path not in pythonpath:
            new_paths.append(path)

    if new_paths:
        os.environ["PYTHONPATH"] = ":".join(new_paths + [pythonpath])
        print(f"✅ Updated PYTHONPATH with {len(new_paths)} paths")


def verify_mcp_integration():
    """Verify MCP server integration."""
    mcp_config_path = Path.home() / ".mcp.json"

    if not mcp_config_path.exists():
        print("⚠️  MCP configuration not found. Some features may be limited.")
        return False

    try:
        with open(mcp_config_path) as f:
            mcp_config = json.load(f)

        servers = mcp_config.get("servers", {})
        required_servers = ["knowledge", "shell_exec", "web_search"]

        missing = [s for s in required_servers if s not in servers]
        if missing:
            print(f"⚠️  Missing MCP servers: {', '.join(missing)}")
            return False

        print("✅ MCP integration verified")
        return True
    except Exception as e:
        print(f"❌ Error verifying MCP: {e}")
        return False


def create_integration_wrapper():
    """Create a wrapper script for seamless integration."""
    wrapper_content = '''#!/usr/bin/env python3
"""
DPO-Orchestrator Integration Wrapper

This wrapper ensures proper environment setup and communication between
DPO and the agent-orchestrator system.
"""

import sys
import os
from pathlib import Path

# Setup paths
DPO_HOME = Path.home() / ".dpo"
ORCHESTRATOR_PATH = Path("/home/opsvi/master_root/apps/agent-orchestrator")

# Add to Python path
sys.path.insert(0, str(ORCHESTRATOR_PATH / "src"))
sys.path.insert(0, str(DPO_HOME.parent / "apps/dpo/src"))

# Import and initialize
from dpo_orchestrator_integration import DPOOrchestrator
from dpo_main_controller import DPOMainController, DPOConfiguration

def main():
    # Load configuration
    config_path = DPO_HOME / "config/dpo_config.json"
    if config_path.exists():
        config = DPOConfiguration.from_file(str(config_path))
    else:
        config = DPOConfiguration()

    # Initialize controller with orchestrator integration
    controller = DPOMainController(config)
    orchestrator = DPOOrchestrator(config)

    # Connect components
    controller.set_orchestrator(orchestrator)

    print("✅ DPO-Orchestrator integration initialized")
    return controller, orchestrator

if __name__ == "__main__":
    controller, orchestrator = main()
'''

    wrapper_path = Path.home() / ".dpo/bin/dpo_integrate.py"
    wrapper_path.parent.mkdir(parents=True, exist_ok=True)
    wrapper_path.write_text(wrapper_content)
    wrapper_path.chmod(0o755)

    print(f"✅ Created integration wrapper: {wrapper_path}")


def test_integration():
    """Test the integration by attempting to import and initialize components."""
    try:
        # Test orchestrator import
        sys.path.insert(0, "/home/opsvi/master_root/apps/agent-orchestrator/src")
        from generic_orchestrator import GenericOrchestrator

        print("✅ Successfully imported GenericOrchestrator")

        # Test DPO import
        sys.path.insert(0, "/home/opsvi/master_root/apps/dpo/src")
        from dpo_main_controller import DPOMainController

        print("✅ Successfully imported DPOMainController")

        # Test initialization
        config = {"output_base_dir": "/tmp/dpo_test"}
        controller = DPOMainController(config)
        print("✅ Successfully initialized DPO controller")

        return True
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


def main():
    """Main integration setup process."""
    print("=" * 60)
    print("  DPO-Orchestrator Integration Setup")
    print("=" * 60)
    print()

    # Step 1: Check orchestrator
    if not check_orchestrator_installation():
        print("\n⚠️  Please install agent-orchestrator first")
        return 1

    # Step 2: Create integration config
    print("\n📝 Creating integration configuration...")
    config = create_integration_config()

    config_path = Path.home() / ".dpo/config/integration.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"✅ Saved integration config to {config_path}")

    # Step 3: Setup symbolic links
    print("\n🔗 Setting up symbolic links...")
    setup_symbolic_links()

    # Step 4: Update Python path
    print("\n🐍 Updating Python path...")
    update_python_path()

    # Step 5: Verify MCP
    print("\n🔌 Verifying MCP integration...")
    verify_mcp_integration()

    # Step 6: Create wrapper
    print("\n📦 Creating integration wrapper...")
    create_integration_wrapper()

    # Step 7: Test integration
    print("\n🧪 Testing integration...")
    if test_integration():
        print("\n✅ Integration setup complete!")
        print("\nYou can now use DPO with full orchestrator integration.")
        print('Try: dpo build "Create a simple web application"')
        return 0
    else:
        print("\n⚠️  Integration setup completed with warnings")
        print("Some features may require additional configuration")
        return 1


if __name__ == "__main__":
    sys.exit(main())
