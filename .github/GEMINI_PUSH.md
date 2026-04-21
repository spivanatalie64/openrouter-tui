Gemini push wrapper

This repository contains a helper script at scripts/gemini_push.sh which invokes the local Gemini CLI in headless mode to perform git pushes and optionally create PR/MR using gh/glab.

Usage:
  mkdir -p scripts
  ./scripts/gemini_push.sh [branch] [remotes]

Examples:
  ./scripts/gemini_push.sh feature/add-smoke-test-and-pr-drafts github,origin

Notes:
- The script requires the gemini CLI to be installed and in PATH (/usr/bin/gemini is expected).
- Gemini must be able to access remotes via SSH (SSH key or agent); the script will not handle passwords.
- To auto-approve actions, set env var GEMINI_YOLO=1 when invoking the script.
- The script logs output to .git/gemini_push*.log and saves the prompt to .git/gemini_prompt_for_push.txt.

Security: do NOT pass secrets or passwords to the script. The wrapper uses SSH BatchMode to avoid interactive prompts.
