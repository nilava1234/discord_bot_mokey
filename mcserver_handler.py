import os
import requests
import subprocess
import asyncio

defualt_path = os.path.abspath(os.getcwd())
vanilla_path = os.path.abspath(os.path.join(os.getcwd(), "vanilla_minecraft/start.sh"))
atm10_path = os.path.abspath(os.path.join(os.getcwd(), "atm10/run.sh"))
dc_path = os.path.abspath(os.path.join(os.getcwd(), "dc/run.sh"))
rf_path = os.path.abspath(os.path.join(os.getcwd(), "rf/run.sh"))
process = None
booting = 0

# Run the server
async def run_server(version:str ):
    global process
    global booting
    if process is None:
        booting = 0
        try:
            if version == "atm10":
                booting = 1
                cwd = os.path.dirname(atm10_path)
                process = subprocess.Popen(atm10_path, shell=True, stdin=subprocess.PIPE, cwd=cwd)
                process_id = process.pid
                await asyncio.sleep(420)
                print(f"Server Started PID: {process_id}")
                booting = 0
                cwd = os.path.dirname(defualt_path)
                return True
            if version == "vanilla":
                booting = 1
                cwd = os.path.dirname(vanilla_path)
                process = subprocess.Popen(vanilla_path, shell=True, stdin=subprocess.PIPE, cwd=cwd)
                process_id = process.pid
                await asyncio.sleep(80)
                print(f"Server Started PID: {process_id}")
                booting = 0
                cwd = os.path.dirname(defualt_path)
                return True
            if version == "dc":
                booting = 1
                cwd = os.path.dirname(dc_path)
                process = subprocess.Popen(dc_path, shell=True, stdin=subprocess.PIPE, cwd=cwd)
                process_id = process.pid
                await asyncio.sleep(300)
                print(f"Server Started PID: {process_id}")
                booting = 0
                cwd = os.path.dirname(defualt_path)
                return True
            if version == "rf":
                booting = 1
                cwd = os.path.dirname(rf_path)
                process = subprocess.Popen(rf_path, shell=True, stdin=subprocess.PIPE, cwd=cwd)
                process_id = process.pid
                await asyncio.sleep(300)
                print(f"Server Started PID: {process_id}")
                booting = 0
                cwd = os.path.dirname(defualt_path)
                return True
            else:
                return False
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            return False
    else:
        return False

# Terminate the server  
async def stop_server():
    global process
    if process is not None:
        try:
            # Send "stop" command to the server
            await asyncio.sleep(30)
            if process.poll() is None:
                try:
                    process.stdin.write(b"stop\n")
                    process.stdin.flush()
                except BrokenPipeError:
                    process = None
                    return False
                try:
                    process.wait(timeout=60)  # Wait for the subprocess to finish
                except subprocess.TimeoutExpired:
                    process.kill
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
