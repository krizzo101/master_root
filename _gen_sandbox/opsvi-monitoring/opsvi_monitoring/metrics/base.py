"""Metrics base for opsvi-monitoring."""
class Metrics:
    def record(self, name: str, value: float) -> None:
        pass
