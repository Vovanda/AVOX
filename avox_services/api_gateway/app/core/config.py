from dotenv import load_dotenv
import os

load_dotenv()

PROJECT_NAME = os.getenv("PROJECT_NAME", "AVOX API Gateway")
PROJECT_VERSION = os.getenv("PROJECT_VERSION", "0.1.0")