# Working in reuse-first

reuse-first is an Agent Skill that guides coding agents to search existing code
and explain reuse decisions before editing. Its optional Python indexer finds
candidate files and declarations. Neither the skill nor the indexer enforces
compliance, proves compatibility, or detects duplicate code.

## Layout

- `SKILL.md`: short entrypoint, frontmatter, and core instructions.
- `references/`: on-demand examples, indexer contract, and evaluation evidence.
- `agents/openai.yaml`: skill display metadata and example invocation.
- `scripts/pattern_index.py`: standalone standard-library CLI.
- `tests/test_pattern_index.py`: automated indexer and portability checks.
- `tests/fixtures/billing_app/`: intentionally unfinished coding exercises and
  `check_tasks.py` acceptance checks; not production code.
- `README.md`, `LICENSE`: user setup and MIT terms.
- `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.github/`: public
  repository process. `.github/workflows/ci.yml` runs unit tests for that
  repository; it is not historical evidence and is not required to use the skill.
- `.test-work/`: ignored scratch space for tests and disposable evaluations.

## Setup and checks

Work from the directory containing this file. Use Python 3.10+; no package
installation, build, or environment variables are required. Git is optional for
the indexer but needed to exercise Git discovery tests. User installation is in
`README.md`; development does not require installing the skill globally.

```sh
python --version
python -m unittest discover -s tests -v
python scripts/pattern_index.py --help
python scripts/pattern_index.py tests/fixtures/billing_app --query format_money --no-git
python scripts/pattern_index.py tests/fixtures/billing_app --query not-present --format json
git diff --check -- .
```

The formatter query should return `legacy.py` and `presentation.py`. The no-match
query should return JSON with `files: []` and exit 0. Filesystem mode emits an
ignore-file warning; this is expected. Review test skips: Git and symlink checks
can be skipped on an unsuitable host. No linter or formatter is configured.
`.github/workflows/ci.yml` runs `python -m unittest discover -s tests -v` on
Python 3.10 and 3.11 for the public repository. That workflow was added at
publication and is not evidence from earlier local checks.

If the host supplies skill-creator, its optional validation command is:

```sh
python "<path-to-skill-creator>/scripts/quick_validate.py" .
```

Replace the placeholder with that tool's actual location. The validator is not
bundled or a development dependency. It checks skill structure, not agent behavior.
For instruction changes, use `references/evaluation.md` to replay relevant tasks
on disposable fixture copies. Do not run acceptance checks against untouched
fixture stubs and mistake the expected failures for indexer regressions.

## Change constraints

- Search and read the existing owner, callers, and relevant tests before edits;
  state the intended reuse decision. Prefer the smallest compatible change.
- Keep this directory self-contained. Do not import sibling projects, depend on
  a surrounding checkout, or write machine-specific paths into committed files.
- Keep the skill short. No numeric token limit is enforced; preserve progressive
  disclosure by keeping examples and edge cases in linked, on-demand references.
  Do not inline every reference or require loading them all.
- Keep runtime and tests free of third-party dependencies. Do not add packaging,
  features, enforcement hooks, or a framework as incidental cleanup.
- Preserve documented CLI behavior, including JSON schema version 1, relative
  paths, warnings, and successful empty results. Update docs/tests with a change.
- Never turn fixture exercises into claims of general improvement. Distinguish
  performed checks, manual review, skips, and untested platforms. Do not fabricate
  search evidence or describe hypothetical examples as observed results.

## Before committing

Run the relevant commands above; review the diff and new files with
`git status --short -- .`. Check links still resolve after copying the project
alone, metadata agrees with the skill, and no scratch output or secrets are
included. Add regression tests for changed executable behavior; documentation
edits need accurate commands and links, not tests that match their wording.
Report what changed, what ran, and what remains unverified. Do not publish or
tag as part of an ordinary code change.
