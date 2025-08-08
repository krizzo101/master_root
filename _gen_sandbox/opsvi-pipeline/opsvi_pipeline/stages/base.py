"""Pipeline stage base for opsvi-pipeline."""
class Stage:
    async def run(self, data):
        return data
