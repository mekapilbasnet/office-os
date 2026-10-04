param([Parameter(ValueFromRemainingArguments=$true)][string[]]$RoutingArgs)
$ErrorActionPreference = 'Stop'
$python = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' } else { 'python' }
$prefix = if ($python -eq 'py') { @('-3') } else { @() }
& $python @prefix (Join-Path $PSScriptRoot 'office-os/routing-tools/routing_manager.py') install @RoutingArgs
exit $LASTEXITCODE
