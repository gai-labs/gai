from gai.common.http_utils import http_post
import gai.common.ConfigHelper as ConfigHelper
API_BASEURL = ConfigHelper.get_api_baseurl()


class TTSClient:

    def __call__(self, input, generator="xtts-2", stream=True, **generator_params):
        if generator == "openai-tts-1":
            return self.openai_tts(input, **generator_params)

        if not input:
            raise Exception("The parameter 'input' is required.")
        data = {
            "model": generator,
            "input": input,
            "stream": stream,
            **generator_params
        }
        lib_config = ConfigHelper.get_lib_config()
        base_url = lib_config["gai_url"]
        url = lib_config["generators"][generator]["url"]
        response = http_post(base_url+url, data)
        return response

    def openai_tts(self, input, **generator_params):
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

        if not input:
            raise Exception("Missing input parameter")

        voice = generator_params.pop("voice", None)
        if not voice:
            voice = "alloy"

        generator_params.pop("language", None)
        generator_params.pop("stream", None)

        response = client.audio.speech.create(
            model='tts-1', input=input, voice=voice, **generator_params)
        return response.content
