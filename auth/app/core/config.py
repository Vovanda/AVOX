from dotenv import load_dotenv
import os

load_dotenv()

PROJECT_NAME = os.getenv("PROJECT_NAME", "AVOX Auth Service")
PROJECT_VERSION = os.getenv("PROJECT_VERSION", "0.1.0")