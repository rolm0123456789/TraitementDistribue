# start_slaves6.ps1
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

# Nettoyage du port 18812
$conn = Get-NetTCPConnection -LocalPort 18812 -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

$PythonPath = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

Write-Host "[PS] Démarrage du Master V6..."
$Master = Start-Process cmd -ArgumentList "/c title MASTER V6 (COLLECTIVE DEATH) & `"$PythonPath`" 6_master.py" -PassThru
Start-Sleep -Seconds 2

if ($Master.HasExited) {
    Write-Host "[PS] Le Master n'a pas démarré. Abandon." -ForegroundColor Red
    exit 1
}

Write-Host "[PS] Lancement des 6 esclaves..."
$Slaves = @{}
for ($i = 1; $i -le 6; $i++) {
    $proc = Start-Process powershell -ArgumentList "-WindowStyle Hidden -NoExit -Command & `"$PythonPath`" 6_slave.py $i" -PassThru
    $Slaves[$i] = $proc
}

Write-Host "[PS] Attente que les esclaves prennent des tâches..."
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "[PS] EXTERMINATION : tous les esclaves vont être tués (SIGKILL)..." -ForegroundColor Magenta
Write-Host ""

for ($i = 1; $i -le 6; $i++) {
    $proc = $Slaves[$i]
    if ($proc -and -not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        Write-Host "[PS] LE SLAVE $i (PID $($proc.Id)) A ÉTÉ CRASHÉ BRUTALEMENT !" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "[PS] Tous les slaves ont été tués."
Write-Host "[PS] Le Master doit détecter la mort collective et s'arrêter proprement..."
Write-Host "[PS] Attente de l'arrêt du Master (max 15s)..."

# Port checks to see if master closed
$MasterStopped = $false
for ($sec = 1; $sec -le 15; $sec++) {
    $conn = Get-NetTCPConnection -LocalPort 18812 -State Listen -ErrorAction SilentlyContinue
    if (-not $conn) {
        Write-Host ""
        Write-Host "[PS] SUCCÈS : le Master s'est arrêté proprement après ~${sec}s." -ForegroundColor Green
        $MasterStopped = $true
        break
    }
    Start-Sleep -Seconds 1
}

if (-not $MasterStopped) {
    Write-Host ""
    Write-Host "[PS] ÉCHEC : le Master tourne encore après 15s." -ForegroundColor Red
    Write-Host "[PS] Arrêt forcé du Master pour nettoyer..."
    if ($Master -and -not $Master.HasExited) {
        Stop-Process -Id $Master.Id -Force -ErrorAction SilentlyContinue
    }
    # Nettoyage par port
    $conn = Get-NetTCPConnection -LocalPort 18812 -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

$Slaves.Values | Stop-Process -Force -ErrorAction SilentlyContinue
