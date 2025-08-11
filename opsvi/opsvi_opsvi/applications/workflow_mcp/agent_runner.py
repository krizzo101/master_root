import datetime
import os
from typing import Any

# Use SharedLogger for unified logging
from src.shared.logging.shared_logger import SharedLogger

# Compliant with 953-openai-api-standards: use shared interface, not raw SDK
try:
    from src.shared.openai_interfaces.responses_interface import (
        OpenAIResponsesInterface,
    )

    openai_interface_available = True
except ImportError:
    openai_interface_available = False

logger = SharedLogger(
    name="workflow_mcp_agent_runner",
    level=os.getenv("LOG_LEVEL", "INFO"),
)


class EmbeddedAgentRunner:
    """
    Embedded agent execution logic for workflows.
    - Uses OpenAIResponsesInterface (shared) for all OpenAI API access (per 953-openai-api-standards).
    - If unavailable, simulates execution by echoing input and workflow spec.
    - Set OPENAI_MODEL env var to select model (default: gpt-4.1).
    """

    def __init__(self):
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1")
        self.api_key = os.getenv("OPENAI_API_KEY")
        if openai_interface_available and self.api_key:
            self.openai = OpenAIResponsesInterface(api_key=self.api_key)
            self.openai_model = self.model  # Store for use in method calls if needed
            logger.debug(f"OpenAI interface initialized with model: {self.model}")
        else:
            self.openai = None
            logger.debug(
                "OpenAI interface not available or API key missing. Using fallback."
            )

    def run_workflow(self, workflow_spec: Any, input_data: Any):
        now = datetime.datetime.utcnow().isoformat()
        logs = []
        logger.debug(
            f"run_workflow called with workflow_spec={workflow_spec}, input_data={input_data}"
        )
        if self.openai:
            try:
                prompt = self._build_prompt(workflow_spec, input_data)
                logger.debug(f"LLM prompt built: {prompt}")
                logs.append(
                    {
                        "timestamp": now,
                        "event": "llm_prompt_built",
                        "prompt": prompt,
                    }
                )
                # Use the shared interface for chat/completion
                logger.debug("Calling OpenAI API via OpenAIResponsesInterface...")
                response = self.openai.chat(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a workflow execution agent.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )
                result_text = response["choices"][0]["message"]["content"].strip()
                logger.debug(f"LLM response received: {result_text}")
                logs.append(
                    {
                        "timestamp": now,
                        "event": "llm_response_received",
                        "result": result_text,
                    }
                )
                return {
                    "status": "complete",
                    "result": {"llm_output": result_text},
                    "logs": logs,
                }
            except Exception as e:
                logger.error(f"LLM error: {e}")
                logs.append(
                    {
                        "timestamp": now,
                        "event": "llm_error",
                        "error": str(e),
                    }
                )
                return {
                    "status": "failed",
                    "result": {"error": str(e)},
                    "logs": logs,
                }
        logger.debug("No LLM available, echo fallback used.")
        logs.extend(
            [
                {
                    "timestamp": now,
                    "event": "workflow_execution_started",
                    "input": input_data,
                    "workflow_spec": workflow_spec,
                },
                {
                    "timestamp": now,
                    "event": "workflow_execution_completed",
                    "result": {"echo": input_data, "spec": workflow_spec},
                },
            ]
        )
        return {
            "status": "complete",
            "result": {"echo": input_data, "spec": workflow_spec},
            "logs": logs,
        }

    def _build_prompt(self, workflow_spec, input_data):
        logger.debug("Building LLM prompt for workflow execution.")
        return f"""
You are an expert workflow execution agent. Here is the workflow spec:
{workflow_spec}

Here is the input:
{input_data}

Please execute the workflow step by step and return the result as structured JSON.
"""
