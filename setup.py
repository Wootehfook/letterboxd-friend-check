"""
Setup script for the Letterboxd Friend Check application
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="letterboxd-friend-check",
    version="1.0.0",
    author="Woo T. Fook",
    description="A tool to compare watchlists between Letterboxd users",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/letterboxd-friend-check",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "letterboxd-friend-check=letterboxd_friend_check.cli:main",
        ],
    },
    install_requires=[
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.1",
        "pillow>=9.2.0",
        "selenium>=4.4.0",
        "webdriver-manager>=3.8.0",
        "tmdbsimple>=2.9.1",
        "pandas>=1.5.0",
    ],
)
