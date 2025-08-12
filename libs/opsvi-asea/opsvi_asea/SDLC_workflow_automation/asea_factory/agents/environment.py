import subprocess
from asea_factory.config.config_loader import ConfigLoader
from asea_factory.agents.base_agent import BaseAgent


class EnvironmentAgent(BaseAgent):
    def __init__(self, config: ConfigLoader):
        super().__init__("Environment", config, debug=True)

    def validate_services(self) -> bool:
        self.logger.info("Validating Docker, ArangoDB, and Redis services.")
        try:
            subprocess.check_call(["docker", "ps"])
            # Add more checks for ArangoDB, Redis, etc.
            return True
        except Exception as e:
            self.logger.error(f"Environment validation failed: {e}")
            return False

    def run(self) -> bool:
        return self.validate_services()
