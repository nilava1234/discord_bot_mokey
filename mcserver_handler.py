import os
import requests
import subprocess
import discord
import threading
import asyncio
from functools import partial

path = os.path.abspath(os.path.join(os.getcwd(), "bedrock_server"))
process = None

#run the server
def run_server(ctx):
    global process
    if process is None:
        try:
            command = f"./{path}"  # Redirect both stdout and stderr to the file
            process = subprocess.Popen(command, shell=True, check=True)
            process_id = process.pid
            print(f"Server Started PID: {process_id}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            return False
    else:
        return False

#terminate the server  
def stop_server():
    global stop_event
    global process
    if process is not None:
        try:
            # Send "stop" command to the server
            process.terminate()  # Wait for the subprocess to finish
            process = None
            return True
        except Exception as e:
            print(f"Error stopping server: {e}")
            return False
    else:
        return False
    
#get the status
def status():
    return process is not None
    
#get the ip
def get_ip():
    response = requests.get("https://api.ipify.org")
    return response.text if response.status_code==200 else 0