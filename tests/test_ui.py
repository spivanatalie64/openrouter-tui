from unittest.mock import patch, MagicMock
from main import main


@patch("main.PromptSession")
@patch("main.Console")
@patch("main.create_chat")
@patch("main.os.getenv")
@patch("main.load_last_messages")
@patch("main.choose_model")
def test_main_loop_commands(
    mock_choose_model,
    mock_load,
    mock_getenv,
    mock_create,
    mock_console,
    mock_session_cls,
):
    # Setup mocks
    mock_getenv.return_value = "fake-api-key"
    mock_load.return_value = None
    mock_choose_model.return_value = "gpt-4"

    mock_session = MagicMock()
    mock_session_cls.return_value = mock_session

    # Simulate user entering commands then exiting
    # 1. /clear
    # 2. /save
    # 3. /export
    # 4. /model
    # 5. Ctrl-C (KeyboardInterrupt)
    mock_session.prompt.side_effect = [
        "/clear",
        "/save",
        "/export",
        "/model",
        KeyboardInterrupt,
    ]

    with (
        patch("main.save_conversation") as mock_save_conv,
        patch("sys.argv", ["main.py"]),
    ):
        main()

    # Verify commands were handled
    # We can check if specific functions were called
    assert mock_save_conv.called
    assert mock_choose_model.call_count == 2  # Once at start, once for /model
