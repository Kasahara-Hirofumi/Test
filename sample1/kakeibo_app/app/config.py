import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


@dataclass(frozen=True)
class Settings:
    app_name: str
    database_url: str
    log_file_path: Path
    template_dir: Path
    static_dir: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    data_dir = BASE_DIR / "data"
    logs_dir = BASE_DIR / "logs"
    data_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    db_raw = Path(os.getenv("DB_PATH", str(data_dir / "kakeibo.db")))
    log_raw = Path(os.getenv("LOG_PATH", str(logs_dir / "app.log")))

    db_path = db_raw if db_raw.is_absolute() else (BASE_DIR / db_raw).resolve()
    log_path = log_raw if log_raw.is_absolute() else (BASE_DIR / log_raw).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    return Settings(
        app_name=os.getenv("APP_NAME", "デモ用 家計簿アプリ"),
        database_url=f"sqlite:///{db_path}",
        log_file_path=log_path,
        template_dir=BASE_DIR / "app" / "templates",
        static_dir=BASE_DIR / "app" / "static",
    )
