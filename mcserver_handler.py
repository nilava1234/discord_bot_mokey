import os
import requests
import subprocess
import discord

path = os.path.abspath(os.path.join(os.getcwd(), "bedrock_server"))
process = None


#run the server
def run_server() :
    global process
    if process is None:
        try:
            process = subprocess.Popen(path)
            process_id = process.pid
            print(f"Server Started PID: {process_id}")
            return True
        except subprocess.CalledProcessError as e:
            # Handle errors, if any
            print(f"Error: {e}")
            return False
    else:
        return False

#terminate the server  
def terminate() :
    global process
    if process is not None:
        try:
            process_id = process.pid
            process.terminate()
            print(f"Server Closed PID: {process_id}")
            process = None
            return True
        except subprocess.CalledProcessError as e:
            return False
        
#get the status
def status():
    if process is None:
        return False
    else:
        return True
    
#get the ip
def get_ip():
    response = requests.get("https://api.ipify.org")
    return response.text if response.status_code==200 else 0