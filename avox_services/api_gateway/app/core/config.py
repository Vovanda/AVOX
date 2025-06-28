import os

from dotenv import load_dotenv

env = os.getenv("APP_ENV", "local")
load_dotenv(dotenv_path=f".env.{env}", override=True)

PROJECT_NAME = os.getenv("PROJECT_NAME", "AVOX API Gateway")
PROJECT_VERSION = os.getenv("PROJECT_VERSION", "0.1.0")