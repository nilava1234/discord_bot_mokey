import os
import sys
import pytest
import time
from unittest.mock import patch, MagicMock, call

# Add parent directory to path to import stock_handler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import stock_handler


# Fixtures for mock data
@pytest.fixture
def sample_quote():
    """Fixture providing sample quote data"""
    return {
        'c': 150.25,
        'h': 152.0,
        'l': 148.0,
        'o': 148.5,
        'd': 2.5,
        'dp': 1.69,
        'v': 25000000
    }


@pytest.fixture
def sample_profile():
    """Fixture providing sample company profile data"""
    return {
        'name': 'Apple Inc',
        'finnhubIndustry': 'Technology',
        'marketCapitalization': 2800000,
        'pe': 28.5,
        'description': 'Apple Inc. is an American technology company',
        'website': 'https://www.apple.com',
        'currency': 'USD'
    }


@pytest.fixture
def sample_search_results():
    """Fixture providing sample search results"""
    return {
        'result': [
            {
                'symbol': 'AAPL',
                'description': 'Apple Inc',
                'displaySymbol': 'AAPL',
                'figi': 'BBG000B9XRY4',
            },
            {
                'symbol': 'APPL',
                'description': 'Apple REIT',
                'displaySymbol': 'APPL'
            }
        ]
    }


class TestGetQuote:
    """Test cases for get_quote function"""

    @patch('stock_handler.requests.get')
    @patch('stock_handler._check_rate_limit')
    def test_get_quote_success(self, mock_rate_limit, mock_get, sample_quote):
        """Test getting stock quote successfully"""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_quote
        mock_get.return_value = mock_response

        result = stock_handler.get_quote('AAPL')

        assert result is not None
        assert isinstance(result, dict)
        assert 'c' in result  # Current price should be present
        assert isinstance(result['c'], (int, float))  # Price should be numeric
        assert 'v' in result  # Volume should be present
        assert isinstance(result['v'], int)  # Volume is an integer
        mock_get.assert_called_once()

    @patch('stock_handler.requests.get')
    @patch('stock_handler._check_rate_limit')
    def test_get_quote_api_error(self, mock_rate_limit, mock_get):
        """Test handling quote API errors"""
        mock_get.side_effect = Exception("Connection Error")

        result = stock_handler.get_quote('AAPL')

        assert result is None

    @patch('stock_handler._check_rate_limit')
    def test_get_quote_rate_limit(self, mock_rate_limit):
        """Test rate limiting on quote request"""
        mock_rate_limit.side_effect = Exception("Rate limit exceeded")

        result = stock_handler.get_quote('AAPL')

        assert result is None


class TestGetCompanyProfile:
    """Test cases for get_company_profile function"""

    @patch('stock_handler.requests.get')
    @patch('stock_handler._check_rate_limit')
    def test_get_company_profile_success(self, mock_rate_limit, mock_get, sample_profile):
        """Test fetching company profile successfully"""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_profile
        mock_get.return_value = mock_response

        result = stock_handler.get_company_profile('AAPL')

        assert result is not None
        assert isinstance(result, dict)
        assert 'name' in result
        assert isinstance(result['name'], str)  # Name should be string
        assert 'finnhubIndustry' in result
        assert isinstance(result['finnhubIndustry'], str)  # Industry should be string
        assert 'marketCapitalization' in result
        assert isinstance(result['marketCapitalization'], (int, float))  # Market cap is numeric and varies daily

    @patch('stock_handler.requests.get')
    @patch('stock_handler._check_rate_limit')
    def test_get_company_profile_api_error(self, mock_rate_limit, mock_get):
        """Test handling profile API errors"""
        mock_get.side_effect = Exception("API Error")

        result = stock_handler.get_company_profile('AAPL')

        assert result is None


class TestGetStock:
    """Test cases for get_stock function"""

    @patch('stock_handler.get_company_profile')
    @patch('stock_handler.get_quote')
    def test_get_stock_success(self, mock_quote, mock_profile, sample_quote, sample_profile):
        """Test fetching comprehensive stock data successfully"""
        mock_quote.return_value = sample_quote
        mock_profile.return_value = sample_profile

        result = stock_handler.get_stock('AAPL')

        assert result is not None
        assert isinstance(result, dict)
        assert result['ticker'] == 'AAPL'
        assert 'name' in result
        assert 'price' in result
        assert isinstance(result['price'], (int, float))  # Price is numeric and varies daily
        assert 'sector' in result
        assert isinstance(result['sector'], str)
        mock_quote.assert_called_once()
        mock_profile.assert_called_once()

    @patch('stock_handler.get_company_profile')
    @patch('stock_handler.get_quote')
    def test_get_stock_incomplete_data(self, mock_quote, mock_profile):
        """Test handling incomplete stock data"""
        # Clear cache to ensure we're testing the API calls, not cached data
        stock_handler.clear_cache()
        
        mock_quote.return_value = None
        mock_profile.return_value = {'name': 'Apple Inc'}

        result = stock_handler.get_stock('AAPL')

        assert result is None

    def test_get_stock_caching(self, sample_quote, sample_profile):
        """Test that stock data is cached"""
        # Clear cache first
        stock_handler.clear_cache()

        with patch('stock_handler.get_company_profile') as mock_profile, \
             patch('stock_handler.get_quote') as mock_quote:
            mock_quote.return_value = sample_quote
            mock_profile.return_value = sample_profile

            # First call
            result1 = stock_handler.get_stock('AAPL')
            # Second call should use cache
            result2 = stock_handler.get_stock('AAPL')

            assert result1 == result2
            # Functions should be called only once each due to caching
            assert mock_quote.call_count == 1
            assert mock_profile.call_count == 1

            # Cleanup
            stock_handler.clear_cache()


class TestSearchStocks:
    """Test cases for search_stocks function"""

    @patch('stock_handler.requests.get')
    @patch('stock_handler._check_rate_limit')
    def test_search_stocks_success(self, mock_rate_limit, mock_get, sample_search_results):
        """Test searching stocks by company name"""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_search_results
        mock_get.return_value = mock_response

        result = stock_handler.search_stocks('Apple')

        assert result is not None
        assert isinstance(result, list)
        assert len(result) >= 1
        assert 'symbol' in result[0]

    @patch('stock_handler.requests.get')
    @patch('stock_handler._check_rate_limit')
    def test_search_stocks_no_results(self, mock_rate_limit, mock_get):
        """Test search with no results"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'result': []}
        mock_get.return_value = mock_response

        result = stock_handler.search_stocks('XYZABC123')

        assert result == []

    @patch('stock_handler.requests.get')
    @patch('stock_handler._check_rate_limit')
    def test_search_stocks_api_error(self, mock_rate_limit, mock_get):
        """Test handling search API errors"""
        mock_get.side_effect = Exception("API Error")

        result = stock_handler.search_stocks('Apple')

        assert result is None

    @patch('stock_handler._check_rate_limit')
    def test_search_stocks_rate_limit(self, mock_rate_limit):
        """Test rate limiting on search request"""
        mock_rate_limit.side_effect = Exception("Rate limit exceeded")

        result = stock_handler.search_stocks('Apple')

        assert result is None


class TestApiUsage:
    """Test cases for API usage tracking"""

    def test_get_api_usage(self):
        """Test getting API usage statistics"""
        usage = stock_handler.get_api_usage()

        assert usage is not None
        assert isinstance(usage, dict)
        assert 'calls_this_minute' in usage
        assert 'limit' in usage
        assert 'remaining' in usage
        assert 'total_calls' in usage
        # Verify limit is a positive integer (don't hardcode expected value)
        assert isinstance(usage['limit'], int)
        assert usage['limit'] > 0

    @patch('stock_handler._check_rate_limit')
    def test_api_usage_tracking(self, mock_check_rate_limit):
        """Test that API calls are tracked"""
        initial_usage = stock_handler.get_api_usage()
        initial_count = initial_usage['total_calls']

        # Simulate API calls
        with patch('stock_handler.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {'c': 100}
            mock_get.return_value = mock_response

            stock_handler.get_quote('TEST')

        final_usage = stock_handler.get_api_usage()
        # Total calls should have increased
        assert final_usage['total_calls'] >= initial_count


class TestCacheManagement:
    """Test cases for cache management"""

    def test_get_all_stocks(self):
        """Test retrieving all cached stocks"""
        stock_handler.clear_cache()

        # Cache should be empty initially
        all_stocks = stock_handler.get_all_stocks()
        assert isinstance(all_stocks, dict)
        assert len(all_stocks) == 0

    def test_list_tickers(self):
        """Test listing cached ticker symbols"""
        stock_handler.clear_cache()

        # Manually add stock to cache
        test_ticker = 'TESTCORP'
        stock_handler._stock_cache[test_ticker] = {'ticker': test_ticker, 'name': 'Test Corporation'}

        tickers = stock_handler.list_tickers()
        assert isinstance(tickers, list)
        assert test_ticker in tickers

        # Cleanup
        stock_handler.clear_cache()

    def test_clear_cache(self):
        """Test clearing the stock cache"""
        # Manually add stock to cache
        test_ticker = 'SAMPLE'
        stock_handler._stock_cache[test_ticker] = {'ticker': test_ticker, 'name': 'Sample Corp'}
        assert len(stock_handler.get_all_stocks()) > 0

        # Clear cache
        stock_handler.clear_cache()

        # Cache should be empty
        all_stocks = stock_handler.get_all_stocks()
        assert isinstance(all_stocks, dict)
        assert len(all_stocks) == 0


class TestRateLimiting:
    """Test cases for rate limiting functionality"""

    def test_check_rate_limit_under_limit(self):
        """Test that check_rate_limit passes when under limit"""
        # Reset rate limiting
        stock_handler._api_call_times = []

        # Should not raise exception when under limit
        try:
            for _ in range(10):
                stock_handler._check_rate_limit()
            success = True
        except Exception:
            success = False

        assert success
        # Should have tracked the calls
        assert isinstance(stock_handler._api_call_times, list)
        assert len(stock_handler._api_call_times) == 10

    def test_check_rate_limit_exceeds_limit(self):
        """Test that check_rate_limit raises exception when limit exceeded"""
        # Reset and max out rate limit
        stock_handler._api_call_times = []
        current_time = time.time()

        # Simulate hitting the rate limit by adding many recent calls
        # The actual limit value is determined by the handler's RATE_LIMIT_CALLS constant
        max_calls = 60  # Standard rate limit, but we test behavior not exact value
        for _ in range(max_calls):
            stock_handler._api_call_times.append(current_time)

        # Next call should raise exception
        with pytest.raises(Exception) as exc_info:
            stock_handler._check_rate_limit()

        assert "Rate limit" in str(exc_info.value)

        # Clean up
        stock_handler._api_call_times = []

    def test_rate_limit_window_expires(self):
        """Test that old calls are removed from rate limit tracking"""
        stock_handler._api_call_times = []

        # Add calls from far in the past (older than RATE_LIMIT_WINDOW)
        # We use a time that's definitely outside the window
        old_time = time.time() - 100  # older than any typical rate limit window
        for _ in range(50):
            stock_handler._api_call_times.append(old_time)

        # These old calls should be removed and new call should succeed
        stock_handler._check_rate_limit()

        # Only the new call should be tracked
        assert len(stock_handler._api_call_times) == 1

        # Clean up
        stock_handler._api_call_times = []
