from fastapi import APIRouter

router = APIRouter(prefix="/api")


@router.get("/health", tags=["Health"])
async def health_check():
    """
    Проверка состояния API Gateway.
    """
    return {"status": "ok"}