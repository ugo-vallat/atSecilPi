#!/usr/bin/env python3
import fcntl
import os
import select
import signal
import socket
import subprocess
import sys
import tempfile
import time


def run_command(cmd):
    """Run a shell command and return the output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Command warning: {cmd}")
            print(f"Output: {result.stderr}")
        return result.stdout.strip()
    except Exception as e:
        print(f"Error: {e}")
        return ""


def setup_bluetooth_server(your_name):
    """Set up Bluetooth server using socket API"""
    print(f"Setting up Bluetooth server as '{your_name}'...")

    # Make sure Bluetooth is powered on
    run_command("bluetoothctl power on")
    run_command("bluetoothctl discoverable on")
    run_command("bluetoothctl pairable on")

    # Get local Bluetooth address for information
    local_addr = get_bluetooth_address()
    print(f"Local Bluetooth address: {local_addr}")

    # Create a Bluetooth socket
    try:
        # Create an RFCOMM socket
        server_sock = socket.socket(
            socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
        )
        server_sock.bind((BDADDR_ANY, PORT))
        server_sock.listen(1)

        port = server_sock.getsockname()[1]
        print(f"Listening on RFCOMM channel {port}")
        print("Waiting for client connection...")

        # Accept a connection
        client_sock, client_info = server_sock.accept()
        print(f"Accepted connection from {client_info}")

        return client_sock, server_sock
    except Exception as e:
        print(f"Socket error: {e}")
        raise


def setup_bluetooth_client(server_name):
    """Set up Bluetooth client using socket API"""
    print(f"Setting up Bluetooth client looking for '{server_name}'...")

    # Make sure Bluetooth is powered on
    run_command("bluetoothctl power on")

    # Scan for devices
    print("Scanning for Bluetooth devices...")
    run_command("bluetoothctl scan on &")

    # Give some time for scanning
    time.sleep(5)

    # Get list of devices
    devices_output = run_command("bluetoothctl devices")
    devices = devices_output.split("\n")

    server_address = None
    print("Available devices:")
    for i, device in enumerate(devices):
        print(f"{i+1}: {device}")
        if server_name.lower() in device.lower():
            parts = device.split(" ", 2)
            if len(parts) >= 2:
                server_address = parts[1]
                print(f"Found server by name: {server_address}")

    # If we couldn't find by name, ask user to select
    if not server_address:
        choice = input("Enter number of server device or MAC address directly: ")
        try:
            # Check if input is a number (selecting from list)
            index = int(choice) - 1
            if 0 <= index < len(devices):
                device = devices[index]
                parts = device.split(" ", 2)
                if len(parts) >= 2:
                    server_address = parts[1]
        except ValueError:
            # Input might be a MAC address directly
            if ":" in choice:
                server_address = choice

    if not server_address:
        print("No server device selected")
        sys.exit(1)

    print(f"Connecting to server at {server_address}")

    # Create a Bluetooth socket
    try:
        client_sock = socket.socket(
            socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
        )

        # Try pairing first
        print("Attempting to pair...")
        run_command(f"bluetoothctl pair {server_address}")

        # Then connect
        print(f"Connecting to {server_address} on channel {PORT}...")
        client_sock.connect((server_address, PORT))
        print("Connected!")

        return client_sock
    except Exception as e:
        print(f"Socket error: {e}")
        raise


def get_bluetooth_address():
    """Get the Bluetooth MAC address of the local adapter"""
    output = run_command("hciconfig | grep 'BD Address' | awk '{print $3}'")
    if not output:
        # Try an alternative command
        output = run_command("bluetoothctl list | head -n 1 | awk '{print $2}'")
    return output


def read_and_consume_new_lines(file_path):
    """Read new lines from file and consume them (remove after reading)"""
    if not os.path.exists(file_path):
        return []

    # Create a temporary file for rewriting
    temp_fd, temp_path = tempfile.mkstemp()
    lines_to_send = []

    try:
        # Lock the file to prevent concurrent modifications
        with open(file_path, "r+") as f:
            # Try to get an exclusive lock
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError as e:
                print(f"Could not lock file: {e}")
                return []

            # Read all lines
            lines = f.readlines()

            # Reopen and truncate the original file
            f.seek(0)
            f.truncate()

            # Keep track of lines we've read to send
            for line in lines:
                line = line.strip()
                if line:  # Skip empty lines
                    lines_to_send.append(line)

            # Release the lock
            fcntl.flock(f, fcntl.LOCK_UN)
    except Exception as e:
        print(f"Error reading file: {e}")
    finally:
        os.close(temp_fd)
        os.unlink(temp_path)

    return lines_to_send


def execute_command(command, working_dir):
    """Execute a command in the specified directory"""
    print(f"Executing: {command}")
    try:
        # Change to the working directory
        original_dir = os.getcwd()
        os.chdir(working_dir)

        # Execute the command
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Collect output with a timeout
        try:
            stdout, stderr = process.communicate(timeout=30)
            exit_code = process.returncode

            if exit_code != 0:
                print(f"Command failed with exit code {exit_code}")
                print(f"Error: {stderr}")
            else:
                print(f"Command executed successfully")
                if stdout:
                    print(
                        f"Output: {stdout[:200]}..."
                    )  # Print first 200 chars of output
        except subprocess.TimeoutExpired:
            process.kill()
            print("Command timed out after 30 seconds")

        # Return to original directory
        os.chdir(original_dir)

    except Exception as e:
        print(f"Error executing command: {e}")
        # Return to original directory
        if "original_dir" in locals():
            os.chdir(original_dir)


def run_server(your_name, other_name, watch_file):
    client_sock = None
    server_sock = None

    # Bluetooth constants
    global BDADDR_ANY, PORT
    BDADDR_ANY = "00:00:00:00:00:00"
    PORT = 1  # Use any available port

    try:
        client_sock, server_sock = setup_bluetooth_server(your_name)

        print(f"Watching file: {watch_file}")
        print("Press Ctrl+C to stop")

        # Check if file exists, create it if it doesn't
        if not os.path.exists(watch_file):
            with open(watch_file, "w") as f:
                pass
            print(f"Created empty file: {watch_file}")

        last_check_time = time.time()

        while True:
            # Check for new lines periodically
            current_time = time.time()
            if current_time - last_check_time >= 1.0:  # Check every second
                commands = read_and_consume_new_lines(watch_file)
                for command in commands:
                    print(f"New command found: {command}")
                    try:
                        client_sock.send((command + "\n").encode())
                        print(f"Sent command to client")
                    except Exception as e:
                        print(f"Error sending command: {e}")
                last_check_time = current_time

            time.sleep(0.1)  # Sleep to prevent CPU hogging
    except KeyboardInterrupt:
        print("\nStopping server...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if client_sock:
            client_sock.close()
        if server_sock:
            server_sock.close()
        # Cleanup
        run_command("bluetoothctl discoverable off")


def run_client(your_name, server_name, execute_dir):
    client_sock = None

    # Bluetooth constants
    global BDADDR_ANY, PORT
    BDADDR_ANY = "00:00:00:00:00:00"
    PORT = 1  # Use any available port

    try:
        client_sock = setup_bluetooth_client(server_name)
        client_sock.settimeout(0.5)  # Short timeout for non-blocking reads

        print(f"Listening for commands. Will execute in directory: {execute_dir}")
        print("Press Ctrl+C to stop")

        buffer = ""
        while True:
            try:
                data = client_sock.recv(1024).decode()
                if not data:
                    print("Connection lost")
                    break

                buffer += data
                while "\n" in buffer:
                    command, buffer = buffer.split("\n", 1)
                    if command:
                        print(f"Received command: {command}")
                        execute_command(command, execute_dir)
            except socket.timeout:
                # This is just a timeout for the recv call, not an error
                pass
            except Exception as e:
                print(f"Error receiving data: {e}")
                break

            time.sleep(0.1)  # Sleep to prevent CPU hogging
    except KeyboardInterrupt:
        print("\nStopping client...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if client_sock:
            client_sock.close()


def main():
    if len(sys.argv) < 5:
        print("Usage:")
        print(
            "  Server mode: python script.py server YOUR_NAME OTHER_DEVICE_NAME FILE_TO_WATCH"
        )
        print(
            "  Client mode: python script.py client YOUR_NAME SERVER_NAME EXECUTION_DIRECTORY"
        )
        sys.exit(1)

    mode = sys.argv[1].lower()
    your_name = sys.argv[2]
    other_name = sys.argv[3]
    path = sys.argv[4]

    if mode == "server":
        run_server(your_name, other_name, path)
    elif mode == "client":
        if not os.path.exists(path) or not os.path.isdir(path):
            print(f"Error: Path '{path}' does not exist or is not a directory")
            sys.exit(1)
        run_client(your_name, other_name, path)
    else:
        print(f"Invalid mode: {mode}. Must be 'server' or 'client'")
        sys.exit(1)


if __name__ == "__main__":
    main()
