FROM mcr.microsoft.com/devcontainers/python:1-3.13-bullseye

COPY requirements.txt ./

RUN pip install uv && uv venv

RUN uv pip install -r requirements.txt
