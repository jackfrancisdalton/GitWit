#!/bin/bash

# Mocks installing the package to CLI for easier development, allowing devs to simply enter gitwit
echo "alias gitwit='python -m gitwit.cli.cli'" >> ~/.bashrc
