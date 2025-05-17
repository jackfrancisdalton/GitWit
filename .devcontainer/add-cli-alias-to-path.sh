#!/bin/bash

# Add venv to path as the command will fail without packages stored in the venv 
echo 'export PATH="$PWD/.venv/bin:$PATH"' >> ~/.bashrc

# Mocks installing the package to CLI for easier development, allowing devs to simply enter gitwit
echo "alias gitwit='python -m gitwit'" >> ~/.bashrc