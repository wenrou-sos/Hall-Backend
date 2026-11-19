# 重编译+重启四个棋牌服务端 (52/u4/colorgame/fishshrimpcrab)
$root = (Resolve-Path '.\fish').Path
$env:GOROOT = "$root\tools\go"; $env:PATH = "$env:GOROOT\bin;$env:PATH"
$env:GOPATH = "$root\gopath"; $env:GOCACHE = "$root\gocache"
$env:GOPROXY = 'https://goproxy.cn,direct'; $env:GOSUMDB = 'off'
$env:GO111MODULE = 'on'; $env:GOPRIVATE = 'gitlab.iplaystar.net'; $env:GOFLAGS = '-mod=mod'
$env:LOCALAPPDATA = "$root\localappdata"
$log = "$root\lobby\cards_rebuild.log"
function L($m){ Add-Content -Path $log -Value ("{0} {1}" -f (Get-Date -Format 'HH:mm:ss'), $m) }
$jobs = @(
  @{ dir='89-game-server'; port=8901; name='pokdeng-dev' },
  @{ dir='paikang52'; port=8911; name='52-dev' },
  @{ dir='u-game-server'; port=8914; name='u4-dev' },
  @{ dir='colorgame'; port=8916; name='colorgame-dev' },
  @{ dir='fishshrimpcrab'; port=8912; name='fsc-dev' }
)
foreach ($j in $jobs) {
  $d = "$root\cards\$($j.dir)"
  Set-Location $d
  $out = & go build -tags dev -o dist\app.exe . 2>&1
  L "$($j.dir) build exit $LASTEXITCODE"
  if ($LASTEXITCODE -ne 0) { L ($out | Select-Object -Last 3 | Out-String); continue }
  $p = Get-NetTCPConnection -LocalPort $j.port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess
  if ($p) { Stop-Process -Id $p -Force; Start-Sleep -Seconds 1 }
  $env:HTTP_PORT = "$($j.port)"; $env:SERVER_NAME = $j.name; $env:LOG_LEVEL='0'; $env:POOL_SIZE='100'; $env:CHAN_SIZE='102400'; $env:VERSION='dev'
  Start-Process -FilePath "$d\dist\app.exe" -WorkingDirectory $d -RedirectStandardOutput "$root\lobby\$($j.dir).out.log" -RedirectStandardError "$root\lobby\$($j.dir).err.log" -NoNewWindow
  L "$($j.dir) restarted on $($j.port)"
}
L "CARDS_REBUILD_DONE"