param([Parameter(ValueFromRemainingArguments=$true)][string[]]$RoutingArgs)
$ErrorActionPreference = 'Stop'
$python = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' } else { 'python' }
$prefix = if ($python -eq 'py') { @('-3') } else { @() }
$scriptPath = Join-Path $PSScriptRoot 'office-os/routing-tools/routing_manager.py'
if ($env:OFFICE_OS_DEBUG) {
  Write-Host "DEBUG python resolved to: $((Get-Command $python).Source)"
  Write-Host "DEBUG scriptPath: $scriptPath exists: $(Test-Path $scriptPath)"
  Write-Host "DEBUG args: install $RoutingArgs"
}
$outFile = [System.IO.Path]::GetTempFileName()
$errFile = [System.IO.Path]::GetTempFileName()
$proc = Start-Process -FilePath $python -ArgumentList (@($prefix) + @($scriptPath, 'install') + $RoutingArgs) -NoNewWindow -Wait -PassThru -RedirectStandardOutput $outFile -RedirectStandardError $errFile
Get-Content $outFile | Write-Host
Get-Content $errFile | Write-Host
$exitCode = $proc.ExitCode
Remove-Item $outFile, $errFile -ErrorAction SilentlyContinue
exit $exitCode
