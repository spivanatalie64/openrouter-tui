from unittest.mock import patch, MagicMock
from pathlib import Path
import json

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

    # Valid messages
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

    # Append another
    messages2 = [{"role": "user", "content": "hello 2"}]
    save_conversation(history_file, messages2)

    data = json.loads(history_file.read_text())
    assert len(data["conversations"]) == 2
    assert data["conversations"][1]["messages"] == messages2


def test_save_conversation_ignores_errors(tmp_path):
    # Pass a path that can't be written to. Just asserting it doesn't crash.
    bad_path = tmp_path / "file.json"
    with patch.object(
        Path, "write_text", side_effect=PermissionError("Permission denied")
    ):
        save_conversation(bad_path, [])
        # Should not raise exception

import os
import sys
from main import _default_history_path, main

def test_default_history_path():
    path = _default_history_path()
    assert path.name == "history.json"
    assert ".openrouter_tui" in str(path)

@patch.dict(os.environ, clear=True)
def test_main_no_api_key(capsys):
    with patch.object(sys, "argv", ["main.py"]):
        main()
    out, _ = capsys.readouterr()
    assert "Please set the OPENROUTER_API_KEY" in out

@patch("main.PromptSession")
@patch.dict(os.environ, {"OPENROUTER_API_KEY": "fake"})
def test_main_exit_immediately(mock_session):
    mock_instance = MagicMock()
    mock_instance.prompt.side_effect = KeyboardInterrupt()
    mock_session.return_value = mock_instance
    with patch.object(sys, "argv", ["main.py"]):
        main()

@patch("main.PromptSession")
@patch.dict(os.environ, {"OPENROUTER_API_KEY": "fake"})
@patch("main.create_chat")
def test_main_chat_flow(mock_create_chat, mock_session, tmp_path):
    history_file = tmp_path / "history.json"
    mock_instance = MagicMock()
    mock_instance.prompt.side_effect = [
        "model", # choose_model at startup
        "hello", # user message
        "/model", # switch model command
        "new-model", # choose_model for /model
        "/save", # save command
        "  ", # empty message, should be ignored
        KeyboardInterrupt() # exit
    ]
    mock_session.return_value = mock_instance
    mock_create_chat.return_value = ["Hi", " there"]
    with patch.object(sys, "argv", ["main.py", "--history-file", str(history_file)]):
        main()
    assert history_file.exists()

@patch("main.PromptSession")
@patch.dict(os.environ, {"OPENROUTER_API_KEY": "fake"})
@patch("main.create_chat")
def test_main_chat_error(mock_create_chat, mock_session, tmp_path):
    history_file = tmp_path / "history.json"
    mock_instance = MagicMock()
    mock_instance.prompt.side_effect = [
        "model", # choose_model at startup
        "hello", # user message
        KeyboardInterrupt() # exit
    ]
    mock_session.return_value = mock_instance
    mock_create_chat.side_effect = Exception("API Error")
    with patch.object(sys, "argv", ["main.py", "--history-file", str(history_file)]):
        main()

@patch("main.PromptSession")
@patch.dict(os.environ, {"OPENROUTER_API_KEY": "fake"})
def test_main_load_history(mock_session, tmp_path):
    history_file = tmp_path / "history.json"
    history_file.write_text('{"conversations": [{"messages": [{"role": "user", "content": "hi"}]}]}')
    mock_instance = MagicMock()
    # prompt for "Load last conversation? (y/N): "
    # then choose_model
    # then KeyboardInterrupt
    mock_instance.prompt.side_effect = ["y", "model", KeyboardInterrupt()]
    mock_session.return_value = mock_instance
    with patch.object(sys, "argv", ["main.py", "--history-file", str(history_file)]):
        main()

