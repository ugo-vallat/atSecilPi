use bluer::{
    adv::Advertisement,
    gatt::local::{
        Application, Characteristic, CharacteristicNotify, CharacteristicRead, CharacteristicWrite,
        Service,
    },
};
use std::error::Error;
use std::time::{Duration, Instant};
use tokio::time::sleep;
use tracing::{info, warn};
use uuid::Uuid;

use crate::utils;

// Define UUIDs for our service and characteristics
const SERVICE_UUID: &str = "00001000-0000-1000-8000-00805f9b34fb";
const READ_CHAR_UUID: &str = "00001001-0000-1000-8000-00805f9b34fb";
const WRITE_CHAR_UUID: &str = "00001002-0000-1000-8000-00805f9b34fb";
const NOTIFY_CHAR_UUID: &str = "00001003-0000-1000-8000-00805f9b34fb";

pub async fn run_server(name: &str, timeout_secs: u64) -> Result<(), Box<dyn Error>> {
    info!("Starting Bluetooth server with name: {}", name);

    // Initialize Bluetooth
    let session = bluer::Session::new().await?;
    let adapter = session.default_adapter().await?;

    // Enable the adapter
    adapter.set_powered(true).await?;
    info!("Bluetooth adapter {} powered on", adapter.name());

    // Create GATT application
    let app = create_gatt_application();

    // Start GATT server
    info!("Registering GATT application...");
    let app_handle = adapter.serve_gatt_application(app).await?;
    info!("GATT application registered");

    // Create advertisement
    let adv = Advertisement {
        service_uuids: vec![SERVICE_UUID.parse().unwrap()].into_iter().collect(),
        discoverable: Some(true),
        local_name: Some(name.to_string()),
        appearance: Some(0x0340), // Generic sensor
        ..Default::default()
    };

    // Start advertising
    info!("Starting advertisement...");
    let adv_handle = adapter.advertise(adv).await?;
    info!(
        "Advertisement started. Device is discoverable as '{}'",
        name
    );

    // Handle the timeout
    if timeout_secs > 0 {
        info!("Server will run for {} seconds", timeout_secs);
        let start_time = Instant::now();
        while start_time.elapsed() < Duration::from_secs(timeout_secs) {
            sleep(Duration::from_secs(1)).await;

            // Display connected devices every 5 seconds
            if start_time.elapsed().as_secs() % 5 == 0 {
                match adapter.device_addresses().await {
                    Ok(addresses) => {
                        for addr in addresses {
                            if let Ok(device) = adapter.device(addr) {
                                if let Ok(true) = device.is_connected().await {
                                    if let Ok(Some(name)) = device.name().await {
                                        info!("Connected to device: {} ({})", name, addr);
                                    } else {
                                        info!("Connected to device: {}", addr);
                                    }
                                }
                            }
                        }
                    }
                    Err(e) => warn!("Failed to get device addresses: {}", e),
                }
            }
        }
        info!("Timeout reached. Shutting down server...");
    } else {
        info!("Server is running indefinitely. Press Ctrl+C to stop.");
        // Run indefinitely
        loop {
            sleep(Duration::from_secs(5)).await;

            // Display connected devices
            match adapter.device_addresses().await {
                Ok(addresses) => {
                    for addr in addresses {
                        if let Ok(device) = adapter.device(addr) {
                            if let Ok(true) = device.is_connected().await {
                                if let Ok(Some(name)) = device.name().await {
                                    info!("Connected to device: {} ({})", name, addr);
                                } else {
                                    info!("Connected to device: {}", addr);
                                }
                            }
                        }
                    }
                }
                Err(e) => warn!("Failed to get device addresses: {}", e),
            }
        }
    }

    // Stop advertising and GATT server
    drop(adv_handle);
    drop(app_handle);
    info!("Server stopped");

    Ok(())
}

fn create_gatt_application() -> Application {
    Application {
        services: vec![Service {
            uuid: SERVICE_UUID.parse().unwrap(),
            primary: true,
            characteristics: vec![
                // Read characteristic
                Characteristic {
                    uuid: READ_CHAR_UUID.parse().unwrap(),
                    read: Some(CharacteristicRead::new(|req| {
                        Box::pin(async move {
                            let device = req.device_address();
                            info!("Read request from {:?}", device);

                            // Return some data
                            let data = utils::get_current_timestamp().as_bytes().to_vec();
                            info!("Sending data: {:?}", String::from_utf8_lossy(&data));
                            Ok(data)
                        })
                    })),
                    ..Default::default()
                },
                // Write characteristic
                Characteristic {
                    uuid: WRITE_CHAR_UUID.parse().unwrap(),
                    write: Some(CharacteristicWrite::new(|value, req| {
                        Box::pin(async move {
                            let device = req.device_address();
                            let value_str = String::from_utf8_lossy(&value);
                            info!("Write request from {:?}: {}", device, value_str);
                            Ok(())
                        })
                    })),
                    ..Default::default()
                },
                // Notify characteristic
                Characteristic {
                    uuid: NOTIFY_CHAR_UUID.parse().unwrap(),
                    notify: Some(CharacteristicNotify::new()),
                    ..Default::default()
                },
            ],
            ..Default::default()
        }],
        _non_exhaustive: Default::default(),
    }
}
