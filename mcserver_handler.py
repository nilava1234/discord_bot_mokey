import os
import requests
import subprocess
import time

path = os.path.abspath(os.path.join(os.getcwd(), "bedrock_server"))
process = None

# Run the server
def run_server():
    global process
    if process is None:
        try:
            process = subprocess.Popen(path, stdin=subprocess.PIPE)
            process_id = process.pid
            print(f"Server Started PID: {process_id}")
            time.sleep(60)  # Wait for 60 seconds
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            return False
    else:
        return False

# Terminate the server  
def stop_server():
    global process
    if process is not None:
        try:
            # Send "stop" command to the server
            process.stdin.write(b"stop\n")
            process.stdin.flush()
            process.wait()  # Wait for the subprocess to finish
            process = None
            return True
        except Exception as e:
            print(f"Error stopping server: {e}")
            return False
    else:
        return False
    
# Get the status
def status():
    return process is not None
    
# Get the IP
def get_ip():
    response = requests.get("https://api.ipify.org")
    return response.text if response.status_code==200 else 0
