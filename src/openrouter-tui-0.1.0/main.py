#!/usr/bin/env python3
"""
OpenRouter TUI — a small, friendly terminal chat client for the OpenRouter API.

Written by Natalie Spiva <natalie@acreetionos.org>
Set OPENROUTER_API_KEY before running.
"""

import os
import json
from pathlib import Path
import argparse
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from openrouter_client import create_chat, MODELS


def choose_model(session, default="gpt-4o-mini"):
    prompt = "Choose a model (comma-separated list shown below). Press Enter to accept default.\n\n"
    for m in MODELS:
        prompt += f" - {m}\n"
    prompt += f"\nModel (default {default}): "
    return session.prompt(prompt, default=default).strip() or default


def _default_history_path() -> Path:
    return Path(os.path.expanduser("~")) / ".openrouter_tui" / "history.json"


def load_last_messages(history_path: Path):
    try:
        if not history_path.exists():
            return None
        data = json.loads(history_path.read_text(encoding="utf-8"))
        convos = data.get("conversations", []) if isinstance(data, dict) else data
        if not convos:
            return None
        last = convos[-1]
        return last.get("messages") if isinstance(last, dict) else last
    except Exception:
        return None


def save_conversation(history_path: Path, messages):
    try:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        existing = []
        if history_path.exists():
            try:
                existing = json.loads(history_path.read_text(encoding="utf-8"))
                if isinstance(existing, dict):
                    existing = existing.get("conversations", [])
            except Exception:
                existing = []
        # Append this conversation as a dict for readability
        existing.append({"messages": messages})
        # Write back as an object with conversations key for future extensibility
        out = {"conversations": existing}
        history_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    except Exception:
        # Persisting history should never crash the app; ignore errors.
        pass


def main():
    parser = argparse.ArgumentParser(description="OpenRouter TUI")
    parser.add_argument(
        "--history-file",
        default=None,
        help="Path to history file (default: ~/.openrouter_tui/history.json)",
    )
    args = parser.parse_args()

    history_path = (
        Path(args.history_file) if args.history_file else _default_history_path()
    )

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Please set the OPENROUTER_API_KEY environment variable and try again.")
        return

    session = PromptSession()

    # Load last conversation if available and offer to restore
    last_messages = load_last_messages(history_path)
    if last_messages:
        try:
            resp = session.prompt("Load last conversation? (y/N): ").strip().lower()
            if resp == "y":
                messages = last_messages
                print("Loaded last conversation. Continuing where you left off.\n")
            else:
                messages = [
                    {"role": "system", "content": "You are a helpful assistant."}
                ]
        except KeyboardInterrupt:
            print("\nTake care — goodbye!")
            return
    else:
        messages = [{"role": "system", "content": "You are a helpful assistant."}]

    # Let the user pick a model at startup
    model = choose_model(session)

    print(
        "\nWelcome to OpenRouter TUI — type a message and press Enter.\nType '/model' at any time to change the model. Type '/save' to save the conversation. Ctrl-C to exit.\n"
    )
    try:
        while True:
            with patch_stdout():
                user_input = session.prompt("You » ")
            if not user_input.strip():
                continue

            # Special command to change model
            if user_input.strip().startswith("/model"):
                model = choose_model(session, default=model)
                print(f"Model switched to: {model}\n")
                continue

            # Save command
            if user_input.strip().startswith("/save"):
                save_conversation(history_path, messages)
                print(f"Conversation saved to: {history_path}\n")
                continue

            messages.append({"role": "user", "content": user_input})

            print("Assistant » ", end="", flush=True)
            buffer = []
            # stream=True will yield chunks as they arrive
            for chunk in create_chat(api_key, messages, model=model, stream=True):
                print(chunk, end="", flush=True)
                buffer.append(chunk)
            final = "".join(buffer)
            print("\n")
            messages.append({"role": "assistant", "content": final})

            # Auto-save last conversation after assistant replies
            save_conversation(history_path, messages)

    except KeyboardInterrupt:
        print("\nTake care — goodbye!")


if __name__ == "__main__":
    main()
