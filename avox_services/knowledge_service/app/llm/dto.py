from enum import Enum
from typing import TypedDict, List, Optional


# Уровень достоверности факта
class FactCertainty(str, Enum):
    HIGH = "high"            # Факт подтверждён с высокой уверенностью
    MEDIUM = "medium"        # Факт вероятен, но есть небольшие сомнения
    LOW = "low"              # Факт с низкой достоверностью
    CONTRADICTS = "contradicts"  # Факт противоречит имеющимся данным

# Чанк документа, который подается на обработку LLM
class DocumentContextChunk(TypedDict):
    chunk_id: str            # Уникальный идентификатор чанка
    chunk_text: str          # Текстовое содержание чанка

# Структура факта
class Fact(TypedDict):
    id: Optional[str]        # Уникальный идентификатор факта, может быть None для новых фактов
    fact: str                # Краткое описание факта
    certainty: FactCertainty # Уровень достоверности факта
    reasoning: str           # Краткое объяснение или источник факта

# Контракт запроса к LLM
class LLMDocumentRequest(TypedDict):
    task: str                                # Инструкция для модели
    question: str                            # Вопрос пользователя
    document_context: List[DocumentContextChunk]  # Список чанков документов для анализа
    previous_facts: List[Fact]              # Список известных фактов до текущего запроса
    previous_answer: str                     # Синтезированный ответ по предыдущим документам
    dialog_history: str                      # Суммарная история переписки пользователя с системой

# Контракт ответа от LLM
class LLMDocumentResponse(TypedDict):
    answer: str               # Синтезированный ответ на вопрос
    reasoning: str            # Логическая цепочка рассуждений модели
    new_facts: List[Fact]     # Список новых извлечённых фактов
    updated_facts: List[Fact] # Список обновлённых фактов (с существующими id)
    can_answer: bool          # Флаг, может ли LLM дать ответ на вопрос
