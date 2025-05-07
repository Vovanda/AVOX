import pytest

from auth.app.services import session
from auth.tests.mocks.mock_vk_oauth_provider import MockVkOAuthProvider


@pytest.fixture(autouse=True)
def clear_sessions():
    session.SESSIONS.clear()
    yield
    session.SESSIONS.clear()

@pytest.fixture
def mock_vk_provider():
    return MockVkOAuthProvider()