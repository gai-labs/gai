from setuptools import setup, find_packages
from os.path import abspath
import subprocess, os, sys
from setuptools.command.install import install

base_dir = os.path.dirname(os.path.abspath(__file__))
version_file = os.path.join(base_dir, 'VERSION')
with open(version_file, 'r') as f:
    VERSION = f.read().strip()

def parse_requirements(filename):
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)) as f:
        required = f.read().splitlines()
    return required

setup(
    name='gai-lib',
    version=VERSION,
    author="kakkoii1337",
    author_email="kakkoii1337@gmail.com",
    packages=find_packages(),
    description = """""",
    long_description="Refer to https://gai-labs.github.io/gai/gai-lib for more information",
    long_description_content_type="text/markdown",
    classifiers=[
        'Programming Language :: Python :: 3.10',
        "Development Status :: 3 - Alpha",        
        'License :: OSI Approved :: MIT License',
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",        
        'Operating System :: OS Independent',
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Python Modules",        
        "Topic :: Scientific/Engineering :: Artificial Intelligence",        
    ],
    python_requires='>=3.10',        
    install_requires=[
        parse_requirements("requirements.txt")
    ],
    extras_require={
    },
    entry_points={
        'console_scripts': [
            'ttt=gai.cli.ttt:main',
            'tts=gai.cli.tts:main',
            'chunker=gai.cli.chunker:main',
            'pdf2txt=gai.cli.pdf2txt:main',
            'txt2md=gai.cli.txt2md:main',
            'gg=gai.cli.gg2:main',
            'summary=gai.cli.summarize:main',
            'scrape=gai.cli.scrape:main',
            'gai=gai.cli.Gaicli:main',
        ],
    }
)