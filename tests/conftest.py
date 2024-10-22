# tests/conftest.py

import pytest
from unittest.mock import patch
from tests.mocks.mock_llm import mock_llm_api_success, mock_llm_api_error, mock_llm_api_empty

@pytest.fixture
def mock_llm_success():
    with patch('utils.llm_utils.call_llm_api', side_effect=mock_llm_api_success):
        yield

@pytest.fixture
def mock_llm_error():
    with patch('utils.llm_utils.call_llm_api', side_effect=mock_llm_api_error):
        yield

@pytest.fixture
def mock_llm_empty():
    with patch('utils.llm_utils.call_llm_api', side_effect=mock_llm_api_empty):
        yield

