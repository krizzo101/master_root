import asyncio
import logging
import os
from typing import Any, Dict

from pydantic import BaseModel
import yaml

from capabilities.documentation_agent import DocumentationAgent

CONFIG_PATH = os.getenv("DOC_BUNDLE_CONFIG", "documentation_bundle_config.yaml")
DEFAULT_MAX_PARALLEL = int(os.getenv("DOC_BUNDLE_MAX_PARALLEL", "4"))


class RequirementsDoc(BaseModel):
    title: str
    requirements: list[str]
    rationale: str


class DesignDoc(BaseModel):
    title: str
    architecture: str
    diagrams: list[str]
    rationale: str


class SpecsDoc(BaseModel):
    title: str
    endpoints: list[dict]
    data_models: list[dict]


class TestPlanDoc(BaseModel):
    title: str
    test_cases: list[dict]


class DocsBundle(BaseModel):
    requirements: RequirementsDoc
    design: DesignDoc
    specs: SpecsDoc
    test_plan: TestPlanDoc


class DocumentationBundleAgent:
    """
    DocumentationBundleAgent orchestrates multiple DocumentationAgent instances for generating documentation bundles.
    Configuration is loaded from documentation_bundle_config.yaml or environment variables.
    Configurable parameters:
      - agent_types: list of doc types to generate
      - schemas: mapping of doc type to schema class
      - max_parallel_tasks: max concurrent doc generations
    """

    def __init__(self):
        self.logger = logging.getLogger("DocumentationBundleAgent")
        self.logger.setLevel(logging.INFO)
        self.config = self._load_config()
        self.agent_types = self.config.get(
            "agent_types", ["requirements", "design", "specs", "test_plan"]
        )
        self.max_parallel_tasks = self.config.get(
            "max_parallel_tasks", DEFAULT_MAX_PARALLEL
        )
        self.logger.info(
            f"Loaded agent_types: {self.agent_types}, max_parallel_tasks: {self.max_parallel_tasks}"
        )
        self.agents = {t: DocumentationAgent(doc_type=t) for t in self.agent_types}
        self.schemas = {
            "requirements": RequirementsDoc,
            "design": DesignDoc,
            "specs": SpecsDoc,
            "test_plan": TestPlanDoc,
        }
        # Allow schema override from config if needed
        self.semaphore = asyncio.Semaphore(self.max_parallel_tasks)

    def _load_config(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH) as f:
                try:
                    config = yaml.safe_load(f)
                    self.logger.info(f"Loaded config from {CONFIG_PATH}")
                    return config or {}
                except Exception as e:
                    self.logger.error(f"Failed to load config: {e}")
        return {}

    async def generate_docs_bundle(
        self, prompt: str, mode: str = "parallel"
    ) -> DocsBundle:
        context = {}
        results = {}
        self.logger.info(
            f"Starting docs bundle generation: mode={mode}, prompt={prompt}"
        )
        if mode == "parallel":
            tasks = [
                self._call_agent(doc_type, prompt, context)
                for doc_type in self.agent_types
            ]
            outputs = await asyncio.gather(*tasks)
            for doc_type, output in zip(self.agent_types, outputs):
                results[doc_type] = output
        elif mode == "sequential":
            for doc_type in self.agent_types:
                output = await self._call_agent(doc_type, prompt, context)
                results[doc_type] = output
                context[doc_type] = output
        else:
            self.logger.error(f"Invalid mode: {mode}")
            raise ValueError("Invalid mode: choose 'parallel' or 'sequential'")
        bundle = DocsBundle(**results)
        self.logger.info("Docs bundle generation complete.")
        return bundle

    async def _call_agent(self, doc_type: str, prompt: str, context: Dict[str, Any]):
        async with self.semaphore:
            self.logger.info(f"Generating doc: {doc_type}")
            agent = self.agents[doc_type]
            agent_prompt = prompt
            if context:
                agent_prompt += f"\nContext: {context}"
            try:
                result = agent.generate(agent_prompt)
                schema = self.schemas[doc_type]
                validated = schema.parse_obj(result)
                self.logger.info(f"Doc generated and validated: {doc_type}")
                return validated
            except Exception as e:
                self.logger.error(f"Error in {doc_type} generation: {e}")
                raise
