"""
Minecraft Server Handler

This module manages the lifecycle of various Minecraft server instances including:
- ATM10 (All The Mods 10)
- Vanilla Minecraft
- DC (Decresed Craft, currently offline)
- RF (Raspberry Flavored)

It provides functions to start, stop, and monitor server processes.
"""

import os
import requests
import subprocess
import asyncio

# ============================================================================
# SERVER CONFIGURATION
# ============================================================================

# Base directory path
DEFAULT_PATH = os.path.abspath(os.getcwd())

# Server start script paths - organized by server type
SERVER_PATHS = {
    "atm10": os.path.abspath(os.path.join(os.getcwd(), "atm10/run.sh")),
    "rf": os.path.abspath(os.path.join(os.getcwd(), "rf/run.sh")),
    "sf5": os.path.abspath(os.path.join(os.getcwd(), "skyfactory5/run.sh")),
    "ll": os.path.abspath(os.path.join(os.getcwd(), "lingolango/run.sh"))
}

# Server startup times (in seconds) - varies by modpack complexity
SERVER_BOOT_TIMES = {
    "atm10": 420,
    "rf": 300,
    "sf5": 300,
    "ll": 300
}

# ============================================================================
# GLOBAL STATE
# ============================================================================

process = None  # Current server process handle
booting = 0     # Flag to track if server is currently booting


# ============================================================================
# SERVER MANAGEMENT FUNCTIONS
# ============================================================================
async def wait_for_server_ready(process):
    ready_keywords = [
        "[minecraft/DedicatedServer]: Done",  # vanilla/paper
        "For help, type",  # common fallback
    ]

    loop = asyncio.get_event_loop()

    while True:
        # Read line without blocking the event loop
        line = await loop.run_in_executor(None, process.stdout.readline)

        if not line:
            # Process ended/crashed
            return False

        # Check for ready message
        if any(keyword in line for keyword in ready_keywords):
            return True

async def run_server(version: str) -> bool:
    """
    Start a Minecraft server of the specified version.

    Args:
        version (str): The server type to start. One of: 'vanilla', 'atm10', 'dc', 'rf'

    Returns:
        bool: True if server started successfully, False otherwise
    
    Raises:
        KeyError: If the version is not in SERVER_PATHS or SERVER_BOOT_TIMES
    """
    global process
    global booting

    # Prevent starting multiple servers simultaneously
    if process is not None:
        return False

    # Validate version
    if version not in SERVER_PATHS:
        return False

    try:
        booting = 1
        server_path = SERVER_PATHS[version]
        boot_time = SERVER_BOOT_TIMES[version]
        cwd = os.path.dirname(server_path)

        # Start the server process with stdin pipe for sending commands
        process = subprocess.Popen(
            server_path,
            shell=True,
            stdin=subprocess.PIPE,
            cwd=cwd
        )
        process_id = process.pid

        # Wait for server to boot up
        await asyncio.sleep(boot_time)

        booting = 0
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error starting server: {e}")
        booting = 0
        return False


async def stop_server() -> bool:
    """
    Stop the running Minecraft server.

    First attempts to send "stop" command via stdin for clean shutdown.
    If that fails or times out, forcefully terminates the process.

    Returns:
        bool: True if server stopped successfully, False if no server was running
    """
    global process

    if process is None:
        return False

    try:
        # Wait before sending stop command to ensure server is ready
        await asyncio.sleep(30)

        # Check if process is still running
        if process.poll() is None:
            try:
                # Send stop command to server console
                process.stdin.write(b"stop\n")
                process.stdin.flush()
            except BrokenPipeError:
                # Pipe already closed, process likely terminated
                process = None
                return False

            try:
                # Wait for graceful shutdown
                process.wait(timeout=60)
            except subprocess.TimeoutExpired:
                # Server didn't stop in time, force kill it
                process.kill()

        process = None
        return True

    except Exception as e:
        print(f"Error stopping server: {e}")
        return False


def status() -> bool:
    """
    Check if a server process is currently running.

    Returns:
        bool: True if server is running, False otherwise
    """
    return process is not None


def get_ip():
    """
    Retrieve the public IP address of the machine.

    Uses the ipify API to get the external IP address. Useful for
    providing connection information to players.

    Returns:
        str: Public IP address on success, or 0 (int) if request fails
    """
    try:
        response = requests.get("https://api.ipify.org")
        return response.text if response.status_code == 200 else 0
    except Exception as e:
        print(f"Error retrieving IP: {e}")
        return 0
