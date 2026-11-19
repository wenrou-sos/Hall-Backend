param([string]$name)
$WS = 'C:\Users\Administrator\AppData\Roaming\AutoClaw-official\accounts\1107e92c0256cf69b2d4deb68f986701a1d7d6a662a340520e9e1f9182371db8\projects\Default'
$env:GOROOT = "$WS\fish\tools\go"
$env:PATH = "$env:GOROOT\bin;$env:PATH"
$env:GOPATH = "$WS\fish\gopath"
$env:GOCACHE = "$WS\fish\gocache"
$env:GOPROXY = 'https://goproxy.cn,direct'
$env:GOSUMDB = 'off'
$env:GO111MODULE = 'on'
$env:GOPRIVATE = 'gitlab.iplaystar.net'
$env:GOFLAGS = '-mod=mod'
$env:LOCALAPPDATA = "$WS\fish\localappdata"
Set-Location "$WS\fish\cards\$name"
New-Item -ItemType Directory -Force -Path dist | Out-Null
Write-Output "BUILD_START $name $(Get-Date -Format o)"
go build -tags dev -o dist\app.exe . 2>&1 | ForEach-Object { "$_" }
Write-Output "BUILD_RC $name $LASTEXITCODE"