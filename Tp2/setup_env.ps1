# setup_env.ps1 (Tp2)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

Write-Host "=== TP2 — Hachage à grande échelle ===" -ForegroundColor Cyan
Write-Host ""

$VenvDir = ".venv"

if (-not (Test-Path $VenvDir)) {
    Write-Host "Création de l'environnement virtuel ($VenvDir)..."
    python -m venv $VenvDir
} else {
    Write-Host "Environnement virtuel déjà présent ($VenvDir)."
}

Write-Host "Aucune dépendance externe requise (utilisation de hashlib, bisect, collections)."
Write-Host ""

# Menu
Write-Host "Que souhaitez-vous lancer ?" -ForegroundColor Green
Write-Host "  1) Étape 1 — Hash naïf (h % N)"
Write-Host "  2) Étape 2 — Rehash (N → N+1)"
Write-Host "  3) Étape 3 — Anneau cohérent"
Write-Host "  4) Étape 4 — Nœuds virtuels"
Write-Host "  a) Toutes les étapes"
Write-Host "  q) Quitter"
Write-Host ""

$choix = Read-Host "Choix [a]"
if ([string]::IsNullOrEmpty($choix)) { $choix = "a" }

$PythonPath = "$VenvDir\Scripts\python.exe"
if (-not (Test-Path $PythonPath)) { $PythonPath = "python" }

switch ($choix) {
    "1" { & $PythonPath etape1_hash_naif.py }
    "2" { & $PythonPath etape2_rehash.py }
    "3" { & $PythonPath etape3_anneau.py }
    "4" { & $PythonPath etape4_vnodes.py }
    "a" {
        Write-Host "## Étape 1 ##" -ForegroundColor Yellow
        & $PythonPath etape1_hash_naif.py
        Write-Host "## Étape 2 ##" -ForegroundColor Yellow
        & $PythonPath etape2_rehash.py
        Write-Host "## Étape 3 ##" -ForegroundColor Yellow
        & $PythonPath etape3_anneau.py
        Write-Host "## Étape 4 ##" -ForegroundColor Yellow
        & $PythonPath etape4_vnodes.py
    }
    "q" { Write-Host "Au revoir!" }
    Default { Write-Host "Choix invalide." }
}
