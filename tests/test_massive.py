import pytest
from unittest.mock import MagicMock
from main import choose_model
from openrouter_client import _parse_stream_line


# 10,000 tests for custom model selection
@pytest.mark.parametrize("i", range(10000))
def test_choose_model_massive_custom(i):
    mock_session = MagicMock()
    mock_session.prompt.return_value = f"custom-model-{i} "
    result = choose_model(mock_session, "default-model")
    assert result == f"custom-model-{i}"


# 10,000 tests for default model fallback
@pytest.mark.parametrize("i", range(10000))
def test_choose_model_massive_default(i):
    mock_session = MagicMock()
    mock_session.prompt.return_value = "   "
    result = choose_model(mock_session, f"default-{i}")
    assert result == f"default-{i}"


# 10,000 tests for stream parsing with various data
@pytest.mark.parametrize("i", range(10000))
def test_parse_stream_line_various(i):
    if i % 2 == 0:
        data = f'data: {{"choices": [{{"delta": {{"content": "chunk-{i}"}}}}]}}'
        assert _parse_stream_line(data) == (f"chunk-{i}", None)
    else:
        junk_data = f"data: {{garbage-{i}}}"
        assert _parse_stream_line(junk_data) == (f"{{garbage-{i}}}", None)
