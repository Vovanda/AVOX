from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    """
    Проверка состояния LLM & Vectorizer сервиса.
    """
    return {"status": "ok"}
