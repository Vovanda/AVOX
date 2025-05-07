from dotenv import load_dotenv
import os

load_dotenv()

PROJECT_NAME = os.getenv("PROJECT_NAME", "AVOX LLM & Vectorizer")
PROJECT_VERSION = os.getenv("PROJECT_VERSION", "0.1.0")
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")