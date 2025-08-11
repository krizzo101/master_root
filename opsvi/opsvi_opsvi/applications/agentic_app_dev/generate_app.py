import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
import dataclasses
import json
import logging
from pathlib import Path
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple, Union

from src.applications.agentic_app_dev.prompt_schema import AgentPromptSchema
from src.shared.openai_interfaces.responses_interface import OpenAIResponsesInterface
from src.tools.config import (
    MODEL_MAP,
    VALIDATION_TOOLS,
)

# --- Logging Setup ---
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "generate_app_debug.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("generate_app")

# --- Checkpoint Utilities ---
CHECKPOINT_FILE = Path(".generate_app_checkpoint.json")


@dataclasses.dataclass
class ArtifactResult:
    fname: str
    out_path: Union[str, Path]
    audit: list


def _to_json_safe(obj: Any) -> Any:
    """
    Recursively convert objects to JSON-serializable forms.
    Handles dict, list, tuple, set, frozenset, Path, dataclasses, and custom objects.
    Fallback: str(obj) for unknown types.
    """
    import dataclasses
    import json
    from pathlib import Path

    if isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set, frozenset)):
        return [_to_json_safe(v) for v in obj]
    elif isinstance(obj, Path):
        return str(obj)
    elif dataclasses.is_dataclass(obj):
        return _to_json_safe(dataclasses.asdict(obj))
    elif hasattr(obj, "__dict__"):
        return _to_json_safe(vars(obj))
    else:
        try:
            json.dumps(obj)
            return obj
        except Exception:
            return str(obj)


def save_checkpoint(stage: str, data: Dict[str, Any]) -> None:
    """
    Save the current pipeline stage and data to a checkpoint file.
    All data is converted to JSON-serializable form.
    """
    checkpoint = {"stage": stage, "data": data}
    # Convert AgentPromptSchema to dict if present
    if "agent_prompt" in checkpoint["data"] and hasattr(
        checkpoint["data"]["agent_prompt"], "__dataclass_fields__"
    ):
        checkpoint["data"]["agent_prompt"] = dataclasses.asdict(
            checkpoint["data"]["agent_prompt"]
        )
    checkpoint = _to_json_safe(checkpoint)
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)
    logger.debug(f"Checkpoint saved at stage: {stage}")


def load_checkpoint() -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Load the last saved checkpoint, if it exists.
    Returns (stage, data) or (None, None) if no checkpoint exists.
    """
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, encoding="utf-8") as f:
            checkpoint = json.load(f)
        logger.debug(f"Checkpoint loaded: {checkpoint['stage']}")
        # Reconstruct AgentPromptSchema if present
        if "agent_prompt" in checkpoint["data"]:
            from src.applications.agentic_app_dev.prompt_schema import AgentPromptSchema

            checkpoint["data"]["agent_prompt"] = AgentPromptSchema(
                **checkpoint["data"]["agent_prompt"]
            )
        return checkpoint["stage"], checkpoint["data"]
    return None, None


def clear_checkpoint() -> None:
    """
    Delete the checkpoint file if it exists.
    """
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()
        logger.debug("Checkpoint cleared.")


# --- Prompt Templates ---
PROMPT_TEMPLATES = {
    "analyst": "You are a requirements analyst. Given the following user prompt, extract and formalize the requirements in a clear, bullet-pointed markdown document.\n\nUser Prompt:\n{user_prompt}\n\n# Requirements\n",
    "design": "You are a software architect. Given the following requirements, produce a high-level design document in markdown.\n\n# Requirements\n{requirements_doc}\n\n# Design\n",
    "spec": "You are a technical writer. Given the following requirements and design, produce a detailed technical specification in markdown.\n\n# Requirements\n{requirements_doc}\n\n# Design\n{design_doc}\n\n# Technical Specification\n",
    "promptgen": "You are a prompt engineer. Given the following requirements, design, and technical specification, generate a highly effective prompt for a code generation LLM. The prompt should reference the docs and instruct the LLM to produce only the required code or documentation, with no extra explanation.\n\n# Requirements\n{requirements_doc}\n\n# Design\n{design_doc}\n\n# Technical Specification\n{spec_doc}\n\n# Prompt\n",
    "code": "You are a Python developer. Given the requirements, design, and spec, generate the main application code file.\n\n# Requirements\n{requirements_doc}\n# Design\n{design_doc}\n# Spec\n{spec_doc}\n# Code\n",
    "doc": "You are a documentation writer. Given the requirements, design, and spec, generate a clear, well-structured markdown document.\n\n# Requirements\n{requirements_doc}\n# Design\n{design_doc}\n# Spec\n{spec_doc}\n# Documentation\n",
    "config": "You are a config generator. Given the requirements, design, and spec, generate a config file (YAML, JSON, or INI) for the application.\n\n# Requirements\n{requirements_doc}\n# Design\n{design_doc}\n# Spec\n{spec_doc}\n# Config\n",
    "diagram": "You are a diagram generator. Given the requirements, design, and spec, generate a Mermaid or ASCII diagram (markdown code block) that illustrates the architecture or workflow.\n\n# Requirements\n{requirements_doc}\n# Design\n{design_doc}\n# Spec\n{spec_doc}\n# Diagram\n",
    "unit_test": "You are a unit test generator. Given the requirements, design, and spec, generate a Python unittest or pytest file that tests the main code artifact.\n\n# Requirements\n{requirements_doc}\n# Design\n{design_doc}\n# Spec\n{spec_doc}\n# Unit Tests\n",
    "documentation": "You are a documentation generator. Given the requirements, design, and spec, generate comprehensive markdown documentation for the code artifact.\n\n# Requirements\n{requirements_doc}\n# Design\n{design_doc}\n# Spec\n{spec_doc}\n# Documentation\n",
}


class BaseLLMAgent:
    def __init__(self, prompt_template: str, model: str = "gpt-4.1"):
        self.llm = OpenAIResponsesInterface()
        self.prompt_template = prompt_template
        self.model = model

    def run(self, **kwargs) -> str:
        prompt = self.prompt_template.format(**kwargs)
        logger.info(
            f"[{self.__class__.__name__}] Running LLM with prompt: {prompt[:100]}..."
        )
        response = self.llm.create_response(
            model=self.model, input=prompt, text_format=None
        )
        output = response.get("output_text") or str(response)
        logger.info(f"[{self.__class__.__name__}] Output: {output[:200]}...")
        return output


class AnalystAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(PROMPT_TEMPLATES["analyst"])

    def run(self, user_prompt: str) -> str:
        return super().run(user_prompt=user_prompt)


class DesignAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(PROMPT_TEMPLATES["design"])

    def run(self, requirements_doc: str) -> str:
        return super().run(requirements_doc=requirements_doc)


class SpecAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(PROMPT_TEMPLATES["spec"])

    def run(self, requirements_doc: str, design_doc: str) -> str:
        return super().run(requirements_doc=requirements_doc, design_doc=design_doc)


class PromptGenAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(PROMPT_TEMPLATES["promptgen"])

    def run(self, requirements_doc: str, design_doc: str, spec_doc: str) -> str:
        return super().run(
            requirements_doc=requirements_doc, design_doc=design_doc, spec_doc=spec_doc
        )


class DocumentationAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(
            PROMPT_TEMPLATES.get(
                "documentation",
                "You are a documentation generator. Given the requirements, design, and spec, generate comprehensive markdown documentation for the code artifact.\n\n# Requirements\n{requirements_doc}\n# Design\n{design_doc}\n# Spec\n{spec_doc}\n# Documentation\n",
            )
        )

    def run(self, requirements_doc: str, design_doc: str, spec_doc: str) -> str:
        return super().run(
            requirements_doc=requirements_doc, design_doc=design_doc, spec_doc=spec_doc
        )


class ConfigAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(
            PROMPT_TEMPLATES.get(
                "config",
                "You are a config generator. Given the requirements, design, and spec, generate a config file (YAML or JSON) for the application.\n\n# Requirements\n{requirements_doc}\n# Design\n{design_doc}\n# Spec\n{spec_doc}\n# Config\n",
            )
        )

    def run(self, requirements_doc: str, design_doc: str, spec_doc: str) -> str:
        return super().run(
            requirements_doc=requirements_doc, design_doc=design_doc, spec_doc=spec_doc
        )


class DiagramAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(
            PROMPT_TEMPLATES.get(
                "diagram",
                "You are a diagram generator. Given the requirements, design, and spec, generate a Mermaid diagram (markdown code block) that illustrates the architecture or workflow.\n\n# Requirements\n{requirements_doc}\n# Design\n{design_doc}\n# Spec\n{spec_doc}\n# Diagram\n",
            )
        )

    def run(self, requirements_doc: str, design_doc: str, spec_doc: str) -> str:
        return super().run(
            requirements_doc=requirements_doc, design_doc=design_doc, spec_doc=spec_doc
        )


class UnitTestAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(
            PROMPT_TEMPLATES.get(
                "unit_test",
                "You are a unit test generator. Given the requirements, design, and spec, generate a Python unittest or pytest file that tests the main code artifact.\n\n# Requirements\n{requirements_doc}\n# Design\n{design_doc}\n# Spec\n{spec_doc}\n# Unit Tests\n",
            )
        )

    def run(self, requirements_doc: str, design_doc: str, spec_doc: str) -> str:
        return super().run(
            requirements_doc=requirements_doc, design_doc=design_doc, spec_doc=spec_doc
        )


# --- File Writing/Validation Utility ---
def write_and_validate_file(
    content: str,
    out_path: Path,
    validator: Any,
    output_type: str,
    language: Optional[str] = None,
) -> Tuple[bool, str, List[Any]]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(content)
    logger.debug(f"Content written for validation: {out_path}")
    validation_results = validator.validate(
        content, output_type, language, filepath=str(out_path)
    )
    logger.debug(f"Validation results: {validation_results}")
    approved = all(r[1] == 0 for r in validation_results)
    not_approved_reason = "" if approved else f"Validation failed: {validation_results}"
    if not approved:
        with open(out_path, "r+") as f:
            file_content = f.read()
            f.seek(0, 0)
            f.write(f"# NOT APPROVED: {not_approved_reason}\n" + file_content)
    return approved, not_approved_reason, validation_results


class CriticAgent:
    def __init__(self):
        self.llm = OpenAIResponsesInterface()

    def review(self, doc, doc_type):
        prompt = (
            f"You are a reviewer. Given the following {doc_type}, check for clarity, completeness, and lack of ambiguity. "
            "For each issue you raise:"
            "\n- Justify your objection with a clear, concrete explanation."
            "\n- Explain how continuing without resolving this issue could result in a poor or failed end result (e.g., user confusion, security risk, non-compliance, etc.)."
            "\n- Classify the issue as critical/blocking, major, or minor/subjective."
            "\nIf only minor/subjective issues remain after several attempts, state that the output is 'good enough to proceed' and explain why."
            "\nIf a critical/blocking issue cannot be resolved, flag it as 'critical' and explain the risk of proceeding."
            f"\n\n# {doc_type.capitalize()}\n{doc}\n\n# Review\n"
        )
        response = self.llm.create_response(
            model="gpt-4.1", input=prompt, text_format=None
        )
        review = response.get("output_text") or str(response)
        return review, [prompt, review]


class Validator:
    def validate(self, content, output_type, language=None, filepath=None):
        from pathlib import Path
        import subprocess

        results = []
        if output_type == "code" and language == "python":
            tmp_path = Path("/tmp/validate_code.py")
            tmp_path.write_text(content)
            # 1. Syntax check
            try:
                proc = subprocess.run(
                    ["python3", "-m", "py_compile", str(tmp_path)],
                    capture_output=True,
                    text=True,
                )
                results.append(
                    ("py_compile", proc.returncode, proc.stdout, proc.stderr)
                )
            except Exception as e:
                results.append(("py_compile", 1, "", str(e)))
            # 2. Linting
            for tool in VALIDATION_TOOLS["python"]:
                try:
                    proc = subprocess.run(
                        [tool, str(tmp_path)], capture_output=True, text=True
                    )
                    results.append((tool, proc.returncode, proc.stdout, proc.stderr))
                except FileNotFoundError:
                    results.append((tool, 1, "", f"{tool} not found"))
            # 3. Only run pytest if 'test_' in filename or content
            if (filepath and "test_" in str(filepath)) or ("test_" in content):
                try:
                    proc = subprocess.run(
                        ["pytest", str(tmp_path)], capture_output=True, text=True
                    )
                    results.append(
                        ("pytest", proc.returncode, proc.stdout, proc.stderr)
                    )
                except FileNotFoundError:
                    results.append(("pytest", 1, "", "pytest not found"))
            tmp_path.unlink(missing_ok=True)
            return results
        elif output_type == "doc":
            tmp_path = Path("/tmp/validate_doc.md")
            tmp_path.write_text(content)
            for tool in VALIDATION_TOOLS["markdown"]:
                try:
                    proc = subprocess.run(
                        [tool, str(tmp_path)], capture_output=True, text=True
                    )
                    results.append((tool, proc.returncode, proc.stdout, proc.stderr))
                except FileNotFoundError:
                    results.append((tool, 1, "", f"{tool} not found"))
            tmp_path.unlink(missing_ok=True)
            return results
        return []


class CoderAgent:
    def __init__(self, model, prompt):
        self.llm = OpenAIResponsesInterface()
        self.model = model
        self.prompt = prompt

    def generate(self, user_prompt, text_format=None, **kwargs):
        allowed_keys = {"temperature", "max_tokens", "stop"}
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in allowed_keys}
        response = self.llm.create_response(
            model=self.model,
            instructions=None,
            input=self.prompt,
            text_format=text_format,
            **filtered_kwargs,
        )
        if response is None:
            logger.error("OpenAI response is None. API call may have failed.")
            return "# ERROR: No response from OpenAI API."
        output_text = response.get("output_text")
        if not output_text:
            try:
                output_text = response["output"][0]["content"][0]["text"]
                logger.info(
                    f"Extracted output_text from nested structure: {output_text[:100]}..."
                )
            except Exception:
                logger.error(
                    f"Failed to extract output_text from response. Full response: {response}"
                )
                return f"# ERROR: No output_text in response. Full response: {response}"
        logger.info(f"OpenAI output_text: {output_text[:100]}...")
        return output_text

    def run(self, context):
        return self.generate(context)


class DocumenterAgent(CoderAgent):
    def run(self, context):
        return self.generate(context)


class RouterAgent:
    def __init__(self, output_type, language=None):
        self.output_type = output_type
        self.language = language
        self.reject_count = 0
        self.log = []

    def select_model(self, output_type, task_complexity="normal"):
        """
        Select the lowest capable model tier for the task.
        Prefer efficient models (mini/nano) to maximize free usage.
        Escalate to premium (gpt-4.1, o3, etc.) only if needed.
        Log the selection and reasoning for audit.
        """
        # Example: if task_complexity is 'high', start with premium
        efficient_models = [
            m for m in MODEL_MAP[output_type] if "mini" in m or "nano" in m
        ]
        premium_models = [
            m for m in MODEL_MAP[output_type] if m not in efficient_models
        ]
        if task_complexity == "high":
            chosen = premium_models[0] if premium_models else efficient_models[0]
            logger.info(
                f"[Router] Task marked high complexity. Using premium model: {chosen}"
            )
            return chosen
        # Try efficient first
        if efficient_models:
            logger.info(f"[Router] Using efficient model: {efficient_models[0]}")
            return efficient_models[0]
        # Fallback to premium
        logger.info(
            f"[Router] No efficient model available, using premium: {premium_models[0]}"
        )
        return premium_models[0]

    def select_prompt(self, user_prompt):
        # Use the engineered prompt directly, do not format with config template
        return user_prompt

    def run(self, filename, target_dir, user_prompt, **kwargs):
        model = self.select_model(self.output_type, kwargs.get("task_complexity"))
        prompt = self.select_prompt(user_prompt)
        agent = (
            CoderAgent(model, prompt)
            if self.output_type == "code"
            else DocumenterAgent(model, prompt)
        )
        validator = Validator()
        critic = CriticAgent()
        approved = False
        not_approved_reason = ""
        output = ""
        schema = kwargs.get("schema")
        text_format = None
        if schema:
            with open(schema) as f:
                schema_dict = json.load(f)
            text_format = {"type": "json_schema", "strict": True, "schema": schema_dict}
        for attempt in range(3):
            try:
                response = agent.generate(
                    user_prompt, text_format=text_format, **kwargs
                )
            except KeyError as e:
                logger.error(
                    f"Prompt formatting error: missing variable {e}. Using raw prompt."
                )
                response = agent.generate(
                    user_prompt, text_format=text_format, **kwargs
                )
            # Robust output extraction
            if isinstance(response, dict):
                output = response.get("output_text", "")
            else:
                output = str(response)
            if self.output_type == "code":
                output = extract_code_from_markdown(output)
            out_path = Path(target_dir) / filename
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w") as f:
                f.write(output)
            print(
                f"[DEBUG] Content written for validation (attempt {attempt+1}):\n{output}"
            )
            validation_results = validator.validate(
                output, self.output_type, self.language, filepath=str(out_path)
            )
            self.log.append(f"Validation results: {validation_results}")
            if all(r[1] == 0 for r in validation_results):
                approved = True
                break
            else:
                not_approved_reason = f"Validation failed: {validation_results}"
                self.reject_count += 1
        if not approved:
            not_approved_reason = f"Rejected {self.reject_count} times. See log."
        out_path = Path(target_dir) / filename
        if not_approved_reason:
            with open(out_path, "r+") as f:
                content = f.read()
                f.seek(0, 0)
                f.write(f"# NOT APPROVED: {not_approved_reason}\n" + content)
        self.log.append(f"File written: {out_path} (approved={approved})")
        self.log_model_selection(
            model,
            f"Task marked {'high' if kwargs.get('task_complexity') == 'high' else 'normal'} complexity",
        )
        return out_path, approved, not_approved_reason, self.log

    def log_model_selection(self, model, reason):
        logger.info(f"[Router] Model selected: {model}. Reason: {reason}")


def extract_code_from_markdown(text):
    import re

    # Try to extract code between code block markers
    match = re.search(r"```(?:python)?\s*([\s\S]+?)```", text)
    if match:
        code = match.group(1).strip()
        print(f"[DEBUG] Extracted code from closed markdown block:\n{code}")
        return code
    # If only an opening code block is found, extract everything after it
    match_open = re.search(r"```(?:python)?\s*([\s\S]+)", text)
    if match_open:
        code = match_open.group(1).strip()
        print(f"[DEBUG] Extracted code from unclosed markdown block:\n{code}")
        return code
    print(f"[DEBUG] No markdown block found, using raw output:\n{text.strip()}")
    return text.strip()


def extract_artifact_content(content, atype):
    import json
    import re

    if atype == "code":
        # Extract first code block (python/js/ts)
        match = re.search(
            r"```(?:python|js|jsx|ts|typescript)?\s*([\s\S]+?)```",
            content,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()
        # Fallback: extract all code blocks and join
        blocks = re.findall(r"```[\w]*\s*([\s\S]+?)```", content)
        if blocks:
            return "\n\n".join(b.strip() for b in blocks)
        # Fallback: return content
        return content.strip()
    elif atype == "config":
        # Extract YAML or JSON block
        match = re.search(
            r"```(?:yaml|yml|json)?\s*([\s\S]+?)```", content, re.IGNORECASE
        )
        if match:
            return match.group(1).strip()
        # Fallback: try to parse as YAML/JSON
        try:
            if content.strip().startswith("{"):
                return json.dumps(json.loads(content), indent=2)
        except Exception:
            pass
        return content.strip()
    elif atype == "doc":
        # Remove LLM explanations, keep markdown after first header
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith("#"):
                return "\n".join(lines[i:]).strip()
        return content.strip()
    elif atype == "diagram":
        # Extract mermaid or PlantUML code block, else image link
        match = re.search(r"```(mermaid|plantuml)[\s\S]+?```", content, re.IGNORECASE)
        if match:
            return match.group(0)
        match_img = re.search(r"\!\[.*?\]\((.*?)\)", content)
        if match_img:
            return match_img.group(1)
        return content.strip()
    else:
        return content.strip()


def run_full_pipeline(
    user_prompt,
    output_type,
    target_dir,
    filename,
    language=None,
    schema=None,
    task_complexity="normal",
):
    logger.info("=== Starting Full Multi-Agent Pipeline ===")
    audit_log = []
    # Step 0: Artifact Planning
    planner = ArtifactPlannerAgent()
    manifest = planner.plan(user_prompt)
    audit_log.append(("ArtifactPlannerAgent", str(manifest), None))
    print("\n=== BREAKPOINT: Artifact Manifest ===")
    print(json.dumps(manifest, indent=2))
    sys.exit(0)
    # Step 1: Generate all artifacts
    results = {}

    def gen_artifact(artifact):
        atype = artifact.get("type")
        fname = artifact.get("filename")
        desc = artifact.get("desc", "")
        deps = artifact.get("dependencies", [])
        context = f"User Prompt:\n{user_prompt}\n\nDescription: {desc}\n\nDependencies: {deps}\n"
        # For code, add language
        if atype == "code":
            agent = CoderAgent(model=MODEL_MAP["code"], prompt=PROMPT_TEMPLATES["code"])
        elif atype == "doc":
            agent = DocumenterAgent(
                model=MODEL_MAP["documentation"],
                prompt=PROMPT_TEMPLATES["documentation"],
            )
        elif atype == "config":
            agent = ConfigAgent(
                model=MODEL_MAP["config"], prompt=PROMPT_TEMPLATES["config"]
            )
        elif atype == "diagram":
            agent = DiagramAgent(
                model=MODEL_MAP["diagram"], prompt=PROMPT_TEMPLATES["diagram"]
            )
        elif atype == "unit_test":
            # For simplicity, use empty strings for requirements/design/spec; in a real pipeline, pass actual docs
            agent = UnitTestAgent(
                model=MODEL_MAP["unit_test"], prompt=PROMPT_TEMPLATES["unit_test"]
            )
            output = agent.run("", "", "")
            critic = CriticAgent()
            review, review_trace = critic.review(output, atype)
            audit = [(f"{atype.capitalize()}Agent", output[:200], review)]
            out_path = Path(target_dir) / fname
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w") as f:
                f.write(output)
            return (fname, out_path, audit)
        else:
            return (fname, None, f"Unknown artifact type: {atype}")
        # Critic/validation loop (bounded: 1 update)
        output = agent.run(context)
        output = extract_artifact_content(output, atype)
        critic = CriticAgent()
        review, review_trace = critic.review(output, atype)
        audit = [(f"{atype.capitalize()}Agent", output[:200], review)]
        if review["errors"]:
            logger.info(
                f"[Critic] {atype.capitalize()}Agent output for {fname} had issues, updating once."
            )
            output = agent.run(context)
            output = extract_artifact_content(output, atype)
            review, review_trace = critic.review(output, atype)
            audit.append((f"{atype.capitalize()}Agent-Update", output[:200], review))
        # Save file
        out_path = Path(target_dir) / fname
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            f.write(output)
        return (fname, out_path, audit)

    with ThreadPoolExecutor() as executor:
        future_to_artifact = {
            executor.submit(gen_artifact, artifact): artifact for artifact in manifest
        }
        for future in as_completed(future_to_artifact):
            artifact = future_to_artifact[future]
            fname, out_path, audit = future.result()
            results[fname] = out_path
            audit_log.extend(audit)
    # Step 2: Aggregate and log
    logger.info("Pipeline complete. Artifacts and logs available.")
    print("\n=== Pipeline Artifacts ===")
    for fname, out_path in results.items():
        print(f"{fname}: {out_path}")
    print("=== End of Pipeline ===\n")
    print("\n=== Audit Log ===")
    for entry in audit_log:
        print(entry)
    print("=== End of Audit Log ===\n")


class ArtifactPlannerAgent:
    def __init__(self):
        self.llm = OpenAIResponsesInterface()

    def plan(self, user_prompt):
        logger.info("[ArtifactPlannerAgent] Planning required artifacts via LLM.")
        plan_prompt = f"""You are an expert software architect and project planner. Given the following user request, output a JSON list describing all files, documents, diagrams, and configs that should be generated to fully satisfy the request. For each artifact, include: filename, type (code, doc, config, diagram), a short description, and a list of dependencies (filenames this artifact depends on, if any). Output only the JSON list, no extra text.\n\nUser Request:\n{user_prompt}\n\n# Artifact Manifest\n"""
        print(
            "\n[ArtifactPlannerAgent] LLM Prompt for Manifest Planning:\n" + plan_prompt
        )
        response = self.llm.create_response(
            model="gpt-4.1", input=plan_prompt, text_format=None
        )
        import json

        try:
            manifest = json.loads(response.get("output_text") or str(response))
        except Exception as e:
            logger.error(
                f"[ArtifactPlannerAgent] Failed to parse manifest: {e}\n{response}"
            )
            manifest = []
        print(
            "\n[ArtifactPlannerAgent] LLM Output for Manifest Planning:\n"
            + json.dumps(manifest, indent=2)
        )
        logger.info(f"[ArtifactPlannerAgent] Planned manifest: {manifest}")
        return manifest


class IngestionAgent:
    def __init__(self):
        self.llm = OpenAIResponsesInterface()

    def run(self, user_prompt, context_files=None):
        audit = []
        # Step 1: Input Validation
        if not user_prompt or not user_prompt.strip():
            raise ValueError("User prompt is empty.")
        audit.append(("Validation", "User prompt validated.", None))
        context_blobs = []
        if context_files:
            context_paths = [f.strip() for f in context_files.split(",") if f.strip()]
            for path in context_paths:
                try:
                    with open(path, encoding="utf-8") as f:
                        content = f.read()
                    context_blobs.append(
                        f"# SUPPORTING CONTEXT: {path}\n{content.strip()}\n"
                    )
                    audit.append(
                        ("ContextIngest", f"Loaded context file: {path}", None)
                    )
                except Exception as e:
                    context_blobs.append(f"# SUPPORTING CONTEXT: {path} (ERROR: {e})\n")
                    audit.append(
                        (
                            "ContextIngest",
                            f"Failed to load context file: {path}",
                            str(e),
                        )
                    )
        # Step 2: Summarization & Deduplication (LLM-powered)
        context_summary = ""
        if context_blobs:
            summary_prompt = f"""You are a technical summarizer. Given the following supporting context, extract and summarize only the most relevant information for the main task. Remove redundancy and focus on actionable requirements, constraints, and background.\n\n# Supporting Context\n{''.join(context_blobs)}\n\n# Summary\n"""
            print("\n[IngestionAgent] LLM Prompt for Summarization:\n" + summary_prompt)
            response = self.llm.create_response(
                model="gpt-4.1", input=summary_prompt, text_format=None
            )
            context_summary = response.get("output_text") or str(response)
            print(
                "\n[IngestionAgent] LLM Output for Summarization:\n" + context_summary
            )
            audit.append(("Summarization", context_summary[:200], None))
        # Step 3: Intent Extraction & Prompt Synthesis (LLM-powered)
        synth_prompt = f"""You are a prompt engineer. Given the following user prompt and summarized supporting context, synthesize a single, clear, comprehensive prompt for a code/documentation artifact planner.\n\n# USER PROMPT\n{user_prompt.strip()}\n\n# SUPPORTING CONTEXT SUMMARY\n{context_summary}\n\n# SYNTHESIZED PROMPT\n"""
        print("\n[IngestionAgent] LLM Prompt for Synthesis:\n" + synth_prompt)
        response = self.llm.create_response(
            model="gpt-4.1", input=synth_prompt, text_format=None
        )
        synthesized_prompt = response.get("output_text") or str(response)
        print("\n[IngestionAgent] LLM Output for Synthesis:\n" + synthesized_prompt)
        audit.append(("PromptSynthesis", synthesized_prompt[:200], None))
        print("\n[IngestionAgent] Data Package after Synthesis:\n" + synthesized_prompt)
        return synthesized_prompt, audit


def build_context_prompt(user_prompt, context_files):
    prompt_sections = [f"# USER PROMPT\n{user_prompt.strip()}\n"]
    if context_files:
        context_paths = [f.strip() for f in context_files.split(",") if f.strip()]
        for path in context_paths:
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                prompt_sections.append(
                    f"# SUPPORTING CONTEXT: {path}\n{content.strip()}\n"
                )
            except Exception as e:
                prompt_sections.append(f"# SUPPORTING CONTEXT: {path} (ERROR: {e})\n")
    return "\n".join(prompt_sections)


class ValidatorAgent:
    def validate(self, user_prompt, context_files):
        errors, warnings = [], []
        if not user_prompt or not user_prompt.strip():
            errors.append("User prompt is empty.")
        context_blobs = []
        # Accept both list and comma-separated string for backward compatibility
        if context_files:
            if isinstance(context_files, str):
                context_paths = [
                    f.strip() for f in context_files.split(",") if f.strip()
                ]
            else:
                context_paths = [
                    f.strip() for f in context_files if f and isinstance(f, str)
                ]
            for path in context_paths:
                try:
                    with open(path, encoding="utf-8") as f:
                        content = f.read()
                    if not content.strip():
                        warnings.append(f"Context file {path} is empty.")
                    context_blobs.append((path, content))
                except Exception as e:
                    errors.append(f"Failed to read context file {path}: {e}")
        return errors, warnings, context_blobs


class SummarizerAgent:
    def __init__(self):
        self.llm = OpenAIResponsesInterface()

    def summarize(self, context_blobs):
        if not context_blobs:
            return "(No context to summarize)", []
        context_text = "\n\n".join(
            f"# {path}\n{content}" for path, content in context_blobs
        )
        prompt = f"You are a technical summarizer. Given the following supporting context, extract and summarize only the most relevant information for the main task. Remove redundancy and focus on actionable requirements, constraints, and background.\n\n# Supporting Context\n{context_text}\n\n# Summary\n"
        response = self.llm.create_response(
            model="gpt-4.1", input=prompt, text_format=None
        )
        summary = response.get("output_text") or str(response)
        return summary, [prompt, summary]


class RequirementsAgent:
    def __init__(self):
        self.llm = OpenAIResponsesInterface()

    def extract(self, user_prompt, context_summary):
        prompt = f"You are a requirements analyst. Given the following user request and supporting context, extract and formalize all requirements as a clear, actionable list. Include functional, non-functional, and constraint requirements. Flag any ambiguities or missing information.\n\n# User Prompt\n{user_prompt}\n\n# Context Summary\n{context_summary}\n\n# Requirements\n"
        response = self.llm.create_response(
            model="gpt-4.1", input=prompt, text_format=None
        )
        requirements = response.get("output_text") or str(response)
        return requirements, [prompt, requirements]


class DesignAgent:
    def __init__(self):
        self.llm = OpenAIResponsesInterface()

    def design(self, requirements_doc):
        prompt = f"You are a software architect. Given the following requirements, produce a high-level design document. Include architecture diagrams, component breakdown, and key technology choices.\n\n# Requirements\n{requirements_doc}\n\n# Design\n"
        response = self.llm.create_response(
            model="gpt-4.1", input=prompt, text_format=None
        )
        design_doc = response.get("output_text") or str(response)
        return design_doc, [prompt, design_doc]


class SpecAgent:
    def __init__(self):
        self.llm = OpenAIResponsesInterface()

    def spec(self, requirements_doc, design_doc):
        prompt = f"You are a technical writer. Given the following requirements and design, produce a detailed technical specification (APIs, data models, interface contracts).\n\n# Requirements\n{requirements_doc}\n\n# Design\n{design_doc}\n\n# Technical Specification\n"
        response = self.llm.create_response(
            model="gpt-4.1", input=prompt, text_format=None
        )
        spec_doc = response.get("output_text") or str(response)
        return spec_doc, [prompt, spec_doc]


class PromptSynthesizer:
    def __init__(self):
        self.llm = OpenAIResponsesInterface()

    def synthesize(self, requirements_doc, design_doc, spec_doc):
        prompt = f"You are a prompt engineer. Given the following requirements, design, and technical specification, synthesize a single, comprehensive planning prompt for an artifact planner. Ensure all context is included, deduplicated, and clearly structured.\n\n# Requirements\n{requirements_doc}\n\n# Design\n{design_doc}\n\n# Technical Specification\n{spec_doc}\n\n# Planning Prompt\n"
        response = self.llm.create_response(
            model="gpt-4.1", input=prompt, text_format=None
        )
        planning_prompt = response.get("output_text") or str(response)
        return planning_prompt, [prompt, planning_prompt]


class CriticFeedbackLog:
    def __init__(self):
        self.entries = (
            []
        )  # List of dicts: {cycle, step, issues, attempted_resolution, success}

    def log(self, cycle, step, issues, attempted_resolution, success):
        self.entries.append(
            {
                "cycle": cycle,
                "step": step,
                "issues": issues,
                "attempted_resolution": attempted_resolution,
                "success": success,
            }
        )

    def summary(self):
        print("\n=== CRITIC FEEDBACK SUMMARY ===")
        for entry in self.entries:
            print(
                f"Cycle {entry['cycle']} | Step: {entry['step']} | Issues: {entry['issues']} | Resolution: {entry['attempted_resolution']} | Success: {entry['success']}"
            )


def load_agent_prompt_schema(prompt_file):
    with open(prompt_file, encoding="utf-8") as f:
        content = f.read()
    if prompt_file.endswith(".yaml") or prompt_file.endswith(".yml"):
        schema = AgentPromptSchema.from_yaml(content)
    elif prompt_file.endswith(".json"):
        schema = AgentPromptSchema.from_json(content)
    else:
        print(f"Unsupported prompt file format: {prompt_file}")
        sys.exit(1)
    errors = schema.validate()
    if errors:
        print("\nERROR: Agent prompt schema validation failed:")
        for e in errors:
            print(f"- {e}")
        sys.exit(1)
    return schema


def decompose_prompt(user_prompt):
    """
    Naive decomposition: split by 'module', 'feature', or numbered list. Replace with LLM-based or regex as needed.
    Returns a list of (subcomponent_name, subcomponent_prompt).
    """
    import re

    # Example: split by 'Module: <name>' or numbered list
    modules = re.findall(r"(Module|Feature)\s*[:\-]\s*(.+)", user_prompt, re.IGNORECASE)
    if modules:
        return [(m[1].strip(), m[1].strip()) for m in modules]
    # Fallback: split by numbered list
    numbered = re.split(r"\n\d+\. ", user_prompt)
    if len(numbered) > 1:
        return [
            (f"Section {i+1}", p.strip()) for i, p in enumerate(numbered) if p.strip()
        ]
    # Fallback: treat whole prompt as one subcomponent
    return [("Main", user_prompt.strip())]


def process_subcomponent(sub_name, sub_prompt, context_summary, max_cycles=5):
    feedback_log = CriticFeedbackLog()
    requirements_doc = None
    for cycle in range(max_cycles):
        requirements_agent = RequirementsAgent()
        requirements_doc, req_trace = requirements_agent.extract(
            sub_prompt, context_summary
        )
        critic = CriticAgent()
        req_review, req_review_trace = critic.review(
            requirements_doc, "requirements document"
        )
        # Parse issues from review
        issues = []
        for line in req_review.splitlines():
            if any(sev in line for sev in ["Critical", "Major", "Minor"]):
                issues.append(line.strip())
        if not issues:
            feedback_log.log(
                cycle, f"requirements-{sub_name}", issues, "No issues found", True
            )
            break
        # --- Automated Remediation ---
        # Example: If missing section, add placeholder; if unclear, rephrase
        remediated = requirements_doc
        for issue in issues:
            if "missing" in issue.lower():
                remediated += f"\n# TODO: Add missing section for: {issue}"
            elif "unclear" in issue.lower():
                remediated = remediated.replace("unclear", "[REPHRASED: clarify]")
        requirements_doc = remediated
        feedback_log.log(
            cycle, f"requirements-{sub_name}", issues, "Auto-remediation applied", False
        )
    else:
        feedback_log.log(
            max_cycles, f"requirements-{sub_name}", issues, "Max cycles reached", False
        )
    # --- Speculative Design/Spec Generation ---
    design_agent = DesignAgent()
    spec_agent = SpecAgent()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        design_future = executor.submit(design_agent.design, requirements_doc)
        spec_future = executor.submit(
            spec_agent.spec, requirements_doc, design_future.result()[0]
        )
        design_doc, _ = design_future.result()
        spec_doc, _ = spec_future.result()
    return {
        "sub_name": sub_name,
        "requirements": requirements_doc,
        "design": design_doc,
        "spec": spec_doc,
        "feedback_log": feedback_log.entries,
    }


# --- Manifest Generation Utility ---
def generate_manifest(subcomponent_results):
    """
    Use ArtifactPlannerAgent to generate a manifest based on requirements, design, and spec outputs.
    """
    planner = ArtifactPlannerAgent()
    # Aggregate all requirements, design, and spec into a single context
    context = "\n\n".join(
        [
            f"# Subcomponent: {r['sub_name']}\n## Requirements\n{r['requirements']}\n## Design\n{r['design']}\n## Spec\n{r['spec']}"
            for r in subcomponent_results
        ]
    )
    manifest = planner.plan(context)
    return manifest


# --- Artifact Generation Utility ---
def generate_artifacts(
    manifest: list,
    requirements_doc: str,
    design_doc: str,
    spec_doc: str,
    user_prompt: str,
    target_dir: str,
) -> List[ArtifactResult]:
    """
    For each artifact in the manifest, generate the artifact using the appropriate agent.
    Returns a list of ArtifactResult objects.
    """
    results = []

    def gen_artifact(artifact) -> ArtifactResult:
        atype = artifact.get("type")
        fname = artifact.get("filename")
        desc = artifact.get("desc", "")
        deps = artifact.get("dependencies", [])
        if atype == "code":
            agent = CoderAgent(model=MODEL_MAP["code"], prompt=PROMPT_TEMPLATES["code"])
            output = agent.run(requirements_doc, design_doc, spec_doc)
        elif atype == "unit_test":
            agent = UnitTestAgent(
                model=MODEL_MAP["unit_test"], prompt=PROMPT_TEMPLATES["unit_test"]
            )
            output = agent.run(requirements_doc, design_doc, spec_doc)
        elif atype == "documentation":
            agent = DocumentationAgent(
                model=MODEL_MAP["documentation"],
                prompt=PROMPT_TEMPLATES["documentation"],
            )
            output = agent.run(requirements_doc, design_doc, spec_doc)
        elif atype == "config":
            agent = ConfigAgent(
                model=MODEL_MAP["config"], prompt=PROMPT_TEMPLATES["config"]
            )
            output = agent.run(requirements_doc, design_doc, spec_doc)
        elif atype == "diagram":
            agent = DiagramAgent(
                model=MODEL_MAP["diagram"], prompt=PROMPT_TEMPLATES["diagram"]
            )
            output = agent.run(requirements_doc, design_doc, spec_doc)
        else:
            output = f"Unknown artifact type: {atype}"
        out_path = Path(target_dir) / fname
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(output)
        audit = [f"Generated {atype} artifact: {fname}"]
        return ArtifactResult(fname=fname, out_path=out_path, audit=audit)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(gen_artifact, artifact) for artifact in manifest]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
    return results


def validate_code(file_path: str) -> str:
    """Run flake8 linter and check for syntax errors."""
    try:
        lint_result = subprocess.run(
            ["flake8", file_path], capture_output=True, text=True
        )
        if lint_result.returncode != 0:
            return f"Linter errors:\n{lint_result.stdout}{lint_result.stderr}"
        compile(file_path, "exec", "exec")
        return "OK"
    except Exception as e:
        return f"Syntax error: {e}"


def validate_config(file_path: str) -> str:
    """Check for valid JSON or YAML syntax."""
    try:
        if file_path.endswith(".json"):
            import json

            with open(file_path) as f:
                json.load(f)
        elif file_path.endswith((".yaml", ".yml")):
            import yaml

            with open(file_path) as f:
                yaml.safe_load(f)
        else:
            return "Unknown config format."
        return "OK"
    except Exception as e:
        return f"Config syntax error: {e}"


def validate_markdown(file_path: str) -> str:
    """Basic Markdown syntax check (headings, links, code blocks)."""
    try:
        with open(file_path) as f:
            content = f.read()
        if not re.search(r"^# ", content, re.MULTILINE):
            return "No top-level heading found."
        if "```" in content or re.search(r"\[.*\]\(.*\)", content):
            return "OK"
        return "No code blocks or links found."
    except Exception as e:
        return f"Markdown error: {e}"


def validate_mermaid(file_path: str) -> str:
    """Basic Mermaid syntax check (looks for graph/flowchart/sequenceDiagram)."""
    try:
        with open(file_path) as f:
            content = f.read()
        if re.search(
            r"^(graph|flowchart|sequenceDiagram|erDiagram)", content, re.MULTILINE
        ):
            return "OK"
        return "No valid Mermaid diagram found."
    except Exception as e:
        return f"Mermaid error: {e}"


def validate_artifact(artifact: ArtifactResult) -> str:
    """
    Run validation for the artifact based on its type.
    """
    fname = artifact.fname
    if fname.endswith(".py"):
        return validate_code(artifact.out_path)
    elif fname.endswith((".json", ".yaml", ".yml")):
        return validate_config(artifact.out_path)
    elif fname.endswith(".md"):
        return validate_markdown(artifact.out_path)
    elif fname.endswith(".mmd") or "diagram" in fname:
        return validate_mermaid(artifact.out_path)
    else:
        return "No validator for this artifact type."


def aggregate_validation_results(artifacts: list) -> str:
    """
    Aggregate validation results for all artifacts.
    """
    results = []
    for artifact in artifacts:
        result = validate_artifact(artifact)
        results.append(f"{artifact.fname}: {result}")
    return "\n".join(results)


def main():
    try:
        print("[START] Pipeline execution begins", flush=True)
        # --- Resume Capability ---
        resume_stage, resume_data = load_checkpoint()
        if resume_stage:
            print(f"[RESUME] Found checkpoint at stage: {resume_stage}", flush=True)
            logger.info(f"Resuming from checkpoint: {resume_stage}")
        else:
            logger.info("No checkpoint found. Starting fresh.")
        # --- Step 1: Input Validation ---
        if resume_stage == "input_validation":
            agent_prompt, user_prompt, context_blobs = (
                resume_data["agent_prompt"],
                resume_data["user_prompt"],
                resume_data["context_blobs"],
            )
            print("[RESUME] Skipping input validation.", flush=True)
        else:
            parser = argparse.ArgumentParser(
                description="Multi-agent code/doc generation pipeline."
            )
            parser.add_argument(
                "--agent_prompt_file",
                type=str,
                required=True,
                help="Path to the agent prompt file.",
            )
            parser.add_argument(
                "--output_type", type=str, choices=["code", "doc"], default="code"
            )
            parser.add_argument("--target_dir", type=str, default="dev_out")
            parser.add_argument("--filename", type=str, default="output.py")
            parser.add_argument("--language", type=str, default="python")
            parser.add_argument("--schema", type=str, default=None)
            parser.add_argument(
                "--task_complexity",
                type=str,
                choices=["normal", "high"],
                default="normal",
            )
            parser.add_argument(
                "--example_usage",
                action="store_true",
                help="Show usage example for --context_files and exit.",
            )
            parser.add_argument(
                "--resume_from_stage",
                type=str,
                choices=[
                    "input_validation",
                    "context_summary",
                    "extraction",
                    "manifest_generation",
                    "artifact_generation",
                    "results_aggregation",
                ],
                help="Resume from a specific stage of the pipeline.",
            )
            args = parser.parse_args()
            os.makedirs(args.target_dir, exist_ok=True)
            agent_prompt = load_agent_prompt_schema(args.agent_prompt_file)
            user_prompt = agent_prompt.title
            validator = ValidatorAgent()
            errors, warnings, context_blobs = validator.validate(
                user_prompt, agent_prompt.context_files
            )
            print("\n=== INPUT VALIDATION REPORT ===", flush=True)
            print(f"User prompt: {repr(user_prompt)}", flush=True)
            print(f"Context files: {agent_prompt.context_files}", flush=True)
            if errors:
                print("Errors:", flush=True)
                for e in errors:
                    print(f"  - {e}", flush=True)
            if warnings:
                print("Warnings:", flush=True)
                for w in warnings:
                    print(f"  - {w}", flush=True)
            if not errors:
                print("All validation checks passed.\n", flush=True)
            else:
                print("Critical errors detected. Please fix and re-run.", flush=True)
                exit(1)
            print("[AUTO] Proceeding to next step...", flush=True)
            sys.stdout.flush()
            save_checkpoint(
                "input_validation",
                {
                    "agent_prompt": agent_prompt,
                    "user_prompt": user_prompt,
                    "context_blobs": context_blobs,
                },
            )
        # --- Step 2: Context Summarization ---
        if resume_stage == "context_summary":
            context_summary = resume_data["context_summary"]
            print("[RESUME] Skipping context summarization.", flush=True)
        else:
            print("[STEP] Context Summarization", flush=True)
            summarizer = SummarizerAgent()
            context_summary, summary_trace = summarizer.summarize(context_blobs)
            print("\n=== CONTEXT SUMMARY ===\n" + context_summary, flush=True)
            print("[AUTO] Proceeding to next step...", flush=True)
            sys.stdout.flush()
            save_checkpoint("context_summary", {"context_summary": context_summary})
        # --- Step 3: Prompt Decomposition & Parallel Processing ---
        if resume_stage == "subcomponent_results":
            results = resume_data["results"]
            print("[RESUME] Skipping subcomponent extraction.", flush=True)
        else:
            print(
                "[STEP] Prompt Decomposition & Parallel Requirements/Design/Spec Extraction",
                flush=True,
            )
            subcomponents = decompose_prompt(user_prompt)
            print(
                f"[INFO] Decomposed into {len(subcomponents)} subcomponents: {[n for n, _ in subcomponents]}",
                flush=True,
            )
            results = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(
                        process_subcomponent, sub_name, sub_prompt, context_summary
                    )
                    for sub_name, sub_prompt in subcomponents
                ]
                for future in concurrent.futures.as_completed(futures):
                    results.append(future.result())
            print("[AUTO] Subcomponent extraction complete.", flush=True)
            save_checkpoint("subcomponent_results", {"results": results})
        # --- Step 4: Manifest Generation ---
        if resume_stage == "manifest":
            manifest = resume_data["manifest"]
            print("[RESUME] Skipping manifest generation.", flush=True)
        else:
            print("[STEP] Manifest Generation", flush=True)
            manifest = generate_manifest(results)
            print(
                "\n=== ARTIFACT MANIFEST ===\n" + json.dumps(manifest, indent=2),
                flush=True,
            )
            print("[AUTO] Manifest generation complete.", flush=True)
            save_checkpoint("manifest", {"manifest": manifest})
        # --- Step 5: Artifact Generation ---
        if resume_stage == "artifact_generation":
            artifact_results = resume_data["artifact_results"]
            print("[RESUME] Skipping artifact generation.", flush=True)
        else:
            print("[STEP] Artifact Generation", flush=True)
            artifact_results = generate_artifacts(
                manifest,
                results[0]["requirements"],
                results[0]["design"],
                results[0]["spec"],
                user_prompt,
                args.target_dir,
            )
            print("\n=== ARTIFACT GENERATION RESULTS ===", flush=True)
            for result in artifact_results:
                print(f"{result.fname}: {result.out_path}", flush=True)
            print("[AUTO] Artifact generation complete.", flush=True)
            save_checkpoint(
                "artifact_generation",
                {"artifact_results": _to_json_safe(artifact_results)},
            )
        # --- Step 6: Results Aggregation & Cleanup ---
        print("\n=== PIPELINE SUMMARY ===", flush=True)
        print(
            f"Artifacts generated: {[result.fname for result in artifact_results]}",
            flush=True,
        )
        validation_report = aggregate_validation_results(artifact_results)
        print("\n=== VALIDATION REPORT ===\n" + validation_report, flush=True)
        print("[END] Pipeline execution complete", flush=True)
        clear_checkpoint()
    except Exception as e:
        logger.exception(f"[ERROR] Exception occurred: {e}")
        print(f"[ERROR] Exception occurred: {e}", flush=True)


# --- Manifest/Config Adapter Stub ---
class ManifestAdapter:
    def __init__(self, manifest_dict):
        self.manifest = manifest_dict

    def get_workflows(self):
        return self.manifest.get("workflows", [])

    # Add more accessors as needed for decoupling


if __name__ == "__main__":
    main()
