from fastapi import FastAPI

from knowledge_service.app.api.routes import router
from knowledge_service.app.core import config

app = FastAPI(
    title=config.PROJECT_NAME,
    version=config.PROJECT_VERSION,
    docs_url="/swagger",
    redoc_url=None
)

app.include_router(router)


#if __name__ == "__main__":
#    import uvicorn
#    uvicorn.run("main:app", host="127.0.0.1", port=8003, log_level="info")
