import os
import sys
import re
import time
import json
from os.path import dirname
import shutil

# Create ~/.gaiaio/cache

# Create ~/.cache/locallm


def mkdir_cache(sub_dir):
    cache_dir = os.path.join(os.path.join(
        os.path.expanduser('~'), '~/gai/cache/'), sub_dir)
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def is_url(s):
    return re.match(r'^https?:\/\/.*[\r\n]*', s) is not None


def sha256(text):
    import hashlib
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def timestamp():
    return int(time.time() * 1000)


def find_url_in_text(text):
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    urls = re.findall(url_pattern, text)
    return urls

# Remove all white spaces and quotation marks from a string for use as a prompt


def clean_string(s):
    if s is None:
        return ''
    s = re.sub(r'[\s\'\"]+', ' ', s)
    s = s.replace('\\"', '"').replace('\\n', '')
    return s.strip()

# Remove unprintable unicode chars


def remove_unprintable(input_str):
    return ''.join(ch for ch in input_str if ch.isprintable() or ch in ('\t', '\n'))

# This is useful when asking for JSON results from LLM


def extract_json_substring(s):
    s = re.sub(r"\s+", " ", s)
    s = s.replace('\\"', '"').replace('\\n', '')
    try:
        match = re.search(r'\[.*\]', s)
        if match:
            json_string = match.group(0)
            return json_string
    except:
        pass
    return None


def extract_double_quoted_substring(s):
    match = re.search(r'\\"(.*)\\"', s)
    if match:
        # This will hold 'What is the original purpose of the Apple Remote?'
        result = match.group(1)
        return result
    return None


def find_site_packages_path(virtual_env_name):
    # Extracting the Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

    # Constructing the path pattern to the virtual environment's site-packages directory
    site_packages_path = os.path.expanduser(
        f"~/miniconda/envs/{virtual_env_name}/lib/python{python_version}/site-packages")
    return site_packages_path


def find_egg_link(virtual_env_name, package_name):
    site_packages_path = find_site_packages_path(virtual_env_name)
    egg_link_file = os.path.join(
        site_packages_path, f"{package_name}.egg-link")
    if os.path.exists(egg_link_file):
        return egg_link_file
    else:
        return None


def find_project_path(virtual_env_name, package_name):
    egg_link_file = find_egg_link(virtual_env_name, package_name)
    if egg_link_file is None:
        return None
    else:
        with open(egg_link_file) as f:
            project_path = f.readline().strip()
            return project_path


def is_data_url(s):
    """
    Check if the given string is a valid data URL.

    Args:
        s (str): The string to check.

    Returns:
        bool: True if the string is a valid data URL, False otherwise.
    """
    data_url_pattern = re.compile(r'data:[\w\-]+\/[\w\-]+;base64,[\w\+=/]+')
    return bool(data_url_pattern.match(s))


def is_image_data_url(s):
    """
    Check if the given string is a valid data URL.

    Args:
        s (str): The string to check.

    Returns:
        bool: True if the string is a valid data URL, False otherwise.
    """
    data_url_pattern = re.compile(r'data:image\/[\w\-]+;base64,[\w\+=/]+')
    return bool(data_url_pattern.match(s))
