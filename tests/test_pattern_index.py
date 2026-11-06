"""Behavioral checks; all scratch files stay inside this standalone project."""

import importlib.util
import json
import os
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


class PathPortabilityTests(unittest.TestCase):
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

    def git_index(self, payload, **kwargs):
        completed = subprocess.CompletedProcess(
            args=["git"], returncode=0, stdout=payload, stderr=b"",
        )
        with patch.object(scanner.subprocess, "run", return_value=completed):
            return scanner.index(self.root, **kwargs)

    def test_macos_style_git_paths_need_no_backslashes(self):
        self.write("My Files/b.py", "def load_account(): pass\n")
        self.write("clients/billing.py", "class BillingClient:\n    pass\n")
        result = self.git_index(b"My Files/b.py\0clients/billing.py\0", query="billing")
        self.assertEqual(result["discovery"], "git")
        self.assertEqual([entry["path"] for entry in result["files"]], ["clients/billing.py"])
        self.assertEqual(result["files"][0]["symbols"][0]["name"], "BillingClient")
        self.assertIn("client", result["files"][0]["categories"])

    def test_windows_separators_normalize_without_hiding_backslash_names(self):
        self.write("clients/billing.py", "class BillingClient:\n    pass\n")
        self.write("node_modules/pkg/index.js", "export function duplicate() {}\n")
        literal = self.write("keep\\slash.py", "def keep_slash(): pass\n")
        self.assertEqual(literal.name, "keep\\slash.py")
        result = self.git_index(
            "clients\\billing.py\0node_modules\\pkg\\index.js\0keep\\slash.py\0".encode(),
            excludes=["scratch"],
        )
        paths = [entry["path"] for entry in result["files"]]
        self.assertIn("clients/billing.py", paths)
        self.assertNotIn("clients\\billing.py", paths)
        self.assertNotIn("node_modules/pkg/index.js", paths)
        self.assertGreaterEqual(result["skipped"].get("excluded", 0), 1)
        literal_entry = next(entry for entry in result["files"] if "keep" in entry["path"])
        self.assertEqual(literal_entry["path"], "keep\\slash.py")
        self.assertEqual(literal_entry["symbols"][0]["name"], "keep_slash")

    def test_symlink_above_project_does_not_hide_files(self):
        project = self.root / "realhome" / "proj"
        project.mkdir(parents=True)
        (project / "a.py").write_text("def hello(): pass\n", encoding="utf-8")
        link_home = self.root / "linkhome"
        try:
            link_home.symlink_to(project.parent, target_is_directory=True)
        except OSError:
            self.skipTest("Creating symlinks is unavailable on this platform")
        linked = link_home / "proj"

        def identity(path, strict=False):
            return path

        with patch.object(Path, "resolve", identity):
            result = scanner.index(linked, no_git=True)
        self.assertEqual([entry["path"] for entry in result["files"]], ["a.py"])
        self.assertNotIn("symlink", result["skipped"])

    def test_aliased_macos_prefix_stays_relative(self):
        project = self.root / "project"
        (project / "clients").mkdir(parents=True)
        (project / "clients" / "billing.py").write_text(
            "class BillingClient:\n    pass\n", encoding="utf-8",
        )
        alias = self.root / "alias"
        try:
            alias.symlink_to(project, target_is_directory=True)
        except OSError:
            self.skipTest("Creating symlinks is unavailable on this platform")

        def fake_walk(root, followlinks=False, onerror=None):
            yield str(alias), ["clients"], []
            yield str(alias / "clients"), [], ["billing.py"]

        with patch.object(scanner.os, "walk", fake_walk):
            result = scanner.index(project, no_git=True)
        self.assertEqual([entry["path"] for entry in result["files"]], ["clients/billing.py"])


class InstallScriptTests(unittest.TestCase):
    def setUp(self):
        scratch = PROJECT / ".test-work"
        scratch.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "home"
        self.project = Path(self.temp.name) / "project"
        self.home.mkdir()
        self.project.mkdir()

    def run_install(self, *args):
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        return subprocess.run(
            ["bash", str(PROJECT / "scripts" / "install.sh"), *args],
            cwd=self.project,
            env=env,
            capture_output=True,
            text=True,
        )

    def assert_skill(self, dest):
        self.assertTrue((dest / "SKILL.md").is_file(), dest)
        self.assertEqual((dest / "SKILL.md").read_bytes(), (PROJECT / "SKILL.md").read_bytes())
        self.assertTrue((dest / "scripts" / "pattern_index.py").is_file(), dest)
        self.assertTrue((dest / "agents" / "openai.yaml").is_file(), dest)
        self.assertFalse((dest / "reuse-first" / "SKILL.md").exists(), dest)
        self.assertFalse((dest / "scripts" / "scripts").exists(), dest)
        text = (dest / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: reuse-first", text)
        self.assertIn("description:", text)

    def test_install_sh_syntax(self):
        result = subprocess.run(
            ["bash", "-n", str(PROJECT / "scripts" / "install.sh")],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_user_default_install_is_not_nested(self):
        first = self.run_install()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("https://github.com/JayCommit/reuse-first", first.stdout)
        user_dests = [
            self.home / ".grok/skills/reuse-first",
            self.home / ".cursor/skills/reuse-first",
            self.home / ".agents/skills/reuse-first",
            self.home / ".gemini/config/skills/reuse-first",
            self.home / ".gemini/antigravity-cli/skills/reuse-first",
            self.home / ".claude/skills/reuse-first",
        ]
        for dest in user_dests:
            self.assert_skill(dest)
        self.assertFalse((self.project / ".grok").exists())
        second = self.run_install("--host", "all", "--scope", "user")
        self.assertEqual(second.returncode, 0, second.stderr)
        for dest in user_dests:
            self.assert_skill(dest)
        installed = user_dests[0] / "scripts" / "pattern_index.py"
        proc = subprocess.run(
            [sys.executable, str(installed),
             str(PROJECT / "tests" / "fixtures" / "billing_app"),
             "--query", "format_money", "--no-git", "--format", "json"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            [entry["path"] for entry in json.loads(proc.stdout)["files"]],
            ["legacy.py", "presentation.py"],
        )

    def test_project_scope_and_single_host(self):
        result = self.run_install("--scope", "project", "--host", "all")
        self.assertEqual(result.returncode, 0, result.stderr)
        for dest in (
            self.project / ".grok/skills/reuse-first",
            self.project / ".cursor/skills/reuse-first",
            self.project / ".agents/skills/reuse-first",
            self.project / ".claude/skills/reuse-first",
        ):
            self.assert_skill(dest)
        self.assertFalse((self.project / ".gemini").exists())
        self.assertFalse((self.project / ".agents/skills/reuse-first/reuse-first").exists())
        self.assertFalse((self.home / ".grok").exists())
        cursor = self.run_install("--host", "cursor", "--scope", "project")
        self.assertEqual(cursor.returncode, 0, cursor.stderr)
        self.assert_skill(self.project / ".cursor/skills/reuse-first")
        bad = self.run_install("--host", "notepad")
        self.assertEqual(bad.returncode, 2)
        self.assertIn("unknown host", bad.stderr)

    def test_grok_bot_user_path_and_prompt(self):
        result = self.run_install("--host", "grok-bot", "--scope", "user")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_skill(self.home / ".grok/skills/reuse-first")
        self.assertIn("https://github.com/JayCommit/reuse-first", result.stdout)
        self.assertIn("/reuse-first", result.stdout)
        self.assertFalse((self.home / ".cursor").exists())
        self.assertFalse((self.home / ".claude").exists())


if __name__ == "__main__":
    unittest.main()
