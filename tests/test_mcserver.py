import os
import sys
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, mock_open, call
import subprocess

# Add parent directory to path to import mcserver_handler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import mcserver_handler


class TestRunServer:
    """Test cases for run_server function"""
    
    @pytest.fixture(autouse=True)
    def reset_globals(self):
        """Reset global variables before each test"""
        mcserver_handler.process = None
        mcserver_handler.booting = 0
        yield
        mcserver_handler.process = None
        mcserver_handler.booting = 0
    
    @pytest.mark.asyncio
    @patch('subprocess.Popen')
    async def test_run_server_atm10_success(self, mock_popen):
        """Test starting ATM10 server successfully"""
        mock_process = MagicMock()
        mock_process.pid = 1234
        mock_popen.return_value = mock_process
        
        result = await mcserver_handler.run_server("atm10")
        
        assert result is True
        mock_popen.assert_called_once()
        assert mcserver_handler.process is not None
        assert mcserver_handler.booting == 0
    
    @pytest.mark.asyncio
    @patch('subprocess.Popen')
    async def test_run_server_vanilla_success(self, mock_popen):
        """Test starting Vanilla server successfully"""
        mock_process = MagicMock()
        mock_process.pid = 5678
        mock_popen.return_value = mock_process
        
        result = await mcserver_handler.run_server("vanilla")
        
        assert result is True
        mock_popen.assert_called_once()
        assert mcserver_handler.process is not None
    
    @pytest.mark.asyncio
    @patch('subprocess.Popen')
    async def test_run_server_dc_success(self, mock_popen):
        """Test starting DC server successfully"""
        mock_process = MagicMock()
        mock_process.pid = 9999
        mock_popen.return_value = mock_process
        
        result = await mcserver_handler.run_server("dc")
        
        assert result is True
        mock_popen.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('subprocess.Popen')
    async def test_run_server_rf_success(self, mock_popen):
        """Test starting RF server successfully"""
        mock_process = MagicMock()
        mock_process.pid = 4321
        mock_popen.return_value = mock_process
        
        result = await mcserver_handler.run_server("rf")
        
        assert result is True
        mock_popen.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_server_already_running(self):
        """Test that run_server returns False if server already running"""
        mcserver_handler.process = MagicMock()
        
        result = await mcserver_handler.run_server("vanilla")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_run_server_invalid_version(self):
        """Test that run_server returns False for invalid version"""
        result = await mcserver_handler.run_server("invalid_version")
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch('subprocess.Popen')
    async def test_run_server_subprocess_error(self, mock_popen):
        """Test that run_server handles subprocess errors"""
        mock_popen.side_effect = subprocess.CalledProcessError(1, 'cmd')
        
        result = await mcserver_handler.run_server("vanilla")
        
        assert result is False


class TestStopServer:
    """Test cases for stop_server function"""
    
    @pytest.fixture(autouse=True)
    def reset_globals(self):
        """Reset global variables before each test"""
        mcserver_handler.process = None
        mcserver_handler.booting = 0
        yield
        mcserver_handler.process = None
        mcserver_handler.booting = 0
    
    @pytest.mark.asyncio
    async def test_stop_server_success(self):
        """Test stopping server successfully"""
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is still running
        mock_process.stdin = MagicMock()
        mock_process.wait.return_value = None
        mcserver_handler.process = mock_process
        
        result = await mcserver_handler.stop_server()
        
        assert result is True
        mock_process.stdin.write.assert_called_with(b"stop\n")
        mock_process.stdin.flush.assert_called_once()
        mock_process.wait.assert_called_with(timeout=60)
        assert mcserver_handler.process is None
    
    @pytest.mark.asyncio
    async def test_stop_server_no_process(self):
        """Test stopping when no server is running"""
        mcserver_handler.process = None
        
        result = await mcserver_handler.stop_server()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_stop_server_process_already_stopped(self):
        """Test stopping when process has already terminated"""
        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Process has exited
        mcserver_handler.process = mock_process
        
        result = await mcserver_handler.stop_server()
        
        assert result is True
        assert mcserver_handler.process is None
    
    @pytest.mark.asyncio
    async def test_stop_server_timeout(self):
        """Test stopping when process doesn't stop within timeout"""
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdin = MagicMock()
        mock_process.wait.side_effect = subprocess.TimeoutExpired('cmd', 60)
        mcserver_handler.process = mock_process
        
        result = await mcserver_handler.stop_server()
        
        assert result is True
        assert mcserver_handler.process is None
    
    @pytest.mark.asyncio
    async def test_stop_server_broken_pipe(self):
        """Test stopping when stdin is broken"""
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdin = MagicMock()
        mock_process.stdin.write.side_effect = BrokenPipeError()
        mcserver_handler.process = mock_process
        
        result = await mcserver_handler.stop_server()
        
        assert result is False
        assert mcserver_handler.process is None
    
    @pytest.mark.asyncio
    async def test_stop_server_generic_exception(self):
        """Test stopping with generic exception"""
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdin = MagicMock()
        mock_process.stdin.write.side_effect = Exception("Generic error")
        mcserver_handler.process = mock_process
        
        result = await mcserver_handler.stop_server()
        
        assert result is False


class TestStatus:
    """Test cases for status function"""
    
    @pytest.fixture(autouse=True)
    def reset_globals(self):
        """Reset global variables before each test"""
        mcserver_handler.process = None
        mcserver_handler.booting = 0
        yield
        mcserver_handler.process = None
        mcserver_handler.booting = 0
    
    def test_status_server_running(self):
        """Test status returns True when server is running"""
        mcserver_handler.process = MagicMock()
        
        result = mcserver_handler.status()
        
        assert result is True
    
    def test_status_server_not_running(self):
        """Test status returns False when server is not running"""
        mcserver_handler.process = None
        
        result = mcserver_handler.status()
        
        assert result is False


class TestGetIp:
    """Test cases for get_ip function"""
    
    @patch('requests.get')
    def test_get_ip_success(self, mock_get):
        """Test getting IP successfully"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "192.168.1.100"
        mock_get.return_value = mock_response
        
        result = mcserver_handler.get_ip()
        
        assert result == "192.168.1.100"
        mock_get.assert_called_once_with("https://api.ipify.org")
    
    @patch('requests.get')
    def test_get_ip_failure(self, mock_get):
        """Test getting IP when request fails"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_get.return_value = mock_response
        
        result = mcserver_handler.get_ip()
        
        assert result == 0
    
    @patch('requests.get')
    def test_get_ip_connection_error(self, mock_get):
        """Test getting IP when connection fails"""
        mock_get.side_effect = Exception("Connection error")
        
        with pytest.raises(Exception):
            mcserver_handler.get_ip()


class TestIntegration:
    """Integration tests for mcserver_handler"""
    
    @pytest.fixture(autouse=True)
    def reset_globals(self):
        """Reset global variables before each test"""
        mcserver_handler.process = None
        mcserver_handler.booting = 0
        yield
        mcserver_handler.process = None
        mcserver_handler.booting = 0
    
    @pytest.mark.asyncio
    @patch('subprocess.Popen')
    async def test_server_lifecycle(self, mock_popen):
        """Test complete server lifecycle: start -> check status -> stop"""
        mock_process = MagicMock()
        mock_process.pid = 1234
        mock_process.poll.return_value = None
        mock_process.stdin = MagicMock()
        mock_process.wait.return_value = None
        mock_popen.return_value = mock_process
        
        # Start server
        start_result = await mcserver_handler.run_server("vanilla")
        assert start_result is True
        
        # Check status
        status_result = mcserver_handler.status()
        assert status_result is True
        
        # Stop server
        stop_result = await mcserver_handler.stop_server()
        assert stop_result is True
        
        # Check status after stop
        final_status = mcserver_handler.status()
        assert final_status is False
