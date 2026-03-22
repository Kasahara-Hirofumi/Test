import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import init_db, init_engine
from app.routers import api, pages


def setup_logging(log_file_path: str) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def create_app(database_url: str | None = None) -> FastAPI:
    settings = get_settings()
    setup_logging(str(settings.log_file_path))
    init_engine(database_url or settings.database_url)
    init_db()

    app = FastAPI(title=settings.app_name)
    app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")

    app.include_router(pages.router)
    app.include_router(api.router)
    logging.getLogger(__name__).info("Application started")
    return app


app = create_app()
