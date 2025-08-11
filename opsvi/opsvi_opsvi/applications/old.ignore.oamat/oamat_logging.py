from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class WorkflowNode:
    """Represents a node in the workflow tree visualization"""

    id: str
    name: str
    agent_role: str
    status: str  # pending, in_progress, completed, failed
    subdivision_status: Optional[str] = None  # none, checking, subdivided, atomic
    sub_nodes: List["WorkflowNode"] = None
    depth: int = 0
    parent_id: Optional[str] = None

    def __post_init__(self):
        if self.sub_nodes is None:
            self.sub_nodes = []


class UserLogger:
    """
    Clean, user-friendly logging interface that shows workflow execution
    as visual tree structures while preserving debug details in files.
    """

    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.workflow_tree: Dict[str, WorkflowNode] = {}
        self.current_depth = 0
        self.indent_chars = "  "  # Two spaces per level

        # Status symbols
        self.symbols = {
            "pending": "⏳",
            "in_progress": "🔄",
            "completed": "✅",
            "failed": "❌",
            "subdivision_checking": "🧠",
            "subdivision_subdivided": "🌳",
            "subdivision_atomic": "⚡",
        }

        # Console colors (for visual hierarchy)
        self.colors = {
            "reset": "\033[0m",
            "bold": "\033[1m",
            "dim": "\033[2m",
            "green": "\033[32m",
            "blue": "\033[34m",
            "yellow": "\033[33m",
            "red": "\033[31m",
            "cyan": "\033[36m",
        }

    def start_workflow(self, user_request: str, workflow_plan: Any):
        """Initialize workflow tracking and display start banner"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        print(
            f"\n{self.colors['bold']}{self.colors['blue']}{'=' * 80}{self.colors['reset']}"
        )
        print(
            f"{self.colors['bold']}🚀 OAMAT Workflow Started{self.colors['reset']} [{timestamp}]"
        )
        print(
            f"{self.colors['bold']}{self.colors['blue']}{'=' * 80}{self.colors['reset']}"
        )
        print(f"\n📋 {self.colors['bold']}Request:{self.colors['reset']} {user_request}")

        if hasattr(workflow_plan, "nodes"):
            print(
                f"🎯 {self.colors['bold']}Planned Nodes:{self.colors['reset']} {len(workflow_plan.nodes)}"
            )

            # Initialize workflow tree
            for node in workflow_plan.nodes:
                workflow_node = WorkflowNode(
                    id=node.id,
                    name=getattr(node, "name", node.id),
                    agent_role=node.agent_role,
                    status="pending",
                    depth=0,
                )
                self.workflow_tree[node.id] = workflow_node

            self._display_workflow_tree()
        print()

    def start_node_execution(self, node_id: str, agent_role: str, depth: int = 0):
        """Mark a node as starting execution"""
        if node_id in self.workflow_tree:
            self.workflow_tree[node_id].status = "in_progress"
            self.workflow_tree[node_id].depth = depth
        else:
            # Create new node for sub-workflows
            self.workflow_tree[node_id] = WorkflowNode(
                id=node_id,
                name=node_id,
                agent_role=agent_role,
                status="in_progress",
                depth=depth,
            )

        indent = self.indent_chars * depth
        timestamp = datetime.now().strftime("%H:%M:%S")

        print(
            f"{indent}🔄 {self.colors['bold']}{agent_role}{self.colors['reset']} starting... [{timestamp}]"
        )

    def log_subdivision_check(
        self, node_id: str, requires_subdivision: bool, reasoning: str = ""
    ):
        """Log subdivision decision with reasoning"""
        if node_id in self.workflow_tree:
            node = self.workflow_tree[node_id]
            indent = self.indent_chars * node.depth

            if requires_subdivision:
                node.subdivision_status = "subdivided"
                symbol = self.symbols["subdivision_subdivided"]
                status_text = (
                    f"{self.colors['yellow']}will be subdivided{self.colors['reset']}"
                )
            else:
                node.subdivision_status = "atomic"
                symbol = self.symbols["subdivision_atomic"]
                status_text = (
                    f"{self.colors['green']}executing atomically{self.colors['reset']}"
                )

            print(
                f"{indent}  {symbol} {self.colors['cyan']}Subdivision:{self.colors['reset']} {status_text}"
            )

            if reasoning and self.debug_mode:
                print(
                    f"{indent}     {self.colors['dim']}Reasoning: {reasoning}{self.colors['reset']}"
                )

    def start_sub_workflow(self, parent_node_id: str, sub_workflow_plan: Any):
        """Start a sub-workflow with visual nesting"""
        parent_node = self.workflow_tree.get(parent_node_id)
        parent_depth = parent_node.depth if parent_node else 0
        sub_depth = parent_depth + 1

        indent = self.indent_chars * parent_depth
        print(
            f"{indent}  🌳 {self.colors['yellow']}Creating sub-workflow...{self.colors['reset']}"
        )

        if hasattr(sub_workflow_plan, "nodes"):
            sub_indent = self.indent_chars * sub_depth
            print(
                f"{sub_indent}{self.colors['dim']}Sub-nodes: {len(sub_workflow_plan.nodes)}{self.colors['reset']}"
            )

            # Add sub-nodes to the tree
            for node in sub_workflow_plan.nodes:
                sub_node = WorkflowNode(
                    id=node.id,
                    name=getattr(node, "name", node.id),
                    agent_role=node.agent_role,
                    status="pending",
                    depth=sub_depth,
                    parent_id=parent_node_id,
                )
                self.workflow_tree[node.id] = sub_node

                if parent_node:
                    parent_node.sub_nodes.append(sub_node)

    def complete_node(
        self, node_id: str, success: bool = True, execution_type: str = "standard"
    ):
        """Mark a node as completed"""
        if node_id in self.workflow_tree:
            node = self.workflow_tree[node_id]
            node.status = "completed" if success else "failed"

            indent = self.indent_chars * node.depth
            symbol = self.symbols["completed"] if success else self.symbols["failed"]

            type_indicator = ""
            if execution_type == "atomic":
                type_indicator = f" {self.colors['dim']}(atomic){self.colors['reset']}"
            elif execution_type == "subdivided":
                type_indicator = (
                    f" {self.colors['dim']}(subdivided){self.colors['reset']}"
                )

            timestamp = datetime.now().strftime("%H:%M:%S")
            print(
                f"{indent}{symbol} {self.colors['bold']}{node.agent_role}{self.colors['reset']} completed{type_indicator} [{timestamp}]"
            )

    def show_progress_summary(self):
        """Display current progress summary"""
        total = len(self.workflow_tree)
        completed = len(
            [node for node in self.workflow_tree.values() if node.status == "completed"]
        )
        in_progress = len(
            [
                node
                for node in self.workflow_tree.values()
                if node.status == "in_progress"
            ]
        )
        failed = len(
            [node for node in self.workflow_tree.values() if node.status == "failed"]
        )

        print(f"\n📊 {self.colors['bold']}Progress Summary:{self.colors['reset']}")
        print(
            f"   Total: {total} | Completed: {self.colors['green']}{completed}{self.colors['reset']} | In Progress: {self.colors['yellow']}{in_progress}{self.colors['reset']} | Failed: {self.colors['red']}{failed}{self.colors['reset']}"
        )

    def start_model_call(self, model: str, purpose: str, agent: str = ""):
        """Log the start of a model call with user-friendly message"""
        agent_prefix = f"{agent} " if agent else ""
        print(
            f"🧠 {agent_prefix}Calling {self.colors['cyan']}{model}{self.colors['reset']} for {purpose}..."
        )

    def complete_model_call(self, model: str, duration: float, success: bool = True):
        """Log the completion of a model call"""
        status_symbol = "✅" if success else "❌"
        duration_str = (
            f"{duration:.1f}s" if duration >= 1.0 else f"{duration*1000:.0f}ms"
        )
        print(f"{status_symbol} Model call completed ({duration_str})")

    def complete_workflow(
        self, success: bool = True, total_time: str = "", error_msg: str = ""
    ):
        """Complete workflow with final banner and summary"""
        if success:
            print(
                f"\n{self.colors['bold']}{self.colors['green']}{'='*80}{self.colors['reset']}"
            )
            print(
                f"{self.colors['bold']}🎉 OAMAT Workflow Completed Successfully{self.colors['reset']} [{datetime.now().strftime('%H:%M:%S')}]"
            )
            if total_time:
                print(f"⏱️  Total Time: {total_time}")
        else:
            print(
                f"\n{self.colors['bold']}{self.colors['red']}{'='*80}{self.colors['reset']}"
            )
            print(
                f"{self.colors['bold']}❌ OAMAT Workflow Failed{self.colors['reset']} [{datetime.now().strftime('%H:%M:%S')}]"
            )
            if total_time:
                print(f"⏱️  Total Time: {total_time}")
            if error_msg:
                print(f"💥 Error: {error_msg}")

        self.show_progress_summary()
        print(
            f"{self.colors['bold']}{self.colors['green'] if success else self.colors['red']}{'='*80}{self.colors['reset']}"
        )
        print()  # Add spacing

    def _display_workflow_tree(self):
        """Display the current workflow tree structure"""
        print(f"\n📋 {self.colors['bold']}Workflow Structure:{self.colors['reset']}")

        # Find root nodes (no parent)
        root_nodes = [
            node for node in self.workflow_tree.values() if node.parent_id is None
        ]

        for node in root_nodes:
            self._display_node_recursive(node, 0)
        print()

    def _display_node_recursive(self, node: WorkflowNode, depth: int):
        """Recursively display a node and its sub-nodes"""
        indent = self.indent_chars * depth
        symbol = self.symbols.get(node.status, "⏳")

        subdivision_indicator = ""
        if node.subdivision_status:
            subdivision_indicator = (
                f" {self.symbols.get(f'subdivision_{node.subdivision_status}', '')}"
            )

        print(f"{indent}{symbol} {node.agent_role}{subdivision_indicator}")

        # Display sub-nodes
        for sub_node in node.sub_nodes:
            self._display_node_recursive(sub_node, depth + 1)


def setup_logging(console_level=logging.INFO, file_level=logging.DEBUG):
    """Enhanced logging setup for OAMAT with readable console output"""

    # Create logs directory under projects for visibility
    log_dir = Path("projects/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamp for log files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Clear existing handlers to avoid duplicate logging
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Enhanced console logging with clean, readable format
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)

    # Conditionally set third-party log levels
    if console_level == logging.DEBUG:
        # Show all details in debug mode
        logging.getLogger("openai").setLevel(logging.INFO)
        logging.getLogger("langchain").setLevel(logging.INFO)
    else:
        # Keep normal logging levels for file output, only filter console
        # These will still log to files at DEBUG level for troubleshooting
        logging.getLogger("openai").setLevel(logging.DEBUG)
        logging.getLogger("httpx").setLevel(logging.DEBUG)
        logging.getLogger("httpcore").setLevel(logging.DEBUG)
        logging.getLogger("urllib3").setLevel(logging.DEBUG)
        logging.getLogger("requests").setLevel(logging.DEBUG)
        logging.getLogger("neo4j").setLevel(logging.WARNING)  # Keep these quieter
        logging.getLogger("langgraph").setLevel(logging.WARNING)
        logging.getLogger("langchain").setLevel(logging.WARNING)
        logging.getLogger("aiohttp").setLevel(logging.DEBUG)

    # Clean console format - no technical garbage
    console_format = "%(message)s"
    console_formatter = logging.Formatter(console_format)
    console_handler.setFormatter(console_formatter)

    # File handlers for debug logging (always detailed)
    debug_file = log_dir / f"oamat_debug_{timestamp}.log"
    debug_handler = logging.FileHandler(debug_file)
    debug_handler.setLevel(file_level)
    debug_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    debug_handler.setFormatter(debug_formatter)

    # Error file handler
    error_file = log_dir / f"oamat_errors_{timestamp}.log"
    error_handler = logging.FileHandler(error_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(debug_formatter)

    # Manager-specific file handler for o3-mini interactions
    manager_file = log_dir / f"oamat_manager_{timestamp}.log"
    manager_handler = logging.FileHandler(manager_file)
    manager_handler.setLevel(logging.INFO)
    manager_formatter = logging.Formatter("%(asctime)s - %(message)s")
    manager_handler.setFormatter(manager_formatter)

    # API-specific file handler for readable API logs
    api_file = log_dir / f"oamat_api_{timestamp}.log"
    api_handler = logging.FileHandler(api_file)
    api_handler.setLevel(logging.INFO)
    api_formatter = logging.Formatter("%(asctime)s - %(message)s")
    api_handler.setFormatter(api_formatter)

    # Configure root logger
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(debug_handler)
    root_logger.addHandler(error_handler)

    # Configure Manager logger separately
    manager_logger = logging.getLogger("oamat.manager")
    manager_logger.addHandler(manager_handler)
    manager_logger.propagate = False  # Don't propagate to root

    # Configure API logger separately
    api_logger = logging.getLogger("oamat.api")
    api_logger.addHandler(api_handler)
    api_logger.propagate = False  # Don't propagate to root

    # Only add the filter if not in debug mode
    if console_level != logging.DEBUG:
        # Custom filter to clean up console output
        class ReadableFilter(logging.Filter):
            def filter(self, record):
                # Block technical debug messages from console
                blocked_patterns = [
                    "Creating streaming response",
                    "Response retrieved:",
                    "LLM wrapper error:",
                    "Graph compilation",
                    "State update:",
                    "Tool execution:",
                    "Checkpointer",
                    "HTTP Request:",
                    "send_request_headers",
                    "send_request_body",
                    "receive_response_headers",
                    "receive_response_body",
                    "response_closed",
                    "connect_tcp",
                    "start_tls",
                    "return_value=",
                    "httpcore",
                    "httpx",
                    "_backends.sync",
                    "ssl_context=",
                    "server_hostname=",
                    "local_address=",
                    "timeout=None",
                    "socket_options=",
                    "HTTP/1.1",
                    "Content-Type",
                    "Transfer-Encoding",
                    "x-ratelimit",
                    "openai-processing",
                    "cf-cache-status",
                    "cloudflare",
                    "Set-Cookie",
                    ".started",
                    ".complete",
                    "api.openai.com",
                    # Block verbose manager agent output patterns
                    "🧠 MANAGER AGENT LLM CALL",
                    "🧠 MANAGER AGENT LLM RESPONSE",
                    "🧠 FULL MANAGER AGENT WORKFLOW RESPONSE",
                    "WORKFLOW GENERATION",
                    "PROMPT LENGTH:",
                    "SYSTEM IDENTITY:",
                    "RESPONSE TYPE:",
                    "NODES GENERATED:",
                    "STRATEGY:",
                    "=== Current Understanding ===",
                ]

                message = record.getMessage()
                return not any(pattern in message for pattern in blocked_patterns)

        console_handler.addFilter(ReadableFilter())

    return {
        "debug_file": str(debug_file),
        "error_file": str(error_file),
        "manager_file": str(manager_file),
        "api_file": str(api_file),
        "console_level": logging.getLevelName(console_level),
        "file_level": logging.getLevelName(file_level),
    }


def analyze_api_errors():
    """Analyze recent API error logs and provide summary"""
    log_dir = Path("projects/logs")

    # Find the most recent API log file
    api_files = list(log_dir.glob("oamat_api_*.log"))
    if not api_files:
        return "No API logs found"

    latest_api_file = max(api_files, key=lambda f: f.stat().st_mtime)

    try:
        with open(latest_api_file) as f:
            content = f.read()

        # Count API calls and errors
        lines = content.strip().split("\n")
        total_calls = len([line for line in lines if "OPENAI API CALL" in line])
        errors = len([line for line in lines if "ERROR" in line or "500" in line])
        successes = len([line for line in lines if "RESPONSE" in line or "200" in line])

        if total_calls > 0:
            error_rate = (
                (errors / (errors + successes)) * 100 if (errors + successes) > 0 else 0
            )

            print(f"\n📊 API Call Analysis ({latest_api_file.name})")
            print(f"   Total API calls: {total_calls}")
            print(f"   Successful: {successes}")
            print(f"   Errors: {errors}")
            print(f"   Error rate: {error_rate:.1f}%")

            if errors > 0:
                print("   ⚠️  High error rate detected!")
                print(f"   Check {latest_api_file} for details")
            else:
                print("   ✅ All API calls successful")
            print(f"   {'-'*50}")

        return f"Analysis complete. Total calls: {total_calls}, Errors: {errors}"

    except Exception as e:
        return f"Error analyzing logs: {e}"


def log_prompt_response(
    content: str,
    content_type: str,  # "prompt" or "response"
    context: str,  # Agent role, operation type, etc.
    timestamp: str,
    truncate_length: int = 200,
    debug_mode: bool = False,
):
    """
    Log prompts and responses with truncation for debug/console and full logging for API.

    Args:
        content: The prompt or response content to log
        content_type: Either "prompt" or "response"
        context: Contextual information (agent role, operation type, etc.)
        timestamp: Formatted timestamp string
        truncate_length: Maximum characters for debug/console output
        debug_mode: Whether debug mode is enabled (affects console output)
    """
    import logging

    # Get the API logger for full content logging
    api_logger = logging.getLogger("oamat.api")

    # Prepare content summary for debug/console
    if len(content) > truncate_length:
        truncated_content = content[:truncate_length] + "..."
    else:
        truncated_content = content

    # Console/debug output (only if debug mode is enabled)
    if debug_mode:
        if content_type == "prompt":
            print(
                f"[{timestamp}] 🚀 DEBUG: {context} prompt preview: {truncated_content}"
            )
        elif content_type == "response":
            print(
                f"[{timestamp}] 📋 DEBUG: {context} response preview: {truncated_content}"
            )

    # Full content to API logger
    api_log_entry = f"""
========================================
🔍 {content_type.upper()} LOG - {context}
========================================
TIMESTAMP: {timestamp}
CONTENT_TYPE: {content_type}
CONTEXT: {context}
CONTENT_LENGTH: {len(content)} characters
CONTENT:
{content}
========================================
"""
    api_logger.info(api_log_entry)
