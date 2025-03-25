use std::error::Error;
use std::time::Duration;

use bluest::{Adapter, Device, DeviceId};
use clap::{Parser, Subcommand};
use futures_lite::StreamExt;
use tokio::time::sleep;
use tracing::metadata::LevelFilter;
use tracing::{error, info, warn};

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
        /// Name of the device to accept connections from
        #[arg(short, long)]
        device_name: String,

        /// Maximum time to wait for connection in seconds
        #[arg(short, long, default_value = "300")]
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

    // Initialize Bluetooth adapter
    let adapter = Adapter::default()
        .await
        .ok_or("Bluetooth adapter not found")?;
    adapter.wait_available().await?;

    match args.mode {
        Mode::Server {
            device_name,
            timeout,
        } => {
            server_mode(&adapter, &device_name, timeout).await?;
        }
        Mode::Client {
            device_name,
            scan_timeout,
        } => {
            client_mode(&adapter, &device_name, scan_timeout).await?;
        }
    }

    Ok(())
}

async fn server_mode(
    adapter: &Adapter,
    target_name: &str,
    timeout_secs: u64,
) -> Result<(), Box<dyn Error>> {
    info!(
        "Starting in server mode, waiting for connection from: {}",
        target_name
    );

    // Since we can't directly monitor connections in bluest, we'll use periodic scanning
    let timeout = Duration::from_secs(timeout_secs);
    let start_time = std::time::Instant::now();

    // Keep checking for devices until timeout
    while start_time.elapsed() < timeout {
        info!("Scanning for devices...");
        let mut scan = adapter.scan(&[]).await?;

        while let Some(discovered_device) = scan.next().await {
            // Check if we've timed out
            if start_time.elapsed() > timeout {
                info!("Server timeout reached after {} seconds", timeout_secs);
                return Ok(());
            }

            let device_name = match discovered_device.device.name() {
                Ok(name) => name,
                Err(_) => continue,
            };

            info!(
                "Found device: '{}' ({:?})",
                device_name,
                discovered_device.device.id()
            );

            // Check if this is the device we're waiting for
            if device_name == target_name {
                let device = adapter.open_device(&discovered_device.device.id()).await?;

                // Check if it's connected
                if device.is_connected().await {
                    info!("Target device '{}' is connected!", target_name);
                    handle_connection(adapter, &device).await?;
                    return Ok(());
                }
            }
        }

        // Wait a bit before scanning again
        sleep(Duration::from_secs(5)).await;
    }

    info!("Server timeout reached after {} seconds", timeout_secs);
    Ok(())
}

async fn client_mode(
    adapter: &Adapter,
    target_name: &str,
    scan_timeout_secs: u64,
) -> Result<(), Box<dyn Error>> {
    info!(
        "Starting in client mode, scanning for device: {}",
        target_name
    );

    // Start scanning for devices
    let mut scan = adapter.scan(&[]).await?;
    info!("Scan started");

    let scan_timeout = Duration::from_secs(scan_timeout_secs);
    let scan_start = std::time::Instant::now();

    let mut target_device_id: Option<DeviceId> = None;

    while let Some(discovered_device) = scan.next().await {
        let device_name = match discovered_device.device.name() {
            Ok(name) => name,
            Err(_) => continue,
        };

        info!(
            "Found device: '{}' ({:?})",
            device_name,
            discovered_device.device.id()
        );

        // Check if this is the device we're looking for
        if device_name == target_name {
            info!("Found target device: {}", target_name);
            target_device_id = Some(discovered_device.device.id().clone());
            break;
        }

        // Check if we've exceeded our scan timeout
        if scan_start.elapsed() > scan_timeout {
            info!("Scan timeout reached. Device '{}' not found.", target_name);
            break;
        }
    }

    // Stop scanning
    drop(scan);

    // If we found the target device, connect to it
    if let Some(device_id) = target_device_id {
        info!("Attempting to connect to device: {}", target_name);

        // Get a Device instance to interact with
        let device = adapter.open_device(&device_id).await?;

        // Check if already connected
        if device.is_connected().await {
            info!("Device is already connected");
        } else {
            // Connect to the device
            adapter.connect_device(&device).await?;

            // Verify connection was successful
            if device.is_connected().await {
                info!("Successfully connected to {}", target_name);
            } else {
                error!("Failed to connect to {}", target_name);
                return Err("Connection failed".into());
            }
        }

        handle_connection(adapter, &device).await?;
    } else {
        error!("Device '{}' not found", target_name);
        return Err("Target device not found".into());
    }

    Ok(())
}

async fn handle_connection(adapter: &Adapter, device: &Device) -> Result<(), Box<dyn Error>> {
    // Discover and interact with services/characteristics
    let services = device.discover_services().await?;
    info!("Discovered {} services", services.len());

    for service in services {
        info!("Service: {}", service.uuid());

        let characteristics = service.discover_characteristics().await?;
        for characteristic in characteristics {
            info!("  Characteristic: {}", characteristic.uuid());
            // Here you would typically read/write to characteristics as needed
        }
    }

    // Keep the connection for a while for demonstration
    info!("Connected and maintaining connection for 30 seconds...");
    sleep(Duration::from_secs(30)).await;

    // Disconnect when done
    if device.is_connected().await {
        adapter.disconnect_device(device).await?;

        // Verify disconnection was successful
        if !device.is_connected().await {
            info!("Successfully disconnected");
        } else {
            warn!("Device appears to still be connected");
        }
    } else {
        info!("Device is already disconnected");
    }

    Ok(())
}
