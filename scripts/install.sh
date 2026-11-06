#!/usr/bin/env bash
# Copy the reuse-first skill into host skill directories.
# macOS is the primary target (Bash 3.2 is enough). Windows uses install.ps1.
# SKILL.md lands at the destination root; scripts/ stays beside it.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: install.sh [--host HOST] [--scope SCOPE]

Copy this skill so SKILL.md is the destination root and scripts/pattern_index.py
stays beside it. Existing copies are replaced in place and are not nested again.

--host HOST    grok | grok-bot | cursor | openai | antigravity | claude | all
               (default: all)
--scope SCOPE  user | project
               (default: user)

User scope writes under $HOME. Project scope writes under the current directory.
EOF
}

host="all"
scope="user"

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --host)
      if [ $# -lt 2 ]; then
        echo "error: --host requires a value" >&2
        exit 2
      fi
      host="$2"
      shift 2
      ;;
    --host=*)
      host="${1#--host=}"
      shift
      ;;
    --scope)
      if [ $# -lt 2 ]; then
        echo "error: --scope requires a value" >&2
        exit 2
      fi
      scope="$2"
      shift 2
      ;;
    --scope=*)
      scope="${1#--scope=}"
      shift
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

case "$host" in
  grok|grok-bot|cursor|openai|antigravity|claude|all) ;;
  *)
    echo "error: unknown host: $host" >&2
    exit 2
    ;;
esac

case "$scope" in
  user|project) ;;
  *)
    echo "error: unknown scope: $scope" >&2
    exit 2
    ;;
esac

if [ "$scope" = "user" ] && [ -z "${HOME:-}" ]; then
  echo "error: HOME is not set" >&2
  exit 2
fi

source_root=$(cd "$(dirname "$0")/.." && pwd)
work_root=$(pwd)

if [ ! -f "$source_root/SKILL.md" ]; then
  echo "error: SKILL.md not found in $source_root" >&2
  exit 1
fi

items="SKILL.md agents references scripts tests README.md LICENSE"
for item in $items; do
  if [ ! -e "$source_root/$item" ]; then
    echo "error: missing $source_root/$item" >&2
    exit 1
  fi
done

destinations=()

add_dest() {
  local dest="$1"
  local existing
  if [ "${#destinations[@]}" -gt 0 ]; then
    for existing in "${destinations[@]}"; do
      if [ "$existing" = "$dest" ]; then
        return 0
      fi
    done
  fi
  destinations+=("$dest")
}

selected() {
  [ "$host" = "all" ] || [ "$host" = "$1" ]
}

if [ "$scope" = "user" ]; then
  if selected grok || selected grok-bot; then
    add_dest "$HOME/.grok/skills/reuse-first"
  fi
  if selected cursor; then
    add_dest "$HOME/.cursor/skills/reuse-first"
  fi
  if selected openai; then
    add_dest "$HOME/.agents/skills/reuse-first"
  fi
  if selected antigravity; then
    add_dest "$HOME/.gemini/config/skills/reuse-first"
    add_dest "$HOME/.gemini/antigravity-cli/skills/reuse-first"
  fi
  if selected claude; then
    add_dest "$HOME/.claude/skills/reuse-first"
  fi
else
  if selected grok || selected grok-bot; then
    add_dest "$work_root/.grok/skills/reuse-first"
  fi
  if selected cursor; then
    add_dest "$work_root/.cursor/skills/reuse-first"
  fi
  if selected openai || selected antigravity; then
    add_dest "$work_root/.agents/skills/reuse-first"
  fi
  if selected claude; then
    add_dest "$work_root/.claude/skills/reuse-first"
  fi
fi

install_to() {
  local dest="$1"
  local item
  local dest_real
  mkdir -p "$dest"
  dest_real=$(cd "$dest" && pwd)
  if [ "$dest_real" = "$source_root" ]; then
    echo "error: refusing to copy the skill onto its own source: $dest" >&2
    exit 1
  fi
  for item in $items; do
    rm -rf "$dest/$item"
    cp -R "$source_root/$item" "$dest/$item"
  done
  # A dirty source tree may contain bytecode. It is not part of the skill.
  find "$dest" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
  printf '%s\n' "$dest"
}

printf 'Installed reuse-first (%s, %s)\n' "$host" "$scope"
if [ "${#destinations[@]}" -eq 0 ]; then
  echo "error: no destination for host=$host scope=$scope" >&2
  exit 1
fi
for dest in "${destinations[@]}"; do
  install_to "$dest"
done

if [ "$host" = "grok-bot" ] || [ "$host" = "all" ]; then
  cat <<'EOF'

Grok Bot paste-in prompt:
Install the reuse-first skill on this computer. Clone https://github.com/JayCommit/reuse-first and copy that checkout so SKILL.md is at ~/.grok/skills/reuse-first/SKILL.md, with scripts/ beside SKILL.md. Do not nest another reuse-first directory inside it. Use that same SKILL.md. Invoke /reuse-first.
EOF
fi
