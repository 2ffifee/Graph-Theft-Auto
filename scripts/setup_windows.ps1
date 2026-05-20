$ErrorActionPreference = "Stop"

py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

Write-Host "Setup complete. Activate with: .\.venv\Scripts\Activate.ps1"
Write-Host "Run with: .\scripts\run_windows.ps1"
