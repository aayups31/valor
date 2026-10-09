from pathlib import Path
import shutil
import subprocess

import pytest


def test_launcher_creation_identity_is_invariant_across_cultures(tmp_path):
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if not shell:
        pytest.skip("PowerShell is needed for Windows launcher regression")
    helper = (Path(__file__).parents[1]/"scripts/Valor-LauncherSupport.ps1").resolve()
    # A controlled repository path, escaped for a literal PowerShell string.
    escaped = str(helper).replace("'", "''")
    script = tmp_path/"launcher-time-check.ps1"
    script.write_text(". '"+escaped+"'\n"+r'''
$ErrorActionPreference = 'Stop'
$valorTimestamp = '2026-10-09T06:00:19.7333830Z'
$valorExpected = [DateTime]::new(2026,10,9,6,0,19,[DateTimeKind]::Utc).AddTicks(7333830)
foreach ($valorCulture in @('en-US','en-GB','fr-FR')) {
    [Threading.Thread]::CurrentThread.CurrentCulture = [Globalization.CultureInfo]::new($valorCulture)
    $valorJson = ('{"created_at_utc":"'+$valorTimestamp+'"}') | ConvertFrom-Json
    foreach ($valorValue in @($valorTimestamp, $valorJson.created_at_utc, [DateTimeOffset]::new($valorExpected))) {
        $valorResult = Get-ValorRecordedCreationUtc $valorValue
        if ($valorResult -ne $valorExpected -or $valorResult.Kind -ne [DateTimeKind]::Utc) {
            throw "Creation identity failed for $valorCulture"
        }
    }
}
$valorRejected = $false
try { Get-ValorRecordedCreationUtc '09/10/2026' | Out-Null } catch { $valorRejected = $true }
if (-not $valorRejected) { throw 'Ambiguous timestamp was accepted' }
Write-Output 'Invariant creation identity passed; ambiguous input rejected.'
''', encoding="utf-8-sig")
    result = subprocess.run([shell,"-NoProfile","-File",str(script)],text=True,capture_output=True,timeout=20)
    assert result.returncode == 0, result.stdout+result.stderr
