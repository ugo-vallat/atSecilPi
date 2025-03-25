use bluer::{Adapter, AdapterEvent, Address, Device, DeviceEvent, DeviceProperty};
use futures::StreamExt;
use std::error::Error;
use std::str::FromStr;
use std::time::{Duration, Instant};
use tokio::time::sleep;
use tracing::{info, warn, error};
use uuid::Uuid;

use crate::server::{SERVICE_UUID, READ_CHAR_UUID, WRITE_CHAR_UUID, NOTIFY_CHAR_UUID};

pub async fn connect_to_device(target_name: &str, scan_timeout_secs: u64) -> Result<(), Box<dyn Error>> {
    info!("Starting client mode, scanning for device: {}", target_name);
    
    // Initialize Bluetooth
    let session = bluer::Session::new().await?;
    let adapter = session.default_adapter().await?;
    
    // Enable the adapter
    adapter.set_powered(true).await?;
    info!("Bluetooth adapter {} powered on", adapter.name());
    
    // Start discovery
    adapter.set_discovery_filter(Default::default()).await?;
    adapter.start_discovery().await?;
    info!("Discovery started");
    
    // Find the device
    let device = find_device(&adapter, target_name, scan_timeout_secs).await?;
    info!("Found device: {} ({})", target_name, device.address());
    
    // Stop discovery before connecting
    adapter.stop_discovery().await?;
    
    // Connect to the device
    info!("Connecting to {}...", target_name);
    if !device.is_connected().await? {
        device.connect().await?;
    }
    
    if device.is_connected().await? {
        info!("Successfully connected to {}", target_name);
        
        // Interact with the device
        interact_with_device(&device).await?;
        
        // Disconnect when done
        device.disconnect().await?;
        info!("Disconnected from {}", target_name);
    } else {
        error!("Failed to connect to {}", target_name);
        return Err("Connection failed".into());
    }
    
    Ok(())
}

async fn find_device(adapter: &Adapter, target_name: &str, timeout_secs: u64) -> Result<Device, Box<dyn Error>> {
    info!("Scanning for device: {}", target_name);
    
    let start_time = Instant::now();
    let timeout = Duration::from_secs(timeout_secs);
    
    // Subscribe to adapter events
    let mut events = adapter.events().await?;
    
    // Also check existing devices
    for address in adapter.device_addresses().await? {
        let device = adapter.device(address)?;
        if let Ok(Some(name)) = device.name().await {
            info!("Found existing device: {} ({})", name, address);
            if name == target_name {
                return Ok(device);
            }
        }
    }
    
    // Wait for device discovery events
    while let Some(event) = events.next().await {
        // Check timeout
        if start_time.elapsed() > timeout {
            return Err(format!("Scan timeout reached. Device '{}' not found.", target_name).into());
        }
        
        if let AdapterEvent::DeviceAdded(addr) = event {
            let device = adapter.device(addr)?;
            
            // Try to get the device name
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
    // Wait for services to be resolved
    info!("Waiting for service discovery...");
    let mut retries = 5;
    
    while !device.is_services_resolved().await? && retries > 0 {
        sleep(Duration::from_secs(1)).await;
        retries -= 1;
    }
    
    if !device.is_services_resolved().await? {
        return Err("Failed to resolve services".into());
    }
    
    // Get services
    let services = device.services().await?;
    info!("Discovered {} services", services.len());
    
    // Find our service
    let service_uuid = Uuid::from_str(SERVICE_UUID).unwrap();
    let service = services.iter().find(|s| s.uuid() == service_uuid);
    
    if let Some(service) = service {
        info!("Found target service: {}", service.uuid());
        
        // Get characteristics
        let characteristics = service.characteristics().await?;
        info!("Service has {} characteristics", characteristics.len());
        
        // Look for our read characteristic
        let read_uuid = Uuid::from_str(READ_CHAR_UUID).unwrap();
        let write_uuid = Uuid::from_str(WRITE_CHAR_UUID).unwrap();
        
        for characteristic in characteristics {
            info!("Characteristic: {}", characteristic.uuid());
            
            if characteristic.uuid() == read_uuid {
                // Read from this characteristic
                info!("Reading from characteristic...");
                let value = characteristic.read().await?;
                let value_str = String::from_utf8_lossy(&value);
                info!("Read value: {}", value_str);
            }
            
            if characteristic.uuid() == write_uuid {
                // Write to this characteristic
                let message = "Hello from Rust client!";
                info!("Writing to characteristic: {}", message);
                characteristic.write(message.as_bytes()).await?;
                info!("Write completed");
            }
        }
    } else {
        warn!("Target service not found on device");
    }
    
    // Keep connection open for a moment
    info!("Maintaining connection for 5 seconds...");
    sleep(Duration::from_secs(5)).await;
    
    Ok(())
}

