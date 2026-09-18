#!/usr/bin/env bash
set -e

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3.11 or newer is required." >&2
    exit 1
fi

if ! python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'; then
    echo "Error: Python 3.11 or newer is required (found $(python3 --version 2>&1))." >&2
    exit 1
fi

if ! python3 -c 'import ensurepip' >/dev/null 2>&1; then
    cat >&2 <<'EOF'
Error: Python's venv support is not installed.

On Debian/Ubuntu, install it with:
  sudo apt install python3-venv

Some releases use a versioned package instead, for example:
  sudo apt install python3.12-venv

Then run this script again.
EOF
    exit 1
fi

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

echo "Setup complete. Activate with: source .venv/bin/activate"
echo "Run with: ./scripts/run_linux.sh"
