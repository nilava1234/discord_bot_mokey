import configparser
import discord
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import yt_dlp as youtube_dl
import asyncio

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
        'preferredcodec': 'mp3',
        'preferredquality': '320',  # Adjust the preferred quality as needed
    }],
}

#play's the next link in queue
async def play_next(message: discord.Interaction):
    global queue
    if queue:
        url, title = queue.pop(0)
        await message.channel.send(f"Now Playing: {title}")
        vc = discord.utils.get(message.client.voice_clients, guild=message.guild)
        def after_play(error):
            # This function will be called after the audio has finished playing
            if error:
                print(f"Error in after_play: {error}")
            # Call play_next again for the next song
            message.client.loop.create_task(play_next(message))

        # Stop and play the next song
        vc.stop()
        vc.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS), after=after_play)
    else:
        await message.channel.send(f"Queue Empty")

#pauses the bot
async def pause(message):
    voice_channel = discord.utils.get(message.bot.voice_clients, guild=message.guild)
    if voice_channel.is_playing():
        voice_channel.pause()

#resumes the bot
async def resume(message):
    voice_channel = discord.utils.get(message.bot.voice_clients, guild=message.guild)
    if voice_channel.is_paused():
        voice_channel.resume()

#shows the play list queue
async def show_queue(message):
    global queue
    response = ""
    if queue:
        
        for i, (url, title) in enumerate(queue, start=1):
            response += f"{i}) {title}\n"
        await message.channel.send(response)
    else:
        await message.channel.send("Queue is empty.")

#stops the bot and clears the queue
async def clear_queue(message, bot):
    global queue
    queue = []
    voice_channel = discord.utils.get(bot.voice_clients, guild=message.guild)
    voice_channel.stop()

def extract_track_id(link):
    parts = link.split('/')
    if len(parts) >= 5 and parts[3] == 'track':
        return parts[4].split('?')[0]
    else:
        return None


async def handle_single_song_via_query(message:discord.interactions, query:str):
    global queue
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            search_result = ydl.extract_info(f"ytsearchmusic:{query}", download=False)
            if not search_result or "entries" not in search_result or not search_result["entries"]:
                await message.channel.send("No results found for the query.")
                return
            
            video_info = search_result["entries"][0]
            title = video_info.get("title", "Unknown Title")
            video_url = video_info.get("url", None)

            if not video_url:
                await message.channel.send("Failed to retrieve a valid URL for the song.")
                return
            queue.append((video_url, title))
            await message.channel.send(f"🎵 Queued: {title}")
    except Exception as e:
        await message.channel.send("An error occurred while searching for the song.")
        print(f"yt-dlp Error: {e}")


async def handle_single_song(message, link):
    global queue

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            video_info = ydl.extract_info(link, download=False)

            # Ensure the result is valid
            if not video_info or "url" not in video_info:
                await message.channel.send("Failed to retrieve a valid URL for the song.")
                return

            title = video_info.get("title", "Unknown Title")
            video_url = video_info["url"]

            # Add song to queue
            queue.append((video_url, title))
            await message.channel.send(f"🎵 Queued: {title}")

    except Exception as e:
        await message.channel.send("An error occurred while processing the song.")
        print(f"yt-dlp Error: {e}")

#METHOD SPOTIFY_SONG    ======Helpers======         ===============================================
async def handle_spotify_song(message, link):
    try:
        track_id = link.split("/track/")[1].split("?")[0]
    except IndexError:
        await message.channel.send("Invalid Spotify track link.")
        return
    track_name = track_info["name"]
    artists = ", ".join([artist["name"] for artist in track_info["artists"]])
    search_query = f"{track_name} {artists} Audio"
    try:
        track_info = sp.track(track_id)
    except Exception as e:
        await message.channel.send("Error fetching track details from Spotify.")
        print(f"Spotify API Error: {e}")
        return
    title = f"{track_name} by {artists}"
    
    await message.channel.send(f"🎶 Queued: {title}")
    await handle_single_song_via_query(message, search_query)

#METHOD SPOTIFY_PLAYLIST    ======Helpers======         ===============================================
async def handle_spotify_playlist(message:discord.interactions, link:str):
    playlist_id = link.split("/playlist/")[1].split("?")[0]
    playlist_tracks = sp.playlist_tracks(playlist_id)

    for item in playlist_tracks['items']:
        track = item['track']
        search_query = f"{track['name']} {', '.join([artist['name'] for artist in track['artists']])} Audio"
        title = f"{track['name']} by {', '.join([artist['name'] for artist in track['artists']])}"

        await message.channel.send(f"Queued: {title}")
        await handle_single_song_via_query(message, search_query)

#METHOD YOUTUBE_PLAYLIST    ======Helpers======         ===============================================   
async def handle_youtube_playlist(message, playlist_link):
    
    global queue

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_link, download=False)

            if not playlist_info or "entries" not in playlist_info or not playlist_info["entries"]:
                await message.channel.send("No videos found in this playlist.")
                return

            for video in playlist_info["entries"]:
                if not video or "url" not in video:
                    continue 

                title = video.get("title", "Unknown Title")
                video_url = video["url"]

                queue.append((video_url, title))

            await message.channel.send(f"📃 Queued {len(playlist_info['entries'])} songs from the playlist!")

    except Exception as e:
        await message.channel.send("An error occurred while processing the YouTube playlist.")
        print(f"yt-dlp Error: {e}")

#METHOD PLAY    ======Helpers======     (check_idle)    ===============================================
async def check_idle(voice_client):
    while voice_client.is_connected():
        await asyncio.sleep(5)
        if not voice_client.is_playing() and not voice_client.is_paused():
            await voice_client.disconnect()
            break

async def play(message:discord.Interaction, link:str):
    #Global Declaration
    #Queue: Required due to song queue
    global queue
    if not message.user.voice:
        await message.channel.send("I dont see you in a voice channel, join one to play music")
        return

    #checking if user is in a VC
    voice_client = discord.utils.get(message.client.voice_clients, guild = message.guild)
    if voice_client is None:
        voice_client = await message.user.voice.channel.connect()

    #idle check
    asyncio.create_task(check_idle(voice_client))
    if "spotify" in link:
        if "playlist" in link:
            await handle_spotify_playlist(message, link)
        else:
            await handle_spotify_song(message, link)
    elif "youtu" in link:
        if "playlist" in link:
            await message.channel.send("Cant handle Youtube Playlists as of this moment. Try inividual songs")
        else:
            await handle_single_song(message, link)
    else:
        await handle_single_song_via_query(message, f"{link} Audio")
    #next song
    if not voice_client.is_playing():
        await play_next(message)