//! Command line interface definition (clap).
//!
//! Kept in its own module so it can also be reused by `examples/gen_man.rs`
//! to generate man pages.

use crate::constants::*;
use clap::{Parser, Subcommand};
use clap_complete::Shell;
use clap_verbosity_flag::{InfoLevel, Verbosity};

/// A Rust CLI boilerplate application
#[derive(Parser)]
#[command(
    name = env!("CARGO_PKG_NAME"),
    version = env!("CARGO_PKG_VERSION"),
    author = env!("CARGO_PKG_AUTHORS"),
    about = env!("CARGO_PKG_DESCRIPTION"),
    long_version = long_version(),
    help_template = "\n\n{name} - {about}\n\n\
        {usage-heading} {usage}\n\n\
        {all-args}{after-help}",
    after_help = format!("For more information, visit: {}\n\n\
        If you encounter any issues, please report them at:\n{}/issues\n",
        env!("CARGO_PKG_REPOSITORY"), env!("CARGO_PKG_REPOSITORY")),
)]
pub struct Cli {
    /// Subcommand to execute
    #[command(subcommand)]
    pub command: Commands,

    /// Control verbosity level (use -v, -vv, -vvv, or -vvvv for more verbose output)
    #[command(flatten)]
    pub verbose: Verbosity<InfoLevel>,
}

/// Available subcommands
#[derive(Subcommand)]
pub enum Commands {
    /// Example command that greets someone
    Greet {
        /// Name of the person to greet
        #[arg(default_value = "World")]
        name: String,
    },

    /// Example command that echoes input
    Echo {
        /// Message to echo
        message: String,
    },

    /// Generate shell completions to stdout
    Completions {
        /// Shell to generate completions for
        #[arg(long, short, value_enum)]
        shell: Shell,
    },
}

/// Returns a static string containing the version information.
/// It uses Box::leak to convert a String into a &'static str.
/// This is a workaround to avoid using a global static variable.
fn long_version() -> &'static str {
    #[cfg(static_linking)]
    let linking_type = "statically linked";
    #[cfg(dynamic_linking)]
    let linking_type = "dynamically linked";
    Box::leak(
        format!(
            "\nVersion   : {}\nCommit    : {}\nBuild Date: {}\nBuilt with: {} ({})",
            VERSION, COMMIT, BUILD_DATE, COMPILE_C_LIB, linking_type
        )
        .into_boxed_str(),
    )
}
