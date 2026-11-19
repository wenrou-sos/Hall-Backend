# 下载并安装 C++ slot 构建所需工具: svn(SlikSVN) / CMake / VS BuildTools(MSVC)
$ErrorActionPreference = 'Continue'
$tools = 'D:\cpp_tools'
New-Item -ItemType Directory -Force -Path $tools | Out-Null
$log = "$tools\setup.log"
function L($m){ Add-Content -Path $log -Value ("{0} {1}" -f (Get-Date -Format 'HH:mm:ss'), $m) }

L "start"
# 1) SlikSVN (svn CLI)
if (-not (Test-Path "$tools\svn\bin\svn.exe")) {
  L "download sliksvn"
  curl.exe -sSL --retry 3 -o "$tools\sliksvn.zip" 'https://sliksvn.com/pub/Slik-Subversion-1.14.5-x64.zip'
  if ((Get-Item "$tools\sliksvn.zip" -ErrorAction SilentlyContinue).Length -gt 1000000) {
    Expand-Archive -Path "$tools\sliksvn.zip" -DestinationPath "$tools\svn_tmp" -Force
    $bin = Get-ChildItem "$tools\svn_tmp" -Recurse -Filter 'svn.exe' | Select-Object -First 1
    if ($bin) { New-Item -ItemType Directory -Force -Path "$tools\svn\bin" | Out-Null; Copy-Item $bin.Directory.FullName\* "$tools\svn\bin\" -Recurse -Force; L "svn ok" }
  } else { L "sliksvn download failed" }
}
# 2) CMake
if (-not (Test-Path "$tools\cmake\bin\cmake.exe")) {
  L "download cmake"
  curl.exe -sSL --retry 3 -o "$tools\cmake.zip" 'https://github.com/Kitware/CMake/releases/download/v3.28.3/cmake-3.28.3-windows-x86_64.zip'
  if ((Get-Item "$tools\cmake.zip" -ErrorAction SilentlyContinue).Length -lt 1000000) {
    curl.exe -sSL --retry 3 -o "$tools\cmake.zip" 'https://cmake.org/files/v3.28/cmake-3.28.3-windows-x86_64.zip'
  }
  if ((Get-Item "$tools\cmake.zip" -ErrorAction SilentlyContinue).Length -gt 1000000) {
    Expand-Archive -Path "$tools\cmake.zip" -DestinationPath "$tools\cmake_tmp" -Force
    $d = Get-ChildItem "$tools\cmake_tmp" -Directory | Select-Object -First 1
    Move-Item $d.FullName "$tools\cmake" -Force; L "cmake ok"
  } else { L "cmake download failed" }
}
# 3) VS BuildTools (MSVC) silent
if (-not (Test-Path "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC")) {
  L "download vs_buildtools"
  curl.exe -sSL --retry 3 -o "$tools\vs_buildtools.exe" 'https://aka.ms/vs/17/release/vs_buildtools.exe'
  if ((Get-Item "$tools\vs_buildtools.exe" -ErrorAction SilentlyContinue).Length -gt 1000000) {
    L "install vs_buildtools (silent, may take long)"
    Start-Process -FilePath "$tools\vs_buildtools.exe" -ArgumentList '--quiet','--wait','--norestart','--nocache','--add','Microsoft.VisualStudio.Workload.VCTools','--includeRecommended' -Wait
    L "vs_buildtools install exit"
  } else { L "vs_buildtools download failed" }
}
L "SETUP_DONE"