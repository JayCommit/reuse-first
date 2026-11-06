# reuse-first

An Agent Skill that asks coding agents to search existing code, inspect likely
owners and callers, and explain a reuse decision **before editing**. It guides
behavior; it cannot enforce compliance or prevent duplicate code.

## Install

Clone or download this project. No packages are required. Run the commands
from the directory that contains `SKILL.md` (the repository root). The copy
puts `SKILL.md` at the destination root and keeps `scripts/pattern_index.py`
beside it. Do not copy the repository directory into a folder that is already
named `reuse-first`; that nests a second `reuse-first` and the agent will not
see `SKILL.md`.

macOS (`cp` and `$HOME`) is the primary form. Windows PowerShell (`Copy-Item`)
is second. The v0.0.2 check did not execute these commands on macOS or Windows;
see [evaluation](references/evaluation.md).

**macOS and other Bash hosts**

```sh
bash scripts/install.sh
bash scripts/install.sh --host cursor --scope project
```

**Windows (PowerShell)**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1 --host cursor --scope project
```

`--host` is `grok`, `grok-bot`, `cursor`, `openai`, `antigravity`, `claude`, or
`all` (default `all`). `--scope` is `user` (default) or `project`. User scope
writes under `$HOME`. Project scope writes under the current directory.

Copied items: `SKILL.md`, `agents/`, `references/`, `scripts/`, `tests/`,
`README.md`, and `LICENSE`. `agents/openai.yaml` stays in the skill folder.

Manual copy uses the same items. Remove an existing destination item before
copying it again so `scripts` does not become `scripts/scripts`.

### 1. Grok

User: `~/.grok/skills/reuse-first/`. Project: `.grok/skills/reuse-first/` from
the project root. Invoke `/reuse-first`.

**macOS**

```sh
dest="$HOME/.grok/skills/reuse-first"
mkdir -p "$dest"
for item in SKILL.md agents references scripts tests README.md LICENSE; do
  rm -rf "$dest/$item"
  cp -R "$item" "$dest/$item"
done
```

**Windows**

```powershell
$dest = Join-Path $HOME ".grok\skills\reuse-first"
New-Item -ItemType Directory -Path $dest -Force | Out-Null
foreach ($item in @("SKILL.md", "agents", "references", "scripts", "tests", "README.md", "LICENSE")) {
  $target = Join-Path $dest $item
  if (Test-Path $target) { Remove-Item $target -Recurse -Force }
  Copy-Item $item -Destination $target -Recurse
}
```

### 2. Grok Bot

On the bot computer the user skill is `~/.grok/skills/reuse-first/` and a
project workspace uses `.grok/skills/reuse-first/`. It is the same `SKILL.md`
as Grok. Invoke `/reuse-first`.

The macOS `cp` / `$HOME` commands and the Windows `Copy-Item` commands are the
Grok commands above (same destination). If you cannot copy files onto that
computer yourself, paste this prompt:

```text
Install the reuse-first skill on this computer. Clone https://github.com/JayCommit/reuse-first and copy that checkout so SKILL.md is at ~/.grok/skills/reuse-first/SKILL.md, with scripts/ beside SKILL.md. Do not nest another reuse-first directory inside it. Use that same SKILL.md. Invoke /reuse-first.
```

### 3. Cursor

User: `~/.cursor/skills/reuse-first/`. Project: `.cursor/skills/reuse-first/`.
The frontmatter `name` is `reuse-first`, matching the folder. Invoke
`/reuse-first`.

**macOS**

```sh
dest="$HOME/.cursor/skills/reuse-first"
mkdir -p "$dest"
for item in SKILL.md agents references scripts tests README.md LICENSE; do
  rm -rf "$dest/$item"
  cp -R "$item" "$dest/$item"
done
```

**Windows**

```powershell
$dest = Join-Path $HOME ".cursor\skills\reuse-first"
New-Item -ItemType Directory -Path $dest -Force | Out-Null
foreach ($item in @("SKILL.md", "agents", "references", "scripts", "tests", "README.md", "LICENSE")) {
  $target = Join-Path $dest $item
  if (Test-Path $target) { Remove-Item $target -Recurse -Force }
  Copy-Item $item -Destination $target -Recurse
}
```

### 4. OpenAI / ChatGPT

User: `~/.agents/skills/reuse-first/`. Project: `.agents/skills/reuse-first/`.
Keep `agents/openai.yaml`. Codex invoke: `$reuse-first`. In the ChatGPT app,
zip the skill folder (the directory whose root is `SKILL.md`) and use
Plugins → Skills → Add → Upload. Do not add another `reuse-first` wrapper
inside that folder.

The user directory is the one in the
[Codex skills documentation](https://learn.chatgpt.com/docs/build-skills).
If the skill does not appear, restart Codex.

**macOS**

```sh
dest="$HOME/.agents/skills/reuse-first"
mkdir -p "$dest"
for item in SKILL.md agents references scripts tests README.md LICENSE; do
  rm -rf "$dest/$item"
  cp -R "$item" "$dest/$item"
done
```

**Windows**

```powershell
$dest = Join-Path $HOME ".agents\skills\reuse-first"
New-Item -ItemType Directory -Path $dest -Force | Out-Null
foreach ($item in @("SKILL.md", "agents", "references", "scripts", "tests", "README.md", "LICENSE")) {
  $target = Join-Path $dest $item
  if (Test-Path $target) { Remove-Item $target -Recurse -Force }
  Copy-Item $item -Destination $target -Recurse
}
```

### 5. Antigravity

`SKILL.md` includes `description` (required). Invoke `/reuse-first`. The folder
is one level deep: `SKILL.md` is directly inside `reuse-first/`, not
`reuse-first/reuse-first/SKILL.md`.

- Project: `.agents/skills/reuse-first/`
- User, app and IDE: `~/.gemini/config/skills/reuse-first/`
- CLI: `~/.gemini/antigravity-cli/skills/reuse-first/`

**macOS**

```sh
for dest in "$HOME/.gemini/config/skills/reuse-first" "$HOME/.gemini/antigravity-cli/skills/reuse-first"; do
  mkdir -p "$dest"
  for item in SKILL.md agents references scripts tests README.md LICENSE; do
    rm -rf "$dest/$item"
    cp -R "$item" "$dest/$item"
  done
done
```

Project scope uses one destination, `.agents/skills/reuse-first` from the
project root. The CLI path is a user directory.

**Windows**

```powershell
foreach ($dest in @(
  (Join-Path $HOME ".gemini\config\skills\reuse-first"),
  (Join-Path $HOME ".gemini\antigravity-cli\skills\reuse-first")
)) {
  New-Item -ItemType Directory -Path $dest -Force | Out-Null
  foreach ($item in @("SKILL.md", "agents", "references", "scripts", "tests", "README.md", "LICENSE")) {
    $target = Join-Path $dest $item
    if (Test-Path $target) { Remove-Item $target -Recurse -Force }
    Copy-Item $item -Destination $target -Recurse
  }
}
```

### 6. Claude

User: `~/.claude/skills/reuse-first/`. Project: `.claude/skills/reuse-first/`.
Invoke `/reuse-first`.

**macOS**

```sh
dest="$HOME/.claude/skills/reuse-first"
mkdir -p "$dest"
for item in SKILL.md agents references scripts tests README.md LICENSE; do
  rm -rf "$dest/$item"
  cp -R "$item" "$dest/$item"
done
```

**Windows**

```powershell
$dest = Join-Path $HOME ".claude\skills\reuse-first"
New-Item -ItemType Directory -Path $dest -Force | Out-Null
foreach ($item in @("SKILL.md", "agents", "references", "scripts", "tests", "README.md", "LICENSE")) {
  $target = Join-Path $dest $item
  if (Test-Path $target) { Remove-Item $target -Recurse -Force }
  Copy-Item $item -Destination $target -Recurse
}
```

## Optional indexer

The script is included in the copy above. It needs Python 3.10+ and its standard
library; there is no `pip install` step. Run from any directory. This example
is a user-level Grok install; use the skill directory you actually copied.

**macOS**

```sh
python "$HOME/.grok/skills/reuse-first/scripts/pattern_index.py" "/path/to/codebase" --query "client retry"
python "$HOME/.grok/skills/reuse-first/scripts/pattern_index.py" "/path/to/codebase" --format json
```

**Windows**

```powershell
python (Join-Path $HOME ".grok\skills\reuse-first\scripts\pattern_index.py") "C:\path\to\codebase" --query "client retry"
```

Alternatively, run the script from this project's root without installing:

```sh
python scripts/pattern_index.py "/path/to/codebase"
```

Use `--help` for options.
Git is optional: it enables discovery of tracked and non-ignored untracked files.
Filesystem fallback warns that it does not read ignore files.

The index gives relative paths and heuristic declaration names with line numbers.
Read candidates before reusing them. See [details and exclusions](references/indexer.md).

## Check that it is being followed

Look at tool activity and the diff, not just the final answer:

- Before editing: actual searches, candidate reads, and a visible reuse decision.
- With multiple matches: a contract/caller comparison, not selection by name alone.
- With no suitable match: broader source search and a reason for separate code.
- After editing: actual reuse in the diff and relevant behavior checks.

A final list of filenames without pre-edit searches does not meet the skill.

## Evidence and evaluation

In three isolated Python fixture tasks, agents reused invoice pagination, chose
the current GBP formatter over a legacy dollar formatter, and added CSV export
after finding no local implementation. All four acceptance checks passed.
[Requests, observed decisions, code excerpts, and replay steps](references/evaluation.md)
are included. These are small smoke exercises, not a controlled comparison or
evidence of a general reduction in duplication.

To evaluate on your own codebase, run the same task from the same revision with
and without the skill. Compare search activity, reused owners, new duplication,
and correctness. Include ambiguous matches and a genuinely missing capability.

## Limitations

- Results depend on the agent and codebase. Agents may skip or fabricate evidence;
  this project has no compliance monitor.
- The indexer uses regexes and path words. It can miss declarations or return
  false positives; it does not resolve imports or detect duplicates.
- Default exclusions, file-size/encoding limits, and ignore rules can hide code.
  No matches does not prove absence. Source reads are still necessary.
- Paths and symbols can be sensitive. Output stays local; review before sharing.
- Historical release checks ran on Windows with Python 3.15.2; see
  [evaluation](references/evaluation.md). That record is unchanged. A later
  Linux check is in the same file. v0.0.2 install scripts were syntax-checked
  and the Bash installer was run against a temporary `HOME` on Linux only.
  They were not executed on macOS or Windows, and PowerShell was not run.
  A newly launched agent session was not checked, so discovery is unverified.
  There is no without-skill baseline and no measured reduction in duplication.
- `.github/workflows/ci.yml` was added for the public repository. It is not
  historical evidence and this README does not claim the GitHub Actions run
  passed. See the repository Actions tab for the result of a given commit.

From a fresh checkout, run the indexer checks with:

```sh
python -m unittest discover -s tests -v
```

Agent behavior is evaluated manually; passing unit tests does not prove skill
compliance. License: [MIT](LICENSE).

## Continuous integration

`.github/workflows/ci.yml` was added for the public repository. It is not
historical evidence from the Windows checks. On `ubuntu-latest` it installs
Python 3.10 and Python 3.11, installs no project packages, and runs:

```sh
python -m unittest discover -s tests -v
```

Whether that workflow passed is the GitHub Actions result for the commit, not
a claim made by this file.
