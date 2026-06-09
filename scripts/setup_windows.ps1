$ErrorActionPreference = "Ignore"

$versions = @("3.12", "3.11")

$selected = $null

foreach ($v in $versions) {
    py -$v -c "pass" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $selected = $v
        break
    }
}

if (-not $selected) {
    throw "Python 3.11+ or 3.12+ required."
}

$ErrorActionPreference = "Stop"

py -$selected -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

Write-Host "Setup complete. Activate with: .\.venv\Scripts\Activate.ps1"
Write-Host "Run with: .\scripts\run_windows.ps1"
