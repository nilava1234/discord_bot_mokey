import asyncio
import os

import discord
from discord import Intents, app_commands
from discord.ext import commands as discord_commands
from dotenv import load_dotenv

import mcserver_handler
import music_handler
import mtg_handler
import stock_handler

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
intents = Intents.all()
client = discord_commands.Bot(command_prefix='!', intents=intents)
commands = client.tree
admin_server_ids = [1301377784505040968,1468135016931524613]
permitted_servers = []
permitted_servers.extend(admin_server_ids)


# ============================================================================
# EVENT HANDLERS
# ============================================================================

@client.event
async def on_ready():
    """Triggered when the bot successfully connects to Discord."""
    try:
        print(f'{client.user} is now running')
        synched = await commands.sync()
        print(f"Synched {len(synched)} command(s)")

        print(f"Checking servers for permissions...")
        for guild in client.guilds:
            if guild.id in permitted_servers:
                print(f"Bot is active in: {guild.name} (ID: {guild.id})")
            else:
                print(f"Killing bot in: {guild.name} (ID: {guild.id})")
                await guild.leave()

    except Exception as e:
        print(f"Failed in on_ready: {e}")
@client.event
async def on_guild_join(guild):
    try:
        print(f"Joined new guild: {guild.name} (ID: {guild.id})")
        if guild.id not in permitted_servers:
            print(f"Killing bot in: {guild.name} (ID: {guild.id})")
            await guild.leave()
        else:
            print(f"Bot is active in: {guild.name} (ID: {guild.id})")
    except Exception as e:
        print(f"Failed in on_guild_join: {e}")

        
@client.hybrid_command(name="sync", description="Sync Commands")
async def sync(ctx):
    """Sync the bot's commands with Discord."""
    try:
        synched = await commands.sync()
        await ctx.send(f"Synched {len(synched)} command(s)")
    except Exception as e:
        print(f"Sync command error: {e}")
        await ctx.send("⚠️ An error has occurred.")

# ============================================================================
# MTG COMMANDS
# ============================================================================

@commands.command(name="mtg", description="Provide a name")
async def mtg(ctx, query: str):
    """Search for Magic: The Gathering card information by name."""
    try:
        await mtg_handler.mtg_main(ctx, query)
    except Exception as e:
        print(f"MTG command error: {e}")
        await ctx.send("⚠️ An error has occurred.")

# ============================================================================
# VOICE COMMANDS
# ============================================================================

@commands.command(name='leave')
async def leave(ctx):
    """Disconnect the bot from the current voice channel."""
    try:
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        else:
            await ctx.send("I'm not in a voice channel.")
    except Exception as e:
        print(e)
        await ctx.send("⚠️ An error has occurred.")

# ============================================================================
# MUSIC COMMANDS
# ============================================================================
@commands.command(name="shuffle", description="Shuffle the current queue")
async def shuffle(message):
    """Shuffle the current music queue."""
    try:
        await music_handler.shuffle_queue(message)
        await message.response.send_message("🔀 Queue shuffled.")
    except Exception as e:
        print(e)
        await message.channel.send("⚠️ An error has occurred.")

@commands.command(name="skip", description="Skip Current Song")
async def next(message):
    """Skip the currently playing song and play the next one in queue."""
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
    """Play a song or playlist from YouTube, Spotify, or search query."""
    try:
        await message.response.send_message("Queuing Up...")
        await music_handler.play(message, link)
    except Exception as e:
        print(e)
        await message.channel.send("⚠️ An error has occurred.")

@commands.command(name="pause", description="Pause Current Song")
async def pause(message):
    """Pause the currently playing song."""
    try:
        await message.response.send_message("Paused ⏸︎")
        await music_handler.pause(message)
    except Exception as e:
        print(e)
        await message.channel.send("⚠️ An error has occurred.")

@commands.command(name="stop", description="Stops the current queue and clears it")
async def stop(message):
    """Stop music playback and clear the entire queue."""
    try:
        await message.response.send_message("Clearing Queue...")
        await music_handler.clear_queue(message)
        await message.channel.send("Music Stopped and Queue Cleared")
    except Exception as e:
        print(e)
        await message.channel.send("⚠️ An error has occurred.")

@commands.command(name="queue", description="Lists all songs in queue")
async def queue(message):
    """Display all songs currently in the music queue."""
    try:
        await message.response.send_message("Fetching Queue...")
        await music_handler.show_queue(message)
    except Exception as e:
        print(e)
        await message.channel.send("⚠️ An error has occurred.")

# ============================================================================
# MINECRAFT SERVER COMMANDS
# ============================================================================

@commands.command(name="mcreboot", description="Reboots the server")
async def mcreboot(message):
    """Reboot the Minecraft server (stop then start)."""
    if message.guild.id in admin_server_ids:
        try:
            await mcstop(message)
            await mcstart(message)
        except Exception as e:
            print(e)
            await message.channel.send("⚠️ An error has occurred.")
    else:
        await message.response.send_message("Sorry, you don't have permission to use this command.")

@commands.command(name="mcstart", description="Starts the a MC Server")
@app_commands.describe(version="vanilla, atm10, dc (Deceased Craft), rf (Raspberry Flavored)")
async def mcstart(message, version: str = "vanilla"):
    """Start a Minecraft server. Versions: vanilla, atm10, dc, rf."""
    if message.guild.id in admin_server_ids:
        version = version.lower()
        try:

            await message.response.send_message("Server Booting Up...")
            if await mcserver_handler.run_server(version):
                await message.channel.send("-Server is Online-")
            else:
                await message.channel.send("Oops something went wrong. Check Server Status.")
        except Exception as e:
            print(e)
            await message.channel.send("⚠️ An error has occurred.")
    else:
        await message.response.send_message("Sorry, you don't have permission to use this command.")

@commands.command(name="mcstop", description="Stops the currently running MC Server")
async def mcstop(message):
    """Stop the currently running Minecraft server."""
    if message.guild.id in admin_server_ids:
        try:
            if not mcserver_handler.booting:
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
    else:
        await message.response.send_message("Sorry, you don't have permission to use this command.")

@commands.command(name="mcstatus", description="Gets the status of the MC:BE Server")
async def mcstatus(message):
    """Check if the Minecraft server is currently online or offline."""
    if message.guild.id in admin_server_ids:
        try:
            stat = mcserver_handler.status()
            if stat:
                await message.response.send_message("Server: Active")
            else:
                await message.response.send_message("Server: Offline")
        except Exception as e:
            print(e)
            await message.channel.send("⚠️ An error has occurred.")
    else:
        await message.response.send_message("Sorry, you don't have permission to use this command.")

@commands.command(name="mcip", description="Gets the IP, Port, and status of the server")
async def mcip(message: discord.Interaction):
    """Get the server IP and port (deletes message after 30 seconds for security)."""
    if message.guild.id in admin_server_ids:
        try:
            ipv4_address = os.getenv("IP")
            stat = "Online" if mcserver_handler.status() else "Offline"
            await message.response.send_message(
                f"⚠️REMEMBER THIS IS SECURITY SENSITIVE⚠️\n--DO NOT SHARE WITH ANYONE--\n"
                f"IP: ||{ipv4_address}|| \nJava Port: ||25565|| \nBE Port: ||19132||\nStatus: {stat}"
            )
            await asyncio.sleep(30)
            await message.delete_original_response()
        except Exception as e:
            print(e)
            await message.channel.send("⚠️ An error has occurred.")
    else:
        await message.response.send_message("Sorry, you don't have permission to use this command.")

# ============================================================================
# STOCK COMMANDS
# ============================================================================

@commands.command(name="apistatus", description="Check current API usage")
async def apistatus(message: discord.Interaction):
    """Display current Finnhub API usage statistics."""
    try:
        usage = stock_handler.get_api_usage()
        
        embed = discord.Embed(
            title="📊 Finnhub API Status",
            color=discord.Color.blue()
        )
        
        # Calculate percentage used
        percentage_used = (usage['calls_this_minute'] / usage['limit']) * 100
        
        # Create a visual progress bar
        filled = int(percentage_used / 5)  # 20 bars max
        bar = "█" * filled + "░" * (20 - filled)
        
        embed.add_field(
            name="Calls This Minute",
            value=f"`{bar}` {usage['calls_this_minute']}/{usage['limit']} ({percentage_used:.1f}%)",
            inline=False
        )
        embed.add_field(
            name="Remaining Calls",
            value=f"{usage['remaining']} calls available",
            inline=False
        )
        embed.add_field(
            name="Total Calls (Session)",
            value=f"{usage['total_calls']} total API calls made",
            inline=False
        )
        
        # Add status indicator
        if usage['calls_this_minute'] >= 50:
            status = "🔴 High usage - approaching limit"
        elif usage['calls_this_minute'] >= 30:
            status = "🟡 Moderate usage"
        else:
            status = "🟢 Low usage"
        
        embed.add_field(name="Status", value=status, inline=False)
        embed.set_footer(text="Rate limit resets every 60 seconds")
        
        await message.response.send_message(embed=embed)
        
    except Exception as e:
        print(f"API status command error: {e}")
        await message.response.send_message("⚠️ An error has occurred.")

@commands.command(name="stock", description="Get stock information by ticker")
@app_commands.describe(ticker="Stock ticker symbol (e.g., AAPL, MSFT)")
async def stock(message: discord.Interaction, ticker: str):
    """Fetch real-time stock information from Finnhub API."""
    try:
        await message.response.defer()
        stock_info = stock_handler.get_stock(ticker.upper())
        
        if not stock_info:
            await message.followup.send(f"❌ Unable to find stock data for **{ticker.upper()}**. Please check the ticker symbol.")
            return
        
        # Format the change color based on positive/negative
        change = stock_info.get("change", 0)
        change_percent = stock_info.get("change_percent", 0)
        change_emoji = "📈" if change >= 0 else "📉"
        
        embed = discord.Embed(
            title=f"{stock_info.get('name', 'N/A')} ({stock_info.get('ticker')})",
            description=stock_info.get("description", "N/A"),
            color=discord.Color.green() if change >= 0 else discord.Color.red()
        )
        
        embed.add_field(name="💰 Price", value=f"${stock_info.get('price', 'N/A')}", inline=True)
        embed.add_field(name=f"{change_emoji} Change", value=f"${change} ({change_percent}%)", inline=True)
        embed.add_field(name="📊 Sector", value=stock_info.get('sector', 'N/A'), inline=True)
        embed.add_field(name="🏢 Market Cap", value=f"${stock_info.get('market_cap', 'N/A')}", inline=True)
        embed.add_field(name="📈 P/E Ratio", value=str(stock_info.get('pe_ratio', 'N/A')), inline=True)
        embed.add_field(name="📅 Previous Close", value=f"${stock_info.get('previous_close', 'N/A')}", inline=True)
        embed.add_field(name="⬆️ High", value=f"${stock_info.get('high', 'N/A')}", inline=True)
        embed.add_field(name="⬇️ Low", value=f"${stock_info.get('low', 'N/A')}", inline=True)
        embed.add_field(name="💾 Volume", value=str(stock_info.get('volume', 'N/A')), inline=True)
        
        if stock_info.get('website'):
            embed.add_field(name="🔗 Website", value=f"[Link]({stock_info.get('website')})", inline=False)
        
        # Add warning message about data accuracy
        embed.add_field(name="⚠️ Data Accuracy", value="Stock data may be delayed by up to 15 minutes. Always verify with official sources before making investment decisions.", inline=False)
        
        # Add API usage counter
        usage = stock_handler.get_api_usage()
        embed.set_footer(text=f"API Calls: {usage['calls_this_minute']}/{usage['limit']} this minute | Total: {usage['total_calls']}")
        
        await message.followup.send(embed=embed)
        
    except Exception as e:
        print(f"Stock command error: {e}")
        await message.followup.send(f"⚠️ {str(e)}")

@commands.command(name="stocksearch", description="Search for stocks by company name")
@app_commands.describe(query="Company name or partial ticker to search for")
async def stocksearch(message: discord.Interaction, query: str):
    """Search for stocks by company name or ticker."""
    try:
        await message.response.defer()
        results = stock_handler.search_stocks(query)
        
        if not results:
            await message.followup.send(f"❌ No results found for **{query}**.")
            return
        
        embed = discord.Embed(
            title=f"Stock Search Results for '{query}'",
            color=discord.Color.blue(),
            description="Click on a ticker to get more information"
        )
        
        # Limit to 25 results (Discord embed field limit)
        for stock in results[:25]:
            ticker = stock.get('symbol', 'N/A')
            name = stock.get('description', 'N/A')
            embed.add_field(name=f"📌 {ticker}", value=name, inline=False)
        
        # Add API usage counter
        usage = stock_handler.get_api_usage()
        embed.set_footer(text=f"Showing {min(len(results), 25)} of {len(results)} results | API Calls: {usage['calls_this_minute']}/{usage['limit']} this minute | Total: {usage['total_calls']}")
        await message.followup.send(embed=embed)
        
    except Exception as e:
        print(f"Stock search error: {e}")
        await message.followup.send(f"⚠️ {str(e)}")

# ============================================================================
# UTILITY COMMANDS
# ============================================================================

@commands.command(name="help", description="List all commands")
async def help(message):
    """Display all available bot commands and their descriptions."""
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
========================
***Stock Market Data***
stock - Get current stock price and information by ticker symbol
stocksearch - Search for stocks by company name
apistatus - Check current API usage and rate limit status
========================
***TCG (Trading Card Games)***
mtg - Search for Magic: The Gathering card information
""")
    except Exception as e:
        print(f"Help command error: {e}")
        await message.channel.send("⚠️ An error has occurred.")

client.run(TOKEN)
