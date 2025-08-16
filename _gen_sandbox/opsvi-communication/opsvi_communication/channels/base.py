"""Comm channel base for opsvi-communication."""
class Channel:
    async def publish(self, message: str) -> None:
        pass
