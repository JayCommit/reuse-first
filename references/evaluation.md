# Evaluation

## Observed exercises — 2026-11-06

Three isolated coding agents explicitly read `SKILL.md` and worked on separate
copies of [a small billing application](../tests/fixtures/billing_app/commands.py).
They received a task and its acceptance-check command, without a prescribed
implementation. The release reviewer inspected the resulting code and reran
the checks. These are constructed, realistic Python exercises, not production
case studies. There was one run per task and no without-skill baseline; they
demonstrate compliant reasoning, not a causal improvement or success rate.

| Request | Actual search and pre-edit decision | Change | Acceptance |
| --- | --- | --- | --- |
| Implement `invoice_ids(client, account)` across all pages; preserve order, empty results, errors, and account totals | `rg --files`; source search for invoice/account/page/cursor/error; read commands, client, checks. Reuse `BillingClient.iter_invoices` because it owns pagination and error propagation. | One line in `commands.py`; no new pagination loop | `check_tasks.ClientTask`: 2 passed |
| Implement invoice rendering using integer cents and the current GBP contract | `rg --files`; source search for invoice/receipt/total/cents/GBP/format/render; read views, presentation, legacy, checks. Choose `presentation.format_money`; reject legacy dollar input/output. | One line in `views.py`; shared formatter unchanged | `check_tasks.AmbiguousTask`: 1 passed |
| Implement CSV export with header, order, and escaping, including empty input | Filename/source search for csv/invoice/export/serialize/writer; read all seven source/check files. No existing local CSV implementation; compose standard-library writer and string buffer. | Implement `exports.py`; no dependency | `check_tasks.MissingTask`: 1 passed |

The first two resulting implementations were:

```python
def invoice_ids(client, account):
    return [invoice["id"] for invoice in client.iter_invoices(account)]

def render_invoice(row):
    return f"Invoice {row['id']}: {format_money(row['cents'])}"
```

The CSV implementation used `io.StringIO(newline="")`, `csv.writer`, a header
row, and `writerows`. No agent introduced another HTTP client, formatter, or CSV
escaping routine. Each changed only its task's implementation file. The examples
in the other reference files remain hypothetical; React/Next.js was not exercised.

## Replay the tasks

Copy `tests/fixtures/billing_app` to a disposable directory. Start each task from
a fresh copy; the `NotImplementedError` stubs are intentional. Give an agent one
of the requests in the table, the path to `SKILL.md`, and the corresponding
acceptance command. Run commands from the disposable copy, for example:

```sh
python -m unittest check_tasks.ClientTask -v
```

For a comparison, run another fresh copy with the same request and agent but
without loading the skill. Preserve the tool transcript and diff. Compare actual
searches before edits, owners reused, duplicate responsibilities, and correctness.
Repeat on your real codebase before drawing conclusions about usefulness.

## Manual behavioral regression checks

| Case | Pass | Fail |
| --- | --- | --- |
| No matches | Broaden to shared/adjacent source; explain the missing contract before adding code | Treat an empty index result as permission to skip inspection |
| Ambiguous matches | Inspect both contracts and callers; choose current GBP behavior | Pick the first `format_money` match, or duplicate the formatter |
| Agent ignores skill | Searches and source reads precede the first edit; reuse note and diff agree | Edit first, fabricate citations, or only append a reuse claim at the end |

The indexer's automated tests cover empty results and both ambiguous formatter
matches. **They do not test agent compliance.** Review the transcript manually;
functional correctness alone cannot establish that the skill was followed.

Negative control during release review: the reviewer deliberately replaced the
invoice stub with inline GBP formatting, without a pre-edit search/evidence note.
The functional `AmbiguousTask` check passed, but the artifact failed the manual
rubric: it copied `presentation.format_money` instead of using it, and had no
pre-edit evidence. This was a constructed noncompliant artifact, not an observed
agent refusal. It checks that the review criteria reject a correct-looking result.

## Release checks

The release review ran on Windows, Python 3.15.2, with Git available. It checked
indexer help, text/JSON output, useful and empty queries, unit tests, and the four
task checks above. A temporary standalone Git snapshot was cloned locally; its
tests and the README's PowerShell install commands were run with the home
destination redirected to a scratch directory. The installed script and its
reference links were then checked.
This verifies packaging/copying; it does not verify automatic skill discovery in
a newly launched Codex session. Bash commands and Python 3.10 were not executed.

## Linux release check — 2026-11-06

This section records a later check on Linux. It does not replace the Windows
results above. There is still no without-skill baseline and no measured
reduction in duplication. No skill-creator validator is installed here, so it
was not run and is not claimed to have passed. Automatic discovery in a newly
launched agent session was not tested.

Host: Linux. `python` and `python3` both reported Python 3.10.22. `python3.11`
reported Python 3.11.2. Git was available. Commands below were run from the
repository root of the publish candidate.

| Command | Result |
| --- | --- |
| `python3 -m unittest discover -s tests -v` | 11 tests, OK, 0 skipped (Python 3.10.22) |
| `python3.11 -m unittest discover -s tests -v` | 11 tests, OK, 0 skipped (Python 3.11.2) |
| `python3 scripts/pattern_index.py --help` | exit 0 |
| `python3 scripts/pattern_index.py tests/fixtures/billing_app --query format_money --no-git` | exit 0; 2 matches, `legacy.py` and `presentation.py`. Stderr: filesystem mode does not read ignore files (expected) |
| `python3 scripts/pattern_index.py tests/fixtures/billing_app --query not-present --format json` | exit 0; JSON `files: []`. The directory was not a Git repository yet, so discovery was `filesystem` and the warning was `Git discovery unavailable; filesystem mode does not read ignore files.` |

`git diff --check` could not run before this directory was a Git repository
(Git exited 129). After `git init`, `git diff --check --cached` reported one
whitespace finding: a blank line at the end of this file. That extra line was
removed. `git diff --check` and `git diff --check --cached` were run again on
the staged publish set and both exited 0.

After this directory was a Git repository, the missing-query command used Git
discovery and still exited 0 with `files: []` and an empty `warnings` list.
The `--no-git` formatter query was unchanged: `legacy.py` and `presentation.py`.

The README Bash install was executed from a temporary copy, with `HOME` pointed
at a temporary directory on this same machine. That is not a separate clean
machine, and PowerShell was not re-run. From another working directory, the
installed script returned both formatter candidates for `format_money` and JSON
`files: []` for `not-present`. Relative Markdown links inside that installed
copy resolved. This checks the copy commands only. It does not prove an agent
will discover the skill.

`curl -I -L` on the README link `https://learn.chatgpt.com/docs/build-skills`
returned HTTP 200. The final URL was the same address (Vercel).

Published procedure, not skill compliance: three disposable copies of
`tests/fixtures/billing_app` were made outside the repository. The stubs were
edited to the implementations already described in the Windows section
(`iter_invoices` for invoice ids, `presentation.format_money` for invoice
rendering, and a standard-library `csv.writer` for export). Acceptance commands
on Python 3.10.22 then passed: `ClientTask` 2, `AmbiguousTask` 1, `MissingTask`
1. Untouched fixture stubs were not executed and were not called regressions.
These edits were made by the release process, not by a separate agent, and they
do not show that loading the skill changed behavior.

`.github/workflows/ci.yml` was added for the public repository. It installs
Python and runs the unit tests on Python 3.10 and 3.11. It is not historical
evidence. This section does not record a GitHub Actions conclusion.

## v0.0.2 Linux check — 2026-11-06

This section records a later check on Linux for the install scripts and path
handling. It does not replace the Windows results above and it is not a macOS
or Windows run. `scripts/install.ps1` was not executed. There is still no
without-skill baseline and no measured reduction in duplication. No
skill-creator validator is installed here, so it was not run. Automatic
discovery in a newly launched agent session was not tested. Billing fixture
stubs were not solved and their acceptance checks were not run.

Host: Linux. `python3` reported Python 3.10.22. `python3.11` reported Python
3.11.2. Git was available. Commands were run from the repository root.

| Command | Result |
| --- | --- |
| `python3 -m unittest discover -s tests -v` | 19 tests, OK, 0 skipped (Python 3.10.22) |
| `python3.11 -m unittest discover -s tests -v` | 19 tests, OK, 0 skipped (Python 3.11.2) |
| `python3 scripts/pattern_index.py --help` | exit 0 |
| `python3 scripts/pattern_index.py tests/fixtures/billing_app --query format_money --no-git` | exit 0; 2 matches, `legacy.py` and `presentation.py`. Stderr: filesystem mode does not read ignore files (expected) |
| `python3 scripts/pattern_index.py tests/fixtures/billing_app --query not-present --format json` | exit 0; JSON `files: []`; discovery `git`; `warnings` empty |
| `bash -n scripts/install.sh` | exit 0 |
| `git diff --check -- .` | exit 0 |

The unit tests ran `scripts/install.sh` with `HOME` pointed at a temporary
directory on this machine and with project scope pointed at another temporary
directory. That is not macOS and not Windows. The installed `SKILL.md` was at
the destination root, `scripts/pattern_index.py` was beside it, a second copy
did not nest `reuse-first/reuse-first` or `scripts/scripts`, and the installed
indexer returned `legacy.py` and `presentation.py` for `format_money`.
PowerShell was not available, so `scripts/install.ps1` was only reviewed.
