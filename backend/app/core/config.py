from pathlib import Path
from pydantic_settings import BaseSettings

_BASE_DIR = Path(__file__).parent.parent.parent  # backend/


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{_BASE_DIR}/data/database.db"
    thumbnail_dir: str = str(_BASE_DIR / "data" / "thumbnails")

    model_config = {"env_file": str(_BASE_DIR / ".env")}


settings = Settings()
