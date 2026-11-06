# Optional pattern indexer

Use Python 3.10+; there are no third-party dependencies. Resolve the script path
relative to this skill's folder, and pass the target repository explicitly. The
current working directory is used only if no root is given.

```sh
python /path/to/reuse-first/scripts/pattern_index.py /path/to/project --query "client retry"
python /path/to/reuse-first/scripts/pattern_index.py /path/to/project --format json
python /path/to/reuse-first/scripts/pattern_index.py /path/to/project --no-git --exclude "scratch/*"
```

Quote paths containing spaces. Options:

| Option | Meaning |
| --- | --- |
| `--query TEXT` | Case-insensitive substring AND search across path, category tags, and declaration names |
| `--format text\|json` | Human-readable output (default), or a versioned JSON object |
| `--exclude GLOB` | Repeatable, case-sensitive glob against relative POSIX paths and ancestors |
| `--no-git` | Always use filesystem discovery |
| `--max-bytes N` | Skip files over this size; default 262144 bytes |

For example, `--exclude "scratch"` excludes that directory and descendants;
`--exclude "**/generated/*"` matches nested generated paths. Globs use Python's
`fnmatchcase` semantics (`*` can match `/`), not full gitignore semantics. Quote
globs so the shell passes them unchanged.

## Discovery and boundaries

When Git is available and the root is inside a worktree, `git ls-files` finds
tracked and non-ignored untracked files under that root. Ignored tracked files
are still included, as they are with Git. Submodules are not recursively indexed.
Git is used only for discovery; the indexer reads current working files.
Index paths use POSIX separators, including macOS-style relatives such as
`clients/billing.py`. A listing that uses backslashes is treated as a
Windows-style relative path when that nested file exists, and is stored with
`/`. A single filename that itself contains a backslash, which is legal on
macOS, is left unchanged when the nested interpretation is not a real file.

Without Git, it walks the target directory. This mode **does not parse
`.gitignore` or other ignore files** and reports a warning. Both modes exclude
common dependency/build directories (see `EXCLUDED_DIRS` in the script). Add
project-specific exclusions with `--exclude`. Symlinks inside the tree are never
followed. A symlink above the project, such as macOS `/tmp`, does not hide the
files underneath it. Lexical aliases of the same directory (for example
`/var/...` and `/private/var/...`) still produce paths relative to the root.
Unreadable, non-UTF-8, binary, and oversized source files are skipped. Run on a
stable checkout; this lightweight local tool does not provide filesystem race
isolation against concurrently changing paths.

Supported extensions include Python, JavaScript/TypeScript, Go, Rust, Java,
Kotlin, C#, Ruby, PHP, Swift, C/C++, Vue, and Svelte. Filename discovery works
across these extensions, but declaration extraction is deliberately partial:
simple classes/functions/types and JS variable declarations are recognized;
many methods, multiline signatures, macros, and language-specific forms are not.
Comments or strings can produce false positives. It does not resolve imports,
infer signatures, detect duplicate code, or discover architectural patterns.
Category labels come from path words, not semantic analysis. Search the source
directly for behavior or languages not captured here.

Output includes relative paths, symbols and 1-based line numbers; it excludes
function bodies and values. Up to 100 symbols per file are displayed, with a
truncation flag; queries search all extracted symbols before truncation. Common
secret filenames are excluded, but paths and symbol names may themselves be
sensitive. The index is local stdout output; review it before sharing. No network
requests or target-code execution occur.

## Output contract

JSON schema version 1 contains `discovery`, `query`, `scanned_files`,
`matched_files`, `skipped` counts, `warnings`, and `files`. Each file has `path`,
`categories`, `symbols` (`name`, `line`), and `symbols_truncated`. Paths and
symbols are sorted by path and source order respectively. There are no timestamps
or absolute root paths in normal index entries. No matches is a successful empty
result (exit 0), not evidence that reusable code does not exist. Invalid CLI
arguments/root exit 2. Text warnings go to stderr; JSON warnings stay in the
JSON object. Redirect stdout to save an index; keep it outside the source tree
when possible and regenerate after changes rather than treating it as current.
