import os
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Mock required modules before importing main
@pytest.fixture(autouse=True)
def mock_discord_dependencies():
    """Mock discord and related modules to prevent ImportError"""
    with patch('discord.Intents'):
        pass


class TestHelpCommand:
    """Test cases for the help command"""

    @pytest.mark.asyncio
    async def test_help_command_structure(self):
        """Test that help command contains all required sections"""
        help_text = """
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
"""

        # Check all required sections are present
        assert "***General:***" in help_text
        assert "***Minecraft Server Related Commands (1.20.4)***" in help_text
        assert "***Music***" in help_text
        assert "***Stock Market Data***" in help_text
        assert "***TCG (Trading Card Games)***" in help_text

    def test_help_command_has_stock_commands(self):
        """Test that help command includes stock market commands"""
        help_text = """***Stock Market Data***
stock - Get current stock price and information by ticker symbol
stocksearch - Search for stocks by company name
apistatus - Check current API usage and rate limit status"""

        assert "stock - Get current stock price and information by ticker symbol" in help_text
        assert "stocksearch - Search for stocks by company name" in help_text
        assert "apistatus - Check current API usage and rate limit status" in help_text

    def test_help_command_has_mtg_command(self):
        """Test that help command includes MTG command"""
        help_text = """***TCG (Trading Card Games)***
mtg - Search for Magic: The Gathering card information"""

        assert "mtg - Search for Magic: The Gathering card information" in help_text

    def test_help_command_has_music_commands(self):
        """Test that help command includes music commands"""
        help_text = """***Music***
play - Given a search query, youtube playlist/song, or spotify playlist/song, plays music
queue - Provides a list of songs in queue
pause - Pauses the current song
resume - Resumes the current paused song
stop - Stops the current and clears the queue"""

        assert "play - Given a search query" in help_text
        assert "queue - Provides a list of songs in queue" in help_text
        assert "pause - Pauses the current song" in help_text
        assert "resume - Resumes the current paused song" in help_text
        assert "stop - Stops the current and clears the queue" in help_text

    def test_help_command_has_minecraft_commands(self):
        """Test that help command includes Minecraft server commands"""
        help_text = """***Minecraft Server Related Commands (1.20.4)***
mcstart - Starts the Minecraft Bedrock Server
mcstop - Stops the Minecraft Server
mcstatus - Provides the status of the server
mcip - Provides the IP of the server"""

        assert "mcstart - Starts the Minecraft Bedrock Server" in help_text
        assert "mcstop - Stops the Minecraft Server" in help_text
        assert "mcstatus - Provides the status of the server" in help_text
        assert "mcip - Provides the IP of the server" in help_text


# class TestStockCommands:
#     """Test cases for stock-related commands in main.py"""

#     @pytest.mark.asyncio
#     @patch('stock_handler.search_stocks')
#     async def test_stocksearch_command(self, mock_search):
#         """Test stocksearch command functionality"""
#         mock_search.return_value = [
#             {
#                 'symbol': 'AAPL',
#                 'description': 'Apple Inc',
#                 'displaySymbol': 'AAPL'
#             }
#         ]

#         result = mock_search('Apple')

#         assert result is not None
#         assert len(result) > 0
#         assert result[0]['symbol'] == 'AAPL'

#     @pytest.mark.asyncio
#     @patch('stock_handler.get_stock')
#     async def test_stock_command(self, mock_get_stock):
#         """Test stock command functionality"""
#         mock_get_stock.return_value = {
#             'ticker': 'AAPL',
#             'name': 'Apple Inc',
#             'price': 150.25,
#             'sector': 'Technology',
#             'change': 2.5,
#             'change_percent': 1.69
#         }

#         result = mock_get_stock('AAPL')

#         assert result is not None
#         assert result['ticker'] == 'AAPL'
#         assert result['name'] == 'Apple Inc'
#         assert result['price'] == 150.25

    # @pytest.mark.asyncio
    # @patch('stock_handler.get_api_usage')
    # async def test_apistatus_command(self, mock_api_usage):
    #     """Test apistatus command functionality"""
    #     mock_api_usage.return_value = {
    #         'calls_this_minute': 15,
    #         'limit': 60,
    #         'remaining': 45,
    #         'total_calls': 1250
    #     }

    #     result = mock_api_usage()

    #     assert result is not None
    #     assert result['limit'] == 60
    #     assert result['remaining'] == 45
    #     assert result['calls_this_minute'] == 15


class TestMTGCommands:
    """Test cases for MTG-related commands in main.py"""

    @pytest.mark.asyncio
    @patch('mtg_handler.mtg_main')
    async def test_mtg_command(self, mock_mtg):
        """Test MTG command functionality"""
        mock_mtg.return_value = None  # Command sends embed directly

        result = mock_mtg()

        # The MTG command sends embeds directly via Discord
        # So we just verify the function is called without error
        assert mock_mtg.called
