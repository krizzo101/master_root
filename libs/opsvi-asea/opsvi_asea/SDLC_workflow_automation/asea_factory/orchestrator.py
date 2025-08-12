from asea_factory.config.config_loader import ConfigLoader
from asea_factory.utils.logger import get_logger
from asea_factory.agents.research import ResearchAgent
from asea_factory.agents.requirements import RequirementsAgent
from asea_factory.agents.architecture import ArchitectureAgent
from asea_factory.agents.design_review import DesignReviewAgent
from asea_factory.agents.management import ManagementAgent
from asea_factory.agents.environment import EnvironmentAgent
from asea_factory.agents.frontend import FrontendAgent
from asea_factory.agents.backend import BackendAgent
from asea_factory.agents.database import DatabaseAgent
from asea_factory.agents.integration import IntegrationAgent
from asea_factory.agents.critic import CriticAgent
from asea_factory.agents.testing import TestingAgent
from asea_factory.agents.documentation import DocumentationAgent


class PipelineOrchestrator:
    def __init__(self, config_path="config.yml", env_path=".env", debug=True):
        self.config = ConfigLoader(env_path, config_path)
        self.logger = get_logger("PipelineOrchestrator", debug)
        self.debug = debug
        self._init_agents()

    def _init_agents(self):
        self.logger.debug("Initializing all agents with config.")
        self.research_agent = ResearchAgent(self.config)
        self.requirements_agent = RequirementsAgent(self.config)
        self.architecture_agent = ArchitectureAgent(self.config)
        self.design_review_agent = DesignReviewAgent(self.config)
        self.management_agent = ManagementAgent(self.config)
        self.environment_agent = EnvironmentAgent(self.config)
        self.frontend_agent = FrontendAgent(self.config)
        self.backend_agent = BackendAgent(self.config)
        self.database_agent = DatabaseAgent(self.config)
        self.integration_agent = IntegrationAgent(self.config)
        self.critic_agent = CriticAgent(self.config)
        self.testing_agent = TestingAgent(self.config)
        self.documentation_agent = DocumentationAgent(self.config)

    def run_pipeline(self):
        self.logger.debug("Starting full SDLC pipeline.")
        # 1. Environment validation
        if not self.environment_agent.run():
            self.logger.error("Environment validation failed. Aborting pipeline.")
            return
        self.logger.debug("Environment validated.")
        # 2. Requirements gathering
        import os
        import yaml

        requirements_input = None
        if os.path.exists("requirements_input.yaml"):
            with open("requirements_input.yaml", "r") as f:
                requirements_input = yaml.safe_load(f)
        requirements = self.requirements_agent.run(
            requirements_input=requirements_input
        )
        self.logger.debug(f"Requirements gathered: {requirements}")
        # 3. Research enrichment
        # Extract functional requirements as a list of descriptions
        if hasattr(requirements, "requirements"):
            functional_reqs = [
                r.description
                for r in requirements.requirements
                if r.type == "functional"
            ]
        else:
            functional_reqs = [
                r["description"]
                for r in requirements["requirements"]
                if r["type"] == "functional"
            ]
        research = self.research_agent.run(functional_reqs)
        self.logger.debug(f"Research results: {research}")
        # 4. Architecture generation
        requirements_ids = [r.id for r in requirements.requirements]
        research_ids = [r.id for r in research]
        architecture = self.architecture_agent.run(requirements_ids, research_ids)
        self.logger.debug(f"Architecture generated: {architecture}")
        # 5. Design review
        design_review = self.design_review_agent.run(architecture.id)
        self.logger.debug(f"Design review: {design_review}")
        # 6. Frontend code generation
        frontend = self.frontend_agent.run(requirements_ids, architecture.id)
        self.logger.debug(f"Frontend code: {frontend}")
        # 7. Backend code generation
        backend = self.backend_agent.run(requirements_ids, architecture.id)
        self.logger.debug(f"Backend code: {backend}")
        # 8. Database code generation
        database = self.database_agent.run(requirements_ids, architecture.id)
        self.logger.debug(f"Database code: {database}")
        # 9. Integration
        artifact_ids = [frontend.id, backend.id, database.id]
        integration = self.integration_agent.run(artifact_ids)
        self.logger.debug(f"Integration: {integration}")
        # 10. Critic review
        critic = self.critic_agent.run(artifact_ids)
        self.logger.debug(f"Critic review: {critic}")
        # 11. Testing
        tests = self.testing_agent.run(artifact_ids)
        self.logger.debug(f"Test results: {tests}")
        # 12. Documentation
        docs = self.documentation_agent.run(artifact_ids)
        self.logger.debug(f"Documentation: {docs}")
        # Generate traceability matrix
        from asea_factory.utils.traceability_matrix import generate_traceability_matrix

        matrix = generate_traceability_matrix(
            requirements=requirements.requirements
            if hasattr(requirements, "requirements")
            else requirements["requirements"],
            architecture=architecture.dict()
            if hasattr(architecture, "dict")
            else architecture,
            code=[
                frontend.dict() if hasattr(frontend, "dict") else frontend,
                backend.dict() if hasattr(backend, "dict") else backend,
                database.dict() if hasattr(database, "dict") else database,
                integration.dict() if hasattr(integration, "dict") else integration,
            ],
            tests=[tests.dict() if hasattr(tests, "dict") else tests],
            docs=[docs.dict() if hasattr(docs, "dict") else docs],
        )
        self.logger.info("Pipeline complete. All artifacts generated.")
        return {
            "requirements": requirements,
            "research": research,
            "architecture": architecture,
            "design_review": design_review,
            "frontend": frontend,
            "backend": backend,
            "database": database,
            "integration": integration,
            "critic": critic,
            "tests": tests,
            "docs": docs,
            "traceability_matrix": matrix.dict() if hasattr(matrix, "dict") else matrix,
        }
