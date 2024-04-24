import unittest
from unittest.mock import patch
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import lol

class MockResponse:
    def __init__(self):
        self.choices = [MockChoice()]

class MockChoice:
    def __init__(self):
        self.message = MockMessage()

class MockMessage:
    def __init__(self):
        self.content = "The LA Dodgers won in 2020."

class TestOpenAIIntegration(unittest.TestCase):
    @patch('lol.get_openai_client')
    def test_api_call(self, mock_get_client):
        mock_client = mock_get_client.return_value
        mock_client.chat.completions.create.return_value = MockResponse()
        response = lol.create_response()
        self.assertTrue(response.choices)
        
if __name__ == '__main__':
    unittest.main()
