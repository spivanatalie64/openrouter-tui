#!/usr/bin/env python3
"""
OpenRouter TUI — a small, friendly terminal chat client for the OpenRouter API.

Written by Natalie Spiva <natalie@acreetionos.org>
Set OPENROUTER_API_KEY before running.
"""
import os
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from openrouter_client import create_chat, MODELS


def choose_model(session, default="gpt-4o-mini"):
    prompt = "Choose a model (comma-separated list shown below). Press Enter to accept default.\n\n"
    for m in MODELS:
        prompt += f" - {m}\n"
    prompt += f"\nModel (default {default}): "
    return session.prompt(prompt, default=default).strip() or default


def main():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Please set the OPENROUTER_API_KEY environment variable and try again.")
        return

    session = PromptSession()
    messages = [{"role": "system", "content": "You are a helpful assistant."}]

    # Let the user pick a model at startup
    model = choose_model(session)

    print("\nWelcome to OpenRouter TUI — type a message and press Enter.\nType '/model' at any time to change the model. Ctrl-C to exit.\n")
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

    except KeyboardInterrupt:
        print("\nTake care — goodbye!")


if __name__ == '__main__':
    main()
