# OpenRouter TUI

OpenRouter TUI is a lightweight, friendly terminal-based chat client for the [OpenRouter API](https://openrouter.ai/). It provides a seamless way to interact with various AI models directly from your command line.

## Features

- **Streaming Responses**: Real-time feedback as the assistant generates text.
- **Model Selection**: Easily switch between models with the `/model` command.
- **Auto-Fallback**: Use `super-model` to automatically fallback across top-performing models for better reliability.
- **Conversation History**: Automatically saves and restores your last conversation.
- **Lightweight**: Minimal dependencies, fast and responsive.

## Installation

### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/spivanatalie64/openrouter-tui.git
   cd openrouter-tui
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

### Arch Linux

This project includes a `PKGBUILD` for Arch Linux users. You can build and install the package using `makepkg`:

```bash
makepkg -si
```

## Usage

### Configuration

Set your OpenRouter API key as an environment variable:

```bash
export OPENROUTER_API_KEY="your_api_key_here"
```

### Running the TUI

Start the chat client:

```bash
python main.py
```

If installed via the Arch Linux package, you can simply run:

```bash
openrouter-tui
```

### In-App Commands

- `/model`: Change the current AI model.
- `/save`: Manually save the current conversation to the history file.
- `Ctrl-C`: Exit the application.

## Development

### Running Tests

To run the smoke tests:

```bash
python -m pytest tests/test_smoke.py
```

### Project Structure

- `main.py`: The entry point for the TUI application.
- `openrouter_client.py`: Core logic for interacting with the OpenRouter API.
- `requirements.txt`: Python dependencies.
- `PKGBUILD`: Arch Linux package build script.

## License

This project is licensed under the MIT License - see the LICENSE file (if available) for details.

## Credits

Developed by **Natalie Spiva** (<natalie@acreetionos.org>).
