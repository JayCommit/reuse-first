# Contributing

Work from the repository root. Python 3.10 or newer is required. There is no
package install, build step, or third-party dependency. The commands below use
`python`, matching the README. If your machine only has `python3`, substitute
that name. The 2026-11-06 Linux check used `python3` (3.10.22) and `python3.11`
(3.11.2); see [evaluation](references/evaluation.md).

```sh
python --version
python -m unittest discover -s tests -v
python scripts/pattern_index.py --help
python scripts/pattern_index.py tests/fixtures/billing_app --query format_money --no-git
python scripts/pattern_index.py tests/fixtures/billing_app --query not-present --format json
git diff --check
```

The formatter query should list `legacy.py` and `presentation.py`. The missing
query should print JSON with `files: []` and exit 0. Filesystem mode prints an
ignore-file warning; that is expected. Git and symlink tests may skip. Report
skips instead of treating them as the same coverage.

Do not run the acceptance checks in `tests/fixtures/billing_app` against the
untouched stubs. Those stubs raise `NotImplementedError` on purpose. To replay
a task, copy that fixture outside this repository and follow
[evaluation](references/evaluation.md). Passing those checks shows the task
commands run; it does not prove an agent followed the skill.

`scripts/install.sh` and `scripts/install.ps1` copy the skill into a host skill
directory with `SKILL.md` at that destination's root. Check the Bourne script
with `bash -n scripts/install.sh`. Do not claim the PowerShell script ran on
Windows unless it did, and do not describe a macOS run that did not happen.

Keep the runtime and tests on the Python standard library. Do not add packaging,
enforcement features, or third-party dependencies. Preserve indexer JSON schema
version 1, relative paths, warnings, and successful empty results.

There is no bundled skill-creator validator. Do not claim it passed unless you
ran that external tool and recorded the actual result.

`.github/workflows/ci.yml` runs the unit tests on Python 3.10 and 3.11 for this
public repository. It was added at publication and is not evidence from earlier
local checks. Do not describe a GitHub Actions result you did not see.

Report what you ran, any skips, and what remains unverified. Remove secrets and
private paths from issues and pull requests.
