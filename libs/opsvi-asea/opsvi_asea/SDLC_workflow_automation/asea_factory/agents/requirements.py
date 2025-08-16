from asea_factory.schemas import RequirementsSpec, Requirement
import uuid
from pydantic import ValidationError
from asea_factory.agents.base_agent import BaseAgent


class RequirementsAgent(BaseAgent):
    def __init__(self, config, debug=True):
        super().__init__("Requirements", config, debug)

    def gather_requirements(self, requirements_input: dict = None) -> RequirementsSpec:
        self.logger.debug("Gathering requirements.")
        requirements = []
        user_stories = []
        acceptance_criteria = []
        if requirements_input is not None:
            # Autonomous mode: parse from provided dict
            for req in requirements_input.get("functional", []):
                requirements.append(
                    Requirement(
                        id=str(uuid.uuid4()), description=req, type="functional"
                    )
                )
            for req in requirements_input.get("non_functional", []):
                requirements.append(
                    Requirement(
                        id=str(uuid.uuid4()), description=req, type="non-functional"
                    )
                )
            for req in requirements_input.get("constraints", []):
                requirements.append(
                    Requirement(
                        id=str(uuid.uuid4()), description=req, type="constraint"
                    )
                )
            user_stories = requirements_input.get("user_stories", [])
            acceptance_criteria = requirements_input.get("acceptance_criteria", [])
        else:
            # Interactive fallback (for CLI --interactive)
            print("Enter functional requirements (type 'done' to finish):")
            while True:
                req = input("> ")
                if req.strip().lower() == "done":
                    break
                if req.strip():
                    requirements.append(
                        Requirement(
                            id=str(uuid.uuid4()),
                            description=req.strip(),
                            type="functional",
                        )
                    )
            print("Enter non-functional requirements (type 'done' to finish):")
            while True:
                req = input("> ")
                if req.strip().lower() == "done":
                    break
                if req.strip():
                    requirements.append(
                        Requirement(
                            id=str(uuid.uuid4()),
                            description=req.strip(),
                            type="non-functional",
                        )
                    )
            print("Enter constraints (type 'done' to finish):")
            while True:
                req = input("> ")
                if req.strip().lower() == "done":
                    break
                if req.strip():
                    requirements.append(
                        Requirement(
                            id=str(uuid.uuid4()),
                            description=req.strip(),
                            type="constraint",
                        )
                    )
            print("Enter user stories (type 'done' to finish):")
            while True:
                story = input("> ")
                if story.strip().lower() == "done":
                    break
                if story.strip():
                    user_stories.append(story.strip())
            print("Enter acceptance criteria (type 'done' to finish):")
            while True:
                crit = input("> ")
                if crit.strip().lower() == "done":
                    break
                if crit.strip():
                    acceptance_criteria.append(crit.strip())
        try:
            spec = RequirementsSpec(
                requirements=requirements,
                user_stories=user_stories,
                acceptance_criteria=acceptance_criteria,
            )
            self.log_response("Requirements gathering", spec.json())
            return spec
        except ValidationError as e:
            self.logger.error(f"Validation error: {e}")
            raise

    def run(self, requirements_input: dict = None) -> RequirementsSpec:
        return self.gather_requirements(requirements_input=requirements_input)
