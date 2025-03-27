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
    Server {
        #[arg(short, long, default_value = "Rust BLE Server")]
        name: String,

        #[arg(short, long, default_value = "0")]
        timeout: u64,
    },

    Client {
        #[arg(short, long)]
        device_name: String,

        #[arg(short, long, default_value = "10000")]
        scan_timeout: u64,
    },
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
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
