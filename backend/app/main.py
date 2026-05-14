"""FastAPI entrypoint. Routes and lifespan wiring land here in later phases."""

from fastapi import FastAPI

app = FastAPI(title="Naverland Recommender", version="0.0.1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
