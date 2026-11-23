//! Shell completion generation.

use clap::CommandFactory;
use clap_complete::{Shell, generate};
use std::io::Write;

use crate::cli::Cli;

/// Writes the completion script for `shell` to `out`.
pub fn generate_completions(shell: Shell, out: &mut dyn Write) {
    let mut cmd = Cli::command();
    let bin_name = cmd.get_name().to_string();
    generate(shell, &mut cmd, bin_name, out);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_shell_produces_a_script_mentioning_the_binary() {
        for shell in [
            Shell::Bash,
            Shell::Elvish,
            Shell::Fish,
            Shell::PowerShell,
            Shell::Zsh,
        ] {
            let mut buffer = Vec::new();
            generate_completions(shell, &mut buffer);
            let script = String::from_utf8(buffer).expect("completions are valid UTF-8");
            assert!(
                script.contains(env!("CARGO_PKG_NAME")),
                "{shell} script lacks binary name"
            );
        }
    }
}
