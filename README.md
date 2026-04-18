OpenRouter TUI — a cozy terminal chat for OpenRouter

A small, friendly terminal chat client for the OpenRouter API. Think of it as a lightweight place to experiment, debug prompts, or have a quick conversation without leaving your terminal.

Prerequisites
- Python 3.8+
- An OpenRouter API key set as the environment variable: OPENROUTER_API_KEY

Installation

    python -m pip install -r requirements.txt

Quick start

    export OPENROUTER_API_KEY="sk_..."
    python main.py

Tips
- This prototype streams responses from the API so you see the assistant as it types.
- Tweak the endpoint, model, or streaming behavior in openrouter_client.py.

Credits
- Written by Natalie Spiva <natalie@acreetionos.org>
