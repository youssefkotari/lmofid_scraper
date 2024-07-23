from setuptools import setup

APP = ['m3u8_downloader_cli.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['moviepy', 'requests', 'tqdm'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
