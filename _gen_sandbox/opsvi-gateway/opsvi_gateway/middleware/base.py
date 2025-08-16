"""Gateway middleware base for opsvi-gateway."""
class Middleware:
    async def process(self, request):
        return request
