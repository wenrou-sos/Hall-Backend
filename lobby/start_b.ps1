param([string]$name, [int]$port)
$WS = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$env:HTTP_PORT = "$port"
$env:SERVER_NAME = "$name-dev"
$env:LOG_LEVEL = "0"
$env:POOL_SIZE = "100"
$env:CHAN_SIZE = "102400"
$env:VERSION = "dev"
$dir = "$WS\fish\cards\$name"
Start-Process -FilePath "$dir\app.exe" -WorkingDirectory $dir -RedirectStandardOutput "$WS\fish\lobby\$name.out.log" -RedirectStandardError "$WS\fish\lobby\$name.err.log" -WindowStyle Hidden
Write-Host "started $name on $port"