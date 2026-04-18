"""FastAPI application with lifespan, CORS, and health endpoint."""

from contextlib import asynccontextmanager

import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, select

from backend.api.routes import (
    adjust,
    auth,
    config,
    feedback,
    generate,
    itineraries,
    scenarios,
    stream,
    test_results,
    test_runner,
)
from backend.config import get_settings
from backend.db import init_db as _db_mod
from backend.db.init_db import init_db
from backend.models.database import POI, Scenario


_FILENAME_TO_CITY = {
    "shanghai": "上海",
    "hangzhou": "杭州",
}


async def _seed_if_empty():
    import logging
    from pathlib import Path

    from backend.db.seed_pois import seed_pois_from_json

    logger = logging.getLogger(__name__)
    pois_dir = Path("data/pois")

    async with _db_mod.AsyncSessionFactory() as db:
        poi_count = await db.scalar(select(func.count(POI.id)))
        if poi_count == 0:
            for poi_file in sorted(pois_dir.glob("*.json")):
                city_name = _FILENAME_TO_CITY.get(poi_file.stem)
                if not city_name:
                    continue
                try:
                    await seed_pois_from_json(str(poi_file), city_name)
                    logger.info("Seeded POIs from %s for %s", poi_file.name, city_name)
                except Exception:
                    logger.exception("Failed to seed %s", poi_file.name)

        scenario_count = await db.scalar(select(func.count(Scenario.id)))
        if scenario_count == 0:
            with open("data/scenarios/scenarios.json", encoding="utf-8") as f:
                scenarios_data = json.load(f)
            for s in scenarios_data:
                db.add(
                    Scenario(
                        id=s["id"],
                        name=s["name"],
                        description=s["description"],
                        user_input=s["user_input"],
                        city=s["city"],
                        tags=json.dumps(s.get("tags", []), ensure_ascii=False),
                    )
                )
            await db.commit()
            logger.info("Seeded %d scenarios", len(scenarios_data))


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.environment == "production":
        if not settings.jwt_secret_key or settings.jwt_secret_key == "dev-only-secret-key-do-not-use-in-production":
            raise RuntimeError(
                "FATAL: JWT_SECRET_KEY must be set in production. "
                "Set JWT_SECRET_KEY in .env or set ENVIRONMENT=development for local dev."
            )
    await init_db()
    await _seed_if_empty()
    yield


app = FastAPI(
    title="拾途 (Shí Tú)",
    description="Taste-based travel itinerary generator",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(generate.router, prefix="/api", tags=["generate"])
app.include_router(stream.router, prefix="/api", tags=["stream"])
app.include_router(scenarios.router, prefix="/api", tags=["scenarios"])
app.include_router(itineraries.router, prefix="/api", tags=["itineraries"])
app.include_router(config.router, prefix="/api", tags=["config"])
app.include_router(adjust.router, prefix="/api", tags=["adjust"])
app.include_router(feedback.router, prefix="/api", tags=["feedback"])
app.include_router(test_results.router, prefix="/api", tags=["test-results"])
app.include_router(test_runner.router, prefix="/api", tags=["test-runner"])


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "db": "connected"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
