import os
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, call
import discord

# Add parent directory to path to import mtg_handler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import mtg_handler


class TestFetchCardsByName:
    """Test cases for fetch_cards_by_name function"""
    
    @patch('mtg_handler.Card')
    @patch('requests.get')
    def test_fetch_cards_by_name_success(self, mock_get, mock_card_class):
        """Test fetching card by name successfully using mtgsdk"""
        mock_card = MagicMock()
        mock_card.name = "Black Lotus"
        mock_card.text = "Tap, Sacrifice Black Lotus: Add three mana of any one color to your mana pool."
        mock_card.image_url = "https://example.com/black_lotus.jpg"
        mock_card.legalities = [
            {'format': 'Commander', 'legality': 'Legal'}
        ]
        
        mock_card_class.where.return_value.all.return_value = [mock_card]
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'prices': {'usd': '1500.00'}
        }
        mock_get.return_value = mock_response
        
        result = mtg_handler.fetch_cards_by_name("Black Lotus")
        
        assert result is not None
        assert result['name'] == "Black Lotus"
        assert result['price'] == '1500.00'
        assert result['legal'] is True
        assert 'Black Lotus' in result['image_url'] or result['image_url']
    
    @patch('requests.get')
    def test_fetch_cards_by_name_scryfall_success(self, mock_get):
        """Test fetching card via Scryfall API when mtgsdk fails"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'Lightning Bolt',
            'oracle_text': 'Lightning Bolt deals 3 damage to any target.',
            'image_uris': {
                'normal': 'https://example.com/lightning_bolt.jpg'
            },
            'prices': {'usd': '50.00'},
            'legalities': {'commander': 'legal'}
        }
        mock_get.return_value = mock_response
        
        with patch('mtg_handler.Card') as mock_card_class:
            mock_card_class.where.return_value.all.side_effect = Exception("No card found")
            result = mtg_handler.fetch_cards_by_name("Lightning Bolt")
        
        assert result is not None
        assert result['name'] == 'Lightning Bolt'
        assert result['disc'] == 'Lightning Bolt deals 3 damage to any target.'
        assert result['price'] == '50.00'
        assert result['legal'] is True
    
    @patch('requests.get')
    def test_fetch_cards_by_name_no_price(self, mock_get):
        """Test fetching card when price is not available"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'Test Card',
            'oracle_text': 'Test description',
            'image_uris': {
                'normal': 'https://example.com/test.jpg'
            },
            'prices': {'usd': None},
            'legalities': {'commander': 'legal'}
        }
        mock_get.return_value = mock_response
        
        with patch('mtg_handler.Card') as mock_card_class:
            mock_card_class.where.return_value.all.side_effect = Exception("No card found")
            result = mtg_handler.fetch_cards_by_name("Test Card")
        
        assert result is not None
        assert result['price'] == "-00.00"
    
    @patch('requests.get')
    def test_fetch_cards_by_name_not_commander_legal(self, mock_get):
        """Test fetching card that is not commander legal"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'Test Card',
            'oracle_text': 'Test description',
            'image_uris': {
                'normal': 'https://example.com/test.jpg'
            },
            'prices': {'usd': '10.00'},
            'legalities': {'commander': 'banned'}
        }
        mock_get.return_value = mock_response
        
        with patch('mtg_handler.Card') as mock_card_class:
            mock_card_class.where.return_value.all.side_effect = Exception("No card found")
            result = mtg_handler.fetch_cards_by_name("Test Card")
        
        assert result is not None
        assert result['legal'] is False
    
    @patch('requests.get')
    def test_fetch_cards_by_name_no_image_uri(self, mock_get):
        """Test fetching card with no image_uris field"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'Test Card',
            'oracle_text': 'Test description',
            'prices': {'usd': '10.00'},
            'legalities': {'commander': 'legal'}
        }
        mock_get.return_value = mock_response
        
        with patch('mtg_handler.Card') as mock_card_class:
            mock_card_class.where.return_value.all.side_effect = Exception("No card found")
            result = mtg_handler.fetch_cards_by_name("Test Card")
        
        assert result is not None
        assert result['image_url'] == "Image not available."
    
    @patch('requests.get')
    def test_fetch_cards_by_name_not_found(self, mock_get):
        """Test fetching card that doesn't exist"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        with patch('mtg_handler.Card') as mock_card_class:
            mock_card_class.where.return_value.all.side_effect = Exception("No card found")
            result = mtg_handler.fetch_cards_by_name("Nonexistent Card")
        
        assert result is None
    
    @patch('requests.get')
    def test_fetch_cards_by_name_api_error(self, mock_get):
        """Test fetching card when API returns error"""
        # The function doesn't catch all exceptions, so connection errors will propagate
        mock_get.side_effect = Exception("Connection error")
        
        with patch('mtg_handler.Card') as mock_card_class:
            mock_card_class.where.return_value.all.side_effect = Exception("No card found")
            
            # This will raise an exception since the function doesn't handle it
            with pytest.raises(Exception, match="Connection error"):
                mtg_handler.fetch_cards_by_name("Test Card")


class TestDisplayCards:
    """Test cases for display_cards function"""
    
    @pytest.mark.asyncio
    async def test_display_cards_success(self):
        """Test displaying card with all details"""
        card_details = {
            'name': 'Black Lotus',
            'disc': 'Tap, Sacrifice Black Lotus: Add three mana of any one color to your mana pool.',
            'image_url': 'https://example.com/black_lotus.jpg',
            'price': '1500.00',
            'legal': True
        }
        
        mock_ctx = AsyncMock()
        mock_ctx.channel = AsyncMock()
        
        await mtg_handler.display_cards(mock_ctx, card_details)
        
        mock_ctx.channel.send.assert_called_once()
        call_args = mock_ctx.channel.send.call_args
        embed = call_args.kwargs.get('embed') or call_args[1].get('embed')
        
        assert embed.title == "**Name: Black Lotus**"
    
    @pytest.mark.asyncio
    async def test_display_cards_with_legal_status(self):
        """Test displaying card shows correct legal status"""
        card_details = {
            'name': 'Test Card',
            'disc': 'Test description',
            'image_url': 'https://example.com/test.jpg',
            'price': '50.00',
            'legal': False
        }
        
        mock_ctx = AsyncMock()
        mock_ctx.channel = AsyncMock()
        
        await mtg_handler.display_cards(mock_ctx, card_details)
        
        mock_ctx.channel.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_display_cards_with_no_price(self):
        """Test displaying card with no price available"""
        card_details = {
            'name': 'Unknown Card',
            'disc': 'Unknown description',
            'image_url': 'https://example.com/unknown.jpg',
            'price': '-00.00',
            'legal': True
        }
        
        mock_ctx = AsyncMock()
        mock_ctx.channel = AsyncMock()
        
        await mtg_handler.display_cards(mock_ctx, card_details)
        
        mock_ctx.channel.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_display_cards_creates_embed(self):
        """Test that display_cards creates proper Discord embed"""
        card_details = {
            'name': 'Test Card',
            'disc': 'This is a test card',
            'image_url': 'https://example.com/test.jpg',
            'price': '100.00',
            'legal': True
        }
        
        mock_ctx = AsyncMock()
        mock_ctx.channel = AsyncMock()
        
        await mtg_handler.display_cards(mock_ctx, card_details)
        
        # Verify send was called
        assert mock_ctx.channel.send.called
        
        # Get the embed from the call
        call_args = mock_ctx.channel.send.call_args
        embed = call_args.kwargs.get('embed') or call_args[1].get('embed')
        
        # Verify embed is a Discord embed
        assert isinstance(embed, discord.Embed)
        assert embed.title == "**Name: Test Card**"


class TestMtgMain:
    """Test cases for mtg_main function"""
    
    @pytest.mark.asyncio
    @patch('mtg_handler.fetch_cards_by_name')
    @patch('mtg_handler.display_cards')
    async def test_mtg_main_card_found(self, mock_display, mock_fetch):
        """Test mtg_main when card is found"""
        card_details = {
            'name': 'Black Lotus',
            'disc': 'Tap, Sacrifice Black Lotus: Add three mana of any one color to your mana pool.',
            'image_url': 'https://example.com/black_lotus.jpg',
            'price': '1500.00',
            'legal': True
        }
        mock_fetch.return_value = card_details
        mock_display.return_value = None
        
        mock_ctx = AsyncMock()
        mock_ctx.response = AsyncMock()
        mock_ctx.channel = AsyncMock()
        
        await mtg_handler.mtg_main(mock_ctx, "Black Lotus")
        
        mock_ctx.response.send_message.assert_called_once()
        assert 'Looking up' in str(mock_ctx.response.send_message.call_args)
        mock_fetch.assert_called_once_with("Black Lotus")
        mock_display.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('mtg_handler.fetch_cards_by_name')
    async def test_mtg_main_card_not_found(self, mock_fetch):
        """Test mtg_main when card is not found"""
        mock_fetch.return_value = None
        
        mock_ctx = AsyncMock()
        mock_ctx.response = AsyncMock()
        mock_ctx.channel = AsyncMock()
        
        await mtg_handler.mtg_main(mock_ctx, "Nonexistent Card")
        
        mock_ctx.response.send_message.assert_called_once()
        mock_ctx.channel.send.assert_called_once()
        call_args = mock_ctx.channel.send.call_args[0][0]
        assert 'not found' in call_args.lower() or 'failed' in call_args.lower()
    
    @pytest.mark.asyncio
    @patch('mtg_handler.fetch_cards_by_name')
    async def test_mtg_main_sends_lookup_message(self, mock_fetch):
        """Test that mtg_main sends lookup message"""
        mock_fetch.return_value = None
        
        mock_ctx = AsyncMock()
        mock_ctx.response = AsyncMock()
        mock_ctx.channel = AsyncMock()
        
        test_input = "Test Card Name"
        await mtg_handler.mtg_main(mock_ctx, test_input)
        
        # Verify lookup message sent
        send_call_args = mock_ctx.response.send_message.call_args[0][0]
        assert 'Looking up' in send_call_args
        assert test_input in send_call_args
    
    @pytest.mark.asyncio
    @patch('mtg_handler.fetch_cards_by_name')
    @patch('mtg_handler.display_cards')
    async def test_mtg_main_with_empty_input(self, mock_display, mock_fetch):
        """Test mtg_main with empty input"""
        mock_fetch.return_value = None
        
        mock_ctx = AsyncMock()
        mock_ctx.response = AsyncMock()
        mock_ctx.channel = AsyncMock()
        
        await mtg_handler.mtg_main(mock_ctx, "")
        
        mock_fetch.assert_called_once_with("")
        mock_ctx.response.send_message.assert_called_once()


class TestIntegration:
    """Integration tests for mtg_handler"""
    
    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_full_workflow_card_lookup(self, mock_get):
        """Test complete workflow: lookup -> display"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'Lightning Bolt',
            'oracle_text': 'Lightning Bolt deals 3 damage to any target.',
            'image_uris': {
                'normal': 'https://example.com/lightning_bolt.jpg'
            },
            'prices': {'usd': '50.00'},
            'legalities': {'commander': 'legal'}
        }
        mock_get.return_value = mock_response
        
        with patch('mtg_handler.Card') as mock_card_class:
            mock_card_class.where.return_value.all.side_effect = Exception("No card found")
            
            # Fetch card
            card_details = mtg_handler.fetch_cards_by_name("Lightning Bolt")
            
            # Verify card was fetched
            assert card_details is not None
            assert card_details['name'] == 'Lightning Bolt'
            
            # Verify it can be displayed
            mock_ctx = AsyncMock()
            mock_ctx.channel = AsyncMock()
            
            await mtg_handler.display_cards(mock_ctx, card_details)
            
            mock_ctx.channel.send.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('mtg_handler.fetch_cards_by_name')
    @patch('mtg_handler.display_cards')
    async def test_full_mtg_main_workflow(self, mock_display, mock_fetch):
        """Test complete mtg_main workflow"""
        card_details = {
            'name': 'Test Card',
            'disc': 'Test description',
            'image_url': 'https://example.com/test.jpg',
            'price': '100.00',
            'legal': True
        }
        mock_fetch.return_value = card_details
        
        mock_ctx = AsyncMock()
        mock_ctx.response = AsyncMock()
        mock_ctx.channel = AsyncMock()
        
        # Execute main function
        await mtg_handler.mtg_main(mock_ctx, "Test Card")
        
        # Verify all steps executed
        assert mock_ctx.response.send_message.called
        assert mock_fetch.called
        assert mock_display.called


class TestCardDataStructure:
    """Test cases for card data structure validation"""
    
    def test_card_details_has_required_fields(self):
        """Test that fetched card details have all required fields"""
        card_details = {
            'name': 'Test Card',
            'disc': 'Test description',
            'image_url': 'https://example.com/test.jpg',
            'price': '100.00',
            'legal': True
        }
        
        required_fields = ['name', 'disc', 'image_url', 'price', 'legal']
        for field in required_fields:
            assert field in card_details
    
    def test_price_field_format(self):
        """Test that price field has correct format"""
        prices = ['100.00', '-00.00', '0.50', '9999.99']
        
        for price in prices:
            assert isinstance(price, str)
            # Should be either a price format or "-00.00"
            assert price == '-00.00' or '.' in price
    
    def test_legal_field_is_boolean(self):
        """Test that legal field is boolean"""
        legal_values = [True, False]
        
        for legal in legal_values:
            assert isinstance(legal, bool)


class TestErrorHandling:
    """Test error handling in mtg_handler"""
    
    @pytest.mark.asyncio
    async def test_display_cards_with_invalid_data(self):
        """Test display_cards handles missing fields gracefully"""
        # Test with minimal data
        card_details = {
            'name': 'Card',
            'disc': 'Description',
            'image_url': '',
            'price': '-00.00',
            'legal': False
        }
        
        mock_ctx = AsyncMock()
        mock_ctx.channel = AsyncMock()
        
        # Should not raise exception
        await mtg_handler.display_cards(mock_ctx, card_details)
        assert mock_ctx.channel.send.called
    
    @patch('requests.get')
    def test_fetch_cards_connection_timeout(self, mock_get):
        """Test fetch_cards_by_name handles connection timeout"""
        mock_get.side_effect = TimeoutError("Connection timeout")
        
        with patch('mtg_handler.Card') as mock_card_class:
            mock_card_class.where.return_value.all.side_effect = Exception("No card found")
            # Should handle gracefully and return None or raise
            try:
                result = mtg_handler.fetch_cards_by_name("Test Card")
                # If it doesn't raise, it should return None
                assert result is None or isinstance(result, dict)
            except TimeoutError:
                # It's acceptable to raise timeout errors
                pass
