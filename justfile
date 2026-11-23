# Default recipe (shows help)
# This must be the first recipe in the file

# Set default shell based on OS
set windows-powershell

# List available recipes
default:
  just --list

# Install git hooks
install-hooks:
  git config core.hooksPath hooks

# Install required cargo plugins for recipes to run
install-cargo-plugins:
  cargo install cargo-binstall
  cargo install cargo-edit
  cargo install cargo-deny
  cargo binstall cargo-semver-checks
  cargo install cargo-outdated --locked
  cargo install cargo-audit --locked
  cargo install cargo-llvm-cov
  cargo binstall git-cliff
  python3 -m pip install diff-cover

# Check for errors in all targets
check:
  cargo check --all-targets

# Build the project
build:
  cargo build

# Run all tests
test:
  cargo test -- --nocapture

# Run only integration tests
test-integration:
  cargo test --test integration -- --nocapture

# Get errors and warnings without running the tests
warnings:
  cargo test --no-run 2>&1 | grep -A 5 "warning\|error" || true

# Run the formatter
fmt:
  cargo fmt

# Run the formatter (checks only)
fmt-check:
  cargo fmt -- --check

# Run the linter on default targets (exclude dependencies)
lint:
  cargo clippy -- --no-deps -D warnings

# Run the linter on all targets (exclude dependencies)
lint-all:
  cargo clippy --all-targets -- --no-deps -D warnings

# Auto-fix compiler suggestions
cargo-fix:
  cargo fix --allow-dirty

# Auto-fix clippy warnings
fix:
  cargo clippy --no-deps --fix --allow-dirty -- -D warnings

# Auto-fix clippy warnings for all targets
fix-all:
  cargo clippy --all-targets --no-deps --fix --allow-dirty -- -D warnings

# Run the formatter and linter on all source files
better: fmt lint-all

# Run pre-commit checks on staged files
pre-commit: fmt-check lint-all

# Run pre-push checks
pre-push: check test

# Run pre-push checks with tags
pre-push-tag:
  hooks_scripts/pre-push-tag.sh

# The following recipe requires git-cliff.
# Generate changelog
changelog version:
  git cliff --tag {{version}} -o CHANGELOG.md
  glow CHANGELOG.md | less

# Prepare release
prepare-release version:
  git cliff --tag {{version}} -o CHANGELOG.md
  nvim CHANGELOG.md
  cargo set-version {{version}}
  git add Cargo.toml Cargo.lock CHANGELOG.md
  git commit -S -m "chore(release): prepare for {{version}}"

# Make and tag a release
make-release version:
  git checkout main
  git tag -s -a v{{version}} -m "{{version}}"

# Build for release
release:
  cargo build --release --locked

# Run cargo artifacts
clean:
  cargo clean

# Clean all downloaded artifacts
clean-dl:
  rm -f *.tar.gz
  rm -f *.tar.bz2
  rm -f *.tar.xz
  rm -f *.zip
  rm -f *.tar
  rm -f *.tgz
  rm -f *.tbz2
  rm -f *.tbz

# Clean all artifacts
clean-all: clean clean-dl

# Generate man pages
man:
  cargo run --example gen_man

# Generate documentation
docs:
  cargo doc --no-deps --open

# Verify that all public items have documentation
docs-verify-public:
  #!/usr/bin/env bash
  set -euo pipefail
  tmp=$(mktemp)
  trap 'rm -f "$tmp"' EXIT
  cargo doc --no-deps 2> "$tmp"
  if grep -q "warning\[missing_docs\]" "$tmp"; then
    echo "Some public items are missing documentation"
    exit 1
  fi
  echo "All public items have documentation"

# Verify that all items have documentation
docs-verify-all:
  cargo clippy --all-targets --no-deps -- -D clippy::missing_docs_in_private_items

# Run benchmarks
bench:
  cargo bench

# Show dependency tree
deps:
  cargo tree

# Update dependencies
update-deps:
  cargo update

# Check for outdated dependencies
outdated-deps:
  cargo outdated --root-deps-only

# Check for security vulnerabilities
audit:
  cargo audit

# Check for license issues
licenses:
  cargo deny check licenses

# Run CI checks
ci: clean fmt-check lint-all build test

# Run compliance checks (audit and license validation)
compliance: audit licenses

# Run code coverage
coverage:
  cargo llvm-cov --all-features --workspace --lcov --output-path lcov.info

# Assumes you have the `browse` command in PATH
# see https://github.com/pirafrank/dotfiles/blob/main/bin/browse
# Browse issues on GitHub
issues:
  browse "https://github.com/pirafrank/rust-cli-boilerplate/issues"

# Check coverage of the current diff against the Codecov patch threshold
coverage-diff: coverage
  python3 -m diff_cover.diff_cover_tool lcov.info --compare-branch=origin/main --fail-under=90 --total-percent-float --exclude 'tests/*' 'build.rs'

# Browse coverage report locally
browse-coverage: coverage
  cargo llvm-cov report --html
  python3 -m http.server --directory ./target/llvm-cov/html 8888

# Assumes you have the `browse` command in PATH
# see https://github.com/pirafrank/dotfiles/blob/main/bin/browse
# Browse coverage report on Codecov
codecov:
  browse "https://app.codecov.io/github/pirafrank/rust-cli-boilerplate"

# Rust MSRV check
msrv:
  version=$(grep 'rust-version =' Cargo.toml | cut -d '=' -f2 | cut -d '"' -f2); \
  cargo +"$version" check --all-targets --locked
