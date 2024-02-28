import configparser
import discord
import json
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import yt_dlp as youtube_dl

#Initilizng and grabing important variables
config = configparser.ConfigParser()
config.read('config.ini')
SP_CLIENT_ID = config['Spotify']['CLIENT_ID']
SP_CLIENT_SC = config['Spotify']['CLIENT_SECRET']
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SP_CLIENT_ID, client_secret=SP_CLIENT_SC))

#Intilizing dynamic variables and settings
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

#play's the next link in queue
async def play_next(ctx: discord.Interaction):

    if queue:
        url, title = queue.pop(0)
        await ctx.channel.send(f"Now Playing: {title}")
        vc = discord.utils.get(ctx.client.voice_clients, guild=ctx.guild)
        vc.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS), after=lambda e: play_next(ctx))
    else:
        await ctx.channel.send(f"Queue Empty")

#pauses the bot
async def pause(ctx):
    voice_channel = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    if voice_channel.is_playing():
        voice_channel.pause()

#resumes the bot
async def resume(ctx):
    voice_channel = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    if voice_channel.is_paused():
        voice_channel.resume()

#shows the play list queue
async def show_queue(ctx):
    global queue
    response = "Queue:\n"
    if queue:
        
        for i, (url, title) in enumerate(queue, start=1):
            response += f"{i}) {title}\n"
        await ctx.response.send_message(response)
    else:
        await ctx.response.send_message("Queue is empty.")

#stops the bot and clears the queue
async def clear_queue(ctx, bot):
    global queue
    queue = []
    voice_channel = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    voice_channel.stop()

def extract_track_id(link):
    parts = link.split('/')
    if len(parts) >= 5 and parts[3] == 'track':
        return parts[4].split('?')[0]
    else:
        return None
async def handle_sp_song(message, link):
    trackID = extract_track_id(link)
    
    track_info  = sp.track(trackID)
    search_query = f"{track_info['name']} {', '.join([artist['name'] for artist in track_info['artists']])} Original Audio"
    await handle_single_song_via_query(message, search_query)

async def handle_single_song_via_query(message, q):
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{q}", download=False)
            link = info["entries"][0].get("url", None)
            url = (link, q)
            queue.append(url)


async def handle_single_song(message, link):
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            title = info["title"]
            await message.response.send_message(f"Queued: {title}")
            url = (info["url"], title)
            queue.append(url)

async def play(message:discord.Interaction,link:str, bot):
    global queue
    try:
        channel = message.user.voice.channel
        voice_client = discord.utils.get(message.client.voice_clients, guild=message.guild)
        voice_channel = voice_client if voice_client is not None else await channel.connect()
        if "spotify" in link:
            if "playlist" in link:
                await message.response.send_message("Cant Handle Spotify Playlists as of this moment. Try Youtube link")
            else:
                await handle_sp_song(message, link)
        elif "youtu" in link:
            if "playlist" in link:
                await message.response.send_message("Cant handle Youtube Playlists as of this moment. Try inividual songs")
            else:
                await handle_single_song(message, link)
        else:
            await message.response.send_message("You have provided an invalid link")
        
        if not voice_channel.is_playing():
            await play_next(message)
    except Exception as e:
        if "NoneType" and "channel" in str(e):
            await message.response.send_message("Must be in a voice channel to play music")
        print(e)