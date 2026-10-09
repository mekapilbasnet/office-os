param([Parameter(ValueFromRemainingArguments=$true)][string[]]$RoutingArgs)
$ErrorActionPreference = 'Stop'
if (Get-Command py -ErrorAction SilentlyContinue) {
  $python = 'py'; $prefix = @('-3')
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  $python = 'python'; $prefix = @()
} else {
  [Console]::Error.WriteLine('ERROR: Python 3.8 or newer was not found (tried py and python). Install it from https://www.python.org/downloads/ and rerun.')
  exit 1
}
$scriptPath = Join-Path $PSScriptRoot 'office-os/routing-tools/routing_manager.py'
if ($env:OFFICE_OS_DEBUG) {
  Write-Host "DEBUG python resolved to: $((Get-Command $python).Source)"
  Write-Host "DEBUG scriptPath: $scriptPath exists: $(Test-Path $scriptPath)"
  Write-Host "DEBUG args: install $RoutingArgs"
}
& $python @prefix $scriptPath install @RoutingArgs
exit $LASTEXITCODE
