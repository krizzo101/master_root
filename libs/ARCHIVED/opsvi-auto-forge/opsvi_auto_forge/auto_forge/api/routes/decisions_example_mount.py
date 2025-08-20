from __future__ import annotations

from fastapi import Depends, FastAPI
from opsvi_auto_forge.api.deps.neo4j_dep import get_neo4j
from opsvi_auto_forge.api.routes.decisions import router as decisions_router

app = FastAPI()

# Inject dependency
decisions_router.dependencies = [Depends(get_neo4j)]
app.include_router(decisions_router)


@app.get("/healthz")
def health():
    return {"ok": True}
