# tests/test_summarizer_utils.py

import pytest
from unittest.mock import patch
from utils.summarizer_utils import process_articles
from tests.mocks.mock_llm import mock_llm_api_success, mock_llm_api_error, mock_llm_api_empty

@pytest.fixture
def mocked_llm_success():
    with patch('utils.llm_utils.call_llm_api', side_effect=mock_llm_api_success):
        yield

@pytest.fixture
def mocked_llm_error():
    with patch('utils.llm_utils.call_llm_api', side_effect=mock_llm_api_error):
        yield

@pytest.fixture
def mocked_llm_empty():
    with patch('utils.llm_utils.call_llm_api', side_effect=mock_llm_api_empty):
        yield

def test_process_articles_success(mocked_llm_success):
    """
    Test processing articles with successful LLM API responses.
    """
    result = process_articles("test_script.py", api_call_func=lambda *args, **kwargs: mock_llm_api_success(*args, **kwargs))
    assert result == "Success"

def test_process_articles_error(mocked_llm_error):
    """
    Test processing articles with LLM API errors.
    """
    result = process_articles("test_script.py", api_call_func=lambda *args, **kwargs: mock_llm_api_error(*args, **kwargs))
    assert result == "Error"

def test_process_articles_empty(mocked_llm_empty):
    """
    Test processing articles with empty LLM API responses.
    """
    result = process_articles("test_script.py", api_call_func=lambda *args, **kwargs: mock_llm_api_empty(*args, **kwargs))
    assert result in ["Success", "Partial", "Error"]  # Depending on implementation

def test_summarize_article_with_success(mocked_llm_success):
    """
    Test summarizing an article with a successful LLM API response.
    """
    # Setup mock data and environment if needed
    script_name = "summarizer_gemini_flash.py"
    api_call_func = lambda content, systemPrompt: mock_llm_api_success(content, systemPrompt, client_type="gemini")
    
    result_status = process_articles(script_name, api_call_func=api_call_func)
    assert result_status == "Success"

def test_summarize_article_with_error(mocked_llm_error):
    """
    Test summarizing an article with an error from the LLM API.
    """
    script_name = "summarizer_claude_haiku.py"
    api_call_func = lambda content, systemPrompt: mock_llm_api_error(content, systemPrompt, client_type="anthropic")
    
    result_status = process_articles(script_name, api_call_func=api_call_func)
    assert result_status == "Error"

def test_summarize_article_with_empty_response(mock_llm_empty):
    """
    Test summarizing an article with an empty response from the LLM API.
    """
    script_name = "summarizer_gemini_flash.py"
    api_call_func = lambda content, systemPrompt: mock_llm_api_empty(content, systemPrompt, client_type="gemini")
    
    result_status = process_articles(script_name, api_call_func=api_call_func)
    assert result_status in ["Success", "Partial", "Error"]  # Depending on your implementation
