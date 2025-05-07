from fastapi import FastAPI
from app.api.routes import router
from app.core import config

app = FastAPI(
    title=config.PROJECT_NAME,
    version=config.PROJECT_VERSION,
    docs_url="/swagger",
    redoc_url=None
)

app.include_router(router)