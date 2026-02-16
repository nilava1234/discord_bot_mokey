from dotenv import load_dotenv
import os
import discord
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import asyncio
import yt_dlp as youtube_dl;
import random


#Initilizng and grabing important variables
load_dotenv()
SP_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SP_CLIENT_SC = os.getenv("SPOTIFY_CLIENT_SECRET")
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SP_CLIENT_ID, client_secret=SP_CLIENT_SC))

#Global Variables
embed_ctx = {}
queue = {}
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
# yt-dlp options for optimal audio extraction and search functionality
ydl_opts = {
    'format': 'bestaudio/best',  # Ensures the highest quality audio is used
    'default_search': 'ytsearch',  # Uses YouTube search if a direct link is not provided
    'source_address': '0.0.0.0',  # Avoids IP bans by binding to all available network interfaces
    'quiet': True,  # Prevents excessive logging from yt-dlp
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

async def shuffle_queue(message: discord.Interaction):
    """Shuffles the current music queue for the guild."""
    global queue
    if message.guild.id not in queue or not queue[message.guild.id]:
        await message.channel.send("🎵 The queue is currently empty. Nothing to shuffle.")
        return

    random.shuffle(queue[message.guild.id])
    await message.channel.send("🔀 Queue shuffled.")
    
async def get_voice_client(interaction: discord.Interaction):
    """Safely gets or connects the bot to the user's voice channel."""
    
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.channel.send("❌ You must be in a voice channel.")
        return None

    voice_client = discord.utils.get(interaction.client.voice_clients, guild=interaction.guild)

    # Already connected
    if voice_client and voice_client.is_connected():
        # Move if in different channel
        if voice_client.channel != interaction.user.voice.channel:
            await voice_client.move_to(interaction.user.voice.channel)
        return voice_client

    # Not connected — connect safely
    try:
        voice_client = await interaction.user.voice.channel.connect(reconnect=True)
        return voice_client
    except Exception as e:
        print(f"Voice connection error: {e}")
        await interaction.channel.send("❌ Failed to connect to voice channel.")
        return None


#Helper: Query search function for yt-dlp
def run_yt_dlp_search(query):
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)


#Handler: Processes a search query and returns the direct streaming URL of the best match
async def handle_single_song(message, query):
    global queue
    global ydl_opts
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            # Use YouTube search instead of direct link
            video_info = run_yt_dlp_search(query)

            # Ensure a valid result exists
            if not video_info or "entries" not in video_info or not video_info["entries"]:
                await message.channel.send("❌ No results found for the search query.")
                return None

            # Extract the first result
            best_match = video_info["entries"][0]
            url = best_match.get("url")  # Get direct streaming URL
            thumbnail = best_match.get("thumbnail")  # Get thumbnail URL for potential embed use

            # Return the streaming URL
            return url, thumbnail
        
    except Exception as e:
        await message.channel.send("⚠️ An error occurred while searching for the song.")
        print(f"yt-dlp Error: {e}")
        return None

#METHOD PLAY_NEXT    ======Helpers======         ==============================================
async def play_next(message: discord.Interaction):
    global queue
    global embed_ctx
    embed, ctx = embed_ctx[message.guild.id]

    voice_client = discord.utils.get(message.client.voice_clients, guild=message.guild)

    if not voice_client or not voice_client.is_connected():
        return

    if not queue[message.guild.id]:
        await message.channel.send("🎵 The queue is empty.")
        await ctx.edit_original_response(embed=None)
        await voice_client.disconnect()
        return

    item = queue[message.guild.id].pop(0)

    if len(item) == 4:
        value, title, is_url, thumbnail = item
    else:
        value, title, is_url = item
        thumbnail = None


    if not is_url:
        value, thumbnail = await handle_single_song(message, value)

    if not value:
        await play_next(message)
        return

    embed.set_field_at(0, name="Song", value=title, inline=False)
    embed.set_image(url=thumbnail)
    await ctx.edit_original_response(embed=embed)

    def after_play(error):
        if error:
            print(f"Playback error: {error}")
        fut = asyncio.run_coroutine_threadsafe(
            play_next(message),
            message.client.loop
        )
        try:
            fut.result()
        except:
            pass

    source = discord.FFmpegPCMAudio(value, **FFMPEG_OPTIONS)
    voice_client.play(source, after=after_play)


    
        


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
    if not queue[message.guild.id]:
        await message.channel.send("🎵 The queue is currently empty.")
        return

    response = "**🎶 Current Queue:**\n"
    for i, (url, title, value) in enumerate(queue[message.guild.id], start=1):
        response += f"`{i}.` {title}\n"

    await message.channel.send(response)


#METHOD CLEAR_QUEUE    ======Helpers======         ===============================================
async def clear_queue(message: discord.Interaction):
    global queue
    queue[message.guild.id] = []
    embed_ctx[message.guild.id] = None

    voice_client = discord.utils.get(message.client.voice_clients, guild=message.guild)

    if voice_client and voice_client.is_connected():
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
        await voice_client.disconnect()
        await message.channel.send("🛑 Music stopped. Queue cleared.")
    else:
        await message.channel.send("❌ The bot is not in a voice channel.")



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

    return search_query, f"{track_name} - {track_artist}", False  # ✅ Fix: Properly return search results


#METHOD SPOTIFY_SONG    ======Helpers======         ===============================================
async def handle_spotify_song(message, link):
    global queue
    global embed_ctx
    embed, ctx = embed_ctx[message.guild.id]
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
    title = f"{track_name} - {artists}"

    queue[message.guild.id].append((search_query, title, False))
    embed.set_field_at(1, name="Queued: ", value=f"✅ {title}", inline=True)
    await ctx.edit_original_response(embed=embed)


#METHOD SPOTIFY_PLAYLIST    ======Helpers======         ===============================================
async def handle_spotify_playlist(message: discord.Interaction, link: str):  
    global queue
    global embed_ctx
    embed, ctx = embed_ctx[message.guild.id]
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
        title = f"{track['name']} - {', '.join([artist['name'] for artist in track['artists']])}"
        queued_songs+=1

        queue[message.guild.id].append((search_query, title, False))
    embed.set_field_at(1, name="Queued: ", value=f"📃 Queued {queued_songs} songs", inline=True)
    await ctx.edit_original_response(embed=embed)

#METHOD YOUTUBE_PLAYLIST    ======Helpers======         ===============================================   
async def handle_youtube_playlist(message: discord.Interaction, playlist_link: str):
    global queue
    global ydl_opts
    global embed_ctx
    embed, ctx = embed_ctx[message.guild.id]
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        playlist_info = await asyncio.to_thread(run_yt_dlp_search, playlist_link)

        for video in playlist_info['entries']:
            title = video["title"]
            url = video['url']
            author = video['uploader']
            thumbnail = video['thumbnail']

            if url:
                queue[message.guild.id].append((url,  f"{title} - {author}", True, thumbnail))

        embed.set_field_at(1, name="Queued: ", value=f"📃 Queued {len(playlist_info['entries'])} songs", inline=True)
        await ctx.edit_original_response(embed=embed)



#METHOD YOUTUBE_SONG    ======Helpers======         ===============================================   
async def handle_youtube_song(message: discord.Interaction, song_link: str):
    global queue
    global ydl_opts
    global embed_ctx
    embed, ctx = embed_ctx[message.guild.id]
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            video_info = await asyncio.to_thread(run_yt_dlp_search, song_link)
            title = video_info['title']
            url = video_info['url']
            author = video_info['uploader']
            thumbnail = video_info['thumbnail']

            if url:
                queue[message.guild.id].append((url,  f"{title} - {author}", True, thumbnail))
                embed.set_field_at(1, name="Queued: ", value=f"✅ {title} - {author}", inline=True)
                await ctx.edit_original_response(embed=embed)
            else: 
                await message.channel.send("⚠️Failed to retrieve a valid URL for the song.")
    except Exception as e:
        print(e)


#METHOD PLAY    ======Helpers======     (check_idle)    ===============================================
async def play(message: discord.Interaction, link: str):
    global queue
    if message.guild.id not in queue:
        queue[message.guild.id] = []
    
    if embed_ctx.get(message.guild.id, None) is None:
        embed = discord.Embed(title="🎵 Mokey Music 🎵", color=discord.Color.blue())
        embed.add_field(name="Song", value="None", inline=False)
        embed.add_field(name="Queued: ", value="None", inline=True)
        embed_ctx[message.guild.id] = embed, message
        await message.edit_original_response(content="", embed=embed)
    else:
        embed, ctx = embed_ctx[message.guild.id]
        embed_ctx[message.guild.id] = embed, message
        await message.edit_original_response(content="", embed=embed)

    voice_client = await get_voice_client(message)
    if not voice_client:
        return

    # Determine source type
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
        search_result = await handle_song_search(message, link)
        if search_result:
            video_url, title, is_url = search_result
            queue[message.guild.id].append((video_url, title, is_url))
            embed, ctx = embed_ctx[message.guild.id]
            embed.set_field_at(1, name="Queued: ", value=f"✅ {title}", inline=True)
            await ctx.edit_original_response(embed=embed)
            

    # Only start playing if not already playing
    if not voice_client.is_playing() and not voice_client.is_paused():
        await play_next(message)

