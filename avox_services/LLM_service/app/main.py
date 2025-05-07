from fastapi import FastAPI
from api.routes import router
from core import config

app = FastAPI(
    title=config.PROJECT_NAME,
    version=config.PROJECT_VERSION,
    docs_url="/swagger",
    redoc_url=None
)

app.include_router(router)