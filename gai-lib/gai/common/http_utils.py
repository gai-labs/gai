from gai.common._exceptions import HttpException
from urllib.parse import urlparse
import os
import pprint
import re
import httpx
import requests
import json
from gai.common.logging import logging
logger = logging.getLogger(__name__)


def is_url(s):
    return re.match(r'^https?:\/\/.*[\r\n]*', s) is not None

# Check if URL contains a file extension (e.g. .pdf, .jpg, .png, etc.)


def has_extension(url):
    parsed_url = urlparse(url)
    _, ext = os.path.splitext(parsed_url.path)
    return bool(ext)


async def http_post_async(url, data):
    return httppost_async(url, data)


async def httppost_async(url, data):
    headers = {"Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        if not isinstance(data, str):
            data = json.dumps(data)
        try:
            response = await client.post(url, data=data, headers=headers)
            if response.status == 200:
                return response
            else:
                try:
                    error_object = response.json()
                    code = error_object.get("code", "unknown")
                    message = error_object.get("message", "unknown")
                except Exception as e2:
                    code = "unknown"
                    message = response.text()
                raise HttpException(response.status_code, code, message, url)
        except httpx.HTTPStatusError as e:
            raise Exception("Connection Error. Is the service Running?")


def http_post(url, data=None, files=None):
    return httppost(url, data, files)


def httppost(url, data=None, files=None):
    if data == None and files == None:
        raise Exception("No data or files provided")

    logger.debug(f"httppost:url={url}")
    logger.debug(f"httppost:data={pprint.pformat(data)}")
    try:
        if files:
            if data and "stream" in data:
                files["stream"] = (None, data["stream"])
            response = requests.post(url, files=files)
        else:
            if "stream" in data:
                response = requests.post(url, json=data, stream=data["stream"])
            else:
                response = requests.post(url, json=data)
        if response.status_code == 200:
            return response
        else:
            try:
                error_object = response.json()
                code = error_object.get("code", "unknown")
                if (code == "unknown"):
                    code = response.reason.lower().replace(' ', '_')
                message = str(error_object)
                if (message == "unknown"):
                    message = response.text
            except Exception as e2:
                if response.reason:
                    code = response.reason.lower().replace(' ', '_')
                    message = response.reason
                else:
                    code = response.status_code
                    message = response.text
            raise HttpException(response.status_code, code, message, url)

    except requests.exceptions.ConnectionError as e:
        raise Exception("Connection Error. Is the service Running?")


def http_get(url):
    return httpget(url)


def httpget(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response
        else:
            raise Exception(f"httpget: Error={response.text}")
    except requests.exceptions.ConnectionError as e:
        raise Exception("Connection Error. Is the service Running?")


async def http_get_async(url):
    return httpget_async(url)


async def httpget_async(url):
    async with httpx.AsyncClient() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return response                      # Returning the data
                else:
                    raise Exception(f"httpget_async: Error={await response.text()}")
        except httpx.HTTPStatusError as e:
            raise Exception("Connection Error. Is the service Running?")


def http_delete(url):
    return httpdelete(url)


def httpdelete(url):
    try:
        response = requests.delete(url)
        if response.status_code == 200:
            return response
        else:
            raise Exception(f"httpdelete: Error={response.text}")
    except requests.exceptions.ConnectionError as e:
        raise Exception("Connection Error. Is the service Running?")


def http_put(url):
    return httpput(url)


def httpput(url):
    try:
        response = requests.put(url)
        if response.status_code == 200:
            return response
        else:
            raise Exception(f"httpput: Error={response.text}")
    except requests.exceptions.ConnectionError as e:
        raise Exception("Connection Error. Is the service Running?")
