#!/bin/bash

# Set the project name
PROJECT_NAME="decyphertek.ai"

# Set the Python version
PYTHON_VERSION="3.13.5"

# Set the PyInstaller version
PYINSTALLER_VERSION="6.16"

# Install dependencies from pyproject.toml (including PyInstaller)
poetry install

# Simple PyInstaller build command for Flet app
poetry run pyinstaller main.py --onefile --name $PROJECT_NAME --noconfirm

# Move
chmod +x decyphertek.ai

# Clean up
rm -rf build .build .venv poetry.lock __pycache__ decyphertek.ai.spec

# Can we add this model to the APP? Lets see what sonnet can achieve. 
# anthropic/claude-sonnet-4.5