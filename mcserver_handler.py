import os
import requests
import subprocess
import discord
import threading
import asyncio
from functools import partial

path = os.path.abspath(os.path.join(os.getcwd(), "bedrock_server"))
process = None
stop_event = threading.Event()
output_file = "server_output.txt"

async def send_output_to_discord(ctx):
    global process
    messages = []  # Keep track of messages sent to the channel

    while process is not None:
        with open(output_file, "r") as file:
            lines = file.readlines()
            if lines:
                lines = lines[-10:]  # Get the last 10 lines
                output = "".join(lines)
                if messages:
                    # Update the last sent message with new output
                    await messages[-1].edit(content=f"```\n{output}\n```")
                else:
                    # Send a new message with the output
                    message = await ctx.channel.send(f"```\n{output}\n```")
                    messages.append(message)
        await asyncio.sleep(5)  # Adjust the sleep duration as needed

#run the server
def run_server(ctx):
    global process
    if process is None:
        try:
            command = f"xterm -hold -e {path}"  # Open a new terminal and run the executable
            process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE)
            process_id = process.pid
            print(f"Server Started PID: {process_id}")
            threading.Thread(target=partial(send_output_to_discord, ctx)).start()
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
            send_command("stop\n")
            process.wait()  # Wait for the subprocess to finish
            process = None
            return True
        except Exception as e:
            print(f"Error stopping server: {e}")
            return False
        finally:
            process = None
            stop_event.set()
    else:
        return False

def send_command(command):
    global process
    if process is not None:
        try:
            process.stdin.write(command.encode('utf-8'))
            process.stdin.flush()
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
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