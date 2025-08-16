"""FS processors base for opsvi-fs."""
class FileProcessor:
    async def process(self, path: str) -> None:
        raise NotImplementedError
