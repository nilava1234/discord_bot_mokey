import configparser
import discord
import json
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import yt_dlp as youtube_dl

config = configparser.ConfigParser()
config.read('config.ini')
SP_CLIENT_ID = config['Spotify']['CLIENT_ID']
SP_CLIENT_SC = config['Spotify']['CLIENT_SECRET']

queue = []
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'm3',
        'preferredquality': '192',
    }],
}
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SP_CLIENT_ID, client_secret=SP_CLIENT_SC))

async def play_spotify(message,link):
    global queue
    try:
        if "playlist" in link:
            results = sp.search(q=link, type='playlist')
            # return results["tracks"]["items"]["external_urls"]
            # return [item['external_urls']['spotify'] for item in results['tracks']['items']]
        else:
            results = sp.search(q=link, type='track')
            print("Spotify Results")
            print(results)
            # return [] + results['tracks']['items'][0]['external_urls']['spotify']
    except Exception as e:
        print("Failed in play_spotify")
        print(e)

async def play_next(ctx: discord.Interaction):

    if queue:
        url, title = queue.pop(0)
        await ctx.channel.send(f"Now Playing: {title}")
        vc = discord.utils.get(ctx.client.voice_clients, guild=ctx.guild)
        vc.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS), after=lambda e: play_next(ctx))
    else:
        await ctx.channel.send(f"Queue Empty")

async def play(message:discord.Interaction,link:str, bot):
    global queue
    channel = message.user.voice.channel
    voice_client = discord.utils.get(message.client.voice_clients, guild=message.guild)
    voice_channel = voice_client if voice_client is not None else await channel.connect()
    if "spotify" in link:
        # link = await play_spotify(message, link)
        # with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        #         info = ydl.extract_info(link, download=False)
        #         print(info)
        await message.response.send_message("Sorry Spotify integration is in Progress")
    elif "youtu" and not "playlist" in link:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            title = info["title"]
            await message.response.send_message(f"Queued: {title}")
            url = (info["url"], title)
            queue.append(url)
    else:
        await message.response.send_message("You have provided an invalid link")
    
    if not voice_channel.is_playing():
        await play_next(message)

    
async def pause(ctx, bot):
    voice_channel = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_channel.is_playing():
        voice_channel.pause()
    

async def resume(ctx, bot):
    voice_channel = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_channel.is_paused():
        voice_channel.resume()

async def show_queue(ctx):
    global queue
    response = "Queue:\n"
    if queue:
        
        for i, (url, title) in enumerate(queue, start=1):
            response += f"{i}) {title}\n"
        await ctx.response.send_message(response)
    else:
        await ctx.response.send_message("Queue is empty.")

async def clear_queue(ctx, bot):
    global queue
    queue = []
    voice_channel = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    voice_channel.stop()