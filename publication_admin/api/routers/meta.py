from fastapi import APIRouter

# Metrics, healthchecks, etc.
meta_router = APIRouter(tags=["meta"])


@meta_router.get("/ping/")
async def ping():
    return "ok"
