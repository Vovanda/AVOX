from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    """
    Проверка состояния Auth сервиса.
    """
    return {"status": "ok"}
