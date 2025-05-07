from fastapi import FastAPI

from auth.app.api.routes import router
from auth.app.core import config

app = FastAPI(
    title=config.PROJECT_NAME,
    version=config.PROJECT_VERSION,
    docs_url="/swagger",
    redoc_url=None
)

app.include_router(router, prefix="/api/auth")

@app.get("/health")
async def health_check():
    '''
    Healthcheck endpoint.
    '''
    return {"status": "ok"}
