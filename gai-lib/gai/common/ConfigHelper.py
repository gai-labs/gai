import os
import json
from os.path import dirname
import shutil
import sys
from dotenv import load_dotenv
load_dotenv(os.path.join(sys.path[0], '.env'))
import yaml


def init():
    with open(os.path.expanduser("~/.gairc"), "w") as file:
        file.write(json.dumps({
            "app_dir": "~/gai",
            "discovery_url": "",
        }, indent=4))
    dir_path = os.path.expanduser("~/gai")
    os.makedirs(dir_path, exist_ok=True)
    os.makedirs(os.path.join(dir_path, 'cache'), exist_ok=True)


def get_rc():
    if (not os.path.exists(os.path.expanduser("~/.gairc"))):
        init()
    return json.load(open(os.path.expanduser("~/.gairc")))


def get_api_baseurl():
    # https://gaiaio.ai/api/gen
    return os.environ.get("GAI_API_BASEURL")

def get_lib_config(config_path=None):
    rc = get_rc()
    app_dir = rc["app_dir"]
    yml = os.path.join(os.path.expanduser(app_dir), "gai.yml")
    if config_path:
        yml = config_path
    lib_config = yaml.safe_load(open(yml))
    return lib_config

def get_default_generator():
    lib_config = get_lib_config()
    return lib_config["default_generator"]


def get_generator_url(generator):
    lib_config_json = get_lib_config()
    if generator not in lib_config_json['generators']:
        raise Exception(f"Generator {generator} not found supported.")
    return lib_config_json['generators'][generator]["url"]
