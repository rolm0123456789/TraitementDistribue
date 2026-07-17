# start_slaves4.ps1
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

# Nettoyage du port 18812
$conn = Get-NetTCPConnection -LocalPort 18812 -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

$PythonPath = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

Write-Host "[PS] Démarrage du Master V2 (Resilient)..."
Start-Process cmd -ArgumentList "/c title MASTER V2 (RESILIENT) & `"$PythonPath`" 4_master.py" -PassThru | Out-Null
Start-Sleep -Seconds 2

Write-Host "[PS] Lancement des 6 esclaves..."
$Slaves = @{}
for ($i = 1; $i -le 6; $i++) {
    $proc = Start-Process powershell -ArgumentList "-WindowStyle Hidden -NoExit -Command & `"$PythonPath`" 4_slave.py $i" -PassThru
    $Slaves[$i] = $proc
}

Start-Sleep -Milliseconds 1500

# Choix de tuer entre 1 et 3 esclaves
$NbToKill = Get-Random -Minimum 1 -Maximum 4
$ShuffledIds = 1..6 | Get-Random -Count 6

Write-Host ""
Write-Host "[PS] Lancement de la roulette russe : Décision de tuer $NbToKill esclave(s)..." -ForegroundColor Yellow

for ($i = 0; $i -lt $NbToKill; $i++) {
    $id = $ShuffledIds[$i]
    $proc = $Slaves[$id]
    if ($proc -and -not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        Write-Host "[PS] LE SLAVE $id (PID $($proc.Id)) A ÉTÉ CRASHÉ BRUTALEMENT !" -ForegroundColor Red
    }
}
Write-Host ""

Write-Host "[PS] Appuyez sur Entrée pour nettoyer et fermer..."
Read-Host

$Slaves.Values | Stop-Process -Force -ErrorAction SilentlyContinue
