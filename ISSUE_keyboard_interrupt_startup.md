Issue: Improper KeyboardInterrupt Handling at Startup

Description:
The application would crash or exit ungracefully if a `KeyboardInterrupt` (Ctrl+C) was triggered during the initial model selection or history restoration prompts. The logic was not consistently wrapped in a try-except block at the top level of the `main()` function.

Fix:
Wrapped the entire interactive block in `main.py` with a `try...except KeyboardInterrupt` handler to ensure a clean exit with a friendly message.

Resolution:
Fixed and verified with `tests/test_main.py` and `tests/test_ui.py`.

Author: Natalie Spiva <natalie@acreetionos.org>
