use std::env;
use std::error::Error;
use std::time::Duration;

use bluest::{Adapter, DeviceId};
use futures_lite::StreamExt;
use tracing::metadata::LevelFilter;
use tracing::{error, info, warn};

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

    // Get target device name from command line arguments
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        return Err("Usage: program <device_name>".into());
    }
    let target_name = &args[1];
    info!("Searching for device: {}", target_name);

    // Initialize Bluetooth adapter
    let adapter = Adapter::default()
        .await
        .ok_or("Bluetooth adapter not found")?;
    adapter.wait_available().await?;

    // Scan for devices and connect to the target
    scan_and_connect(&adapter, target_name).await?;

    Ok(())
}

async fn scan_and_connect(adapter: &Adapter, target_name: &str) -> Result<(), Box<dyn Error>> {
    info!("Scanning for device: {}", target_name);

    // Start scanning for devices
    let mut scan = adapter.scan(&[]).await?;
    info!("Scan started");

    let scan_timeout = Duration::from_secs(30);
    let scan_start = std::time::Instant::now();

    let mut target_device_id: Option<DeviceId> = None;

    while let Some(discovered_device) = scan.next().await {
        let device_name = discovered_device.device.name().unwrap_or_default();

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

        // Here you would typically discover services, read/write characteristics, etc.
        // For example:
        let services = device.discover_services().await?;
        info!("Discovered {} services", services.len());

        for service in services {
            info!("Service: {}", service.uuid());

            let characteristics = service.discover_characteristics().await?;
            for characteristic in characteristics {
                info!("  Characteristic: {}", characteristic.uuid());
            }
        }

        // Disconnect when done
        if device.is_connected().await {
            adapter.disconnect_device(&device).await?;

            // Verify disconnection was successful
            if !device.is_connected().await {
                info!("Successfully disconnected from {}", target_name);
            } else {
                warn!("Device appears to still be connected");
            }
        } else {
            info!("Device is already disconnected");
        }
    } else {
        error!("Device '{}' not found", target_name);
        return Err("Target device not found".into());
    }

    Ok(())
}
