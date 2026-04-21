import json
from unittest.mock import patch, MagicMock
from pathlib import Path

from main import choose_model, load_last_messages, save_conversation


def test_choose_model():
    mock_session = MagicMock()
    mock_session.prompt.return_value = "my-custom-model "
    result = choose_model(mock_session, "default-model")
    assert result == "my-custom-model"

    mock_session.prompt.return_value = ""
    result = choose_model(mock_session, "default-model")
    assert result == "default-model"


def test_load_last_messages(tmp_path):
    history_file = tmp_path / "history.json"

    # Missing file
    assert load_last_messages(history_file) is None

    # Empty conversations list
    history_file.write_text('{"conversations": []}')
    assert load_last_messages(history_file) is None

    # Valid messages (new format)
    messages = [{"role": "user", "content": "hello"}]
    history_file.write_text(json.dumps({"conversations": [{"messages": messages}]}))
    assert load_last_messages(history_file) == messages

    # Legacy format (list of conversations, which were lists of messages)
    history_file.write_text(json.dumps([[{"role": "user", "content": "hi"}]]))
    assert load_last_messages(history_file) == [{"role": "user", "content": "hi"}]

    # Invalid JSON
    history_file.write_text("definitely not json")
    assert load_last_messages(history_file) is None


def test_save_conversation(tmp_path):
    history_file = tmp_path / "history.json"
    messages = [{"role": "user", "content": "hello"}]

    save_conversation(history_file, messages)
    assert history_file.exists()

    data = json.loads(history_file.read_text())
    assert "conversations" in data
    assert len(data["conversations"]) == 1
    assert data["conversations"][0]["messages"] == messages
    assert "timestamp" in data["conversations"][0]


def test_save_conversation_ignores_errors(tmp_path):
    bad_path = tmp_path / "file.json"
    with patch.object(
        Path, "write_text", side_effect=PermissionError("Permission denied")
    ):
        save_conversation(bad_path, [])
        # Should not raise exception


import os
import sys


@patch.dict(os.environ, clear=True)
def test_main_no_api_key(capsys):
    with patch.object(sys, "argv", ["main.py"]):
        from main import main

        main()
    out, _ = capsys.readouterr()
    assert "Please set the OPENROUTER_API_KEY" in out


@patch("main.PromptSession")
@patch.dict(os.environ, {"OPENROUTER_API_KEY": "fake"})
@patch("main.create_chat")
def test_main_chat_flow(mock_create_chat, mock_session_cls, tmp_path):
    history_file = tmp_path / "history.json"
    mock_session = MagicMock()
    # 1. Startup model choice
    # 2. User message
    # 3. /save command
    # 4. /clear command
    # 5. /export command
    # 6. /model command
    # 7. Model choice for /model
    # 8. KeyboardInterrupt to exit
    mock_session.prompt.side_effect = [
        "m1",
        "hello",
        "/save",
        "/clear",
        "/export",
        "/model",
        "m2",
        KeyboardInterrupt(),
    ]
    mock_session_cls.return_value = mock_session

    # mock_create_chat yields (chunk, usage)
    mock_create_chat.return_value = [("Hi", None), ("!", {"total_tokens": 10})]

    from main import main

    with patch.object(sys, "argv", ["main.py", "--history-file", str(history_file)]):
        main()

    assert history_file.exists()
    # Check if export file exists
    exports = list(Path.cwd().glob("conversation_export_*.md"))
    for f in exports:
        f.unlink()

