from fastapi import FastAPI

from app.api.routes.analysis import router as analysis_router
from app.api.routes.health import router as health_router
from app.api.routes.logs import router as logs_router
from app.core.logging import configure_logging
from app.db.sqlite import init_db


def create_app() -> FastAPI:
    configure_logging()
    init_db()

    app = FastAPI(title="Emergent Fraud Lab API")
    app.include_router(health_router)
    app.include_router(analysis_router)
    app.include_router(logs_router)
    return app


app = create_app()
