from dotenv import load_dotenv
import os

load_dotenv()

PROJECT_NAME = os.getenv("PROJECT_NAME", "AVOX Auth Service")
PROJECT_VERSION = os.getenv("PROJECT_VERSION", "0.1.0")

# VK OAuth credentials
VK_CLIENT_ID = os.getenv("VK_CLIENT_ID")
VK_CLIENT_SECRET = os.getenv("VK_CLIENT_SECRET")
VK_REDIRECT_URI = os.getenv("VK_REDIRECT_URI")

# Google OAuth credentials
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
