from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    """
    Проверка состояния Task Manager сервиса.
    """
    return {"status": "ok"}
