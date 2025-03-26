use bluer::{Adapter, AdapterEvent, Device};
use futures::StreamExt;
use std::error::Error;
use std::str::FromStr;
use std::time::{Duration, Instant};
use tokio::time::sleep;
use tracing::{error, info, warn};
use uuid::Uuid;

use crate::constants::*;

pub async fn connect_to_device(
    target_name: &str,
    scan_timeout_secs: u64,
) -> Result<(), Box<dyn Error>> {
    info!("Starting client mode, scanning for device: {}", target_name);

    let session = bluer::Session::new().await?;
    let adapter = session.default_adapter().await?;

    adapter.set_powered(true).await?;
    info!("Bluetooth adapter {} powered on", adapter.name());

    let discovery_filter = bluer::DiscoveryFilter {
        transport: bluer::DiscoveryTransport::Auto,
        ..Default::default()
    };
    adapter.set_discovery_filter(discovery_filter).await?;
    let _ = adapter.discover_devices().await?;
    info!("Discovery started");

    let device = find_device(&adapter, target_name, scan_timeout_secs).await?;
    info!("Found device: {} ({})", target_name, device.address());

    info!("Connecting to {}...", target_name);
    if !device.is_connected().await? {
        device.connect().await?;
    }

    if device.is_connected().await? {
        info!("Successfully connected to {}", target_name);

        interact_with_device(&device).await?;

        device.disconnect().await?;
        info!("Disconnected from {}", target_name);
    } else {
        error!("Failed to connect to {}", target_name);
        return Err("Connection failed".into());
    }

    Ok(())
}

async fn find_device(
    adapter: &Adapter,
    target_name: &str,
    timeout_secs: u64,
) -> Result<Device, Box<dyn Error>> {
    info!("Scanning for device: {}", target_name);

    let start_time = Instant::now();
    let timeout = Duration::from_secs(timeout_secs);

    let mut events = adapter.events().await?;

    for address in adapter.device_addresses().await? {
        let device = adapter.device(address)?;
        if let Ok(Some(name)) = device.name().await {
            info!("Found existing device: {} ({})", name, address);
            if name == target_name {
                return Ok(device);
            }
        }
    }

    while let Some(event) = events.next().await {
        if start_time.elapsed() > timeout {
            return Err(
                format!("Scan timeout reached. Device '{}' not found.", target_name).into(),
            );
        }

        if let AdapterEvent::DeviceAdded(addr) = event {
            let device = adapter.device(addr)?;

            if let Ok(Some(name)) = device.name().await {
                info!("Discovered device: {} ({})", name, addr);

                if name == target_name {
                    return Ok(device);
                }
            }
        }
    }

    Err(format!("Device '{}' not found", target_name).into())
}

async fn interact_with_device(device: &Device) -> Result<(), Box<dyn Error>> {
    info!("Waiting for service discovery...");
    let mut retries = 5;

    while !device.is_services_resolved().await? && retries > 0 {
        sleep(Duration::from_secs(1)).await;
        retries -= 1;
    }

    if !device.is_services_resolved().await? {
        return Err("Failed to resolve services".into());
    }

    let services = device.services().await?;
    info!("Discovered {} services", services.len());

    let service_uuid = Uuid::from_str(SERVICE_UUID).unwrap();
    let mut found_service = false;

    for service in services {
        let uuid = service.uuid().await?;
        info!("Service: {}", uuid);

        if uuid == service_uuid {
            info!("Found target service: {}", uuid);
            found_service = true;

            // Get characteristics
            let characteristics = service.characteristics().await?;
            info!("Service has {} characteristics", characteristics.len());

            // Look for our read and write characteristics
            let read_uuid = Uuid::from_str(READ_CHAR_UUID).unwrap();
            let write_uuid = Uuid::from_str(WRITE_CHAR_UUID).unwrap();

            for characteristic in characteristics {
                let char_uuid = characteristic.uuid().await?;
                info!("Characteristic: {}", char_uuid);

                if char_uuid == read_uuid {
                    // Read from this characteristic
                    info!("Reading from characteristic...");
                    let value = characteristic.read().await?;
                    let value_str = String::from_utf8_lossy(&value);
                    info!("Read value: {}", value_str);
                }

                if char_uuid == write_uuid {
                    // Write to this characteristic
                    let message = "Hello from Rust client!";
                    info!("Writing to characteristic: {}", message);
                    characteristic.write(message.as_bytes()).await?;
                    info!("Write completed");
                }
            }
        }
    }

    if !found_service {
        warn!("Target service not found on device");
    }

    // Keep connection open for a moment
    info!("Maintaining connection for 5 seconds...");
    sleep(Duration::from_secs(5)).await;

    Ok(())
}
