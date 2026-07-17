# start_slaves3.ps1
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

# Nettoyage du port 18812
$conn = Get-NetTCPConnection -LocalPort 18812 -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

$PythonPath = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

Write-Host "[PS] Démarrage du Master dans une nouvelle fenêtre..."
Start-Process cmd -ArgumentList "/c title MASTER V1 (NO RESILIENCE) & `"$PythonPath`" 2_master.py" -PassThru | Out-Null
Start-Sleep -Seconds 2

Write-Host "[PS] Lancement du Slave 1 (va être crashé)..."
$Slave1 = Start-Process powershell -ArgumentList "-WindowStyle Hidden -NoExit -Command & `"$PythonPath`" 2_slave.py 1" -PassThru

Write-Host "[PS] Lancement des autres esclaves..."
$Slaves = @()
for ($i = 2; $i -le 6; $i++) {
    $Slaves += Start-Process powershell -ArgumentList "-WindowStyle Hidden -NoExit -Command & `"$PythonPath`" 2_slave.py $i" -PassThru
}

Start-Sleep -Seconds 1

Write-Host ""
Write-Host "[PS] LE SLAVE 1 A ÉTÉ CRASHÉ BRUTALEMENT (SIGKILL) !" -ForegroundColor Red
Stop-Process -Id $Slave1.Id -Force -ErrorAction SilentlyContinue
Write-Host ""

# Attendre que le Master s'arrête ou que l'utilisateur appuie sur Entrée
Write-Host "[PS] Appuyez sur Entrée pour nettoyer les esclaves restants et fermer..."
Read-Host

$Slaves | Stop-Process -Force -ErrorAction SilentlyContinue
