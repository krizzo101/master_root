"""
Audit Logger for Code Generation

Captures and saves research results, execution logs, and prompts
for transparency and future reference in generated projects.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AuditLogger:
    """Captures and saves audit information for generated projects."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.audit_dir = output_dir / "audit"
        self.audit_dir.mkdir(exist_ok=True)

        # Initialize audit data
        self.execution_log: List[Dict[str, Any]] = []
        self.prompts_used: List[Dict[str, Any]] = []
        self.research_results: Optional[Dict[str, Any]] = None
        self.start_time = time.time()

    def log_execution_step(
        self,
        step_name: str,
        status: str,
        message: str = "",
        error: Optional[str] = None,
        duration: Optional[float] = None,
    ):
        """Log an execution step with timing and status."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "step": step_name,
            "status": status,
            "message": message,
            "duration_seconds": duration,
        }

        if error:
            log_entry["error"] = error

        self.execution_log.append(log_entry)
        logger.info(f"[AUDIT] {step_name}: {status} - {message}")

    def log_prompt(
        self,
        agent_name: str,
        prompt_type: str,
        prompt: str,
        response: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """Log a prompt used by an AI agent."""
        timestamp = datetime.now().isoformat()
        prompt_entry = {
            "timestamp": timestamp,
            "agent": agent_name,
            "type": prompt_type,
            "prompt": prompt,
            "response": response,
            "model": model,
        }

        self.prompts_used.append(prompt_entry)
        logger.debug(f"[AUDIT] Prompt logged for {agent_name} ({prompt_type})")

    def save_research_results(self, research_topics: Any, research_insights: str):
        """Save research results for future reference."""
        self.research_results = {
            "timestamp": datetime.now().isoformat(),
            "topics": {
                "primary_technologies": (
                    research_topics.primary_technologies
                    if hasattr(research_topics, "primary_technologies")
                    else []
                ),
                "secondary_topics": (
                    research_topics.secondary_topics
                    if hasattr(research_topics, "secondary_topics")
                    else []
                ),
                "reasoning": (
                    research_topics.reasoning
                    if hasattr(research_topics, "reasoning")
                    else ""
                ),
            },
            "insights": research_insights,
        }

    def save_audit_files(self) -> List[str]:
        """Save all audit information to files and return list of created files."""
        files_created = []

        # Save execution log
        execution_log_path = self.audit_dir / "execution_log.json"
        with open(execution_log_path, "w") as f:
            json.dump(self.execution_log, f, indent=2)
        files_created.append(str(execution_log_path))

        # Save prompts
        prompts_path = self.audit_dir / "prompts_used.json"
        with open(prompts_path, "w") as f:
            json.dump(self.prompts_used, f, indent=2)
        files_created.append(str(prompts_path))

        # Save research results
        if self.research_results:
            research_path = self.audit_dir / "research_results.json"
            with open(research_path, "w") as f:
                json.dump(self.research_results, f, indent=2)
            files_created.append(str(research_path))

            # Also save as markdown for easy reading
            research_md_path = self.audit_dir / "research_results.md"
            research_md_content = self._format_research_markdown()
            research_md_path.write_text(research_md_content)
            files_created.append(str(research_md_path))

        # Save audit summary
        summary_path = self.audit_dir / "audit_summary.md"
        summary_content = self._format_audit_summary()
        summary_path.write_text(summary_content)
        files_created.append(str(summary_path))

        logger.info(f"Audit files saved: {len(files_created)} files created")
        return files_created

    def _format_research_markdown(self) -> str:
        """Format research results as markdown."""
        if not self.research_results:
            return "# Research Results\n\nNo research was performed for this project."

        content = "# Research Results\n\n"
        content += f"**Generated:** {self.research_results['timestamp']}\n\n"

        # Research topics
        content += "## Research Topics\n\n"
        topics = self.research_results["topics"]

        if topics["primary_technologies"]:
            content += "### Primary Technologies\n"
            for tech in topics["primary_technologies"]:
                content += f"- {tech}\n"
            content += "\n"

        if topics["secondary_topics"]:
            content += "### Secondary Topics\n"
            for topic in topics["secondary_topics"]:
                content += f"- {topic}\n"
            content += "\n"

        if topics["reasoning"]:
            content += f"### Reasoning\n{topics['reasoning']}\n\n"

        # Research insights
        if self.research_results["insights"]:
            content += "## Research Insights\n\n"
            content += self.research_results["insights"]
        else:
            content += "## Research Insights\n\nNo insights were generated."

        return content

    def _format_audit_summary(self) -> str:
        """Format audit summary as markdown."""
        total_duration = time.time() - self.start_time

        content = "# Code Generation Audit Summary\n\n"
        content += f"**Generated:** {datetime.now().isoformat()}\n"
        content += f"**Total Duration:** {total_duration:.2f} seconds\n\n"

        # Execution summary
        content += "## Execution Summary\n\n"
        successful_steps = [
            step for step in self.execution_log if step["status"] == "success"
        ]
        failed_steps = [
            step for step in self.execution_log if step["status"] == "failed"
        ]

        content += f"- **Total Steps:** {len(self.execution_log)}\n"
        content += f"- **Successful:** {len(successful_steps)}\n"
        content += f"- **Failed:** {len(failed_steps)}\n\n"

        # Step details
        content += "## Step Details\n\n"
        for step in self.execution_log:
            status_icon = "✅" if step["status"] == "success" else "❌"
            duration = (
                f" ({step['duration_seconds']:.2f}s)"
                if step.get("duration_seconds")
                else ""
            )
            content += (
                f"{status_icon} **{step['step']}** - {step['status']}{duration}\n"
            )
            if step.get("message"):
                content += f"  - {step['message']}\n"
            if step.get("error"):
                content += f"  - Error: {step['error']}\n"
            content += "\n"

        # AI prompts summary
        content += "## AI Prompts Used\n\n"
        content += f"- **Total Prompts:** {len(self.prompts_used)}\n"

        # Group by agent
        agents = {}
        for prompt in self.prompts_used:
            agent = prompt["agent"]
            if agent not in agents:
                agents[agent] = []
            agents[agent].append(prompt)

        for agent, prompts in agents.items():
            content += f"- **{agent}:** {len(prompts)} prompts\n"

        content += "\nSee `prompts_used.json` for detailed prompt content.\n\n"

        # Research summary
        if self.research_results:
            content += "## Research Summary\n\n"
            topics = self.research_results["topics"]
            content += (
                f"- **Primary Technologies:** {len(topics['primary_technologies'])}\n"
            )
            content += f"- **Secondary Topics:** {len(topics['secondary_topics'])}\n"
            content += f"- **Insights Generated:** {'Yes' if self.research_results['insights'] else 'No'}\n\n"
            content += "See `research_results.md` for detailed research information.\n"
        else:
            content += (
                "## Research Summary\n\nNo research was performed for this project.\n"
            )

        return content


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> Optional[AuditLogger]:
    """Get the current audit logger instance."""
    return _audit_logger


def init_audit_logger(output_dir: Path) -> AuditLogger:
    """Initialize the audit logger for a new generation job."""
    global _audit_logger
    _audit_logger = AuditLogger(output_dir)
    return _audit_logger


def log_execution_step(
    step_name: str,
    status: str,
    message: str = "",
    error: Optional[str] = None,
    duration: Optional[float] = None,
):
    """Log an execution step using the global audit logger."""
    if _audit_logger:
        _audit_logger.log_execution_step(step_name, status, message, error, duration)


def log_prompt(
    agent_name: str,
    prompt_type: str,
    prompt: str,
    response: Optional[str] = None,
    model: Optional[str] = None,
):
    """Log a prompt using the global audit logger."""
    if _audit_logger:
        _audit_logger.log_prompt(agent_name, prompt_type, prompt, response, model)
