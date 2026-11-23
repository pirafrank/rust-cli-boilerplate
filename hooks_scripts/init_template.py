#!/usr/bin/env python3
"""Customize a project created from the rust-cli-boilerplate template.

Every value that is not given as an option is asked interactively:

  --owner NAME         GitHub user or organization owning the repository
  --repo-name NAME     GitHub repository name
  --crate-name NAME    Cargo package and binary name (default: repo name)
  --tool-name NAME     Human-readable tool name, used as README title (default: crate name)
  --description TEXT   One-line description (Cargo.toml and README)
  --author TEXT        Cargo.toml author, e.g. "Jane Doe <jane@example.com>"
                       (default: git user.name and user.email)
  -y, --yes            Do not ask for confirmation

What it does:
  - replaces the template crate name and GitHub slug in all tracked text files except
    README.md and this script's own files;
  - sets `authors` and `description` in Cargo.toml;
  - sets the title and the description line in README.md;
  - removes itself, its test, the `init` and `test-init` recipes and the CI step, as they are only
    useful once.

Requires Python 3 and git. Works on Linux, macOS and Windows.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

OLD_NAME = "rust-cli-boilerplate"
OLD_SLUG = "pirafrank/" + OLD_NAME
OLD_README_TITLE = "# Rust CLI boilerplate"
OLD_README_DESCRIPTION = "A template for cross-platform binary CLI projects written in Rust."

ROOT = Path(__file__).resolve().parent.parent
SELF = Path(__file__).resolve()
SELF_TEST = SELF.with_name("test_init_template.py")
# Files never touched by the rename: this tooling and the README (handled separately).
SKIPPED_FILES = {SELF, SELF_TEST, ROOT / "README.md"}

OWNER_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?$")
REPO_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
CRATE_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


def die(message: str) -> None:
    """Print an error message and exit with a failure status."""
    print("Error: " + message, file=sys.stderr)
    sys.exit(1)


def git(*args: str) -> str:
    """Run a git command in the repository root and return its stdout ('' on failure)."""
    try:
        result = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return result.stdout


def tracked_files() -> List[Path]:
    """Return the absolute paths of all files tracked by git."""
    output = git("ls-files", "-z")
    return [ROOT / name for name in output.split("\0") if name]


def default_author() -> str:
    """Build a default author string from the git configuration."""
    name = git("config", "user.name").strip()
    email = git("config", "user.email").strip()
    if name and email:
        return "{} <{}>".format(name, email)
    return name


def ask(value: Optional[str], prompt: str, default: str = "") -> str:
    """Return `value` if set, otherwise prompt for it (falling back to `default`)."""
    if value:
        return value
    if not sys.stdin.isatty():
        die("missing value for '{}' and stdin is not interactive (see --help)".format(prompt))
    suffix = " [{}]".format(default) if default else ""
    reply = input("{}{}: ".format(prompt, suffix)).strip()
    return reply or default


def toml_escape(text: str) -> str:
    """Escape text for use inside a TOML basic (double-quoted) string."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def read_text(path: Path) -> Optional[str]:
    """Read a UTF-8 file keeping its line endings, or return None for binary files."""
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            return handle.read()
    except UnicodeDecodeError:
        return None


def write_text(path: Path, content: str) -> None:
    """Write a UTF-8 file without translating line endings."""
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def replace_line(path: Path, pattern: str, replacement: str) -> None:
    """Replace the first line matching `pattern` in `path`, warning if there is none."""
    content = read_text(path)
    regex = re.compile(pattern, re.MULTILINE)
    if content is None or not regex.search(content):
        print(
            "warning: expected line not found in {}, edit it manually: {}".format(
                path.name, replacement
            ),
            file=sys.stderr,
        )
        return
    write_text(path, regex.sub(lambda _: replacement, content, count=1))
    print("updated " + path.relative_to(ROOT).as_posix())


def rename_everywhere(new_slug: str, crate_name: str) -> int:
    """Replace the old slug and crate name in tracked text files; return the files changed."""
    changed = 0
    for path in tracked_files():
        if path in SKIPPED_FILES or not path.is_file():
            continue
        content = read_text(path)
        if content is None or OLD_NAME not in content:
            continue
        # Slug first, because it contains the bare name.
        updated = content.replace(OLD_SLUG, new_slug).replace(OLD_NAME, crate_name)
        write_text(path, updated)
        print("updated " + path.relative_to(ROOT).as_posix())
        changed += 1
    return changed


def remove_block(path: Path, pattern: str) -> None:
    """Remove the first block matching `pattern` (up to the next blank line) from a text file."""
    content = read_text(path) if path.is_file() else None
    if content is None:
        return
    cleaned = re.sub(pattern + r".*?\r?\n\r?\n", "", content,
                     count=1, flags=re.MULTILINE | re.DOTALL)
    write_text(path, cleaned)


def remove_init_tooling() -> None:
    """Remove the `init` and `test-init` recipes and the CI step testing this script."""
    justfile = ROOT / "justfile"
    remove_block(justfile, r"^# Customize the template")
    remove_block(justfile, r"^# Run the tests of the template initialization script")
    remove_block(ROOT / ".github" / "workflows" / "ci.yml", r"^ +- name: Test template init script")


def parse_args(argv: Optional[List[str]]) -> argparse.Namespace:
    """Parse command line options."""
    parser = argparse.ArgumentParser(
        description="Customize a project created from the rust-cli-boilerplate template. "
        "Missing values are asked interactively."
    )
    parser.add_argument("--owner", help="GitHub user or organization owning the repository")
    parser.add_argument("--repo-name", help="GitHub repository name")
    parser.add_argument("--crate-name", help="Cargo package and binary name (default: repo name)")
    parser.add_argument("--tool-name", help="tool name used as README title (default: crate name)")
    parser.add_argument("--description", help="one-line description")
    parser.add_argument("--author", help="Cargo.toml author (default: git user.name and email)")
    parser.add_argument("-y", "--yes", action="store_true", help="do not ask for confirmation")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    """Collect and validate the values, then apply them."""
    args = parse_args(argv)

    owner = ask(args.owner, "GitHub owner (user or organization)")
    repo_name = ask(args.repo_name, "GitHub repository name")
    crate_name = ask(args.crate_name, "Crate name", repo_name)
    tool_name = ask(args.tool_name, "Tool name (used as README title)", crate_name)
    description = ask(args.description, "Tool description (one line)")
    author = ask(args.author, "Author", default_author())

    if not OWNER_RE.match(owner):
        die("invalid owner '{}': use letters, digits and '-'.".format(owner))
    if not REPO_NAME_RE.match(repo_name):
        die("invalid repository name '{}': use letters, digits, '.', '-' and '_'.".format(repo_name))
    if not CRATE_NAME_RE.match(crate_name):
        die("invalid crate name '{}': use lowercase letters, digits, '-' and '_'.".format(crate_name))
    if not tool_name:
        die("tool name must not be empty.")
    if not description:
        die("description must not be empty.")
    if any(ch in value for value in (tool_name, description, author) for ch in "\r\n"):
        die("values must be single-line.")

    new_slug = "{}/{}".format(owner, repo_name)

    if not args.yes:
        if not sys.stdin.isatty():
            die("confirmation needed but stdin is not interactive (use --yes).")
        print("\nAbout to apply:")
        print("  repository   : " + new_slug)
        print("  crate name   : " + crate_name)
        print("  tool name    : " + tool_name)
        print("  description  : " + description)
        print("  author       : " + author)
        if input("Proceed? [y/N]: ").strip().lower() not in ("y", "yes"):
            die("aborted, nothing changed.")

    changed = rename_everywhere(new_slug, crate_name)

    cargo_toml = ROOT / "Cargo.toml"
    replace_line(cargo_toml, r"^authors = .*$", 'authors = ["{}"]'.format(toml_escape(author)))
    replace_line(cargo_toml, r"^description = .*$",
                 'description = "{}"'.format(toml_escape(description)))
    readme = ROOT / "README.md"
    replace_line(readme, "^" + re.escape(OLD_README_TITLE) + "$", "# " + tool_name)
    replace_line(readme, "^" + re.escape(OLD_README_DESCRIPTION) + "$", description)

    remove_init_tooling()

    print("Done: {} file(s) renamed, Cargo.toml and README.md customized.".format(changed))
    print("Next: review README.md (badges, template-only sections) and AGENTS.md, "
          "then run 'just ci'.")

    # Last step: delete this script and its test.
    for path in (SELF_TEST, SELF):
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
