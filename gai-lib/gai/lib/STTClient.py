import gai.common.ConfigHelper as ConfigHelper
from gai.common.http_utils import http_post
lib_config = ConfigHelper.get_lib_config()
base_url = lib_config["gai_url"]

class STTClient:

    def __call__(self, generator="whisper-transformers", file=None, file_path=None):
        if generator == "openai-whisper":
            return self.openai_whisper(file=file)

        url = lib_config["generators"][generator]["url"]

        if file_path:
            with open(file_path, "rb") as f:
                data = f.read()
            files = {
                "model": (None, generator),
                "file": (file_path, data)
            }

            url = lib_config["generators"][generator]["url"]
            response = http_post(base_url+url, files=files)

            response.decode = lambda: response.json()["text"]
            return response

        if file:
            files = {
                "model": (None, generator),
                "file": (file.name, file.read())
            }
            response = http_post(base_url+url, files=files)
            response.decode = lambda: response.json()["text"]
            return response

        raise Exception("No file provided")

    def openai_whisper(self, **model_params):
        import os
        import openai
        from openai import OpenAI
        from dotenv import load_dotenv
        load_dotenv()
        if not os.environ.get("OPENAI_API_KEY"):
            raise Exception(
                "OPENAI_API_KEY not found in environment variables")
        openai.api_key = os.environ["OPENAI_API_KEY"]
        client = OpenAI()

        if "file" not in model_params:
            raise Exception("Missing file parameter")

        file = model_params["file"]

        # If file is a bytes object, we need to write it to a temporary file then pass the file object to the API
        if isinstance(file, bytes):
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav') as temp:
                temp.write(file)
                temp.flush()
                temp.seek(0)
                model_params["file"] = temp.file
                response = client.audio.transcriptions.create(
                    model='whisper-1', **model_params)
        else:
            response = client.audio.transcriptions.create(
                model='whisper-1', **model_params)

        return response
