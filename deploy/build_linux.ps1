# 交叉编译 Linux amd64 服务端 (CGO off)
$root = (Resolve-Path '.\fish').Path
$env:GOROOT = "$root\tools\go"; $env:PATH = "$env:GOROOT\bin;$env:PATH"
$env:GOPATH = "$root\gopath"; $env:GOCACHE = "$root\gocache"
$env:GOPROXY = 'https://goproxy.cn,direct'; $env:GOSUMDB = 'off'
$env:GO111MODULE = 'on'; $env:GOPRIVATE = 'gitlab.iplaystar.net'; $env:GOFLAGS = '-mod=mod'
$env:LOCALAPPDATA = "$root\localappdata"
$env:GOOS = 'linux'; $env:GOARCH = 'amd64'; $env:CGO_ENABLED = '0'
$log = "$root\deploy\linux_build.log"
function L($m){ Add-Content -Path $log -Value ("{0} {1}" -f (Get-Date -Format 'HH:mm:ss'), $m) }
$jobs = @(
  @{ dir='Fish-Game-Server'; out='fish' },
  @{ dir='cards\89-game-server'; out='card89' },
  @{ dir='cards\paikang52'; out='card52' },
  @{ dir='cards\u-game-server'; out='cardu4' },
  @{ dir='cards\colorgame'; out='cardcg' },
  @{ dir='cards\fishshrimpcrab'; out='cardfsc' }
)
New-Item -ItemType Directory -Force -Path "$root\deploy\bin" | Out-Null
foreach ($j in $jobs) {
  Set-Location "$root\$($j.dir)"
  $out = & go build -tags dev -o "$root\deploy\bin\$($j.out)" . 2>&1
  L "$($j.out) build exit $LASTEXITCODE"
  if ($LASTEXITCODE -ne 0) { L ($out | Select-Object -Last 3 | Out-String) }
}
L "LINUX_BUILD_DONE"