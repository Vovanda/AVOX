import os
from urllib.parse import urlparse, urlunparse

from dotenv import load_dotenv

base_dir = os.path.dirname(os.path.abspath(__file__))  # knowledge_service/app/core
project_dir = os.path.dirname(os.path.dirname(base_dir))  # knowledge_service

env = os.getenv("APP_ENV", "local")

load_dotenv(dotenv_path=os.path.join(project_dir, f".env.{env}"), override=True)
load_dotenv(dotenv_path=os.path.join(project_dir, f".env.{env}.secrets"), override=True)


def get_database_url():
    app_env = os.getenv("APP_ENV", "local")
    db_driver = os.getenv("DB_DRIVER", "psycopg")
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Определяем путь к паролю
    password = ""
    secret_file = os.getenv("POSTGRES_PASSWORD_FILE")
    if secret_file and os.path.isfile(secret_file):
        # Используется в Docker-контейнере
        password_path = secret_file
    else:
        # Используется вне Docker
        password_path = os.path.join(
            project_dir,
            "secrets", app_env,
            "db_password.txt")

    if os.path.isfile(password_path):
        with open(password_path, "r") as f:
            password = f.read().strip()

    # Собираем URL
    db_url_env = os.getenv("DATABASE_URL")
    if db_url_env:
        parsed = urlparse(db_url_env)
        scheme = f"postgresql+{db_driver}"
        if password:
            netloc = f"{parsed.username}:{password}@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            rebuilt = parsed._replace(scheme=scheme, netloc=netloc)
            return urlunparse(rebuilt)
        else:
            return db_url_env

    # Фолбэк URL
    return f"postgresql+{db_driver}://postgres:{password}@localhost:5432/avox_kno"

PROJECT_NAME = os.getenv("PROJECT_NAME", "AVOX Knowledge")
PROJECT_VERSION = os.getenv("PROJECT_VERSION", "0.1.0")
REDIS_URL = os.getenv("REDIS_URL")
DATABASE_URL = get_database_url()

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")
VLLM_MODEL_PATH = os.getenv("VLLM_MODEL_PATH", "local/t5-model")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "")
OPENROUTER_SITE_NAME = os.getenv("OPENROUTER_SITE_URL", "")