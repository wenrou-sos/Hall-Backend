# 提取 ps-scm 中 slot externals 裸库并 svn checkout 到 D:\slot_src 对应目录
$svn = 'C:\Program Files\SlikSvn\bin\svn.exe'
$log = 'D:\slot_src\externals.log'
function L($m){ Add-Content -Path $log -Value ("{0} {1}" -f (Get-Date -Format 'HH:mm:ss'), $m) }
$map = @(
  @{ repo='server/lib-src/protobuf-3.0.0-beta-1'; dst='lib\protobuf-3.0.0-beta-1' },
  @{ repo='server/lib-src/rapidjson-0.11'; dst='lib\rapidjson-0.11' },
  @{ repo='server/lib-src/gtest-1.7.0'; dst='lib\gtest-1.7.0' },
  @{ repo='server/lib-src/glog-0.4.0'; dst='lib\glog-0.4.0' },
  @{ repo='server/lib-bin/poco-1.6.0'; dst='lib\poco-1.6.0' },
  @{ repo='server/lib-src/snappy-1.1.8'; dst='lib\snappy-1.1.8' },
  @{ repo='server/lib-data/ps-challenge'; dst='res\ps-challenge' },
  @{ repo='server/lib-data/math-data'; dst='res\math-data' },
  @{ repo='server/lib-data/ssl-cert'; dst='res\ssl-cert' },
  @{ repo='server/lib-src/rng'; dst='src\rng' },
  @{ repo='server/lib-src/utility'; dst='src\utility' },
  @{ repo='server/lib-src/math'; dst='src\math' },
  @{ repo='server/lib-src/math-proto'; dst='src\math-proto' },
  @{ repo='server/lib-src/mps-math'; dst='src\mps-math' },
  @{ repo='server/lib-src/arcade'; dst='src\arcade' },
  @{ repo='server/lib-src/arcade-proto'; dst='src\arcade-proto' }
)
foreach ($m in $map) {
  $name = $m.repo.Split('/')[-1]
  $bare = "D:\pscm_repos\$name"
  if (-not (Test-Path "$bare\db")) {
    L "extract $name"
    python (Join-Path $PSScriptRoot 'pscm_extract.py') "ps-scm/repositories/svn/$($m.repo)/" $bare | Out-Null
  }
  $target = "D:\slot_src\$($m.dst)"
  if (-not (Test-Path $target)) {
    L "checkout $name -> $($m.dst)"
    & $svn checkout "file:///D:/pscm_repos/$name/trunk" $target --quiet 2>&1 | Out-Null
    L "checkout exit $LASTEXITCODE"
  }
}
L "EXTERNALS_DONE"