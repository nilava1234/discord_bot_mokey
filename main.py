import configparser
import discord
from discord import Intents
from discord import app_commands
from discord.ext import commands as discord_commands
import asyncio
import mcserver_handler
import music_handler
import mtg_handler

config = configparser.ConfigParser()
config.read('config.ini')
TOKEN = config['Bot']['TOKEN']
intents = Intents.all()
client = discord_commands.Bot(command_prefix='!', intents=intents)
commands = client.tree

@client.event
async def on_ready():
    try:
        print(f'{client.user} is now running')
        synched = await commands.sync()
        print(f"Synched {len(synched)} command(s)")
    except Exception as e:
        print("Failed in on_ready")
        print(e)

@commands.command(name="mtg", description="Provide a name")
async def mtg(ctx, query: str):
    try:
        await mtg_handler.mtg_main(ctx, query)
    except Exception as e:
        print(e)
        await ctx.send("⚠️ An error has occurred.")

@commands.command(name='leave')
async def leave(ctx):
    try:
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        else:
            await ctx.send("I'm not in a voice channel.")
    except Exception as e:
        print(e)
        await ctx.send("⚠️ An error has occurred.")

@commands.command(name="skip", description="Skip Current Song")
async def next(message):
    try:
        await message.response.send_message("⏭️ Skipping Current Song...")
        voice_client = discord.utils.get(message.client.voice_clients, guild=message.guild)
        if voice_client and voice_client.is_playing():
            voice_client.stop()
    except Exception as e:
        print(e)
        await message.channel.send("⚠️ An error has occurred.")

@commands.command(name="play", description="Play Music from Spotify or Youtube")
@app_commands.describe(link="Youtube, Spotify, or a Search Query")
async def play(message, link: str):
    try:
        await message.response.send_message("Queuing Up...")
        await music_handler.play(message, link)
    except Exception as e:
        print(e)
        await message.channel.send("⚠️ An error has occurred.")

@commands.command(name="pause", description="Pause Current Song")
async def pause(message):
    try:
        await message.response.send_message("Paused ⏸︎")
        await music_handler.pause(message)
    except Exception as e:
        print(e)
        await message.channel.send("⚠️ An error has occurred.")

@commands.command(name="stop", description="Stops the current queue and clears it")
async def stop(message):
    try:
        await message.response.send_message("Clearing Queue...")
        await music_handler.clear_queue(message)
        await message.channel.send("Music Stopped and Queue Cleared")
    except Exception as e:
        print(e)
        await message.channel.send("⚠️ An error has occurred.")

@commands.command(name="queue", description="Lists all songs in queue")
async def queue(message):
    try:
        await message.response.send_message("Fetching Queue...")
        await music_handler.show_queue(message)
    except Exception as e:
        print(e)
        await message.channel.send("⚠️ An error has occurred.")

@commands.command(name="mcreboot", description="Reboots the server")
async def mcreboot(message):
    try:
        await mcstop(message)
        await mcstart(message)
    except Exception as e:
        print(e)
        await message.channel.send("⚠️ An error has occurred.")

@commands.command(name="mcstart", description="Starts the MC:BE Server")
@app_commands.describe(version="vanilla, atm10")
async def mcstart(message, version:str = "vanilla"):
    version = version.lower()
    try:
        print("Attempting to start the server...")
        await message.response.send_message("Server Booting Up...")
        if await mcserver_handler.run_server(version):
            await message.channel.send("-Server is Online-")
        else:
            await message.channel.send("Oops something went wrong. Check Server Status.")
    except Exception as e:
        print(e)
        await message.channel.send("⚠️ An error has occurred.")

@commands.command(name="mcstop", description="Stops the MC:BE Server")
async def mcstop(message):
    try:
        if not mcserver_handler.booting:
            print("Closing the server...")
            await message.response.send_message("Server shutting down...")
            if await mcserver_handler.stop_server():
                await message.channel.send("-Server is Offline-")
            else:
                await message.channel.send("Oops something went wrong. Check Server Status")
        else:
            await message.response.send_message("Oops, looks like a server is currently booting up, please wait.")
    except Exception as e:
        print(e)
        await message.channel.send("⚠️ An error has occurred.")

@commands.command(name="mcstatus", description="Gets the status of the MC:BE Server")
async def mcstatus(message):
    try:
        print("Grabbing server status")
        stat = mcserver_handler.status()
        if stat:
            await message.response.send_message("Server: Active")
        else:
            await message.response.send_message("Server: Offline")
    except Exception as e:
        print(e)
        await message.channel.send("⚠️ An error has occurred.")

@commands.command(name="mcip", description="Gets the IP, Port, and status of the server")
async def mcip(message: discord.Interaction):
    try:
        ipv4_address = "nilavashub.duckdns.org"
        print(f"IP: {ipv4_address}")
        stat = "Online" if mcserver_handler.status() else "Offline"
        await message.response.send_message(
            f"REMEMBER THIS IS SECURITY SENSITIVE, DON'T SHARE WITH PEOPLE\n"
            f"IP: ||{ipv4_address}|| \nPort: ||19132||\nStatus: {stat}"
        )
        await asyncio.sleep(30)
        await message.delete_original_response()
    except Exception as e:
        print(e)
        await message.channel.send("⚠️ An error has occurred.")

@commands.command(name="help", description="List all commands")
async def help(message):
    try:
        print("Asking for help")
        await message.response.send_message("""
Here are a list of commands:
======================
***General:***
help - List all commands
========================
***Minecraft Server Related Commands (1.20.4)***
mcstart - Starts the Minecraft Bedrock Server
mcstop - Stops the Minecraft Server
mcstatus - Provides the status of the server
mcip - Provides the IP of the server
========================
***Music***
play - Given a search query, youtube playlist/song, or spotify playlist/song, plays music
queue - Provides a list of songs in queue
pause - Pauses the current song
resume - Resumes the current paused song
stop - Stops the current and clears the queue
""")
    except Exception as e:
        print(e)
        await message.channel.send("⚠️ An error has occurred.")

client.run(TOKEN)
