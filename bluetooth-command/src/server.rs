use bluer::{
    adv::Advertisement,
    gatt::local::{
        characteristic_control, Application, Characteristic, CharacteristicNotify,
        CharacteristicNotifyMethod, CharacteristicWrite, CharacteristicWriteMethod, Service,
    },
};
use std::error::Error;
use std::time::{Duration, Instant};
use tokio::time::sleep;
use tracing::{info, warn};

use crate::constants::*;

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
    let (_, char_handle) = characteristic_control();
    Application {
        services: vec![Service {
            uuid: SERVICE_UUID.parse().unwrap(),
            primary: true,
            characteristics: vec![Characteristic {
                uuid: CHARACTERISTIC_UUID.parse().unwrap(),
                write: Some(CharacteristicWrite {
                    write_without_response: true,
                    method: CharacteristicWriteMethod::Io,
                    ..Default::default()
                }),
                notify: Some(CharacteristicNotify {
                    notify: true,
                    method: CharacteristicNotifyMethod::Io,
                    ..Default::default()
                }),
                control_handle: char_handle,
                ..Default::default()
            }],
            // Read characteristic
            ..Default::default()
        }],
        _non_exhaustive: Default::default(),
    }
}
