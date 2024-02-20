import unittest
from unittest.mock import patch, mock_open
import json
import os,io

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..','..')))
print(sys.path)

from gai.common import constants 
from gai.common.utils import get_rc, get_app_path,get_gen_config,get_lib_config

class TestGaiUtils(unittest.TestCase):

    def test_GAIRC_is_valid_constant(self):   
        self.assertTrue(constants.GAIRC == "~/.gairc")

    def test_GAIRC_contains_APP_DIR(self):
        json = get_rc()
        self.assertTrue(json["app_dir"] == "~/.gai")

    # Check if get_config_path returns absolute path of ~/.gai
    def test_get_config_path(self):
        config_path = get_app_path()
        self.assertTrue(config_path == os.path.expanduser("~/.gai"))

    # Check if ~/.gai/gai.json exists and returns the json object
    def test_get_config(self):
        config = get_gen_config()
        self.assertTrue(config["gen"]["default"] == "mistral7b-exllama")

    # Check if ~/.gai/gai.yml exists and returns the yml object
    def test_lib_config(self):
        config = get_lib_config()
        self.assertTrue(config["default_generator"] == "mistral7b-exllama")

    # @patch("os.path.exists")
    # @patch("utils.init")
    # @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({"app_dir": "~/.gai"}))
    # def test_get_rc(self, mock_file, mock_init, mock_exists):
    #     mock_exists.return_value = True
    #     rc = utils.get_rc()
    #     self.assertEqual(rc, {"app_dir": "~/.gai"})
    #     mock_exists.assert_called_once_with(os.path.expanduser(constants.GAIRC))
    #     mock_file.assert_called_once_with(os.path.expanduser(constants.GAIRC), 'r')
    #     mock_init.assert_not_called()

    # @patch("os.path.exists")
    # @patch("utils.init")
    # def test_get_rc_no_file(self, mock_init, mock_exists):
    #     mock_exists.return_value = False
    #     get_rc()
    #     mock_exists.assert_called_once_with(os.path.expanduser(GAIRC))
    #     mock_init.assert_called_once()

    # @patch("utils.get_rc", return_value={"app_dir": "~/.gai"})
    # def test_get_config_path(self, mock_get_rc):
    #     config_path = get_config_path()
    #     expected_path = os.path.abspath(os.path.expanduser("~/.gai"))
    #     self.assertEqual(config_path, expected_path)
    #     mock_get_rc.assert_called_once()

    # @patch("utils.get_rc", return_value={"app_dir": "~/.gai"})
    # @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({"key": "value"}))
    # def test_get_config(self, mock_file, mock_get_rc):
    #     config = get_config()
    #     self.assertEqual(config, {"key": "value"})
    #     mock_get_rc.assert_called_once()
    #     mock_file.assert_called_once_with(os.path.join(os.path.abspath(os.path.expanduser("~/.gai")), 'gai.json'), 'r')

if __name__ == '__main__':
    unittest.main()
