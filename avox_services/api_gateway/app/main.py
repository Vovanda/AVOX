from fastapi import FastAPI

from api_gateway.app.api.routers.rag import router as rag_router
from api_gateway.app.api.routers.routes import router as base_router
from api_gateway.app.core import config

app = FastAPI(
    title=config.PROJECT_NAME,
    version=config.PROJECT_VERSION,
    docs_url="/swagger",
    redoc_url=None,
)

# Подключаем роутеры
app.include_router(base_router)
app.include_router(rag_router)
