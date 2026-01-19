import os
import sys
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, call
import discord

# Add parent directory to path to import music_handler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock Spotify and spotipy before importing music_handler
with patch('spotipy.Spotify'):
    with patch.dict(os.environ, {'SPOTIFY_CLIENT_ID': 'test_id', 'SPOTIFY_CLIENT_SECRET': 'test_secret'}):
        import music_handler


class TestQueueManagement:
    """Test cases for queue management functions"""
    
    @pytest.fixture(autouse=True)
    def reset_queue(self):
        """Reset queue before each test"""
        music_handler.queue = []
        yield
        music_handler.queue = []
    
    @pytest.mark.asyncio
    async def test_show_queue_empty(self):
        """Test showing queue when empty"""
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        
        await music_handler.show_queue(mock_message)
        
        mock_message.channel.send.assert_called_once()
        args = mock_message.channel.send.call_args[0][0]
        assert "empty" in args.lower()
    
    @pytest.mark.asyncio
    async def test_show_queue_with_songs(self):
        """Test showing queue with songs"""
        music_handler.queue = [
            ("url1", "Song 1", True),
            ("url2", "Song 2", False),
            ("url3", "Song 3", True),
        ]
        
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        
        await music_handler.show_queue(mock_message)
        
        mock_message.channel.send.assert_called_once()
        args = mock_message.channel.send.call_args[0][0]
        assert "Song 1" in args
        assert "Song 2" in args
        assert "Song 3" in args
        assert "1." in args
        assert "2." in args
        assert "3." in args
    
    @pytest.mark.asyncio
    async def test_clear_queue_with_playing_music(self):
        """Test clearing queue while music is playing"""
        music_handler.queue = [("url1", "Song 1", True)]
        
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        mock_message.guild = MagicMock()
        mock_message.client = MagicMock()
        
        mock_voice_client = MagicMock()
        mock_voice_client.is_playing.return_value = True
        
        with patch('discord.utils.get', return_value=mock_voice_client):
            await music_handler.clear_queue(mock_message)
        
        assert music_handler.queue == []
        mock_voice_client.stop.assert_called()
        mock_voice_client.disconnect.assert_called()
        mock_message.channel.send.assert_called()
    
    @pytest.mark.asyncio
    async def test_clear_queue_without_playing_music(self):
        """Test clearing queue when no music is playing"""
        music_handler.queue = [("url1", "Song 1", True)]
        
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        mock_message.guild = MagicMock()
        mock_message.client = MagicMock()
        
        mock_voice_client = MagicMock()
        mock_voice_client.is_playing.return_value = False
        
        with patch('discord.utils.get', return_value=mock_voice_client):
            await music_handler.clear_queue(mock_message)
        
        assert music_handler.queue == []
        mock_message.channel.send.assert_called()


class TestPauseResume:
    """Test cases for pause and resume functions"""
    
    @pytest.mark.asyncio
    async def test_pause_when_playing(self):
        """Test pausing when music is playing"""
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        mock_message.guild = MagicMock()
        mock_message.client = MagicMock()
        
        mock_voice_client = MagicMock()
        mock_voice_client.is_playing.return_value = True
        
        with patch('discord.utils.get', return_value=mock_voice_client):
            await music_handler.pause(mock_message)
        
        mock_voice_client.pause.assert_called_once()
        mock_message.channel.send.assert_called_once()
        args = mock_message.channel.send.call_args[0][0]
        assert "paused" in args.lower()
    
    @pytest.mark.asyncio
    async def test_pause_when_not_playing(self):
        """Test pausing when no music is playing"""
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        mock_message.guild = MagicMock()
        mock_message.client = MagicMock()
        
        mock_voice_client = MagicMock()
        mock_voice_client.is_playing.return_value = False
        
        with patch('discord.utils.get', return_value=mock_voice_client):
            await music_handler.pause(mock_message)
        
        mock_voice_client.pause.assert_not_called()
        mock_message.channel.send.assert_called_once()
        args = mock_message.channel.send.call_args[0][0]
        assert "no music" in args.lower()
    
    @pytest.mark.asyncio
    async def test_pause_when_voice_client_none(self):
        """Test pausing when no voice client exists"""
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        mock_message.guild = MagicMock()
        mock_message.client = MagicMock()
        
        with patch('discord.utils.get', return_value=None):
            await music_handler.pause(mock_message)
        
        mock_message.channel.send.assert_called_once()
        args = mock_message.channel.send.call_args[0][0]
        assert "no music" in args.lower()
    
    @pytest.mark.asyncio
    async def test_resume_when_paused(self):
        """Test resuming when music is paused"""
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        mock_message.guild = MagicMock()
        mock_message.client = MagicMock()
        
        mock_voice_client = MagicMock()
        mock_voice_client.is_paused.return_value = True
        
        with patch('discord.utils.get', return_value=mock_voice_client):
            await music_handler.resume(mock_message)
        
        mock_voice_client.resume.assert_called_once()
        mock_message.channel.send.assert_called_once()
        args = mock_message.channel.send.call_args[0][0]
        assert "resumed" in args.lower()
    
    @pytest.mark.asyncio
    async def test_resume_when_not_paused(self):
        """Test resuming when music is not paused"""
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        mock_message.guild = MagicMock()
        mock_message.client = MagicMock()
        
        mock_voice_client = MagicMock()
        mock_voice_client.is_paused.return_value = False
        
        with patch('discord.utils.get', return_value=mock_voice_client):
            await music_handler.resume(mock_message)
        
        mock_voice_client.resume.assert_not_called()
        mock_message.channel.send.assert_called_once()
        args = mock_message.channel.send.call_args[0][0]
        assert "no paused music" in args.lower()


class TestSpotifySongHandling:
    """Test cases for Spotify song handling"""
    
    @pytest.fixture(autouse=True)
    def reset_queue(self):
        """Reset queue before each test"""
        music_handler.queue = []
        yield
        music_handler.queue = []
    
    @pytest.mark.asyncio
    @patch('music_handler.sp')
    async def test_handle_spotify_song_success(self, mock_sp):
        """Test handling Spotify song link successfully"""
        mock_sp.track.return_value = {
            "name": "Test Song",
            "artists": [{"name": "Artist 1"}, {"name": "Artist 2"}]
        }
        
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        
        await music_handler.handle_spotify_song(
            mock_message, 
            "https://open.spotify.com/track/123456?si=abc"
        )
        
        assert len(music_handler.queue) == 1
        assert "Test Song" in music_handler.queue[0][1]
        assert "Artist 1" in music_handler.queue[0][1]
        mock_message.channel.send.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('music_handler.sp')
    async def test_handle_spotify_song_invalid_link(self, mock_sp):
        """Test handling invalid Spotify link"""
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        
        await music_handler.handle_spotify_song(
            mock_message, 
            "https://open.spotify.com/invalid"
        )
        
        mock_message.channel.send.assert_called_once()
        args = mock_message.channel.send.call_args[0][0]
        assert "invalid" in args.lower() or "failed" in args.lower()
    
    @pytest.mark.asyncio
    @patch('music_handler.sp')
    async def test_handle_spotify_song_api_error(self, mock_sp):
        """Test handling Spotify API error"""
        mock_sp.track.side_effect = Exception("API Error")
        
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        
        await music_handler.handle_spotify_song(
            mock_message, 
            "https://open.spotify.com/track/123456?si=abc"
        )
        
        mock_message.channel.send.assert_called_once()
        args = mock_message.channel.send.call_args[0][0]
        assert "invalid" in args.lower() or "failed" in args.lower()


class TestSpotifyPlaylistHandling:
    """Test cases for Spotify playlist handling"""
    
    @pytest.fixture(autouse=True)
    def reset_queue(self):
        """Reset queue before each test"""
        music_handler.queue = []
        yield
        music_handler.queue = []
    
    @pytest.mark.asyncio
    @patch('music_handler.sp')
    async def test_handle_spotify_playlist_success(self, mock_sp):
        """Test handling Spotify playlist successfully"""
        mock_sp.playlist_tracks.return_value = {
            'items': [
                {
                    'track': {
                        'name': 'Song 1',
                        'artists': [{'name': 'Artist 1'}]
                    }
                },
                {
                    'track': {
                        'name': 'Song 2',
                        'artists': [{'name': 'Artist 2'}]
                    }
                }
            ]
        }
        
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        mock_message.guild = MagicMock()
        mock_message.user = MagicMock()
        mock_message.user.voice = None
        mock_message.client = MagicMock()
        
        with patch('discord.utils.get', return_value=MagicMock()):
            await music_handler.handle_spotify_playlist(
                mock_message,
                "https://open.spotify.com/playlist/123456?si=abc"
            )
        
        assert len(music_handler.queue) == 2
        assert "Song 1" in music_handler.queue[0][1]
        assert "Song 2" in music_handler.queue[1][1]
        mock_message.channel.send.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('music_handler.sp')
    async def test_handle_spotify_playlist_api_error(self, mock_sp):
        """Test handling Spotify playlist API error"""
        mock_sp.playlist_tracks.side_effect = Exception("API Error")
        
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        mock_message.guild = MagicMock()
        mock_message.user = MagicMock()
        mock_message.user.voice = None
        mock_message.client = MagicMock()
        
        with patch('discord.utils.get', return_value=MagicMock()):
            await music_handler.handle_spotify_playlist(
                mock_message,
                "https://open.spotify.com/playlist/123456?si=abc"
            )
        
        mock_message.channel.send.assert_called_once()
        args = mock_message.channel.send.call_args[0][0]
        assert "failed" in args.lower()


class TestSongSearch:
    """Test cases for song search functionality"""
    
    @pytest.fixture(autouse=True)
    def reset_queue(self):
        """Reset queue before each test"""
        music_handler.queue = []
        yield
        music_handler.queue = []
    
    @pytest.mark.asyncio
    @patch('music_handler.sp')
    async def test_handle_song_search_success(self, mock_sp):
        """Test song search on Spotify successfully"""
        mock_sp.search.return_value = {
            'tracks': {
                'items': [
                    {
                        'name': 'Search Result Song',
                        'artists': [{'name': 'Search Result Artist'}]
                    }
                ]
            }
        }
        
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        
        result = await music_handler.handle_song_search(mock_message, "test query")
        
        assert result is not None
        assert "Search Result Song" in result[1]
        assert "Search Result Artist" in result[1]
        mock_sp.search.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('music_handler.sp')
    async def test_handle_song_search_no_results(self, mock_sp):
        """Test song search with no results"""
        mock_sp.search.return_value = {'tracks': {'items': []}}
        
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        
        result = await music_handler.handle_song_search(mock_message, "nonexistent song")
        
        assert result is None
        mock_message.channel.send.assert_called_once()
        args = mock_message.channel.send.call_args[0][0]
        assert "no results" in args.lower()
    
    @pytest.mark.asyncio
    @patch('music_handler.sp')
    async def test_handle_song_search_multiple_artists(self, mock_sp):
        """Test song search with multiple artists"""
        mock_sp.search.return_value = {
            'tracks': {
                'items': [
                    {
                        'name': 'Collab Song',
                        'artists': [
                            {'name': 'Artist 1'},
                            {'name': 'Artist 2'},
                            {'name': 'Artist 3'}
                        ]
                    }
                ]
            }
        }
        
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        
        result = await music_handler.handle_song_search(mock_message, "collab")
        
        assert result is not None
        assert "Artist 1" in result[1]
        assert "Artist 2" in result[1]
        assert "Artist 3" in result[1]


class TestPlayFunction:
    """Test cases for the play function"""
    
    @pytest.fixture(autouse=True)
    def reset_queue(self):
        """Reset queue before each test"""
        music_handler.queue = []
        yield
        music_handler.queue = []
    
    @pytest.mark.asyncio
    @patch('music_handler.handle_spotify_playlist')
    async def test_play_spotify_playlist(self, mock_handle):
        """Test playing Spotify playlist"""
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        mock_message.user = MagicMock()
        mock_message.user.voice = MagicMock()
        mock_message.user.voice.channel = MagicMock()
        mock_message.guild = MagicMock()
        mock_message.client = MagicMock()
        
        mock_voice_client = MagicMock()
        mock_voice_client.is_playing.return_value = False
        
        with patch('discord.utils.get', return_value=mock_voice_client):
            with patch('music_handler.play_next', new_callable=AsyncMock):
                await music_handler.play(
                    mock_message,
                    "https://open.spotify.com/playlist/123456"
                )
        
        mock_handle.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('music_handler.handle_spotify_song')
    async def test_play_spotify_track(self, mock_handle):
        """Test playing single Spotify track"""
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        mock_message.user = MagicMock()
        mock_message.user.voice = MagicMock()
        mock_message.user.voice.channel = MagicMock()
        mock_message.guild = MagicMock()
        mock_message.client = MagicMock()
        
        mock_voice_client = MagicMock()
        mock_voice_client.is_playing.return_value = False
        
        with patch('discord.utils.get', return_value=mock_voice_client):
            with patch('music_handler.play_next', new_callable=AsyncMock):
                await music_handler.play(
                    mock_message,
                    "https://open.spotify.com/track/123456"
                )
        
        mock_handle.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_play_no_voice_channel(self):
        """Test playing when user is not in voice channel"""
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        mock_message.user = MagicMock()
        mock_message.user.voice = None
        
        await music_handler.play(mock_message, "test song")
        
        mock_message.channel.send.assert_called_once()
        args = mock_message.channel.send.call_args[0][0]
        assert "voice channel" in args.lower()
    
    @pytest.mark.asyncio
    @patch('music_handler.handle_song_search')
    async def test_play_text_query(self, mock_search):
        """Test playing with text search query"""
        mock_search.return_value = ("search query", "Song Title", False)
        
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        mock_message.user = MagicMock()
        mock_message.user.voice = MagicMock()
        mock_message.user.voice.channel = MagicMock()
        mock_message.guild = MagicMock()
        mock_message.client = MagicMock()
        
        mock_voice_client = MagicMock()
        mock_voice_client.is_playing.return_value = False
        
        with patch('discord.utils.get', return_value=mock_voice_client):
            with patch('music_handler.play_next', new_callable=AsyncMock):
                await music_handler.play(mock_message, "test song")
        
        assert len(music_handler.queue) == 1
        mock_message.channel.send.assert_called()


class TestYouTubeSongHandling:
    """Test cases for YouTube song handling"""
    
    @pytest.fixture(autouse=True)
    def reset_queue(self):
        """Reset queue before each test"""
        music_handler.queue = []
        yield
        music_handler.queue = []
    
    @pytest.mark.asyncio
    @patch('music_handler.run_yt_dlp_search')
    async def test_handle_youtube_song_success(self, mock_search):
        """Test handling YouTube song successfully"""
        mock_search.return_value = {
            'title': 'Test Video',
            'url': 'http://example.com/stream',
            'uploader': 'Test Uploader'
        }
        
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = {
                'title': 'Test Video',
                'url': 'http://example.com/stream',
                'uploader': 'Test Uploader'
            }
            await music_handler.handle_youtube_song(
                mock_message,
                "https://youtu.be/123456"
            )
        
        assert len(music_handler.queue) == 1
        mock_message.channel.send.assert_called_once()


class TestYouTubePlaylistHandling:
    """Test cases for YouTube playlist handling"""
    
    @pytest.fixture(autouse=True)
    def reset_queue(self):
        """Reset queue before each test"""
        music_handler.queue = []
        yield
        music_handler.queue = []
    
    @pytest.mark.asyncio
    @patch('music_handler.run_yt_dlp_search')
    async def test_handle_youtube_playlist_success(self, mock_search):
        """Test handling YouTube playlist successfully"""
        mock_search.return_value = {
            'entries': [
                {
                    'title': 'Video 1',
                    'url': 'http://example.com/stream1',
                    'uploader': 'Uploader 1'
                },
                {
                    'title': 'Video 2',
                    'url': 'http://example.com/stream2',
                    'uploader': 'Uploader 2'
                }
            ]
        }
        
        mock_message = AsyncMock()
        mock_message.channel = AsyncMock()
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = {
                'entries': [
                    {
                        'title': 'Video 1',
                        'url': 'http://example.com/stream1',
                        'uploader': 'Uploader 1'
                    },
                    {
                        'title': 'Video 2',
                        'url': 'http://example.com/stream2',
                        'uploader': 'Uploader 2'
                    }
                ]
            }
            await music_handler.handle_youtube_playlist(
                mock_message,
                "https://www.youtube.com/playlist?list=123456"
            )
        
        assert len(music_handler.queue) == 2
        mock_message.channel.send.assert_called_once()
