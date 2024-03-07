import unittest
from unittest.mock import patch
from gai.ttt import JsonOutputParser

class TestJsonOutputParser(unittest.TestCase):

    def setUp(self):
        self.parser = JsonOutputParser()

    def test_ut0221_json_output_test(self):
        text = '{"type": "json", "json": {"search_query": "latest news Singapore" } }'
        output, stop_type = self.parser.parse(text)
        self.assertEqual(output, '{ "search_query": "latest news Singapore" }')

if __name__ == '__main__':
    unittest.main()