# start_slaves2.ps1
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

# Nettoyage du port 18812
$conn = Get-NetTCPConnection -LocalPort 18812 -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

$PythonPath = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

Write-Host "[PS] Lancement des esclaves en arrière-plan (attente de 2s)..."
$Jobs = @()
for ($i = 1; $i -le 6; $i++) {
    $Jobs += Start-Job -ScriptBlock {
        param($py, $id, $dir)
        Set-Location $dir
        Start-Sleep -Seconds 2  # Attendre le démarrage du Master
        & $py 2_slave.py $id
    } -ArgumentList $PythonPath, $i, $ScriptDir
}

Write-Host "[PS] Lancement du Master..."
& $PythonPath 2_master.py

# Nettoyage
$Jobs | Stop-Job | Out-Null
$Jobs | Remove-Job -Force | Out-Null
