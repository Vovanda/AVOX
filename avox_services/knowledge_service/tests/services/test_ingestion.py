import uuid
from unittest.mock import patch, MagicMock

import numpy as np
from knowledge_service.app.api.schemas.document import DocumentIngestResponse

from knowledge_service.app.models.enums import SourceType, DocAccessLevel
from knowledge_service.app.services import DocumentIngestor


@patch("knowledge_service.app.services.ingestion.SentenceTransformer")
@patch("knowledge_service.app.services.ingestion.AutoTokenizer")
@patch("knowledge_service.app.services.ingestion.sent_tokenize")
def test_ingest_successful_flow(
    mock_sent_tokenize,
    mock_tokenizer_class,
    mock_model_class,
    sample_text,
    mock_db_session
):
    # Arrange: подменяем модель
    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([[0.1] * 384] * 2)  # эмуляция двух эмбеддингов
    mock_model_class.return_value = mock_model

    # Подменяем токенайзер
    mock_tokenizer_instance = MagicMock()
    mock_tokenizer_instance.return_value = {
        'input_ids': [[0] * 256, [1] * 256],
        'offset_mapping': [[(0, 50), (51, 100)], [(100, 150), (151, 200)]]
    }
    mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer_instance
    mock_tokenizer_class.return_value = mock_tokenizer_instance

    # Подменяем разбиение на предложения
    mock_sent_tokenize.return_value = sample_text.split(". ")

    # Создаём инжестор
    ingestor = DocumentIngestor(mock_db_session)

    # Входные данные
    company_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    title = "Test Doc"

    # Act
    result = ingestor.ingest(
        text=sample_text,
        title=title,
        company_id=company_id,
        owner_id=owner_id,
        source_type=SourceType.TEXT_INPUT,
        access_level=DocAccessLevel.RESTRICTED,
    )

    # Assert
    assert isinstance(result, DocumentIngestResponse)
    assert result.status == "success"
    assert result.title == title

    # Проверяем, что вызовы были
    assert mock_model.encode.called
    assert mock_db_session.add.called
    assert mock_db_session.flush.called
    assert mock_db_session.commit.called
