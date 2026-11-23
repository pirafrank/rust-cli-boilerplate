#!/usr/bin/env python3
"""Tests for init_template.py. They run the script on throwaway copies of the repository.

Usage: python3 hooks_scripts/test_init_template.py
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = "hooks_scripts/init_template.py"
TEST = "hooks_scripts/test_init_template.py"

VALID_ARGS = [
    "--yes",
    "--owner", "octo",
    "--repo-name", "my-repo",
    "--crate-name", "my-tool",
    "--tool-name", "My Tool",
    "--description", 'Does "things" & more',
    "--author", "Jane Doe <jane@example.com>",
]


def git(cwd: Path, *args: str) -> str:
    """Run git in `cwd` and return its stdout."""
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout


class InitTemplateTest(unittest.TestCase):
    """Runs the init script against a copy of the repository."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.copy = Path(tmp.name)
        files = git(REPO_ROOT, "ls-files", "-z", "--cached", "--others",
                    "--exclude-standard").split("\0")
        for name in filter(None, files):
            source = REPO_ROOT / name
            if source.is_file():
                target = self.copy / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        git(self.copy, "init", "-q")
        git(self.copy, "add", "-A")

    def run_init(self, *args: str) -> subprocess.CompletedProcess:
        """Run the script in the copy with stdin closed (non-interactive)."""
        return subprocess.run(
            [sys.executable, SCRIPT, *args],
            cwd=self.copy, capture_output=True, text=True, stdin=subprocess.DEVNULL,
        )

    def read(self, name: str) -> str:
        """Read a file of the copy."""
        return (self.copy / name).read_text(encoding="utf-8")

    def assert_untouched(self) -> None:
        """Nothing changed and the tooling is still present after a failed run."""
        self.assertTrue((self.copy / SCRIPT).exists())
        self.assertIn('name = "rust-cli-boilerplate"', self.read("Cargo.toml"))

    def test_rejects_invalid_crate_name(self) -> None:
        args = [a if a != "my-tool" else "Bad Name" for a in VALID_ARGS]
        self.assertNotEqual(self.run_init(*args).returncode, 0)
        self.assert_untouched()

    def test_rejects_invalid_owner(self) -> None:
        args = [a if a != "octo" else "bad owner" for a in VALID_ARGS]
        self.assertNotEqual(self.run_init(*args).returncode, 0)
        self.assert_untouched()

    def test_rejects_missing_values_when_not_interactive(self) -> None:
        result = self.run_init("--yes", "--owner", "octo", "--repo-name", "tool")
        self.assertNotEqual(result.returncode, 0)
        self.assert_untouched()

    def test_customizes_project(self) -> None:
        result = self.run_init(*VALID_ARGS)
        self.assertEqual(result.returncode, 0, result.stderr)

        cargo = self.read("Cargo.toml")
        self.assertIn('name = "my-tool"', cargo)
        self.assertIn('repository = "https://github.com/octo/my-repo"', cargo)
        self.assertIn('authors = ["Jane Doe <jane@example.com>"]', cargo)
        self.assertIn('description = "Does \\"things\\" & more"', cargo)
        self.assertIn('name = "my-tool"', self.read("Cargo.lock"))
        self.assertIn("BIN_NAME: my-tool", self.read(".github/workflows/release.yml"))

        readme = self.read("README.md")
        self.assertIn("# My Tool", readme.splitlines())
        self.assertIn('Does "things" & more', readme.splitlines())
        self.assertIn("template_name=rust-cli-boilerplate", readme)

        for name in filter(None, git(self.copy, "ls-files", "-z").split("\0")):
            if name == "README.md" or not (self.copy / name).is_file():
                continue
            try:
                text = self.read(name)
            except UnicodeDecodeError:
                continue
            self.assertNotIn("rust-cli-boilerplate", text, name)

        # Unrelated references to the original author's other projects are preserved.
        self.assertIn("pirafrank/dotfiles", self.read("justfile"))
        self.assertIn("pirafrank/audit-check-action", self.read(".github/workflows/security.yml"))

    def test_removes_its_own_tooling(self) -> None:
        self.assertEqual(self.run_init(*VALID_ARGS).returncode, 0)
        self.assertFalse((self.copy / SCRIPT).exists(), "script not removed")
        self.assertFalse((self.copy / TEST).exists(), "test not removed")
        justfile = self.read("justfile")
        self.assertNotIn("init_template", justfile)
        self.assertNotIn("\ninit ", justfile)
        self.assertNotIn("test-init", justfile)
        self.assertNotIn("test_init_template", self.read(".github/workflows/ci.yml"))
        self.assertNotIn("Test template init script", self.read(".github/workflows/ci.yml"))
        self.assertIn("\nbuild:", justfile)


if __name__ == "__main__":
    unittest.main()
