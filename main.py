#!/usr/bin/env python3
"""
OpenRouter TUI — a small, friendly terminal chat client for the OpenRouter API.

Written by Natalie Spiva <natalie@acreetionos.org>
Set OPENROUTER_API_KEY before running.
"""

import argparse
import datetime
import json
import os
from pathlib import Path
from typing import Iterable, Optional

from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.status import Status

from openrouter_client import MODELS, Message, OpenRouterError, Usage, create_chat


def choose_model(session: PromptSession, default: str = "super-model") -> str:
    """
    Prompt the user to select a model from the available list.

    Args:
        session: The current PromptSession instance.
        default: The default model to use if no input is provided.

    Returns:
        The selected model name string.
    """
    prompt = "Choose a model (comma-separated list shown below). Press Enter to accept default.\n\n"
    prompt += " - super-model (Auto-fallback across top 20 models)\n"
    for m in MODELS:
        prompt += f" - {m}\n"
    prompt += f"\nModel (default {default}): "
    return str(session.prompt(prompt, default=default).strip() or default)


def _default_history_path() -> Path:
    """Return the default path for the history file."""
    return Path(os.path.expanduser("~")) / ".openrouter_tui" / "history.json"


def load_last_messages(history_path: Path) -> Optional[list[Message]]:
    """
    Load the messages from the most recent conversation in the history file.

    Args:
        history_path: Path to the JSON history file.

    Returns:
        A list of message dictionaries if found, otherwise None.
    """
    try:
        if not history_path.exists():
            return None
        data = json.loads(history_path.read_text(encoding="utf-8"))
        # Support both new and legacy formats
        convos = data.get("conversations", []) if isinstance(data, dict) else data
        if not convos:
            return None
        last = convos[-1]
        # Handle list of conversations or single conversation
        if isinstance(last, dict):
            return last.get("messages")  # type: ignore
        if isinstance(last, list):
            return last  # type: ignore
        return None
    except Exception:
        return None


def save_conversation(history_path: Path, messages: list[Message]) -> None:
    """
    Save the current conversation messages to the history file.

    Args:
        history_path: Path to the JSON history file.
        messages: List of message dictionaries to save.
    """
    try:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        existing = []
        if history_path.exists():
            try:
                data = json.loads(history_path.read_text(encoding="utf-8"))
                existing = (
                    data.get("conversations", []) if isinstance(data, dict) else data
                )
            except Exception:
                existing = []
        # Append this conversation as a dict for readability
        existing.append(
            {"messages": messages, "timestamp": str(datetime.datetime.now())}
        )
        # Write back as an object with conversations key for future extensibility
        out = {"conversations": existing}
        history_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    except Exception:
        # Persisting history should never crash the app; ignore errors.
        pass  # nosec B110


def main() -> None:
    """Main entry point for the OpenRouter TUI."""
    load_dotenv()  # Load .env file if it exists

    parser = argparse.ArgumentParser(description="OpenRouter TUI")
    parser.add_argument(
        "--history-file",
        default=None,
        help="Path to history file (default: ~/.openrouter_tui/history.json)",
    )
    parser.add_argument(
        "--system-prompt",
        default="You are a helpful assistant.",
        help="Custom system prompt to start the conversation.",
    )
    args = parser.parse_args()

    history_path = (
        Path(args.history_file) if args.history_file else _default_history_path()
    )

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print(
            "Please set the OPENROUTER_API_KEY environment variable or in a .env file and try again."
        )
        return

    session: PromptSession = PromptSession()
    console = Console()

    # Load last conversation if available and offer to restore
    last_messages = load_last_messages(history_path)
    if last_messages:
        try:
            resp = session.prompt("Load last conversation? (y/N): ").strip().lower()
            if resp == "y":
                messages = last_messages
                console.print(
                    "[green]Loaded last conversation. Continuing where you left off.\n[/green]"
                )
            else:
                messages = [{"role": "system", "content": args.system_prompt}]
        except KeyboardInterrupt:
            console.print("\n[yellow]Take care — goodbye![/yellow]")
            return
    else:
        messages = [{"role": "system", "content": args.system_prompt}]

    # Let the user pick a model at startup
    model = choose_model(session)

    console.print(
        "\nWelcome to [bold blue]OpenRouter TUI[/bold blue] — type a message and press Enter.\n"
        "Commands: [cyan]/model[/cyan] (change model), [cyan]/save[/cyan] (save history), "
        "[cyan]/clear[/cyan] (reset), [cyan]/export[/cyan] (save as MD), [red]Ctrl-C[/red] (exit).\n"
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
                console.print(f"Model switched to: [bold]{model}[/bold]\n")
                continue

            # Save command
            if user_input.strip().startswith("/save"):
                save_conversation(history_path, messages)
                console.print(f"Conversation saved to: [dim]{history_path}[/dim]\n")
                continue

            # Clear command
            if user_input.strip().startswith("/clear"):
                messages = [{"role": "system", "content": args.system_prompt}]
                console.print("[yellow]Conversation cleared.[/yellow]\n")
                continue

            # Export command
            if user_input.strip().startswith("/export"):
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = Path.cwd() / f"conversation_export_{ts}.md"
                md_content = f"# OpenRouter Conversation Export - {ts}\n\n"
                for msg in messages:
                    role = msg["role"].capitalize()
                    md_content += f"### {role}\n\n{msg['content']}\n\n"
                export_path.write_text(md_content, encoding="utf-8")
                console.print(f"Conversation exported to: [dim]{export_path}[/dim]\n")
                continue

            messages.append({"role": "user", "content": user_input})

            buffer: list[str] = []
            usage: Optional[Usage] = None

            try:
                with Status("[bold green]Thinking...", console=console) as status:
                    # stream=True will yield chunks as they arrive
                    response_gen = create_chat(
                        api_key, messages, model=model, stream=True
                    )
                    # We need to handle the fact that create_chat returns an Iterable when stream=True
                    if not isinstance(response_gen, Iterable):
                        raise OpenRouterError(
                            "Expected streaming response from create_chat"
                        )

                    first_chunk = True
                    md = Markdown("")
                    with Live(md, console=console, refresh_per_second=10) as live:
                        # Help MyPy understand we are iterating over the generator
                        for chunk, usage_info in response_gen:  # type: ignore[str-unpack, assignment]
                            if first_chunk:
                                status.stop()
                                print("Assistant » ", end="", flush=True)
                                first_chunk = False

                            if chunk:
                                buffer.append(chunk)
                                md = Markdown("".join(buffer))
                                live.update(md)

                            if usage_info:
                                usage = usage_info  # type: ignore[assignment]

                final = "".join(buffer)
                print("\n")
                if usage:
                    tokens = usage.get("total_tokens", 0)
                    console.print(f"[dim]Usage: {tokens} tokens[/dim]\n")

                messages.append({"role": "assistant", "content": final})

                # Auto-save last conversation after assistant replies
                save_conversation(history_path, messages)
            except Exception as e:
                console.print(f"\n[red]Error: {e}[/red]\n")
                # Remove the last user message if the assistant failed to reply,
                # so the conversation state remains consistent.
                if messages[-1]["role"] == "user":
                    messages.pop()

    except KeyboardInterrupt:
        console.print("\n[yellow]Take care — goodbye![/yellow]")


if __name__ == "__main__":
    main()
