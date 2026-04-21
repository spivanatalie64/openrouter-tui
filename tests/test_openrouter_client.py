import pytest
from unittest.mock import patch, MagicMock
from openrouter_client import _parse_stream_line, create_chat, OpenRouterError


def test_parse_stream_line_empty():
    assert _parse_stream_line("") == ""
    assert _parse_stream_line("data: [DONE]") == ""


def test_parse_stream_line_valid_json():
    raw = 'data: {"choices": [{"delta": {"content": "Hello"}}]}'
    assert _parse_stream_line(raw) == "Hello"

    raw_text = 'data: {"choices": [{"text": " World"}]}'
    assert _parse_stream_line(raw_text) == " World"


def test_parse_stream_line_invalid_json():
    raw = "data: {invalid json}"
    assert _parse_stream_line(raw) == "{invalid json}"


def test_parse_stream_line_bytes():
    raw = b'data: {"choices": [{"delta": {"content": "!"}}]}'
    assert _parse_stream_line(raw) == "!"


def test_create_chat_no_api_key():
    with pytest.raises(OpenRouterError, match="Missing OpenRouter API key"):
        create_chat("", [])


@patch("openrouter_client.requests.post")
def test_create_chat_non_stream(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"choices": [{"message": {"content": "Hi there!"}}]}
    mock_post.return_value = mock_resp

    result = create_chat("fake-key", [{"role": "user", "content": "hi"}])
    assert result == ["Hi there!"]
    mock_post.assert_called_once()
    assert mock_post.call_args[1]["headers"]["Authorization"] == "Bearer fake-key"
    assert mock_post.call_args[1]["json"]["stream"] is False
    assert mock_post.call_args[1]["json"]["model"] == "openai/gpt-5.4"


@patch("openrouter_client.requests.post")
def test_create_chat_super_model(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"choices": [{"message": {"content": "Hi there!"}}]}
    mock_post.return_value = mock_resp

    create_chat("fake-key", [], model="super-model")
    assert "models" in mock_post.call_args[1]["json"]
    assert isinstance(mock_post.call_args[1]["json"]["models"], list)


@patch("openrouter_client.requests.post")
def test_create_chat_stream(mock_post):
    mock_resp = MagicMock()
    # Mocking iter_lines to yield a few chunks
    mock_resp.iter_lines.return_value = [
        b'data: {"choices": [{"delta": {"content": "Hello"}}]}',
        b'data: {"choices": [{"delta": {"content": " stream"}}]}',
        b"data: [DONE]",
    ]
    # __enter__ and __exit__ for the context manager
    mock_post.return_value.__enter__.return_value = mock_resp

    result_gen = create_chat("fake-key", [], stream=True)
    results = list(result_gen)
    assert results == ["Hello", " stream"]


@patch("openrouter_client.requests.post")
def test_create_chat_http_error(mock_post):
    import requests

    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "404 Client Error"
    )
    mock_post.return_value = mock_resp

    with pytest.raises(
        OpenRouterError, match="OpenRouter HTTP error: 404 Client Error"
    ):
        create_chat("fake-key", [])


@patch("openrouter_client.requests.post")
def test_create_chat_network_error(mock_post):
    import requests

    mock_post.side_effect = requests.exceptions.ConnectionError("Connection Refused")

    with pytest.raises(OpenRouterError, match="Network error when calling OpenRouter"):
        create_chat("fake-key", [])
