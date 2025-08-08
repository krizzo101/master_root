"""Communication base for opsvi-agents."""
class Communicator:
    async def send(self, message: str) -> None:
        pass
