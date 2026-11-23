//! Integration tests: run the compiled binary and check its output.

use std::process::{Command, Output};

/// Runs the built binary with `args` and returns its captured output.
fn run(args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_rust-cli-boilerplate"))
        .args(args)
        .output()
        .expect("failed to run the binary")
}

#[test]
fn greet_uses_the_default_name() {
    let output = run(&["greet"]);
    assert!(output.status.success());
    assert_eq!(
        String::from_utf8_lossy(&output.stdout).trim(),
        "Hello, World!"
    );
}

#[test]
fn echo_prints_the_message() {
    let output = run(&["echo", "hi there"]);
    assert!(output.status.success());
    assert_eq!(String::from_utf8_lossy(&output.stdout).trim(), "hi there");
}

#[test]
fn unknown_subcommand_fails() {
    assert!(!run(&["no-such-command"]).status.success());
}
