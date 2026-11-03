"""Tests for LLM Client configuration and connectivity."""

from unittest.mock import MagicMock, patch

from src.config import Settings
from src.llm.client import LLMClient


def test_settings_validation():
    """Verify that Settings requires groq_api_key and sets defaults."""
    s = Settings(groq_api_key="gsk_test_key_12345")
    assert s.groq_api_key == "gsk_test_key_12345"
    assert s.default_model == "openai/gpt-oss-120b"
    assert s.llm_temperature == 0.1


def test_client_generate_mocked():
    """Verify LLMClient forwards messages properly to Groq SDK."""
    mock_groq = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Mocked Agent Response"
    mock_groq.chat.completions.create.return_value.choices = [mock_choice]

    # patch replaces Groq(...) with our mock during this test block
    with patch("src.llm.client.Groq", return_value=mock_groq):
        client = LLMClient(api_key="mock_key")
        messages = [{"role": "user", "content": "Hello"}]
        result = client.generate(messages)

        assert result == "Mocked Agent Response"
        mock_groq.chat.completions.create.assert_called_once()


def test_client_stream_mocked():
    """Verify LLMClient.stream yields chunks as they arrive."""
    mock_groq = MagicMock()
    chunk1 = MagicMock()
    chunk1.choices = [MagicMock(delta=MagicMock(content="Hello "))]
    chunk2 = MagicMock()
    chunk2.choices = [MagicMock(delta=MagicMock(content="World!"))]
    mock_groq.chat.completions.create.return_value = [chunk1, chunk2]

    with patch("src.llm.client.Groq", return_value=mock_groq):
        client = LLMClient(api_key="mock_key")
        messages = [{"role": "user", "content": "Hi"}]
        tokens = list(client.stream(messages))

        assert tokens == ["Hello ", "World!"]
        mock_groq.chat.completions.create.assert_called_once()
