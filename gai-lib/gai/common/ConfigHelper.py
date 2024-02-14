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
    return os.environ.get("GAI_API_BASEURL")
    # return "https://gaiaio.ai/api"


def get_lib_config():
    rc = get_rc()
    app_dir = rc["app_dir"]
    yml = os.path.join(os.path.expanduser(app_dir), "gai.yml")
    lib_config = yaml.safe_load(open(yml))

    if not lib_config:
        lib_config = {
            "default_generator": "mistral7b-exllama",
            "gai_url": f"{get_api_baseurl()}/gen/v1",
            "generators": {
                "mistral7b-exllama": {
                    "type": "ttt",
                    "url": f"{get_api_baseurl()}/gen/v1/chat/completions",
                    "whitelist": [
                        "temperature",
                        "top_p",
                        "min_p",
                        "top_k",
                        "max_new_tokens",
                        "typical",
                        "n",
                        "token_repetition_penalty_max",
                        "token_repetition_penalty_sustain",
                        "token_repetition_penalty_decay",
                        "beams",
                        "beam_length"
                    ],
                    "default": {
                        "temperature": 1.2,
                        "top_p": 0.15,
                        "min_p": 0.0,
                        "top_k": 50,
                        "max_new_tokens": 1000,
                        "typical": 0.0,
                        "token_repetition_penalty_max": 1.25,
                        "token_repetition_penalty_sustain": 256,
                        "token_repetition_penalty_decay": 128,
                        "beams": 1,
                        "beam_length": 1
                    }
                },
                "mistral7b_128k-exllama": {
                    "type": "ttt",
                    "url": f"{get_api_baseurl()}/gen/v1/longchat/completions",
                    "whitelist": [
                        "temperature",
                        "top_p",
                        "min_p",
                        "top_k",
                        "max_new_tokens",
                        "typical",
                        "n",
                        "token_repetition_penalty_max",
                        "token_repetition_penalty_sustain",
                        "token_repetition_penalty_decay",
                        "beams",
                        "beam_length"
                    ],
                    "default": {
                        "temperature": 1.2,
                        "top_p": 0.15,
                        "min_p": 0.0,
                        "top_k": 50,
                        "max_new_tokens": 1000,
                        "typical": 0.0,
                        "token_repetition_penalty_max": 1.25,
                        "token_repetition_penalty_sustain": 256,
                        "token_repetition_penalty_decay": 128,
                        "beams": 1,
                        "beam_length": 1
                    }
                },
                "gpt-4": {
                    "type": "ttt",
                    "whitelist": [
                        "max_tokens",
                        "temperature",
                        "top_p",
                        "presence_penalty",
                        "frequency_penalty",
                        "stop",
                        "logit_bias",
                        "n",
                        "stream",
                        "openai_api_key"
                    ],
                    "default": {
                        "temperature": 1.2,
                        "top_p": 0.15,
                        "top_k": 50,
                        "max_tokens": 1000
                    }
                },
                "claude2-100k": {
                    "type": "ttt",
                    "whitelist": [
                        "max_tokens_to_sample",
                        "temperature",
                        "top_p",
                        "top_k",
                        "stop_sequences"
                    ],
                    "default": {
                        "temperature": 1.2,
                        "top_p": 0.15,
                        "top_k": 50,
                        "max_tokens_to_sample": 1000
                    }
                },
                "whisper-transformers": {
                    "type": "stt",
                    "url": f"{get_api_baseurl()}/gen/v1/audio/transcriptions",
                },
                "xtts-2": {
                    "type": "tts",
                    "url": f"{get_api_baseurl()}/gen/v1/audio/speech",
                },
                "llava-transformers": {
                    "type": "itt",
                    "url": f"{get_api_baseurl()}/gen/v1/vision/completions",
                },
                "rag-index-file": {
                    "url": f"{get_api_baseurl()}/gen/v1/rag/index-file",
                },
                "rag-retrieve": {
                    "url": f"{get_api_baseurl()}/gen/v1/rag/retrieve",
                },
                "rag-collections": {
                    "url": f"{get_api_baseurl()}/gen/v1/rag/collections",
                },
                "rag-collection": {
                    "url": f"{get_api_baseurl()}/gen/v1/rag/collection",
                },
                "rag-document": {
                    "url": f"{get_api_baseurl()}/gen/v1/rag/document",
                }
            },
        }

    return lib_config


def get_default_generator():
    lib_config = get_lib_config()
    return lib_config["default_generator"]


def get_generator_url(generator):
    lib_config_json = get_lib_config()
    if generator not in lib_config_json['generators']:
        raise Exception(f"Generator {generator} not found supported.")
    return lib_config_json['generators'][generator]["url"]
