use bluer::{
    adv::Advertisement,
    gatt::local::{
        characteristic_control, Application, Characteristic, CharacteristicNotify,
        CharacteristicNotifyMethod, CharacteristicWrite, CharacteristicWriteMethod, Service,
    },
};
use std::time::{Duration, Instant};
use std::{error::Error, f64::INFINITY};
use tokio::time::sleep;
use tracing::{info, warn};

use crate::constants::*;

pub async fn run_server(name: &str, timeout_secs: u64) -> Result<(), Box<dyn Error>> {
    info!("Starting Bluetooth server with name: {}", name);

    let session = bluer::Session::new().await?;
    let adapter = session.default_adapter().await?;

    // Enable the adapter
    adapter.set_powered(true).await?;
    info!("Bluetooth adapter {} powered on", adapter.name());

    info!(
        "Advertising on Bluetooth adapter {} with address {}",
        adapter.name(),
        adapter.address().await?
    );
    let adv = Advertisement {
        service_uuids: vec![SERVICE_UUID.parse().unwrap()].into_iter().collect(),
        discoverable: Some(true),
        local_name: Some(name.to_string()),
        ..Default::default()
    };

    info!("Starting advertisement...");
    let adv_handle = adapter.advertise(adv).await?;
    info!(
        "Advertisement started. Device is discoverable as '{}'",
        name
    );

    info!("Registering GATT application...");
    let (_, char_handle) = characteristic_control();
    let app_handle = Application {
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
    };
    let app_handle = adapter.serve_gatt_application(app_handle).await?;
    info!("GATT application registered");

    if timeout_secs < 0 {
        timeout_secs = f64::INFINITY;
        info!("Server will run until it's stopped");
    } else {
        info!("Server will run for {} seconds", timeout_secs);
    }

    let start_time = Instant::now();
    while start_time.elapsed() < Duration::from_secs(timeout_secs) {
        sleep(Duration::from_secs(1)).await;

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

    drop(adv_handle);
    drop(app_handle);
    info!("Server stopped");

    Ok(())
}
