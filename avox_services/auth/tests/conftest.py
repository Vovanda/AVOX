import pytest

from auth.tests.mocks.mock_vk_oauth_provider import MockVkOAuthProvider


@pytest.fixture
def mock_vk_provider():
    return MockVkOAuthProvider()