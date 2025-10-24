"""Setup script for pdf-agent package."""

from setuptools import setup, find_packages

setup(
    name="pdf-agent",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "pdf2tasks=src.cli.main:main",
        ],
    },
)
