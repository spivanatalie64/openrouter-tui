import pytest
from unittest.mock import patch, MagicMock
from openrouter_client import _parse_stream_line, create_chat, OpenRouterError


def test_parse_stream_line_empty():
    assert _parse_stream_line("") == ("", None)
    assert _parse_stream_line("data: [DONE]") == ("", None)


def test_parse_stream_line_valid_json():
    raw = 'data: {"choices": [{"delta": {"content": "Hello"}}]}'
    assert _parse_stream_line(raw) == ("Hello", None)

    raw_text = 'data: {"choices": [{"text": " World"}]}'
    assert _parse_stream_line(raw_text) == (" World", None)


def test_parse_stream_line_with_usage():
    raw = 'data: {"choices": [{"delta": {"content": "Hello"}}], "usage": {"total_tokens": 10}}'
    assert _parse_stream_line(raw) == ("Hello", {"total_tokens": 10})


def test_parse_stream_line_invalid_json():
    raw = "data: {invalid json}"
    assert _parse_stream_line(raw) == ("{invalid json}", None)


def test_parse_stream_line_bytes():
    raw = b'data: {"choices": [{"delta": {"content": "!"}}]}'
    assert _parse_stream_line(raw) == ("!", None)


def test_create_chat_no_api_key():
    with pytest.raises(OpenRouterError, match="Missing OpenRouter API key"):
        create_chat("", [])


@patch("openrouter_client.requests.post")
def test_create_chat_non_stream(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Hi there!"}}],
        "usage": {"total_tokens": 5},
    }
    mock_post.return_value = mock_resp

    result = create_chat("fake-key", [{"role": "user", "content": "hi"}])
    assert result["content"] == "Hi there!"
    assert result["usage"]["total_tokens"] == 5
    mock_post.assert_called_once()


@patch("openrouter_client.requests.post")
def test_create_chat_stream(mock_post):
    mock_resp = MagicMock()
    mock_resp.iter_lines.return_value = [
        b'data: {"choices": [{"delta": {"content": "Hello"}}]}',
        b'data: {"choices": [{"delta": {"content": " stream"}}], "usage": {"total_tokens": 15}}',
        b"data: [DONE]",
    ]
    mock_post.return_value.__enter__.return_value = mock_resp

    result_gen = create_chat("fake-key", [], stream=True)
    results = list(result_gen)
    assert results == [("Hello", None), (" stream", {"total_tokens": 15})]


def test_parse_stream_line_bytes_error():
    raw = b"data: \xff\xfe"
    assert _parse_stream_line(raw) == ("", None)


@patch("openrouter_client.requests.post")
def test_create_chat_list_models(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"choices": [{"message": {"content": "Hi"}}]}
    mock_post.return_value = mock_resp

    create_chat("fake-key", [], model=["m1", "m2"])
    assert mock_post.call_args[1]["json"]["models"] == ["m1", "m2"]


@patch("openrouter_client.requests.post")
def test_create_chat_fallback_parsing(mock_post):
    # Test choices without message but with text
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"choices": [{"text": "fallback text"}]}
    mock_post.return_value = mock_resp

    result = create_chat("fake-key", [])
    assert result["content"] == "fallback text"

    # Test full fallback to json dump
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"error": "bad"}
    mock_post.return_value = mock_resp

    result = create_chat("fake-key", [])
    assert '{"error": "bad"}' in result["content"]


@patch("openrouter_client.requests.post")
def test_create_chat_network_error(mock_post):
    import requests

    mock_post.side_effect = requests.exceptions.ConnectionError("fail")

    with pytest.raises(OpenRouterError, match="Network error"):
        create_chat("fake-key", [])

