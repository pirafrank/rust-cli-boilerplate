//! A Rust CLI boilerplate application.

#![warn(missing_docs)]

mod cli;
mod completions;
mod constants;
use crate::cli::{Cli, Commands};
use anyhow::Result;
use clap::Parser;
use log::{debug, info};

fn run() -> Result<()> {
    let cli = Cli::parse();

    // Set up logging based on verbosity flags
    env_logger::Builder::new()
        .filter_level(cli.verbose.log_level_filter())
        .format_timestamp(None)
        .format_module_path(false)
        .format_target(false)
        .init();

    debug!("Debug logging enabled");
    info!("Starting application");

    // Handle subcommands
    match cli.command {
        Commands::Greet { name } => {
            info!("Executing greet command");
            println!("Hello, {}!", name);
        }
        Commands::Echo { message } => {
            info!("Executing echo command");
            println!("{}", message);
        }
        Commands::Completions { shell } => {
            completions::generate_completions(shell, &mut std::io::stdout());
        }
    }

    Ok(())
}

fn main() -> Result<()> {
    let result = run();

    if let Err(ref e) = result {
        log::error!("Application error: {:?}", e);
    }

    result
}
