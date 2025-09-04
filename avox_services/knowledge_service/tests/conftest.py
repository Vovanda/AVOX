import uuid
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def sample_text():
    return (
        "This is the first sentence. Here is the second sentence. "
        "Third sentence comes next. Then the fourth one. And finally the fifth. "
        "Here is the sixth sentence. Seventh is also here."
    )


@pytest.fixture
def mock_db_session():
    """
    Возвращает замоканный SQLAlchemy Session
    с поддержкой .add, .flush, .commit.
    """
    session = MagicMock()
    session.add = MagicMock()
    session.flush = MagicMock()
    session.commit = MagicMock()

    # Автоинкрементируемые ID-шники
    mock_doc = MagicMock()
    mock_doc.id = uuid.uuid4()

    mock_chunk = MagicMock()
    mock_chunk.id = uuid.uuid4()

    session.add.side_effect = lambda obj: setattr(obj, 'id', uuid.uuid4())

    return session