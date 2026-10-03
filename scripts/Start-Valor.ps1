param(
    [switch]$NoBrowser,
    [switch]$Stop,
    [ValidateRange(1024, 65535)][int]$Port = 8765
)

$ErrorActionPreference = 'Stop'
$projectDirectory = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runtimePython = Join-Path $projectDirectory '.venv\Scripts\python.exe'
$artifactDirectory = Join-Path $projectDirectory 'artifacts'
$launchRecord = Join-Path $artifactDirectory "demo-launcher-$Port.json"
$demoUrl = "http://127.0.0.1:$Port"
$projectBytes = [System.Text.Encoding]::UTF8.GetBytes($projectDirectory.ToLowerInvariant())
$hashAlgorithm = [System.Security.Cryptography.SHA256]::Create()
$projectHash = [BitConverter]::ToString($hashAlgorithm.ComputeHash($projectBytes)).Replace('-', '').Substring(0, 16)
$hashAlgorithm.Dispose()
$launcherMutex = [System.Threading.Mutex]::new($false, "Local\ValorDemo-$projectHash-$Port")
$mutexHeld = $false

function Get-ValorHealth {
    try {
        $health = Invoke-RestMethod "$demoUrl/api/health" -TimeoutSec 2
        if ($health.application -eq 'valor' -and $health.interface_version -eq 2) { return $health }
    } catch { }
    return $null
}

function Test-DemoRuntime {
    $previousErrorPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $runtimePython -c 'import aace, numpy, gymnasium' 2>$null
        return $LASTEXITCODE -eq 0
    } finally { $ErrorActionPreference = $previousErrorPreference }
}

try {
    try { $mutexHeld = $launcherMutex.WaitOne(10000) }
    catch [System.Threading.AbandonedMutexException] { $mutexHeld = $true }
    if (-not $mutexHeld) { throw 'Another VALOR launcher is still preparing the demo. Wait a moment and try again.' }
    if ($Stop) {
        if (-not (Test-Path -LiteralPath $launchRecord)) {
            Write-Host 'No demo started by this launcher is recorded. Nothing was stopped.'
            exit 0
        }
        $record = Get-Content -LiteralPath $launchRecord -Raw | ConvertFrom-Json
        $ownedProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $([int]$record.process_id)"
        if (-not $ownedProcess) { Write-Host 'VALOR is already closed.'; exit 0 }
        $expectedCommand = '"' + $runtimePython + '" -m aace demo --port ' + $Port
        $expectedCreation = [DateTime]::Parse($record.created_at_utc).ToUniversalTime()
        $actualCreation = $ownedProcess.CreationDate.ToUniversalTime()
        if ($ownedProcess.CommandLine.Trim() -ne $expectedCommand -or
            [Math]::Abs(($actualCreation - $expectedCreation).TotalSeconds) -gt 1) {
            throw 'The recorded process no longer matches this demo. No application was stopped.'
        }
        & taskkill.exe /PID ([int]$record.process_id) /T /F | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'The demo could not be closed. Close its terminal if one is open.' }
        Write-Host 'VALOR is closed. Double-click Start VALOR whenever you want to return.'
        exit 0
    }

    Write-Host 'VALOR'
    Write-Host 'Preparing your local demo...'
    $health = Get-ValorHealth
    if (-not $health) {
        # Refuse to replace another service. The launcher only starts its own local process.
        $portProbe = New-Object System.Net.Sockets.TcpClient
        try {
            $attempt = $portProbe.BeginConnect('127.0.0.1', $Port, $null, $null)
            $connected = $attempt.AsyncWaitHandle.WaitOne(500) -and $portProbe.Connected
        } finally { $portProbe.Dispose() }
        if ($connected) { throw "Another local app is using port $Port. Close that app, or ask for help choosing a different port." }

        if (-not (Test-Path -LiteralPath $runtimePython)) {
            Write-Host 'Setting up VALOR once. This may take a few minutes and needs internet.'
            $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
            $pythonArguments = @('-3')
            if (-not $pythonCommand) {
                $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
                $pythonArguments = @()
            }
            if (-not $pythonCommand) { throw 'Python 3.11 or newer is needed for the first setup. Ask for help installing Python from python.org, then open Start VALOR again.' }
            & $pythonCommand.Source @pythonArguments -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'
            if ($LASTEXITCODE -ne 0) { throw 'The installed Python is too old. Python 3.11 or newer is needed.' }
            & $pythonCommand.Source @pythonArguments -m venv (Join-Path $projectDirectory '.venv')
            if ($LASTEXITCODE -ne 0) { throw 'The local runtime could not be created. The error above explains what failed.' }
        }
        if (-not (Test-DemoRuntime)) {
            Write-Host 'Installing the small local demo runtime. No paid service is used.'
            & $runtimePython -m pip install --disable-pip-version-check -e $projectDirectory
            if ($LASTEXITCODE -ne 0) { throw 'Setup could not finish. Check your internet connection and open Start VALOR again.' }
        }
        New-Item -ItemType Directory -Force -Path $artifactDirectory | Out-Null
        $outputLog = Join-Path $artifactDirectory "demo-$Port.stdout.log"
        $errorLog = Join-Path $artifactDirectory "demo-$Port.stderr.log"
        $serverProcess = Start-Process -WindowStyle Hidden -FilePath $runtimePython `
            -ArgumentList '-m','aace','demo','--port',"$Port" -WorkingDirectory $projectDirectory `
            -RedirectStandardOutput $outputLog -RedirectStandardError $errorLog -PassThru
        $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $($serverProcess.Id)"
        @{process_id=$serverProcess.Id; created_at_utc=$processInfo.CreationDate.ToUniversalTime().ToString('o');
          port=$Port; project_directory=$projectDirectory} | ConvertTo-Json | Set-Content -LiteralPath $launchRecord -Encoding UTF8
        $startupDeadline = [DateTime]::UtcNow.AddSeconds(20)
        do {
            Start-Sleep -Milliseconds 200
            $health = Get-ValorHealth
            if ($serverProcess.HasExited) { throw "VALOR could not start. Details are saved in $errorLog" }
        } while (-not $health -and [DateTime]::UtcNow -lt $startupDeadline)
        if (-not $health) { throw "VALOR took too long to start. Details are saved in $errorLog" }
    }
    Write-Host "Ready: $demoUrl"
    if (-not $NoBrowser) { Start-Process $demoUrl }
    Write-Host 'Press Start the demo on the page. Use Stop VALOR when you are finished.'
} catch {
    Write-Host ''
    Write-Host 'VALOR needs a little help starting.' -ForegroundColor Yellow
    Write-Host $_.Exception.Message
    exit 1
} finally {
    if ($mutexHeld) { $launcherMutex.ReleaseMutex() }
    $launcherMutex.Dispose()
}
