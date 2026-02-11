# Company Stock Information from Finnhub.io API
import requests
import os
import time
from typing import Dict, Optional, List
from dotenv import load_dotenv

load_dotenv()

# Finnhub API Configuration
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

if not FINNHUB_API_KEY:
    raise ValueError("FINNHUB_API_KEY not found in .env file")

# Rate limiting: 60 calls per minute
RATE_LIMIT = 60
RATE_LIMIT_WINDOW = 60  # seconds

# Cache for storing fetched data to reduce API calls
_stock_cache = {}
_api_call_times = []  # Track timestamps of API calls
_total_api_calls = 0  # Counter for total API calls made

def _check_rate_limit():
    """
    Check if we've exceeded the rate limit.
    Removes calls older than the time window and raises exception if limit exceeded.
    """
    global _api_call_times, _total_api_calls
    
    current_time = time.time()
    
    # Remove calls older than the time window
    _api_call_times = [call_time for call_time in _api_call_times 
                       if current_time - call_time < RATE_LIMIT_WINDOW]
    
    # Check if we've exceeded the limit
    if len(_api_call_times) >= RATE_LIMIT:
        oldest_call = _api_call_times[0]
        wait_time = RATE_LIMIT_WINDOW - (current_time - oldest_call)
        raise Exception(f"⚠️ Rate limit exceeded ({len(_api_call_times)}/{RATE_LIMIT}). Please wait {wait_time:.1f} seconds before making another API call.")
    
    # Record this API call
    _api_call_times.append(current_time)
    _total_api_calls += 1

def get_quote(ticker: str) -> Optional[Dict]:
    """
    Fetch real-time stock quote data from Finnhub API.
    
    Returns: Dictionary with price, change, and volume data
    """
    try:
        _check_rate_limit()
        url = f"{FINNHUB_BASE_URL}/quote"
        params = {
            "symbol": ticker.upper(),
            "token": FINNHUB_API_KEY
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching quote for {ticker}: {e}")
        return None

def get_company_profile(ticker: str) -> Optional[Dict]:
    """
    Fetch company profile information from Finnhub API.
    
    Returns: Dictionary with company name, sector, market cap, description, etc.
    """
    try:
        _check_rate_limit()
        url = f"{FINNHUB_BASE_URL}/stock/profile2"
        params = {
            "symbol": ticker.upper(),
            "token": FINNHUB_API_KEY
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching profile for {ticker}: {e}")
        return None

def get_stock(ticker: str) -> Optional[Dict]:
    """
    Retrieve comprehensive stock information by ticker symbol.
    Combines quote and company profile data from Finnhub API.
    """
    ticker = ticker.upper()
    
    # Check cache first
    if ticker in _stock_cache:
        return _stock_cache[ticker]
    
    try:
        quote = get_quote(ticker)
        profile = get_company_profile(ticker)
        
        if not quote or not profile:
            print(f"Unable to fetch complete data for {ticker}")
            return None
        
        # Combine data into a single stock information object
        stock_info = {
            "ticker": ticker,
            "name": profile.get("name", "N/A"),
            "sector": profile.get("finnhubIndustry", "N/A"),
            "market_cap": profile.get("marketCapitalization", "N/A"),
            "price": quote.get("c", "N/A"),  # current price
            "open": quote.get("o", "N/A"),
            "high": quote.get("h", "N/A"),
            "low": quote.get("l", "N/A"),
            "previous_close": quote.get("pc", "N/A"),
            "change": quote.get("d", "N/A"),
            "change_percent": quote.get("dp", "N/A"),
            "pe_ratio": profile.get("pe", "N/A"),
            "description": profile.get("description", "N/A"),
            "website": profile.get("website", "N/A"),
            "currency": profile.get("currency", "N/A"),
            "volume": quote.get("v", "N/A"),
        }
        
        # Cache the result
        _stock_cache[ticker] = stock_info
        return stock_info
        
    except Exception as e:
        print(f"Error retrieving stock data for {ticker}: {e}")
        return None

def search_stocks(query: str) -> Optional[List[Dict]]:
    """
    Search for stocks by company name or ticker symbol.
    
    Returns: List of matching companies
    """
    try:
        _check_rate_limit()
        url = f"{FINNHUB_BASE_URL}/search"
        params = {
            "q": query,
            "token": FINNHUB_API_KEY
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("result", [])
    except Exception as e:
        print(f"Error searching for stocks: {e}")
        return None

def get_all_stocks() -> Dict:
    """Return cached stocks. Call get_stock() first to populate cache."""
    return _stock_cache

def list_tickers() -> List[str]:
    """Return a list of cached ticker symbols."""
    return list(_stock_cache.keys())

def clear_cache():
    """Clear the stock data cache."""
    global _stock_cache
    _stock_cache = {}

def get_api_usage() -> Dict[str, int]:
    """
    Get current API usage statistics.
    
    Returns: Dictionary with call counts and limits
    """
    current_time = time.time()
    # Count calls in the current minute window
    calls_this_minute = len([t for t in _api_call_times 
                             if current_time - t < RATE_LIMIT_WINDOW])
    
    return {
        "calls_this_minute": calls_this_minute,
        "limit": RATE_LIMIT,
        "remaining": RATE_LIMIT - calls_this_minute,
        "total_calls": _total_api_calls
    }
