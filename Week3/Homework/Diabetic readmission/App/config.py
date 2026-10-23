import os
from pathlib import Path
from dotenv import load_dotenv
from .errors import ConfigurationError
PROJECT_ROOT = Path(__file__).resolve().parent.parent
for directory in (PROJECT_ROOT, *PROJECT_ROOT.parents):
    env_file = directory / ".env"
    if env_file.is_file():
        load_dotenv(env_file)
        break

def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url: raise ConfigurationError("DATABASE_URL is not set. Copy .env.example to .env and fill it in.")
    return url

def get_dataset_path() -> Path:
    path = Path(os.getenv("DATASET_PATH", "data/diabetic_data.csv"))
    return path if path.is_absolute() else PROJECT_ROOT / path

APP_NAME = os.getenv("APP_NAME", "Diabetes Readmission Intervention Queue")
APP_ENV = os.getenv("APP_ENV", "local")
