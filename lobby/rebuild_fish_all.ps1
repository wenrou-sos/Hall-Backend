# 重构建 fish00001 + 6 变体 (语言补丁生效)
$env:NODE_OPTIONS = '--openssl-legacy-provider'
$log = 'D:\fish_frontend\rebuild_all.log'
function L($m){ Add-Content -Path $log -Value ("{0} {1}" -f (Get-Date -Format 'HH:mm:ss'), $m) }
Set-Location 'D:\fish_frontend\srv\svn\game\PSF-ON-00001\trunk'
npx webpack --config webpack.dev.js 2>&1 | Out-Null
L "fish00001 webpack exit $LASTEXITCODE"
.\tools\replace_atlas_plist.exe .\publish\assets 2>&1 | Out-Null
L "fish00001 atlas done"
python (Join-Path $PSScriptRoot 'build_variants.py') 2>&1 | ForEach-Object { L $_ }
L "FISH_REBUILD_ALL_DONE"