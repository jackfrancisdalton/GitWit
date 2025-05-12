#!/bin/bash


VENV_PATH="$PWD/.venv/bin/activate"
if [ -f "$VENV_PATH" ]; then
  # echo "Activating UV venv at $VENV_PATH"
  # shellcheck disable=SC1090
  source "$VENV_PATH"
else
  echo "⚠️  No UV venv found at $VENV_PATH.  Run 'uv venv' first."
fi

# Mocks installing the package to CLI for easier development, allowing devs to simply enter gitwit
echo "alias gitwit='python -m gitwit.cli'" >> ~/.bashrc
