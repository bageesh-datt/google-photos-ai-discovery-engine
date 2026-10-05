import pytest
from unittest.mock import patch, MagicMock
from backend.app.services.llm_client import clean_json_text, LLMClient

def test_clean_json_text_with_markdown_fences():
    fenced_input = "```json\n{\"relevant\": true, \"reason\": \"Test\"}\n```"
    cleaned = clean_json_text(fenced_input)
    assert cleaned == '{"relevant": true, "reason": "Test"}'


def test_clean_json_text_without_language_tag():
    fenced_input = "```\n[{\"id\": \"R01\"}]\n```"
    cleaned = clean_json_text(fenced_input)
    assert cleaned == '[{"id": "R01"}]'


def test_provider_auto_detection():
    # Groq detection via model name
    groq_client_1 = LLMClient(api_key="gsk_dummy", model="llama-3.3-70b-versatile")
    assert groq_client_1.get_provider() == "groq"

    # Groq detection via API key prefix
    groq_client_2 = LLMClient(api_key="gsk_12345", model="custom-model")
    assert groq_client_2.get_provider() == "groq"

    # Gemini detection via model name
    gemini_client = LLMClient(api_key="AIzaSy_dummy", model="gemini-2.5-flash")
    assert gemini_client.get_provider() == "gemini"

    # OpenAI detection
    openai_client = LLMClient(api_key="sk-dummy", model="gpt-4o-mini")
    assert openai_client.get_provider() == "openai"


def test_groq_api_call_structure():
    client = LLMClient(api_key="gsk_test_key_123", model="llama-3.3-70b-versatile")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "{\"relevant\": true}"}}]
    }
    mock_response.raise_for_status.return_value = None

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        result = client.generate_json("Test prompt")
        assert result == {"relevant": True}
        
        # Verify endpoint URL, headers, and payload
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.groq.com/openai/v1/chat/completions"
        assert kwargs["headers"]["Authorization"] == "Bearer gsk_test_key_123"
        assert kwargs["json"]["model"] == "llama-3.3-70b-versatile"
        assert kwargs["json"]["messages"][0]["content"] == "Test prompt"


def test_gemini_api_call_structure():
    client = LLMClient(api_key="AIzaSy_test_key", model="gemini-2.5-flash")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "{\"relevant\": true}"}]}}]
    }
    mock_response.raise_for_status.return_value = None

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        result = client.generate_json("Test prompt")
        assert result == {"relevant": True}
        
        # Verify Gemini endpoint URL
        args, kwargs = mock_post.call_args
        assert "generativelanguage.googleapis.com" in args[0]
        assert "gemini-2.5-flash" in args[0]


def test_llm_client_fallback_mode():
    client = LLMClient(api_key="", model="llama-3.3-70b-versatile")
    fallback_data = {"test": "data"}
    res = client.generate_json("Test prompt", mock_fallback=fallback_data)
    assert res == fallback_data


def test_llm_client_missing_key_raises_value_error():
    client = LLMClient(api_key="", model="llama-3.3-70b-versatile")
    with pytest.raises(ValueError) as exc_info:
        client.generate_json("Test prompt", mock_fallback=None)
    assert "No valid LLM_API_KEY provided" in str(exc_info.value)
