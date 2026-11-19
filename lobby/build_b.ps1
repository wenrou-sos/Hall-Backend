param([string]$name, [string]$tags = "dev")
$WS = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)  # .../Default (fish/lobby -> fish -> Default)
$env:GOROOT = "$WS\fish\tools\go"
$env:PATH = "$env:GOROOT\bin;$env:PATH"
$env:GOPATH = "$WS\fish\gopath"
$env:GOCACHE = "$WS\fish\gocache"
$env:GOPROXY = "https://goproxy.cn,direct"
$env:GOSUMDB = "off"
$env:GO111MODULE = "on"
$env:GOPRIVATE = "gitlab.iplaystar.net"
$env:GOFLAGS = "-mod=mod"
$env:LOCALAPPDATA = "$WS\fish\localappdata"
Set-Location "$WS\fish\cards\$name"
go build -tags $tags -o app.exe .
exit $LASTEXITCODE