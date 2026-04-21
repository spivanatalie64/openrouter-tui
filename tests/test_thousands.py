import pytest
from unittest.mock import MagicMock
from main import choose_model
from openrouter_client import _parse_stream_line


# Generate 2000 tests for custom model selection
@pytest.mark.parametrize("i", range(2000))
def test_choose_model_massive_custom(i):
    mock_session = MagicMock()
    mock_session.prompt.return_value = f"custom-model-{i} "
    result = choose_model(mock_session, "default-model")
    assert result == f"custom-model-{i}"


# Generate 2000 tests for default model fallback
@pytest.mark.parametrize("i", range(2000))
def test_choose_model_massive_default(i):
    mock_session = MagicMock()
    mock_session.prompt.return_value = "   "
    result = choose_model(mock_session, f"default-{i}")
    assert result == f"default-{i}"


# Generate 1000 tests for stream parsing with junk data
@pytest.mark.parametrize("i", range(1000))
def test_parse_stream_line_junk(i):
    junk_data = f"data: {{garbage-{i}}}"
    assert _parse_stream_line(junk_data) == f"{{garbage-{i}}}"
