mod client;
mod constants;
mod server;
mod utils;

use clap::{Parser, Subcommand};
use std::error::Error;
use tracing::metadata::LevelFilter;

#[derive(Parser, Debug)]
#[command(author, version, about = "Bluetooth connection utility")]
struct Args {
    #[command(subcommand)]
    mode: Mode,
}

#[derive(Subcommand, Debug)]
enum Mode {
    /// Server mode: Wait for a connection from a specific device
    Server {
        /// Name to advertise the server as
        #[arg(short, long, default_value = "Rust BLE Server")]
        name: String,

        /// Timeout in seconds (0 for indefinite)
        #[arg(short, long, default_value = "0")]
        timeout: u64,
    },

    /// Client mode: Actively scan for and connect to a specific device
    Client {
        /// Name of the device to connect to
        #[arg(short, long)]
        device_name: String,

        /// Maximum time to scan for the device in seconds
        #[arg(short, long, default_value = "30")]
        scan_timeout: u64,
    },
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    // Set up logging
    use tracing_subscriber::prelude::*;
    use tracing_subscriber::{fmt, EnvFilter};

    tracing_subscriber::registry()
        .with(fmt::layer())
        .with(
            EnvFilter::builder()
                .with_default_directive(LevelFilter::INFO.into())
                .from_env_lossy(),
        )
        .init();

    let args = Args::parse();

    match args.mode {
        Mode::Server { name, timeout } => {
            server::run_server(&name, timeout).await?;
        }
        Mode::Client {
            device_name,
            scan_timeout,
        } => {
            client::connect_to_device(&device_name, scan_timeout).await?;
        }
    }

    Ok(())
}
