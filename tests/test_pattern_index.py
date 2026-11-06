"""Behavioral checks; all scratch files stay inside this standalone project."""

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


PROJECT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT / "scripts" / "pattern_index.py"
spec = importlib.util.spec_from_file_location("pattern_index", SCRIPT)
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)


class IndexTests(unittest.TestCase):
    def setUp(self):
        scratch = PROJECT / ".test-work"
        scratch.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, body):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def scan(self, **kwargs):
        return scanner.index(self.root, no_git=True, **kwargs)

    def test_symbols_lines_and_cross_field_query(self):
        self.write("clients/billing.py", "class BillingClient:\n    async def retry(self):\n        pass\n")
        self.write("ui/EntitySelect.tsx", "export const EntitySelect = () => null;\n")
        self.write("services/server.go", "func (c *Client) Fetch() {}\n")
        self.write("src/lib.rs", "pub async fn load() {}\n")
        result = self.scan(query="CLIENT retry")
        self.assertEqual(result["scanned_files"], 4)
        self.assertEqual(result["matched_files"], 1)
        self.assertEqual(result["files"][0]["path"], "clients/billing.py")
        self.assertEqual(result["files"][0]["symbols"], [
            {"name": "BillingClient", "line": 1}, {"name": "retry", "line": 2},
        ])
        all_entries = {entry["path"]: entry for entry in self.scan()["files"]}
        self.assertIn("component", all_entries["ui/EntitySelect.tsx"]["categories"])
        self.assertEqual(all_entries["services/server.go"]["symbols"][0]["name"], "Fetch")
        self.assertEqual(all_entries["src/lib.rs"]["symbols"][0]["name"], "load")

    def test_exclusions_and_bounded_reads(self):
        self.write("node_modules/pkg/index.js", "export function duplicate() {}")
        self.write("build/generated.py", "def generated(): pass")
        self.write("scratch/local.py", "def local(): pass")
        self.write("secrets.py", "SECRET = 'never report values'")
        self.write("valid.py", "def valid(): pass")
        self.write("large.py", "x" * 101)
        self.write("binary.py", "\x00def binary(): pass")
        (self.root / "legacy.py").write_bytes(b"\xff\xfe")
        result = self.scan(excludes=["scratch"], max_bytes=100)
        self.assertEqual([f["path"] for f in result["files"]], ["valid.py"])
        self.assertEqual(result["skipped"]["oversized"], 1)
        self.assertEqual(result["skipped"]["binary"], 1)
        self.assertEqual(result["skipped"]["non_utf8"], 1)
        self.assertNotIn("never report values", json.dumps(result))

    def test_deterministic_and_empty_queries(self):
        self.write("z.py", "def z(): pass")
        self.write("a.py", "def a(): pass")
        self.assertEqual(self.scan(), self.scan())
        self.assertEqual([f["path"] for f in self.scan()["files"]], ["a.py", "z.py"])
        result = self.scan(query="not-present")
        self.assertEqual(result["files"], [])
        self.assertEqual(result["scanned_files"], 2)

    def test_ambiguous_candidates_are_both_returned(self):
        result = scanner.index(PROJECT / "tests" / "fixtures" / "billing_app",
                               no_git=True, query="format_money")
        self.assertEqual([f["path"] for f in result["files"]],
                         ["legacy.py", "presentation.py"])
        self.assertTrue(all(f["symbols"][0]["name"] == "format_money"
                            for f in result["files"]))

    def test_query_searches_symbols_beyond_display_limit(self):
        self.write("many.py", "\n".join(f"def item_{i}(): pass" for i in range(110)))
        entry = self.scan(query="item_109")["files"][0]
        self.assertTrue(entry["symbols_truncated"])
        self.assertEqual(len(entry["symbols"]), 100)

    def test_filesystem_fallback_without_git(self):
        self.write("helper.py", "def normalize(): pass")
        with patch.object(scanner.subprocess, "run", side_effect=FileNotFoundError):
            result = scanner.index(self.root)
        self.assertEqual(result["discovery"], "filesystem")
        self.assertEqual(result["matched_files"], 1)
        self.assertTrue(result["warnings"])

    def test_unreadable_file_is_reported(self):
        target = self.write("helper.py", "def helper(): pass")
        original = Path.open

        def open_file(path, *args, **kwargs):
            if path == target:
                raise PermissionError("test denied")
            return original(path, *args, **kwargs)

        with patch.object(Path, "open", open_file):
            result = self.scan()
        self.assertEqual(result["skipped"], {"unreadable": 1})

    def test_symlinks_are_not_followed(self):
        outside = self.root / "other"
        outside.mkdir()
        (outside / "hidden.py").write_text("def hidden(): pass", encoding="utf-8")
        target = self.root / "target"
        target.mkdir()
        try:
            (target / "link.py").symlink_to(outside / "hidden.py")
            (target / "linked_dir").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Creating symlinks is unavailable on this platform")
        self.assertEqual(scanner.index(target, no_git=True)["files"], [])
        with patch.object(scanner, "discover", return_value=(["link.py", "linked_dir/hidden.py"], "git", [])):
            result = scanner.index(target)
        self.assertEqual(result["files"], [])
        self.assertEqual(result["skipped"]["symlink"], 2)

    @unittest.skipUnless(shutil.which("git"), "Git is optional")
    def test_git_ignore_tracked_files_and_subdirectory_root(self):
        def git(*args):
            return subprocess.run(["git", "-C", str(self.root), *args],
                                  check=True, capture_output=True)

        git("init", "-q")
        self.write(".gitignore", "ignored/\ntracked.py\n")
        self.write("ignored/hidden.py", "def hidden(): pass")
        self.write("tracked.py", "def tracked(): pass")
        self.write("src/client.py", "def request(): pass")
        git("add", "-f", "tracked.py")
        result = scanner.index(self.root)
        self.assertEqual(result["discovery"], "git")
        self.assertEqual([f["path"] for f in result["files"]], ["src/client.py", "tracked.py"])
        sub = scanner.index(self.root / "src")
        self.assertEqual([f["path"] for f in sub["files"]], ["client.py"])

    def test_cli_json_text_and_errors(self):
        self.write("helper.py", "def normalize(): pass")

        def run(*args):
            return subprocess.run([sys.executable, str(SCRIPT), *args],
                                  capture_output=True, text=True)

        result = run(str(self.root), "--no-git", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["matched_files"], 1)
        self.assertEqual(result.stderr, "")
        text = run(str(self.root), "--no-git")
        self.assertIn("helper.py", text.stdout)
        self.assertIn("Warning:", text.stderr)
        empty = run(str(self.root), "--no-git", "--query", "not-present")
        self.assertEqual(empty.returncode, 0, empty.stderr)
        self.assertIn("0 matches / 1 scanned", empty.stdout)
        self.assertIn("absence is not proven", empty.stdout)
        empty_json = run(str(self.root), "--no-git", "--query", "not-present", "--format", "json")
        self.assertEqual(empty_json.returncode, 0, empty_json.stderr)
        self.assertEqual(json.loads(empty_json.stdout)["files"], [])
        help_result = run("--help")
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn("--query", help_result.stdout)
        self.assertEqual(help_result.stderr, "")
        for args in [(str(self.root / "missing"),), (str(self.root), "--max-bytes", "0")]:
            failure = run(*args)
            self.assertEqual(failure.returncode, 2)
            self.assertNotIn("Traceback", failure.stderr)

    def test_copied_project_is_self_contained(self):
        copy = self.root / "standalone"
        shutil.copytree(PROJECT, copy, ignore=shutil.ignore_patterns(
            ".test-work", "__pycache__", ".git"))
        fixture = self.write("codebase/utils.py", "def portable(): pass")
        result = subprocess.run([
            sys.executable, str(copy / "scripts" / "pattern_index.py"),
            str(fixture.parent), "--no-git", "--format", "json",
        ], cwd=copy, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["files"][0]["symbols"],
                         [{"name": "portable", "line": 1}])
        # All Markdown support links must resolve within the copied project.
        import re
        for doc in copy.rglob("*.md"):
            for link in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8")):
                if "://" not in link and not link.startswith("#"):
                    target = (doc.parent / link.split("#")[0]).resolve()
                    self.assertTrue(target.is_relative_to(copy.resolve()), link)
                    self.assertTrue(target.exists(), link)


if __name__ == "__main__":
    unittest.main()
