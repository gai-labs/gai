from gai.lib.ttt.ChunkWrapper import ChunkWrapper
from gai.lib.ttt.OpenAIChunkWrapper import OpenAIChunkWrapper
from gai.lib.ttt.AnthropicChunkWrapper import AnthropicChunkWrapper
import gai.common.ConfigHelper as ConfigHelper
from gai.common.http_utils import http_post
from gai.common.generators_utils import chat_string_to_list, chat_list_to_string
from gai.common._exceptions import HttpException
import json

API_BASEURL = ConfigHelper.get_api_baseurl()


class TTTClient:

    def api(self, generator="mistral7b-exllama", messages=None, stream=True, **generator_params):
        if not messages:
            raise Exception("Messages not provided")

        if isinstance(messages, str):
            messages = chat_string_to_list(messages)

        lib_config = ConfigHelper.get_lib_config()
        if not generator:
            generator = lib_config["default_generator"]

        data = {
            "model": generator,
            "messages": messages,
            "stream": stream,
            **lib_config["generators"][generator]["default"],
            **generator_params
        }

        def streamer(response):
            for chunk in response.iter_lines():
                yield ChunkWrapper(chunk)

        try:
            base_url = lib_config["gai_url"]
            url = lib_config["generators"][generator]["url"]
            response = http_post(base_url + url, data)
        except HttpException as he:
            if he.code == "context_length_exceeded":
                try:
                    generator = "mistral7b_128k-exllama"
                    data["model"] = generator
                    url = lib_config["generators"][generator]["url"]
                    response = http_post(url, data)
                except Exception as e:
                    raise e
            else:
                raise he
        except Exception as e:
            raise e

        if not stream:
            if response.json()["choices"][0]["message"]["tool_calls"]:
                response.decode = lambda: {
                    "type":"function",
                    "name": response.json()["choices"][0]["message"]["tool_calls"][0]["function"]["name"],
                    "arguments": response.json()["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"],
                }
            elif response.json()["choices"][0]["message"]["content"]:
                response.decode = lambda: {
                    "type": "content",
                    "content": response.json()["choices"][0]["message"]["content"]
                }
            return response
        return streamer(response)

    def __call__(self, generator=None, messages=None, stream=True, **generator_params):
        if generator == "gpt-4":
            return self.gpt_4(messages=messages, stream=stream, **generator_params)
        elif generator == "claude2-100k":
            return self.claude_2(messages=messages, stream=stream, **generator_params)
        return self.api(generator, messages, stream, **generator_params)

    def gpt_4(self, messages=None, stream=True, **generator_params):
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

        if not messages:
            raise Exception("Messages not provided")

        def streamer(response):
            for chunk in response:
                yield OpenAIChunkWrapper(chunk)

        model = "gpt-4"
        if isinstance(messages, str):
            messages = chat_string_to_list(messages)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream,
            **generator_params
        )

        if not stream:
            if response.choices[0].message.tool_calls:
                response.decode = lambda: {
                    "type":"function",
                    "name": response.choices[0].message.tool_calls[0].function.name,
                    "arguments": response.choices[0].message.tool_calls[0].function.arguments,
                }
            elif response.choices[0].message.content:
                response.decode = lambda: {
                    "type": "content",
                    "content": response.choices[0].message.content
                }
            return response


        if not stream:
            response.decode = lambda: response.choices[
                0].message.content if response.choices[0].message.content else ""
            return response
        return streamer(response)

    def claude_2(self, messages=None, stream=True, **generator_params):
        import os
        from anthropic import Anthropic
        from dotenv import load_dotenv
        load_dotenv()
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise Exception(
                "ANTHROPIC_API_KEY not found in environment variables")
        client = Anthropic()

        if not messages:
            raise Exception("Messages not provided")

        def streamer(response):
            for chunk in response:
                yield AnthropicChunkWrapper(chunk)

        model = "claude-2"
        message = messages
        if isinstance(messages, list):
            message = chat_list_to_string(messages)
        prompt_template = "\n\nHuman: {message}\n\nAssistant:"
        messages = prompt_template.format(message=message)
        response = client.completions.create(
            model=model,
            prompt=messages,
            stream=stream,
            **generator_params
        )

        if not stream:
            response.decode = lambda: response.completion
            return response
        return streamer(response)
