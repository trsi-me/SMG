#Requires -Version 5.1
# One script: Flutter Web -> backend/static/web (Render-ready) + optional full Python venv.
#   .\Build-ForRender.ps1              # venv, pip, model if missing, flutter web, copy
#   .\Build-ForRender.ps1 -WebOnly     # flutter web + copy only (fast)
#   .\Build-ForRender.ps1 -StartServer # full build then FastAPI on :8000

param(
    [switch]$WebOnly,
    [switch]$StartServer
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

function Test-Cmd {
    param([string]$Name)
    [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-VenvPython {
    Join-Path $Root ".venv\Scripts\python.exe"
}

Write-Host "==> SMG root: $Root" -ForegroundColor Cyan

if (-not (Test-Cmd "flutter")) {
    Write-Error "Flutter not in PATH. Install Flutter and run: flutter config --enable-web"
}

$webOut = Join-Path $Root "mobile\smg_app\build\web"
$staticTarget = Join-Path $Root "backend\static\web"

if (-not $WebOnly) {
    if (-not (Test-Cmd "python")) {
        Write-Error "Python not in PATH (or use -WebOnly for Flutter web only)."
    }

    $sysDrive = (Get-Item $Root).PSDrive.Name
    $freeGB = [math]::Round((Get-PSDrive $sysDrive).Free / 1GB, 2)
    Write-Host "==> Free space on drive ${sysDrive}: ${freeGB} GB" -ForegroundColor Yellow

    $venvPy = Get-VenvPython
    if (-not (Test-Path $venvPy)) {
        Write-Host "==> Creating .venv" -ForegroundColor Cyan
        python -m venv (Join-Path $Root ".venv")
    }

    Write-Host "==> pip install backend (no-cache-dir)" -ForegroundColor Cyan
    & $venvPy -m pip install --upgrade pip
    & $venvPy -m pip install --no-cache-dir -r (Join-Path $Root "backend\requirements.txt")

    $modelPath = Join-Path $Root "ml\models\efficientnet_b4_v1.pt"
    if (-not (Test-Path $modelPath)) {
        Write-Host "==> create_default_model.py" -ForegroundColor Cyan
        & $venvPy (Join-Path $Root "create_default_model.py")
    }
}

Write-Host "==> Flutter: pub get + build web --release" -ForegroundColor Cyan
$appDir = Join-Path $Root "mobile\smg_app"
Push-Location $appDir
try {
    flutter pub get
    flutter build web --release
}
finally {
    Pop-Location
}

if (-not (Test-Path $webOut)) {
    Write-Error "build/web missing. Check flutter build errors."
}

Write-Host "==> Copy web -> backend\static\web (this folder is what Render serves with FastAPI)" -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $staticTarget | Out-Null
Get-ChildItem -Path $staticTarget -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Copy-Item -Path (Join-Path $webOut "*") -Destination $staticTarget -Recurse -Force

Write-Host "==> Done. Web bundle: $staticTarget" -ForegroundColor Green
Write-Host "==> Before Render: git add backend/static/web ; if model is missing on server, git add -f ml/models/efficientnet_b4_v1.pt" -ForegroundColor Yellow

if ($StartServer) {
    if ($WebOnly) {
        Write-Warning "-StartServer ignored with -WebOnly (no venv Python). Run without -WebOnly or run: cd backend; python main.py"
        exit 0
    }
    $venvPy = Get-VenvPython
    Write-Host "==> FastAPI http://localhost:8000" -ForegroundColor Green
    $env:PORT = "8000"
    $env:SERVER_HOST = "0.0.0.0"
    Set-Location (Join-Path $Root "backend")
    & $venvPy main.py
}
