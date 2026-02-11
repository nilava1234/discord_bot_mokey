Project Name:
Personal Discord Bot

Summary:
A bot that uses the DiscordPy to connect with the discord API to interact with discord users. Currently used for managing Minecraft servers of various versions as well as a query bot for music and trading card games.

Features:

- Music Player (music_handler.py):
Can be used as a music player by streaming music through discordPy. Connects to server channels and streams using ffmpeg

- TCG Search (mtg_handler.py):
Using Scryfall API quiries cards, card prices, and legality within the game and provide all of that information within a consumable package.

- Server management (mcserver_handler.py):
Handles server initialization and termination using cmd prompts, using a primitive lock system to handle potential runtime issues.

- Stock Data (stock_data.py):
Fetches real-time stock information using the Finnhub API. Users can get stock quotes, company information, and detailed market data with built-in rate limiting and caching.