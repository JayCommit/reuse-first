#!/usr/bin/env python3
"""Find reusable-code candidates using only the Python standard library."""

from __future__ import annotations

import argparse
from collections import Counter
import fnmatch
import json
import os
from pathlib import Path
import re
import subprocess
import sys


EXTENSIONS = {
    ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".go", ".rs", ".java", ".kt", ".kts", ".cs", ".rb", ".php",
    ".swift", ".c", ".h", ".cc", ".cpp", ".hpp", ".vue", ".svelte",
}
EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", ".venv", "venv",
    "__pycache__", ".next", ".nuxt", "dist", "build", "target", "coverage",
    ".cache", ".tox", ".test-work",
}
SENSITIVE = (".env*", "*.pem", "*.key", "secrets.*", "credentials.*")
DECLARATIONS = [
    re.compile(r"^\s*(?:export\s+(?:default\s+)?)?(?:async\s+)?(?:def|class|function|interface|type|enum|struct|trait|mod)\s+(?P<name>[A-Za-z_$][\w$]*)"),
    re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(?P<name>[A-Za-z_$][\w$]*)\s*(?::[^=]+)?="),
    re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+(?P<name>[A-Za-z_]\w*)"),
    re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?(?P<name>[A-Za-z_]\w*)\s*[\[(]"),
    re.compile(r"^\s*def\s+(?:self\.)?(?P<name>[A-Za-z_]\w*[!?]?)"),
    re.compile(r"^\s*(?:(?:public|private|protected|internal|abstract|final|static|open|data|sealed)\s+)+(?:class|interface|enum|record|struct)\s+(?P<name>[A-Za-z_]\w*)"),
    re.compile(r"^\s*(?:suspend\s+)?fun\s+(?P<name>[A-Za-z_]\w*)"),
    re.compile(r"^\s*(?:(?:public|private|protected|static|override|mutating)\s+)*func\s+(?P<name>[A-Za-z_]\w*)"),
    re.compile(r"^\s*(?:(?:public|private|protected|static)\s+)*function\s+(?P<name>[A-Za-z_]\w*)"),
]


def excluded(path: str, patterns: list[str]) -> bool:
    """Match custom globs against a POSIX path or any of its ancestors."""
    parts = path.split("/")
    if any(part in EXCLUDED_DIRS for part in parts[:-1]):
        return True
    if any(fnmatch.fnmatchcase(parts[-1].lower(), p) for p in SENSITIVE):
        return True
    ancestors = ["/".join(parts[:i]) for i in range(1, len(parts) + 1)]
    return any(
        fnmatch.fnmatchcase(candidate, pattern.rstrip("/"))
        for pattern in patterns for candidate in ancestors
    )


def discover(root: Path, no_git: bool) -> tuple[list[str], str, list[str]]:
    warnings = []
    if not no_git:
        try:
            result = subprocess.run(
                ["git", "-c", "core.fsmonitor=false", "-C", str(root), "ls-files", "--cached", "--others",
                 "--exclude-standard", "-z", "--", "."],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
                timeout=30,
            )
            if result.returncode == 0:
                names = result.stdout.decode("utf-8", errors="surrogateescape").split("\0")
                return sorted(set(filter(None, names))), "git", warnings
            warnings.append("Git discovery unavailable; filesystem mode does not read ignore files.")
        except (OSError, subprocess.TimeoutExpired):
            warnings.append("Git discovery unavailable; filesystem mode does not read ignore files.")
    else:
        warnings.append("Filesystem mode does not read ignore files; use --exclude where needed.")

    paths = []

    def walk_error(error: OSError) -> None:
        warnings.append(f"Cannot list directory: {error.filename}")

    for directory, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        dirs[:] = sorted(
            name for name in dirs
            if name not in EXCLUDED_DIRS and not (Path(directory) / name).is_symlink()
        )
        for name in sorted(files):
            paths.append((Path(directory) / name).relative_to(root).as_posix())
    return sorted(paths), "filesystem", warnings


def categories(path: str) -> list[str]:
    words = set(re.findall(r"[a-z]+", path.lower()))
    groups = {
        "component": {"component", "components", "ui", "tsx", "jsx", "vue", "svelte"},
        "utility": {"util", "utils", "utilities", "helper", "helpers", "lib"},
        "client": {"client", "clients", "sdk"},
        "service": {"service", "services", "api", "routes", "handlers"},
        "test": {"test", "tests", "spec", "specs"},
    }
    return [name for name, terms in groups.items() if words & terms]


def index(root: Path, *, query: str = "", no_git: bool = False,
          excludes: list[str] | None = None, max_bytes: int = 262144) -> dict:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")
    paths, discovery, warnings = discover(root, no_git)
    skipped: Counter[str] = Counter()
    entries = []
    scanned = 0
    terms = query.casefold().split()
    for relative in paths:
        if excluded(relative, excludes or []):
            skipped["excluded"] += 1
            continue
        path = root / relative
        if path.suffix.lower() not in EXTENSIONS:
            skipped["unsupported_extension"] += 1
            continue
        try:
            # Never follow file or directory symlinks, including Git-discovered ones.
            if any(part.is_symlink() for part in [path, *path.parents] if part != root):
                skipped["symlink"] += 1
                continue
            if not path.resolve().is_relative_to(root):
                skipped["outside_root"] += 1
                continue
            with path.open("rb") as source:
                raw = source.read(max_bytes + 1)
            if len(raw) > max_bytes:
                skipped["oversized"] += 1
                continue
            if b"\0" in raw:
                skipped["binary"] += 1
                continue
            content = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            skipped["non_utf8"] += 1
            continue
        except OSError:
            skipped["unreadable"] += 1
            continue
        scanned += 1
        symbols = []
        for number, line in enumerate(content.splitlines(), 1):
            for pattern in DECLARATIONS:
                match = pattern.match(line)
                if match:
                    symbols.append({"name": match.group("name"), "line": number})
                    break
        tags = categories(relative)
        searchable = " ".join([relative, *tags, *(s["name"] for s in symbols)]).casefold()
        if all(term in searchable for term in terms):
            entries.append({
                "path": relative, "categories": tags,
                "symbols": symbols[:100], "symbols_truncated": len(symbols) > 100,
            })
    return {
        "schema_version": 1,
        "discovery": discovery,
        "query": query,
        "scanned_files": scanned,
        "matched_files": len(entries),
        "skipped": dict(sorted(skipped.items())),
        "warnings": warnings,
        "files": entries,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path.cwd())
    parser.add_argument("--query", default="", help="AND-match terms in paths, categories, or symbols")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--exclude", action="append", default=[], help="Repeatable POSIX path glob")
    parser.add_argument("--no-git", action="store_true", help="Use filesystem discovery")
    parser.add_argument("--max-bytes", type=int, default=262144, help="Maximum bytes per source file")
    args = parser.parse_args(argv)
    try:
        result = index(args.root, query=args.query, no_git=args.no_git,
                       excludes=args.exclude, max_bytes=args.max_bytes)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        for warning in result["warnings"]:
            print(f"Warning: {warning}", file=sys.stderr)
        print(f"{result['matched_files']} matches / {result['scanned_files']} scanned files ({result['discovery']})")
        if not result["files"]:
            print("No candidates found. Broaden terms or search source directly; absence is not proven.")
        for entry in result["files"]:
            tags = ", ".join(entry["categories"]) or "source"
            print(f"{entry['path']} [{tags}]")
            for symbol in entry["symbols"]:
                print(f"  {symbol['line']}: {symbol['name']}")
            if entry["symbols_truncated"]:
                print("  ... additional symbols omitted")
        if result["skipped"]:
            print("Skipped: " + ", ".join(f"{k}={v}" for k, v in result["skipped"].items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
