import configparser
import discord
from discord import Intents
from discord import app_commands
from discord.ext import commands as discord_commands

import mcserver_handler
import music_handler



#Intilziing and setting up bot via token and intents
config = configparser.ConfigParser()
config.read('config.ini')
TOKEN = config['Bot']['TOKEN']
intents = Intents.all()
client = discord_commands.Bot(command_prefix='!', intents=intents)
commands = client.tree

#ON_READY method that runs when bot is started
@client.event
async def on_ready():
    print(f'{client.user} is now running')
    try:
        synched = await commands.sync()
        print(f"Synched {len(synched)} command(s)")
    except Exception as e:
        print("Failed in on_ready")
        print(e)


#skips current song
@commands.command(name="next", description="Skip Current Song")
async def next(message):
    await music_handler.play_next(message)

#play music via a link from spotify or youtube
@commands.command(name="play", description="Play Music from Spotify or Youtube")
@app_commands.describe(link = "Youtube or Spotify Link")
async def play(message, link:str):
    global client
    await music_handler.play(message, link, client)

#pause the current song
@commands.command(name="pause", description="Pause Current Song")
async def pause(message):
    global client
    await music_handler.pause(message, client)

#stop the current song and clear queue
@commands.command(name="stop", description="Stops the current queue and clears it")
async def stop(message):
    global client
    await music_handler.clear_queue(message, client)

#list the current queue
@commands.command(name="queue", description="Lists all songs in queue")
async def queue(message):
    await music_handler.show_queue(message)

#start the mc server
@commands.command(name="mcstart", description="Starts the MC:BE Server")
async def mcstart(message):
    print("Attempting to start the server...")
    await message.response.send_message("Server Booting Up...")
    if mcserver_handler.run_server():
        await message.channel.send("-Server is Online-")
    else:
        await message.channel.send("Oops something went wrong. Check Server Status.")

#stop the mc server
@commands.command(name="mcstop", description="Stops the MC:BE Server")
async def mcstop(message):
    print("Closing the server...")
    await message.response.send_message("Server shutting down...")
    if mcserver_handler.terminate():
        await message.channel.send("-Server is Offline-")
    else:
        await message.channel.send("Oops something went wrong. Check Server Status")

#get the status of the mc server
@commands.command(name="mcstatus", description="Gets the status of the MC:BE Server")
async def mcstatus(message):
    print("Grabing server status")
    stat = mcserver_handler.status()
    if stat:
        await message.response.send_message("Server: Active")
    else:
        await message.response.send_message("Server: Offline")

#grab the ip of the current mc server
@commands.command(name="mcip", description="Gets the IP, Port, and status of the server")
async def mcip(message):
    ipv4_address = mcserver_handler.get_ip()
    print(f"ip: {ipv4_address}")
    stat = "Online" if mcserver_handler.status() else "Offline"
    await message.response.send_message(f"REMEMBER THIS IS SECURITY SENSITIVE DONT SHARE WITH PEOPLE\nip: ||{ipv4_address}|| \nport: ||19132||\nStatus: {stat}")

#Command that lists all avalible commands
@commands.command(name="help", description="list all commands")
async def help(message):
    try:
        print("Asking for help")
        await message.response.send_message("""
Here are a list of commands:
======================
***General:***
help - List of out all the commands I know
========================
***Minecraft Server Related Commands***
mcstart - Starts the Minecraft Bedrock Server
mcstop - Stops the Minecraft Server
mcstatus - Provides the status of the server
mcip - Provides the IP of the server
========================
***Music***
play - Given a Youtube Link or a Spotify Link plays a song.
queue - Provides a list of songs in queue
pause - Pauses the current song
stop - Stops the current and clears the queue
            """)
    except Exception as e:
        print("Failed in help")
        print(e)


#runs the bot with a token
client.run(TOKEN)
