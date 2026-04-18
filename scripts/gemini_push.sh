#!/usr/bin/env bash
# Wrapper to invoke the local Gemini CLI to perform git pushes and create PR/MR non-interactively.
# Safety: This wrapper never accepts passwords. Gemini must be configured to use SSH keys or tokens already.
# Usage:
#   ./scripts/gemini_push.sh [branch] [remotes]
# Examples:
#   ./scripts/gemini_push.sh feature/add-smoke-test-and-pr-drafts github,origin
#   ./scripts/gemini_push.sh        # uses current branch and remotes github,origin

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

BRANCH="${1:-$(git rev-parse --abbrev-ref HEAD)}"
REMOTES="${2:-github,origin}"
GEMINI_CMD="$(command -v gemini || true)"
LOGFILE=".git/gemini_push_$(date +%Y%m%d%H%M%S).log"

if [[ -z "$GEMINI_CMD" ]]; then
  echo "gemini CLI not found in PATH. Install or add it to PATH." >&2
  exit 2
fi

# Build the prompt for Gemini. Keep it explicit and short.
read -r -d '' PROMPT <<'EOF' || true
You are a senior developer Natalie Spiva <natalie@acreetionos.org>.
Run these commands non-interactively in this repo, using SSH (do not request or use passwords):

# For each remote in the provided list, run a git push of the given branch and set upstream.
# After pushing, if gh (GitHub CLI) exists, create a pull request using gh pr create --fill.
# If glab (GitLab CLI) exists, create a merge request using glab mr create --fill.

Note:
- Do not expose any secrets or ask for passwords.
- Use BatchMode SSH (ssh -o BatchMode=yes) for any git operations to avoid interactive prompts.
- Print concise success/failure lines with which remote succeeded or failed.

Commands to run (in order):
EOF

# Append push commands per remote
for remote in ${REMOTES//,/ } ; do
  PROMPT+=$"\n# Push to ${remote}\n"
  PROMPT+=$"GIT_SSH_COMMAND=\"ssh -o BatchMode=yes -o ConnectTimeout=10\" git push ${remote} ${BRANCH} --set-upstream || echo 'PUSH_FAILED ${remote}'\n"
done

# Add PR/MR creation steps
PROMPT+=$"\n# Try to create PR on GitHub if gh present\n"
PROMPT+=$"if command -v gh >/dev/null 2>&1; then gh pr create --fill --head ${BRANCH} --base main || echo 'GH_PR_CREATE_FAILED'; fi\n"
PROMPT+=$"\n# Try to create MR on GitLab if glab present\n"
PROMPT+=$"if command -v glab >/dev/null 2>&1; then glab mr create --fill --source ${BRANCH} --target main || echo 'GLAB_MR_CREATE_FAILED'; fi\n"

# Ask Gemini to print a short summary at the end
PROMPT+=$"\n# Print remotes and exit status summary:\n git remote -v\n echo 'DONE'\n"

# Run gemini in headless mode with the constructed prompt
echo "Running gemini to push branch '${BRANCH}' to remotes: ${REMOTES}"
# Save prompt for debugging
mkdir -p .git
printf '%s\n' "$PROMPT" > .git/gemini_prompt_for_push.txt

# Run gemini; capture output
# Use --yolo to auto-approve actions only if GEMINI_YOLO=1 is set by the caller
GEMINI_YOLO_FLAG=""
if [[ "${GEMINI_YOLO:-0}" == "1" ]]; then GEMINI_YOLO_FLAG="--yolo"; fi

# Execute and stream to console and logfile
set +e
$GEMINI_CMD -p "$PROMPT" $GEMINI_YOLO_FLAG --output-format text 2>&1 | tee "$LOGFILE"
EXIT_CODE=${PIPESTATUS[0]}
set -e

if [[ $EXIT_CODE -ne 0 ]]; then
  echo "gemini reported exit code $EXIT_CODE. See $LOGFILE and .git/gemini_prompt_for_push.txt for details." >&2
  exit $EXIT_CODE
fi

echo "gemini push finished; see $LOGFILE for details."
exit 0
