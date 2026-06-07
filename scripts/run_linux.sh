#!/usr/bin/env bash
set -e

source .venv/bin/activate
PYTHONPATH="src"  python -m cops_and_robbers.main
