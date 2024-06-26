import configparser
import discord
from discord import Intents
from discord import app_commands
from discord.ext import commands as discord_commands
import asyncio
import mcserver_handler
import music_handler
import mtg_handler



#Intilziing and setting up bot via token and intents
config = configparser.ConfigParser()
config.read('config.ini')
TOKEN = config['Bot']['TOKEN']
intents = Intents.all()
client = discord_commands.Bot(command_prefix='!', intents=intents)
commands = client.tree
'''
    This part of the code is simple set-ups for the discord bot. Not much to it
'''
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
@commands.command(name="mtg", description="Provide a name")
async def mtg(ctx, query:str):
    await mtg_handler.mtg_main(ctx, query)

@commands.command(name='leave')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("I'm not in a voice channel.")
'''
    All proceding methods are for the music player functions. The names should be self explanitory
'''

#skips current song
@commands.command(name="skip", description="Skip Current Song")
async def next(message):

    await message.response.send_message("Skipping Current Song...")
    await music_handler.play_next(message)

#play music via a link from spotify or youtube
@commands.command(name="play", description="Play Music from Spotify or Youtube")
@app_commands.describe(link = "Youtube, Spotify, or a Search Query")
async def play(message, link:str):
    global client

    await message.response.send_message("Queuing Up...")
    await music_handler.play(message, link, client)

#pause the current song
@commands.command(name="pause", description="Pause Current Song")
async def pause(message):
    global client

    await message.response.send_message("Paused ⏸︎")
    await music_handler.pause(message, client)

#stop the current song and clear queue
@commands.command(name="stop", description="Stops the current queue and clears it")
async def stop(message):
    global client

    await message.response.send_message("Clearing Queue...")
    await music_handler.clear_queue(message, client)
    await message.channel.send("Music Stopped and Queue Cleared")

#list the current queue
@commands.command(name="queue", description="Lists all songs in queue")
async def queue(message):
    message.response.send_message("Queue:")
    await music_handler.show_queue(message)

'''
    The code that handles the minecraft server.
    
    This code cannot be ran by any computer other than the minecraft server
    host computer. But computers set-up to properly to run such code may.
'''
#start the mc server
@commands.command(name="mcstart", description="Starts the MC:BE Server")
async def mcstart(message):
    print("Attempting to start the server...")
    await message.response.send_message("Server Booting Up...")
    if await mcserver_handler.run_server():
        await message.channel.send("-Server is Online-")
    else:
        await message.channel.send("Oops something went wrong. Check Server Status.")

#stop the mc server
@commands.command(name="mcstop", description="Stops the MC:BE Server")
async def mcstop(message):
    try:
        if(not mcserver_handler.booting):
    
            print("Closing the server...")
            await message.response.send_message("Server shutting down...")
            if await mcserver_handler.stop_server():
                await message.channel.send("-Server is Offline-")
            else:
                await message.channel.send("Oops something went wrong. Check Server Status")
        else:
            await message.response.send_message("Oop. looks like a server is currently booting up, please wait")
    except Exception as e:
        print("Failed in mcstop: {e}")
    

#get the status of the mc server
@commands.command(name="mcstatus", description="Gets the status of the MC:BE Server")
async def mcstatus(message):
    try:
        print("Grabing server status")
        stat = mcserver_handler.status()
        if stat:
            await message.response.send_message("Server: Active")
        else:
            await message.response.send_message("Server: Offline")
    except Exception as e:
        print("Failed in mcstatus: {e}")


#grab the ip of the current mc server
@commands.command(name="mcip", description="Gets the IP, Port, and status of the server")
async def mcip(message:discord.Interaction):
    try:
        ipv4_address = mcserver_handler.get_ip()
        print(f"ip: {ipv4_address}")
        stat = "Online" if mcserver_handler.status() else "Offline"
        await message.response.send_message(f"REMEMBER THIS IS SECURITY SENSITIVE DONT SHARE WITH PEOPLE\nip: ||{ipv4_address}|| \nport: ||19132||\nStatus: {stat}")
        await asyncio.sleep(30)
        await message.delete_original_response()
    except Exception as e:
        print("Failed in MCIP: {e}")

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
***Minecraft Server Related Commands (1.20.4)***
mcstart - Starts the Minecraft Bedrock Server
mcstop - Stops the Minecraft Server
mcstatus - Provides the status of the server
mcip - Provides the IP of the server
========================
***Music***
play - Given a Youtube Link or a Spotify Link plays a song.
queue - Provides a list of songs in queue
pause - Pauses the current song
resume - Resumes the current paused song
stop - Stops the current and clears the queue
            """)
    except Exception as e:
        print("Failed in help")
        print(e)


#runs the bot with a token
client.run(TOKEN)
