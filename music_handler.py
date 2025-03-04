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

#Global Variables
name_queue = []
queue = []
# ✅ FFmpeg Settings for Stable Playback
FFMPEG_OPTIONS = {
    'before_options': (
        '-reconnect 1 '  # Enables reconnection in case of network issues
        '-reconnect_streamed 1 '  # Ensures streamed media reconnects if interrupted
        '-reconnect_delay_max 5 '  # Sets max delay for reconnect attempts to 5 seconds
        '-nostdin '  # Prevents FFmpeg from waiting for user input, avoiding crashes
        '-loglevel panic '  # Hides unnecessary FFmpeg logs to prevent console spam
    ),
    'options': '-vn'  # Disables video processing, ensuring only audio is used
}

# ✅ yt-dlp Settings for Extracting High-Quality YouTube Music Audio
ydl_opts = {
    'silent': True,  # Prevents yt-dlp from printing output to console
    'format': 'bestaudio/best',  # Ensures the highest quality audio is used
    'default_search': 'ytsearch',  # Uses YouTube search if a direct link is not provided
    'source_address': '0.0.0.0',  # Avoids IP bans by binding to all available network interfaces
    'quiet': False,  # Prevents excessive logging from yt-dlp
    'extractor_args': {'youtube': {'music': True}},  # Ensures YouTube Music is prioritized
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',  # Uses FFmpeg to process extracted audio
        'preferredcodec': 'mp3',  # Converts audio to MP3 format
        'preferredquality': '320',  # Ensures maximum audio quality at 320kbps
    }],
    'geo_bypass': True,  # Allows access to region-locked content
    'ignoreerrors': True,  # Prevents yt-dlp from stopping on minor errors
    'nocheckcertificate': True,  # Bypasses SSL certificate verification to avoid connection issues
    'skip_download': True,  # Ensures yt-dlp only fetches URLs, without downloading files
}


def run_yt_dlp_search(query):
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)

#METHOD PLAY_NEXT    ======Helpers======         ===============================================
async def handle_single_song(message, query):
    global queue
    global ydl_opts

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            # Use YouTube search instead of direct link
            video_info = await asyncio.to_thread(run_yt_dlp_search, query)

            # Ensure a valid result exists
            if not video_info or "entries" not in video_info or not video_info["entries"]:
                await message.channel.send("❌ No results found for the search query.")
                return None

            # Extract the first result
            best_match = video_info["entries"][0]
            title = best_match.get("title", "Unknown Title")
            url = best_match.get("url")  # Get direct streaming URL
            author = best_match.get("uploader", "Unknown Artist")

            # Return the streaming URL
            return url

    except Exception as e:
        await message.channel.send("⚠️ An error occurred while searching for the song.")
        print(f"yt-dlp Error: {e}")
        return None

async def play_next(message: discord.Interaction, skip=False):
    """Plays the next song in the queue or disconnects if empty."""
    global queue

    voice_client = discord.utils.get(message.client.voice_clients, guild=message.guild)

    if not queue:
        await message.channel.send("🎵 The queue is empty.")
        await voice_client.disconnect()  # ✅ Ensures bot disconnects when queue is empty
        return

    # Get the next song in the queue
    value, title, is_url = queue.pop(0)
    await message.channel.send(f"▶️ Now Playing: **{title}**")

    # ✅ Stop the current track before playing the new one
    if voice_client.is_playing():
        voice_client.stop()

    # ✅ Convert query-based searches to a playable URL
    if not is_url:
        value = await handle_single_song(message, value)

    def after_play(error):
        if error:
            print(f"Error in after_play: {error}")

        if not voice_client.is_playing():
            message.client.loop.create_task(play_next(message))

    # ✅ Play the next song with FFmpeg
    voice_client.play(discord.FFmpegPCMAudio(value, **FFMPEG_OPTIONS), after=after_play)

    
        


#METHOD PAUSE    ======Helpers======         ===============================================
async def pause(message: discord.Interaction):
    """Pauses the currently playing track if music is playing."""
    
    voice_client = discord.utils.get(message.client.voice_clients, guild=message.guild)

    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await message.channel.send("⏸️ Music paused.")
    else:
        await message.channel.send("❌ No music is currently playing.")


#METHOD RESUME    ======Helpers======         ===============================================
async def resume(message: discord.Interaction):
    """Resumes playback if the music is paused."""
    
    voice_client = discord.utils.get(message.client.voice_clients, guild=message.guild)

    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await message.channel.send("▶️ Music resumed.")
    else:
        await message.channel.send("❌ No paused music to resume.")


#METHOD SHOW_QUEUE    ======Helpers======         ===============================================
async def show_queue(message: discord.Interaction):
    """Displays the current music queue."""
    global queue
    if not queue:
        await message.channel.send("🎵 The queue is currently empty.")
        return

    response = "**🎶 Current Queue:**\n"
    for i, (url, title, value) in enumerate(queue, start=1):
        response += f"`{i}.` {title}\n"

    await message.channel.send(response)


#METHOD CLEAR_QUEUE    ======Helpers======         ===============================================
async def clear_queue(message: discord.Interaction):
    """Clears the song queue and stops playback if the bot is in a voice channel."""
    
    global queue
    queue = []

    # Get the bot's voice client
    voice_client = discord.utils.get(message.client.voice_clients, guild=message.guild)

    if voice_client and voice_client.is_playing():
        voice_client.stop()
        voice_client.disconnect()
        await message.channel.send("🛑 Music stopped. The queue has been cleared.")
    else:
        voice_client.stop()
        voice_client.disconnect()
        await message.channel.send("❌ The bot is not playing anything.")


#METHOD handle_song_search    ======Helpers======         ===============================================   
async def handle_song_search(message: discord.Interaction, query: str):
    """Searches for a song on Spotify and returns a properly formatted query for YouTube search."""
    
    global queue
    result = sp.search(q=query, type="track", limit=1)

    if not result or not result["tracks"]["items"]:
        await message.channel.send("❌ No results found for the search query.")
        return None

    track_info = result["tracks"]["items"][0]
    track_name = track_info["name"]
    track_artist = ", ".join(artist["name"] for artist in track_info["artists"])  
    search_query = f"{track_name} {track_artist} Audio"

    return search_query, f"{track_name} by {track_artist}", False  # ✅ Fix: Properly return search results


#METHOD SPOTIFY_SONG    ======Helpers======         ===============================================
async def handle_spotify_song(message, link):
    try:
        track_id = link.split("/track/")[1].split("?")[0]
        track_info = sp.track(track_id)
    except (IndexError, Exception) as e:
        await message.channel.send("❌ Invalid Spotify track link or failed to fetch details.")
        print(f"Spotify API Error: {e}")
        return

    track_name = track_info["name"]
    artists = ", ".join([artist["name"] for artist in track_info["artists"]])
    search_query = f"{track_name} {artists} Audio"
    title = f"{track_name} by {artists}"

    queue.append((search_query, title, False))
    await message.channel.send(f"🎵 Queued: **{title}**")


#METHOD SPOTIFY_PLAYLIST    ======Helpers======         ===============================================
async def handle_spotify_playlist(message: discord.Interaction, link: str):  
    global queue

    voice_client = discord.utils.get(message.client.voice_clients, guild=message.guild)
    if not voice_client:
        if not message.user.voice or not message.user.voice.channel:
            await message.channel.send("You must be in a voice channel to play music.")
            return
        voice_client = await message.user.voice.channel.connect()

    try:
        playlist_id = link.split("/playlist/")[1].split("?")[0]
        playlist_tracks = sp.playlist_tracks(playlist_id)
    except Exception as e:
        await message.channel.send("Failed to fetch playlist from Spotify.")
        print(f"Spotify API Error: {e}")
        return

    queued_songs = 0

    for item in playlist_tracks['items']:
        track = item['track']
        if not track:
            continue

        search_query = f"{track['name']} {', '.join([artist['name'] for artist in track['artists']])} Audio"
        title = f"{track['name']} by {', '.join([artist['name'] for artist in track['artists']])}"
        queued_songs+=1

        queue.append((search_query, title, False))
    await message.channel.send(f"📃 Queued {queued_songs} songs from the playlist!")

#METHOD YOUTUBE_PLAYLIST    ======Helpers======         ===============================================   
async def handle_youtube_playlist(message: discord.Interaction, playlist_link: str):
    global queue
    global ydl_opts
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        playlist_info = await asyncio.to_thread(run_yt_dlp_search, playlist_link)

        for video in playlist_info['entries']:
            title = video["title"]
            url = video['url']
            author = video['uploader']

            if url:
                queue.append((url,  f"{title} by {author}", True))
            else: 
                print(url)
        await message.channel.send(f"📃 Queued {len(playlist_info['entries'])} songs from the playlist!")



#METHOD YOUTUBE_SONG    ======Helpers======         ===============================================   
async def handle_youtube_song(message: discord.Interaction, song_link: str):
    global queue
    global ydl_opts
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            video_info = await asyncio.to_thread(run_yt_dlp_search, song_link)
            title = video_info['title']
            url = video_info['url']
            author = video_info['uploader']

            if url:
                queue.append((url,  f"{title} by {author}", True))
                await message.channel.send(f"🎵 Queued: **{title} by {author}**")
            else: 
                await message.channel.send("⚠️Failed to retrieve a valid URL for the song.")
    except Exception as e:
        print(e)


#METHOD PLAY    ======Helpers======     (check_idle)    ===============================================

async def play(message: discord.Interaction, link: str):
    """Handles playing songs from links or text queries, ensuring proper queue management."""
    global queue

    if not message.user.voice or not message.user.voice.channel:
        await message.channel.send("❌ You must be in a voice channel to play music.")
        return

    voice_client = discord.utils.get(message.client.voice_clients, guild=message.guild)
    if not voice_client:
        voice_client = await message.user.voice.channel.connect()

    # Determine if the input is a Spotify/Youtube link or a query
    if "spotify" in link:
        if "playlist" in link:
            await handle_spotify_playlist(message, link)
        else:
            await handle_spotify_song(message, link)

    elif "youtu" in link:
        if "playlist" in link:
            await handle_youtube_playlist(message, link)
        else:
            await handle_youtube_song(message, link)

    else:
        # Handle text-based search queries
        search_result = await handle_song_search(message, link)
        if search_result:
            video_url, title, is_url = search_result
            queue.append((video_url, title, is_url))
            await message.channel.send(f"🎵 Queued: **{title}**")

    # ✅ Only start playing if nothing is currently playing
    if not voice_client.is_playing():
        await play_next(message)