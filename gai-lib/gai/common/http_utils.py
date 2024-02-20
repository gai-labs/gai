import asyncio
from gai.common.errors import ApiException
from urllib.parse import urlparse
import os
import pprint
import re
import httpx
import requests
import json
from gai.common.logging import getLogger
logger = getLogger(__name__)


def is_url(s):
    return re.match(r'^https?:\/\/.*[\r\n]*', s) is not None

# Check if URL contains a file extension (e.g. .pdf, .jpg, .png, etc.)

def has_extension(url):
    parsed_url = urlparse(url)
    _, ext = os.path.splitext(parsed_url.path)
    return bool(ext)

import json

def _handle_failed_response(response):
    error_code = "unknown"
    if response.status_code == 401:
        raise ApiException(status_code=401, code=error_code, message="Unauthorized", url=response.url)

    content_type = response.headers.get("Content-Type")
    if content_type and "application/json" in content_type:
        error_data = response.json()
    else:
        error_data = response.text()

    e = Exception()
    e.response = response
    e.status = response.status_code

    if isinstance(error_data, str):
        raise ApiException(status_code=response.status_code, code=error_code, message=error_data, url=response.url)
    
    if 'detail' in error_data:

        if isinstance(error_data['detail'], str):
            raise ApiException(status_code=response.status_code, code=error_code, message=error_data['detail'], url=response.url)

        if 'code' in error_data['detail']:
            error_code = error_data['detail']['code']

        if 'message' in error_data['detail'] and isinstance(error_data['detail']['message'], str):
            raise ApiException(status_code=response.status_code, code=error_code, message=error_data['detail']['message'], url=response.url)

    if 'code' in error_data:
        error_code = error_data['code']
        if 'message' in error_data:
            raise ApiException(status_code=response.status_code, code=error_code, message=error_data['message'], url=response.url)    
        
    raise ApiException(status_code=response.status_code, code=error_code, message=json.dumps(error_data), url=response.url)    

async def _handle_failed_response_async(response):
    error_code = "unknown"
    if response.status == 401:
        raise ApiException(status_code=401, code=error_code, message="Unauthorized", url=response.url)

    content_type = response.headers.get("Content-Type")
    if content_type and "application/json" in content_type:
        error_data = await response.json()
    else:
        error_data = await response.text()

    e = Exception()
    e.response = response
    e.status = response.status

    if isinstance(error_data, str):
        raise ApiException(status_code=response.status, code=error_code, message=error_data, url=response.url)

    if 'detail' in error_data:

        if isinstance(error_data['detail'], str):
            raise ApiException(status_code=response.status_code, code=error_code, message=error_data['detail'], url=response.url)

        if 'code' in error_data['detail']:
            error_code = error_data['detail']['code']

        if 'message' in error_data['detail'] and isinstance(error_data['detail']['message'], str):
            raise ApiException(status_code=response.status_code, code=error_code, message=error_data['detail']['message'], url=response.url)

    if 'code' in error_data:
        error_code = error_data['code']
        if 'message' in error_data:
            raise ApiException(status_code=response.status_code, code=error_code, message=error_data['message'], url=response.url)    
        
    raise ApiException(status_code=response.status_code, code=error_code, message=json.dumps(error_data), url=response.url)    

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
                await _handle_failed_response_async(response)
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
            _handle_failed_response(response)

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
            _handle_failed_response(response)
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
                    await _handle_failed_response_async(response)
        except httpx.HTTPStatusError as e:
            raise Exception("Connection Error. Is the service Running?")

### DELETE method

def http_delete(url):
    return httpdelete(url)

def httpdelete(url):
    try:
        response = requests.delete(url)
        if response.status_code == 200:
            return response
        else:
            _handle_failed_response(response)
    except requests.exceptions.ConnectionError as e:
        raise Exception("Connection Error. Is the service Running?")

async def http_delete_async(url):
    return httpdelete_async(url)

async def httpdelete_async(url):
    async with httpx.AsyncClient() as session:
        try:
            response = await session.delete(url)
            if response.status_code == 200:
                return response
            else:
                await _handle_failed_response_async(response)
        except httpx.HTTPStatusError as e:
            raise Exception("Connection Error. Is the service Running?")

### PUT method

def http_put(url):
    return httpput(url)

def httpput(url):
    try:
        response = requests.put(url)
        if response.status_code == 200:
            return response
        else:
            _handle_failed_response(response)
    except requests.exceptions.ConnectionError as e:
        raise Exception("Connection Error. Is the service Running?")

async def http_put_async(url):
    return httpput_async(url)

async def httpput_async(url):
    async with httpx.AsyncClient() as session:
        try:
            response = await session.put(url)
            if response.status_code == 200:
                return response
            else:
                await _handle_failed_response_async(response)
        except httpx.HTTPStatusError as e:
            raise Exception("Connection Error. Is the service Running?")
