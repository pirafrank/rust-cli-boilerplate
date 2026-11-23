//! Example binary that generates a man page using `clap-mangen`.
//!
//! Run with `cargo run --example gen_man` (or `just man`) to produce `man/<app-name>.1`.
#![allow(unused)]
use clap::{ArgAction, Command, CommandFactory};
use clap_mangen::Man;
use std::fs;
use std::io::{Result, Write};
use std::path::PathBuf;

/// Re-exported constants module from the main crate.
#[path = "../src/constants.rs"]
mod constants;

/// Re-exported CLI module from the main crate.
#[path = "../src/cli.rs"]
mod cli;

use cli::Cli;

/// Renders a single clap subcommand as a `.SS` man-page section into `buf`.
fn render_subcommand(sub: &Command, buf: &mut Vec<u8>) -> Result<()> {
    // Subsection title: command name
    writeln!(buf, ".SS \"{}\"", sub.get_name())?;

    // Description
    if let Some(about) = sub.get_about() {
        writeln!(buf, "{}", about)?;
    }
    writeln!(buf)?;

    // Arguments / options, without the automatic help flag
    let args = sub
        .get_arguments()
        .filter(|arg| arg.get_id().as_str() != "help");

    for arg in args {
        writeln!(buf, ".TP")?;

        let mut opt_str = String::new();

        // Short flag
        if let Some(s) = arg.get_short() {
            opt_str.push_str(&format!("\\fB-{}\\fR", s));
        }

        // Long flag
        if let Some(l) = arg.get_long() {
            if !opt_str.is_empty() {
                opt_str.push_str(", ");
            }
            opt_str.push_str(&format!("\\fB--{}\\fR", l));
        }

        // Determine if the argument takes a value
        let takes_value = !matches!(
            arg.get_action(),
            ArgAction::SetTrue
                | ArgAction::SetFalse
                | ArgAction::Help
                | ArgAction::Version
                | ArgAction::Count
        );

        if opt_str.is_empty() {
            // Positional argument
            opt_str.push_str(&format!("\\fI<{}>\\fR", arg.get_id()));
        } else if takes_value {
            // Option with value(s)
            if let Some(val_names) = arg.get_value_names() {
                for val in val_names {
                    opt_str.push_str(&format!(" \\fI<{}>\\fR", val));
                }
            }
        }

        writeln!(buf, "{}", opt_str)?;

        // Help text
        if let Some(help) = arg.get_help() {
            writeln!(buf, "{}", help)?;
        }
    }

    Ok(())
}

/// Entry point: creates the `man/` directory and generates the man page.
fn main() -> Result<()> {
    let mut out_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    out_dir.push("man");
    fs::create_dir_all(&out_dir)?;

    // Build the clap app
    let mut cmd = Cli::command();
    cmd.build(); // Ensure arguments are propagated/finalized

    let app_name = cmd.get_name().to_string();
    let file_path = out_dir.join(format!("{}.1", app_name));

    // Hide subcommands in the main page to suppress the default table;
    // they are rendered in a custom SUBCOMMANDS section below.
    let mut main_cmd = cmd.clone();
    for sub in main_cmd.get_subcommands_mut() {
        *sub = std::mem::take(sub).hide(true);
    }

    let mut buffer: Vec<u8> = Vec::new();
    Man::new(main_cmd).render(&mut buffer)?;

    // GLOBAL OPTIONS
    writeln!(&mut buffer, ".SH \"GLOBAL OPTIONS\"")?;
    writeln!(
        &mut buffer,
        "These options are available for all subcommands:"
    )?;
    writeln!(&mut buffer)?;
    writeln!(&mut buffer, ".TP")?;
    writeln!(&mut buffer, "\\fB-h\\fR, \\fB--help\\fR")?;
    writeln!(&mut buffer, "Print help")?;
    writeln!(&mut buffer, ".TP")?;
    writeln!(&mut buffer, "\\fB-V\\fR, \\fB--version\\fR")?;
    writeln!(&mut buffer, "Print version")?;

    // ENVIRONMENT
    writeln!(&mut buffer, ".SH \"ENVIRONMENT\"")?;
    writeln!(&mut buffer, ".TP")?;
    writeln!(&mut buffer, "\\fBRUST_LOG\\fR")?;
    writeln!(
        &mut buffer,
        "Controls the verbosity of logging output. This is useful for troubleshooting issues."
    )?;
    writeln!(&mut buffer)?;
    writeln!(
        &mut buffer,
        "Available log levels (from least to most verbose):"
    )?;
    writeln!(&mut buffer)?;
    writeln!(&mut buffer, "\\fBerror\\fR - Only show errors")?;
    writeln!(&mut buffer)?;
    writeln!(&mut buffer, "\\fBwarn\\fR - Show warnings and errors")?;
    writeln!(&mut buffer)?;
    writeln!(
        &mut buffer,
        "\\fBinfo\\fR - Show informational messages (default)"
    )?;
    writeln!(&mut buffer)?;
    writeln!(
        &mut buffer,
        "\\fBdebug\\fR - Show debug information for troubleshooting"
    )?;
    writeln!(&mut buffer)?;
    writeln!(
        &mut buffer,
        "\\fBtrace\\fR - Show all available logging information"
    )?;
    writeln!(&mut buffer)?;
    writeln!(&mut buffer, "Example:")?;
    writeln!(&mut buffer)?;
    writeln!(
        &mut buffer,
        "Enable debug logging: \\fBRUST_LOG=debug {} greet\\fR",
        app_name
    )?;

    // SUBCOMMANDS
    writeln!(&mut buffer, ".SH \"SUBCOMMANDS\"")?;
    for sub in cmd.get_subcommands().filter(|s| !s.is_hide_set()) {
        render_subcommand(sub, &mut buffer)?;
    }

    fs::write(&file_path, buffer)?;
    println!("Man page generated at: {}", file_path.display());
    Ok(())
}
