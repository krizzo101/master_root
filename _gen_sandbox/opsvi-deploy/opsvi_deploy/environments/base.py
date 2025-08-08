"""Environments base for opsvi-deploy."""
class EnvironmentManager:
    def current(self) -> str:
        return "dev"
