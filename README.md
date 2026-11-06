# reuse-first

An Agent Skill that asks coding agents to search existing code, inspect likely
owners and callers, and explain a reuse decision **before editing**. It guides
behavior; it cannot enforce compliance or prevent duplicate code.

## Install

Clone or download this project. From the folder containing `SKILL.md`, copy the
skill into your agent's skill directory. No packages are required for the skill.

For a new personal Codex installation, use either:

**PowerShell**

```powershell
$reuseFirstPath = Join-Path $HOME ".agents/skills/reuse-first"
New-Item -ItemType Directory -Path $reuseFirstPath -Force | Out-Null
Copy-Item SKILL.md, agents, references, scripts, tests, README.md, LICENSE -Destination $reuseFirstPath -Recurse
```

**Bash**

```sh
mkdir -p "$HOME/.agents/skills/reuse-first"
cp -R SKILL.md agents references scripts tests README.md LICENSE "$HOME/.agents/skills/reuse-first/"
```

These use the user skill directory in [official Codex documentation](https://learn.chatgpt.com/docs/build-skills).
If the skill does not appear, restart Codex. Invoke it explicitly:

```text
Use $reuse-first to add a customer picker to the invoice form.
```

For another agent, load `SKILL.md` through its supported skill mechanism, or ask
it to read and follow that file explicitly. Discovery varies by agent.

## Optional indexer

The script is included in the copy above. It needs Python 3.10+ and its standard
library; there is no `pip install` step. Run from any directory, replacing the
target path with your codebase:

```sh
python "$HOME/.agents/skills/reuse-first/scripts/pattern_index.py" "/path/to/codebase" --query "client retry"
python "$HOME/.agents/skills/reuse-first/scripts/pattern_index.py" "/path/to/codebase" --format json
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
  [evaluation](references/evaluation.md). A later Linux check on 2026-11-06
  reran the unit tests with Python 3.10.22 and 3.11.2 and followed the Bash
  install into a temporary directory on that same machine. PowerShell was not
  re-run. A newly launched agent session was not checked, so discovery is
  unverified. There is no without-skill baseline and no measured reduction in
  duplication.
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
