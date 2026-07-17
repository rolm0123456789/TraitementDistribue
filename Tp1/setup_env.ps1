# setup_env.ps1
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

Write-Host "=== Configuration de l'environnement (Windows) ===" -ForegroundColor Cyan

$VenvDir = ".venv"

if (-not (Test-Path $VenvDir)) {
    Write-Host "Création de l'environnement virtuel ($VenvDir)..."
    python -m venv $VenvDir
} else {
    Write-Host "Environnement virtuel déjà présent ($VenvDir)."
}

$PythonVenv = "$VenvDir\Scripts\python.exe"
if (Test-Path $PythonVenv) {
    Write-Host "Installation / Mise à jour de rpyc..."
    & $PythonVenv -m pip install --upgrade pip
    & $PythonVenv -m pip install rpyc
} else {
    Write-Error "Impossible de trouver l'exécutable Python dans le venv."
    exit 1
}

Write-Host ""
Write-Host "Installation et configuration terminées avec succès !" -ForegroundColor Green
Write-Host ""
Write-Host "Pour activer l'environnement manuellement :"
Write-Host "  .venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "Les scripts start_slaves*.ps1 utiliseront automatiquement le venv local."
