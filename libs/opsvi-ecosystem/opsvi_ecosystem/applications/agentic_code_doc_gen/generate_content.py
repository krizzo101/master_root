import argparse
import json
import logging
import os
import pickle
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from shared.openai_interfaces.responses_interface import OpenAIResponsesInterface

from tools.config import (
    MODEL_MAP,
    VALIDATION_TOOLS,
)

from .prompt_schema import AgentPromptSchema

# Fix: Insert project root (parent of 'src') into sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
print(f"[DEBUG] sys.path: {sys.path}")
print(f"[DEBUG] src/ in: {os.listdir(project_root)}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("generate_content")


# --- Agent Stubs ---
class AnalystAgent:
    def __init__(self):
        self.llm = OpenAIResponsesInterface()

    def run(self, user_prompt, standards=None):
        standards_text = (
            f"\n\n# Standards and Requirements\n{standards}" if standards else ""
        )
        prompt = f"""You are a requirements analyst. Given the following user prompt, extract and formalize the requirements in a clear, bullet-pointed markdown document.\nStrictly follow all referenced standards and requirements. Ensure the output will pass a structured critic review (description, justification, impact, classification for all issues). Output only compliant requirements, with no commentary or code block tags.{standards_text}\n\nUser Prompt:\n{user_prompt}\n\n# Requirements\n"""
        response = self.llm.create_response(
            model="gpt-4.1", input=prompt, text_format=None
        )
        output = response.get("output_text") or str(response)
        logger.info(f"[AnalystAgent] Requirements doc generated.\n{output[:200]}...")
        return output


class DesignAgent:
    def __init__(self):
        self.llm = OpenAIResponsesInterface()
        # Define a strict schema for the design document
        self.design_schema = {
            "type": "object",
            "properties": {
                "architecture": {"type": "string"},
                "components": {"type": "array", "items": {"type": "string"}},
                "diagrams": {"type": "array", "items": {"type": "string"}},
                "technology_choices": {"type": "array", "items": {"type": "string"}},
                "rationale": {"type": "string"},
            },
            "required": [
                "architecture",
                "components",
                "diagrams",
                "technology_choices",
                "rationale",
            ],
            "additionalProperties": False,
        }

    def design(self, requirements_doc, standards=None):
        standards_text = (
            f"\n\n# Standards and Requirements\n{standards}" if standards else ""
        )
        prompt = (
            "You are a software architect. Given the following requirements, output ONLY a structured design document in the following JSON schema. Strictly follow all referenced standards and requirements. Ensure the output will pass a structured critic review (description, justification, impact, classification for all issues). Output only compliant artifacts, with no commentary or code block tags. Reference the standards and requirements in the output as needed.\n"
            "Schema: { 'architecture': str, 'components': [str], 'diagrams': [str], 'technology_choices': [str], 'rationale': str }\n"
            f"\n# Requirements\n{requirements_doc}{standards_text}\n# Design Document\n"
        )
        response = self.llm.create_response(
            model="gpt-4.1",
            input=prompt,
            text_format={
                "type": "json_schema",
                "name": "design",
                "strict": True,
                "schema": self.design_schema,
            },
        )
        output = response.get("output_text") or str(response)
        output = strip_code_blocks_and_commentary(output)
        return output, [prompt, output]


class SpecAgent:
    def __init__(self):
        self.llm = OpenAIResponsesInterface()
        self.spec_schema = {
            "type": "object",
            "properties": {
                "apis": {"type": "array", "items": {"type": "string"}},
                "data_models": {"type": "array", "items": {"type": "string"}},
                "interfaces": {"type": "array", "items": {"type": "string"}},
                "contracts": {"type": "array", "items": {"type": "string"}},
                "traceability": {"type": "string"},
            },
            "required": [
                "apis",
                "data_models",
                "interfaces",
                "contracts",
                "traceability",
            ],
            "additionalProperties": False,
        }

    def spec(self, requirements_doc, design_doc, standards=None):
        standards_text = (
            f"\n\n# Standards and Requirements\n{standards}" if standards else ""
        )
        prompt = (
            "You are a technical writer. Given the following requirements and design, output ONLY a structured technical specification in the following JSON schema. Strictly follow all referenced standards and requirements. Ensure the output will pass a structured critic review (description, justification, impact, classification for all issues). Output only compliant artifacts, with no commentary or code block tags. Reference the standards and requirements in the output as needed.\n"
            "Schema: { 'apis': [str], 'data_models': [str], 'interfaces': [str], 'contracts': [str], 'traceability': str }\n"
            f"\n# Requirements\n{requirements_doc}\n# Design\n{design_doc}{standards_text}\n# Technical Specification\n"
        )
        response = self.llm.create_response(
            model="gpt-4.1",
            input=prompt,
            text_format={
                "type": "json_schema",
                "name": "spec",
                "strict": True,
                "schema": self.spec_schema,
            },
        )
        output = response.get("output_text") or str(response)
        output = strip_code_blocks_and_commentary(output)
        return output, [prompt, output]


class PromptGenAgent:
    def __init__(self):
        self.llm = OpenAIResponsesInterface()

    def run(self, requirements_doc, design_doc, spec_doc, standards=None):
        standards_text = (
            f"\n\n# Standards and Requirements\n{standards}" if standards else ""
        )
        prompt = f"""You are a prompt engineer. Given the following requirements, design, and technical specification, generate a highly effective prompt for a code generation LLM. Strictly follow all referenced standards and requirements. Ensure the output will pass a structured critic review (description, justification, impact, classification for all issues). Output only compliant prompts, with no extra explanation, commentary, or code block tags. Reference the standards and requirements in the output as needed.{standards_text}\n\n# Requirements\n{requirements_doc}\n\n# Design\n{design_doc}\n\n# Technical Specification\n{spec_doc}\n\n# Prompt\n"""
        response = self.llm.create_response(
            model="gpt-4.1", input=prompt, text_format=None
        )
        output = response.get("output_text") or str(response)
        logger.info(f"[PromptGenAgent] Custom prompt generated.\n{output[:200]}...")
        return output


class CriticAgent:
    def __init__(self):
        self.llm = OpenAIResponsesInterface()

    def review(self, doc, doc_type):
        if not isinstance(doc_type, str):
            doc_type = str(doc_type)
        prompt = (
            f"You are a reviewer. Given the following {doc_type}, output ONLY a structured review in the following JSON schema. Do NOT add any commentary, explanations, or code block tags. Output only the JSON object.\n"
            "Schema: { 'issues': [{ 'description': str, 'justification': str, 'impact': str, 'classification': str }], 'verdict': str }\n"
            f"\n# {doc_type.capitalize()}\n{doc}\n# Review\n"
        )
        response = self.llm.create_response(
            model="gpt-4.1", input=prompt, text_format=None
        )
        output = response.get("output_text") or str(response)
        output = strip_code_blocks_and_commentary(output)
        return output, [prompt, output]


class Validator:
    def validate(self, content, output_type, language=None, filepath=None):
        from pathlib import Path

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
            response = agent.generate(user_prompt, text_format=text_format, **kwargs)
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


class ConfigAgent:
    def __init__(self):
        self.llm = OpenAIResponsesInterface()

    def run(self, context):
        logger.info("[ConfigAgent] Generating config file via LLM.")
        prompt = f"You are a configuration file generator. Given the following context, generate the required config file.\n\n{context}\n\n# Config File\n"
        response = self.llm.create_response(
            model="gpt-4.1", input=prompt, text_format=None
        )
        return response.get("output_text") or str(response)


class DiagramAgent:
    def __init__(self):
        self.llm = OpenAIResponsesInterface()

    def run(self, context):
        logger.info("[DiagramAgent] Generating diagram via LLM.")
        prompt = f"You are a system architect. Given the following context, generate a mermaid diagram (or describe the diagram if not possible).\n\n{context}\n\n# Diagram\n"
        response = self.llm.create_response(
            model="gpt-4.1", input=prompt, text_format=None
        )
        return response.get("output_text") or str(response)


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
            agent = CoderAgent("gpt-4.1", context)
        elif atype == "doc":
            agent = DocumenterAgent("gpt-4.1", context)
        elif atype == "config":
            agent = ConfigAgent()
        elif atype == "diagram":
            agent = DiagramAgent()
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

    def plan(self, user_prompt, standards=None):
        standards_text = (
            f"\n\n# Standards and Requirements\n{standards}" if standards else ""
        )
        plan_prompt = f"""You are an expert software architect and project planner. Given the following user request, output a JSON list describing all files, documents, diagrams, and configs that should be generated to fully satisfy the request. Strictly follow all referenced standards and requirements. Ensure the output will pass a structured critic review (description, justification, impact, classification for all issues). Output only compliant artifacts, with no extra text, commentary, or code block tags. Reference the standards and requirements in the output as needed.{standards_text}\n\nUser Request:\n{user_prompt}\n\n# Artifact Manifest\n"""
        print(
            "\n[ArtifactPlannerAgent] LLM Prompt for Manifest Planning:\n" + plan_prompt
        )
        response = self.llm.create_response(
            model="gpt-4.1", input=plan_prompt, text_format=None
        )
        print("[DEBUG] Raw LLM response (ArtifactPlannerAgent):", response, flush=True)
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

    def extract(self, user_prompt, context_summary, standards=None):
        standards_text = (
            f"\n\n# Standards and Requirements\n{standards}" if standards else ""
        )
        prompt = (
            "You are a requirements extraction agent. Given the user prompt and context summary, output ONLY a structured requirements document in the following JSON schema. Strictly follow all referenced standards and requirements. Ensure the output will pass a structured critic review (description, justification, impact, classification for all issues). Output only compliant requirements, with no commentary or code block tags. Reference the standards and requirements in the output as needed.\n"
            "Schema: { 'functional': [...], 'non_functional': [...], 'constraints': [...], 'ambiguities': [...], 'summary_table': [...] }\n"
            f"\n# User Prompt\n{user_prompt}\n# Context Summary\n{context_summary}{standards_text}\n# Requirements Document\n"
        )
        response = self.llm.create_response(
            model="gpt-4.1", input=prompt, text_format=None
        )
        output = response.get("output_text") or str(response)
        output = strip_code_blocks_and_commentary(output)
        return output, [prompt, output]


class PromptSynthesizer:
    def __init__(self):
        self.llm = OpenAIResponsesInterface()
        self.planning_schema = {
            "type": "object",
            "properties": {
                "planning_prompt": {"type": "string"},
                "deduped_context": {"type": "string"},
                "requirements_summary": {"type": "string"},
            },
            "required": ["planning_prompt", "deduped_context", "requirements_summary"],
        }

    def synthesize(self, requirements_doc, design_doc, spec_doc, standards=None):
        standards_text = (
            f"\n\n# Standards and Requirements\n{standards}" if standards else ""
        )
        prompt = (
            "You are a prompt engineer. Given the following requirements, design, and technical specification, output ONLY a structured planning prompt in the following JSON schema. Strictly follow all referenced standards and requirements. Ensure the output will pass a structured critic review (description, justification, impact, classification for all issues). Output only compliant artifacts, with no commentary or code block tags. Reference the standards and requirements in the output as needed.\n"
            "Schema: { 'planning_prompt': str, 'deduped_context': str, 'requirements_summary': str }\n"
            f"\n# Requirements\n{requirements_doc}\n# Design\n{design_doc}\n# Technical Specification\n{spec_doc}{standards_text}\n# Planning Prompt\n"
        )
        response = self.llm.create_response(
            model="gpt-4.1",
            input=prompt,
            text_format={
                "type": "json_schema",
                "strict": True,
                "schema": self.planning_schema,
            },
        )
        output = response.get("output_text") or str(response)
        output = strip_code_blocks_and_commentary(output)
        return output, [prompt, output]


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


def save_checkpoint(context_summary, requirements_doc):
    try:
        checkpoint = {
            "context_summary": context_summary,
            "requirements_doc": requirements_doc,
        }
        # Only save JSON-serializable data
        with open(".context_summary_checkpoint.json", "w") as f:
            json.dump(checkpoint, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save checkpoint: {e}", flush=True)
        raise


def load_checkpoint():
    try:
        if not os.path.exists(".context_summary_checkpoint.json"):
            print("[INFO] No checkpoint found. Starting fresh.", flush=True)
            return None, None
        with open(".context_summary_checkpoint.json") as f:
            checkpoint = json.load(f)
        return checkpoint.get("context_summary"), checkpoint.get("requirements_doc")
    except Exception as e:
        print(f"[ERROR] Failed to load checkpoint: {e}", flush=True)
        return None, None


def remediate_requirements(requirements_doc, issues):
    # Stub: For each issue, append a placeholder fix to the requirements doc
    remediated = requirements_doc
    for issue in issues:
        remediated += f"\n# AUTO-REMEDIATION: Addressed issue: {issue}"
    return remediated


def strip_code_blocks_and_commentary(text):
    # Remove code block tags and any leading/trailing commentary
    # Remove triple backtick code blocks
    text = re.sub(r"```[a-zA-Z0-9]*", "", text)
    text = text.replace("```", "")
    # Remove lines that are pure commentary (e.g., start with #, //, or are empty)
    lines = [
        line
        for line in text.splitlines()
        if not line.strip().startswith(("#", "//")) and line.strip()
    ]
    return "\n".join(lines)


def save_design_checkpoint(design_doc):
    with open(".design_checkpoint.pkl", "wb") as f:
        pickle.dump({"design_doc": design_doc}, f)


def load_design_checkpoint():
    if not os.path.exists(".design_checkpoint.pkl"):
        return None
    with open(".design_checkpoint.pkl", "rb") as f:
        data = pickle.load(f)
    return data.get("design_doc")


def remediate_design(design_doc, issues):
    # Stub: For each issue, append a placeholder fix to the design doc
    remediated = design_doc
    for issue in issues:
        remediated += f"\n# AUTO-REMEDIATION: Addressed design issue: {issue}"
    return remediated


def remediate_spec(spec_doc, issues):
    remediated = spec_doc
    for issue in issues:
        remediated += f"\n# AUTO-REMEDIATION: Addressed spec issue: {issue}"
    return remediated


def save_spec_checkpoint(spec_doc):
    with open(".spec_checkpoint.pkl", "wb") as f:
        pickle.dump({"spec_doc": spec_doc}, f)


def load_spec_checkpoint():
    if not os.path.exists(".spec_checkpoint.pkl"):
        return None
    with open(".spec_checkpoint.pkl", "rb") as f:
        data = pickle.load(f)
    return data.get("spec_doc")


def remediate_planning(planning_doc, issues):
    remediated = planning_doc
    for issue in issues:
        remediated += f"\n# AUTO-REMEDIATION: Addressed planning issue: {issue}"
    return remediated


def save_planning_checkpoint(planning_doc):
    with open(".planning_checkpoint.pkl", "wb") as f:
        pickle.dump({"planning_doc": planning_doc}, f)


def load_planning_checkpoint():
    if not os.path.exists(".planning_checkpoint.pkl"):
        return None
    with open(".planning_checkpoint.pkl", "rb") as f:
        data = pickle.load(f)
    return data.get("planning_doc")


def remediate_input_validation(validation_report, issues):
    remediated = validation_report
    for issue in issues:
        remediated += f"\n# AUTO-REMEDIATION: Addressed input validation issue: {issue}"
    return remediated


def save_input_validation_checkpoint(validation_report):
    try:
        with open(".input_validation_checkpoint.json", "w") as f:
            json.dump({"validation_report": validation_report}, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save input validation checkpoint: {e}", flush=True)
        raise


def load_input_validation_checkpoint():
    try:
        if not os.path.exists(".input_validation_checkpoint.json"):
            return None
        with open(".input_validation_checkpoint.json") as f:
            data = json.load(f)
        return data.get("validation_report")
    except Exception as e:
        print(f"[ERROR] Failed to load input validation checkpoint: {e}", flush=True)
        return None


def remediate_context_summary(context_summary, issues):
    remediated = context_summary
    for issue in issues:
        remediated += f"\n# AUTO-REMEDIATION: Addressed context summary issue: {issue}"
    return remediated


def save_context_summary_checkpoint(context_summary):
    try:
        with open(".context_summary_checkpoint.json", "w") as f:
            json.dump({"context_summary": context_summary}, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save context summary checkpoint: {e}", flush=True)
        raise


def load_context_summary_checkpoint():
    try:
        if not os.path.exists(".context_summary_checkpoint.json"):
            return None
        with open(".context_summary_checkpoint.json") as f:
            data = json.load(f)
        return data.get("context_summary")
    except Exception as e:
        print(f"[ERROR] Failed to load context summary checkpoint: {e}", flush=True)
        return None


def main(args):
    try:
        print("[START] Pipeline execution begins", flush=True)
        # --- Step 1: Input Validation ---
        print("[PHASE] Starting Input Validation phase", flush=True)
        input_validation_feedback_log = CriticFeedbackLog()
        max_input_validation_cycles = 5
        input_validation_cycle = 0
        validation_report = None
        while input_validation_cycle < max_input_validation_cycles:
            input_validation_cycle += 1
            print(
                f"[LOOP] Critic cycle {input_validation_cycle} for input validation review",
                flush=True,
            )
            agent_prompt = load_agent_prompt_schema(args.agent_prompt_file)
            user_prompt = agent_prompt.title
            validator = ValidatorAgent()
            errors, warnings, context_blobs = validator.validate(
                user_prompt, agent_prompt.context_files
            )
            validation_report = f"User prompt: {repr(user_prompt)}\nContext files: {agent_prompt.context_files}\nErrors: {errors}\nWarnings: {warnings}"
            print(
                "\n=== INPUT VALIDATION REPORT (Cycle {input_validation_cycle}) ===\n"
                + validation_report
            )
            critic = CriticAgent()
            validation_review, validation_review_trace = critic.review(
                validation_report, "input validation report"
            )
            print(
                f"\n=== INPUT VALIDATION REVIEW (Cycle {input_validation_cycle}) ===\n"
                + validation_review,
                flush=True,
            )
            issues = []
            for line in validation_review.splitlines():
                if any(sev in line for sev in ["Critical", "Major", "Minor"]):
                    issues.append(line.strip())
            if not issues:
                input_validation_feedback_log.log(
                    input_validation_cycle,
                    "input_validation",
                    issues,
                    "No issues found",
                    True,
                )
                print(
                    f"[SUCCESS] No issues found in input validation cycle {input_validation_cycle}",
                    flush=True,
                )
                break
            remediated_report = remediate_input_validation(validation_report, issues)
            attempted_resolution = (
                f"Auto-remediation: injected placeholder fixes for: {issues}"
            )
            input_validation_feedback_log.log(
                input_validation_cycle,
                "input_validation",
                issues,
                attempted_resolution,
                False,
            )
            print(f"[AUTO] Remediation attempted: {attempted_resolution}", flush=True)
            validation_report = remediated_report
            save_input_validation_checkpoint(validation_report)
            sys.stdout.flush()
        else:
            print(
                "[AUTO] Max critic cycles reached for input validation review.",
                flush=True,
            )
        input_validation_feedback_log.summary()
        print("[END] Input Validation phase complete", flush=True)
        print(
            f"[WRITE] Writing input validation report to {args.target_dir}/{args.filename or 'input_validation_report.md'}",
            flush=True,
        )
        with open(
            Path(args.target_dir) / (args.filename or "input_validation_report.md"), "w"
        ) as f:
            f.write(validation_report)
        print(
            f"[WRITE] Finished writing input validation report to {args.target_dir}/{args.filename or 'input_validation_report.md'}",
            flush=True,
        )
        # --- Step 2: Context Summarization ---
        print("[PHASE] Starting Context Summarization phase", flush=True)
        context_summary_feedback_log = CriticFeedbackLog()
        max_context_summary_cycles = 5
        context_summary_cycle = 0
        context_summary = None
        while context_summary_cycle < max_context_summary_cycles:
            context_summary_cycle += 1
            print(
                f"[LOOP] Critic cycle {context_summary_cycle} for context summary review",
                flush=True,
            )
            summarizer = SummarizerAgent()
            context_summary, summary_trace = summarizer.summarize(context_blobs)
            print(
                "\n=== CONTEXT SUMMARY (Cycle {context_summary_cycle}) ===\n"
                + context_summary
            )
            critic = CriticAgent()
            context_summary_review, context_summary_review_trace = critic.review(
                context_summary, "context summary"
            )
            print(
                f"\n=== CONTEXT SUMMARY REVIEW (Cycle {context_summary_cycle}) ===\n"
                + context_summary_review,
                flush=True,
            )
            issues = []
            for line in context_summary_review.splitlines():
                if any(sev in line for sev in ["Critical", "Major", "Minor"]):
                    issues.append(line.strip())
            if not issues:
                context_summary_feedback_log.log(
                    context_summary_cycle,
                    "context_summary",
                    issues,
                    "No issues found",
                    True,
                )
                print(
                    f"[SUCCESS] No issues found in context summary cycle {context_summary_cycle}",
                    flush=True,
                )
                break
            remediated_summary = remediate_context_summary(context_summary, issues)
            attempted_resolution = (
                f"Auto-remediation: injected placeholder fixes for: {issues}"
            )
            context_summary_feedback_log.log(
                context_summary_cycle,
                "context_summary",
                issues,
                attempted_resolution,
                False,
            )
            print(f"[AUTO] Remediation attempted: {attempted_resolution}", flush=True)
            context_summary = remediated_summary
            save_context_summary_checkpoint(context_summary)
            sys.stdout.flush()
        else:
            print(
                "[AUTO] Max critic cycles reached for context summary review.",
                flush=True,
            )
        context_summary_feedback_log.summary()
        print("[END] Context Summarization phase complete", flush=True)
        print(
            f"[WRITE] Writing context summary to {args.target_dir}/{args.filename or 'context_summary.md'}",
            flush=True,
        )
        with open(
            Path(args.target_dir) / (args.filename or "context_summary.md"), "w"
        ) as f:
            f.write(context_summary)
        print(
            f"[WRITE] Finished writing context summary to {args.target_dir}/{args.filename or 'context_summary.md'}",
            flush=True,
        )
        print(
            "[DEBUG] After context summary write, before requirements extraction",
            flush=True,
        )
        # --- Step 3: Requirements Extraction ---
        print("[PHASE] Starting Requirements Extraction phase", flush=True)
        requirements_feedback_log = CriticFeedbackLog()
        max_requirements_cycles = 5
        requirements_cycle = 0
        requirements_doc = None
        while requirements_cycle < max_requirements_cycles:
            requirements_cycle += 1
            print(
                f"[LOOP] Critic cycle {requirements_cycle} for requirements extraction review",
                flush=True,
            )
            print("[DEBUG] Instantiating RequirementsAgent", flush=True)
            requirements_agent = RequirementsAgent()
            print("[DEBUG] About to call requirements_agent.extract", flush=True)
            try:
                requirements_doc, req_trace = requirements_agent.extract(
                    user_prompt, context_summary
                )
                print(
                    f"[DEBUG] requirements_doc type: {type(requirements_doc)}",
                    flush=True,
                )
                print(
                    f"[DEBUG] requirements_doc value: {repr(requirements_doc)[:500]}",
                    flush=True,
                )
                print(f"[DEBUG] req_trace type: {type(req_trace)}", flush=True)
                print(f"[DEBUG] req_trace value: {repr(req_trace)[:500]}", flush=True)
            except Exception as e:
                print(
                    f"[ERROR] Exception in requirements_agent.extract: {e}", flush=True
                )
                import traceback

                traceback.print_exc()
                raise
            print(
                f"\n=== REQUIREMENTS DOC (Cycle {requirements_cycle}) ===\n"
                + str(requirements_doc),
                flush=True,
            )
            print("[DEBUG] Instantiating CriticAgent", flush=True)
            critic = CriticAgent()
            print("[DEBUG] About to call critic.review", flush=True)
            requirements_review, requirements_review_trace = critic.review(
                requirements_doc, "requirements document"
            )
            print(
                f"[DEBUG] requirements_review type: {type(requirements_review)}",
                flush=True,
            )
            print(
                f"[DEBUG] requirements_review value: {repr(requirements_review)[:500]}",
                flush=True,
            )
            print(
                f"[DEBUG] requirements_review_trace type: {type(requirements_review_trace)}",
                flush=True,
            )
            print(
                f"[DEBUG] requirements_review_trace value: {repr(requirements_review_trace)[:500]}",
                flush=True,
            )
            print(
                f"\n=== REQUIREMENTS REVIEW (Cycle {requirements_cycle}) ===\n"
                + str(requirements_review),
                flush=True,
            )
            issues = []
            for line in requirements_review.splitlines():
                if any(sev in line for sev in ["Critical", "Major", "Minor"]):
                    issues.append(line.strip())
            print(f"[DEBUG] issues: {issues}", flush=True)
            if not issues:
                requirements_feedback_log.log(
                    requirements_cycle, "requirements", issues, "No issues found", True
                )
                print(
                    f"[SUCCESS] No issues found in requirements cycle {requirements_cycle}",
                    flush=True,
                )
                break
            print("[DEBUG] About to call remediate_requirements", flush=True)
            remediated_requirements = remediate_requirements(requirements_doc, issues)
            print(
                f"[DEBUG] remediated_requirements type: {type(remediated_requirements)}",
                flush=True,
            )
            print(
                f"[DEBUG] remediated_requirements value: {repr(remediated_requirements)[:500]}",
                flush=True,
            )
            attempted_resolution = (
                f"Auto-remediation: injected placeholder fixes for: {issues}"
            )
            requirements_feedback_log.log(
                requirements_cycle, "requirements", issues, attempted_resolution, False
            )
            print(f"[AUTO] Remediation attempted: {attempted_resolution}", flush=True)
            requirements_doc = remediated_requirements
            print("[DEBUG] About to call save_checkpoint", flush=True)
            save_checkpoint(context_summary, requirements_doc)
            print("[DEBUG] save_checkpoint complete", flush=True)
            sys.stdout.flush()
        else:
            print(
                "[AUTO] Max critic cycles reached for requirements extraction review.",
                flush=True,
            )
        requirements_feedback_log.summary()
        print("[END] Requirements Extraction phase complete", flush=True)
        print(
            f"[WRITE] Writing requirements to {args.target_dir}/{args.filename or 'workflow_runner_requirements.md'}",
            flush=True,
        )
        try:
            print("[DEBUG] About to write requirements_doc to file", flush=True)
            with open(
                Path(args.target_dir)
                / (args.filename or "workflow_runner_requirements.md"),
                "w",
            ) as f:
                f.write(requirements_doc)
            print(
                f"[WRITE] Finished writing requirements to {args.target_dir}/{args.filename or 'workflow_runner_requirements.md'}",
                flush=True,
            )
        except Exception as e:
            print(f"[ERROR] Failed to write requirements: {e}", flush=True)
            import traceback

            traceback.print_exc()
            raise
        # --- Step 4: Design Generation ---
        print("[PHASE] Starting Design Generation phase", flush=True)
        design_feedback_log = CriticFeedbackLog()
        max_design_cycles = 5
        design_cycle = 0
        design_doc = None
        while design_cycle < max_design_cycles:
            design_cycle += 1
            print(f"[LOOP] Critic cycle {design_cycle} for design review", flush=True)
            design_agent = DesignAgent()
            design_doc, design_trace = design_agent.design(requirements_doc)
            print("\n=== DESIGN DOC (Cycle {design_cycle}) ===\n" + design_doc)
            critic = CriticAgent()
            design_review, design_review_trace = critic.review(
                design_doc, "design document"
            )
            print(
                f"\n=== DESIGN REVIEW (Cycle {design_cycle}) ===\n" + design_review,
                flush=True,
            )
            issues = []
            for line in design_review.splitlines():
                if any(sev in line for sev in ["Critical", "Major", "Minor"]):
                    issues.append(line.strip())
            if not issues:
                design_feedback_log.log(
                    design_cycle, "design", issues, "No issues found", True
                )
                print(
                    f"[SUCCESS] No issues found in design cycle {design_cycle}",
                    flush=True,
                )
                break
            remediated_design = remediate_design(design_doc, issues)
            attempted_resolution = (
                f"Auto-remediation: injected placeholder fixes for: {issues}"
            )
            design_feedback_log.log(
                design_cycle, "design", issues, attempted_resolution, False
            )
            print(f"[AUTO] Remediation attempted: {attempted_resolution}", flush=True)
            design_doc = remediated_design
            save_design_checkpoint(design_doc)
            sys.stdout.flush()
        else:
            print("[AUTO] Max critic cycles reached for design review.", flush=True)
        design_feedback_log.summary()
        print("[END] Design Generation phase complete", flush=True)
        print(
            f"[WRITE] Writing design to {args.target_dir}/{args.filename or 'workflow_runner_design.md'}",
            flush=True,
        )
        try:
            with open(
                Path(args.target_dir) / (args.filename or "workflow_runner_design.md"),
                "w",
            ) as f:
                f.write(design_doc)
            print(
                f"[WRITE] Finished writing design to {args.target_dir}/{args.filename or 'workflow_runner_design.md'}",
                flush=True,
            )
        except Exception as e:
            print(f"[ERROR] Failed to write design: {e}", flush=True)
            raise
        # --- Step 5: Spec Generation ---
        print("[PHASE] Starting Spec Generation phase", flush=True)
        spec_feedback_log = CriticFeedbackLog()
        max_spec_cycles = 5
        spec_cycle = 0
        spec_doc = None
        while spec_cycle < max_spec_cycles:
            spec_cycle += 1
            print(f"[LOOP] Critic cycle {spec_cycle} for spec review", flush=True)
            spec_agent = SpecAgent()
            spec_doc, spec_trace = spec_agent.spec(requirements_doc, design_doc)
            print("\n=== SPEC DOC (Cycle {spec_cycle}) ===\n" + spec_doc)
            critic = CriticAgent()
            spec_review, spec_review_trace = critic.review(spec_doc, "spec document")
            print(
                f"\n=== SPEC REVIEW (Cycle {spec_cycle}) ===\n" + spec_review,
                flush=True,
            )
            issues = []
            for line in spec_review.splitlines():
                if any(sev in line for sev in ["Critical", "Major", "Minor"]):
                    issues.append(line.strip())
            if not issues:
                spec_feedback_log.log(
                    spec_cycle, "spec", issues, "No issues found", True
                )
                print(
                    f"[SUCCESS] No issues found in spec cycle {spec_cycle}", flush=True
                )
                break
            remediated_spec = remediate_spec(spec_doc, issues)
            attempted_resolution = (
                f"Auto-remediation: injected placeholder fixes for: {issues}"
            )
            spec_feedback_log.log(
                spec_cycle, "spec", issues, attempted_resolution, False
            )
            print(f"[AUTO] Remediation attempted: {attempted_resolution}", flush=True)
            spec_doc = remediated_spec
            save_spec_checkpoint(spec_doc)
            sys.stdout.flush()
        else:
            print("[AUTO] Max critic cycles reached for spec review.", flush=True)
        spec_feedback_log.summary()
        print("[END] Spec Generation phase complete", flush=True)
        print(
            f"[WRITE] Writing spec to {args.target_dir}/{args.filename or 'workflow_runner_spec.md'}",
            flush=True,
        )
        try:
            with open(
                Path(args.target_dir) / (args.filename or "workflow_runner_spec.md"),
                "w",
            ) as f:
                f.write(spec_doc)
            print(
                f"[WRITE] Finished writing spec to {args.target_dir}/{args.filename or 'workflow_runner_spec.md'}",
                flush=True,
            )
        except Exception as e:
            print(f"[ERROR] Failed to write spec: {e}", flush=True)
            raise
        # --- Step 6: Manifest Generation ---
        print("[PHASE] Starting Manifest Generation phase", flush=True)
        manifest_feedback_log = CriticFeedbackLog()
        max_manifest_cycles = 5
        manifest_cycle = 0
        manifest_doc = None
        while manifest_cycle < max_manifest_cycles:
            manifest_cycle += 1
            print(
                f"[LOOP] Critic cycle {manifest_cycle} for manifest review", flush=True
            )
            planner = ArtifactPlannerAgent()
            manifest_doc = json.dumps(planner.plan(user_prompt), indent=2)
            print("\n=== MANIFEST DOC (Cycle {manifest_cycle}) ===\n" + manifest_doc)
            critic = CriticAgent()
            manifest_review, manifest_review_trace = critic.review(
                manifest_doc, "manifest document"
            )
            print(
                f"\n=== MANIFEST REVIEW (Cycle {manifest_cycle}) ===\n"
                + manifest_review,
                flush=True,
            )
            issues = []
            for line in manifest_review.splitlines():
                if any(sev in line for sev in ["Critical", "Major", "Minor"]):
                    issues.append(line.strip())
            if not issues:
                manifest_feedback_log.log(
                    manifest_cycle, "manifest", issues, "No issues found", True
                )
                print(
                    f"[SUCCESS] No issues found in manifest cycle {manifest_cycle}",
                    flush=True,
                )
                break
            remediated_manifest = (
                manifest_doc
                + "\n# AUTO-REMEDIATION: Addressed manifest issues: "
                + ", ".join(issues)
            )
            attempted_resolution = (
                f"Auto-remediation: injected placeholder fixes for: {issues}"
            )
            manifest_feedback_log.log(
                manifest_cycle, "manifest", issues, attempted_resolution, False
            )
            print(f"[AUTO] Remediation attempted: {attempted_resolution}", flush=True)
            manifest_doc = remediated_manifest
            save_planning_checkpoint(manifest_doc)
            sys.stdout.flush()
        else:
            print("[AUTO] Max critic cycles reached for manifest review.", flush=True)
        manifest_feedback_log.summary()
        print("[END] Manifest Generation phase complete", flush=True)
        print(
            f"[WRITE] Writing manifest to {args.target_dir}/{args.filename or 'workflow_runner_manifest.md'}",
            flush=True,
        )
        try:
            with open(
                Path(args.target_dir)
                / (args.filename or "workflow_runner_manifest.md"),
                "w",
            ) as f:
                f.write(manifest_doc)
            print(
                f"[WRITE] Finished writing manifest to {args.target_dir}/{args.filename or 'workflow_runner_manifest.md'}",
                flush=True,
            )
        except Exception as e:
            print(f"[ERROR] Failed to write manifest: {e}", flush=True)
            raise
        print("[END] Pipeline execution complete", flush=True)
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}", flush=True)
        import traceback

        traceback.print_exc()
        sys.stdout.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent_prompt_file", required=True)
    parser.add_argument("--output_type", default="doc")
    parser.add_argument("--target_dir", default="./out")
    parser.add_argument("--filename", default=None)
    parser.add_argument("--resume_requirements", action="store_true")
    args = parser.parse_args()
    main(args)
