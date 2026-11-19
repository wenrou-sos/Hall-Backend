# CMake 配置+编译 slot C++ 服务端 (MSVC Win32)
$cmake = 'D:\cpp_tools\cmake\bin\cmake.exe'
$log = 'D:\slot_build\build.log'
New-Item -ItemType Directory -Force -Path 'D:\slot_build' | Out-Null
function L($m){ Add-Content -Path $log -Value ("{0} {1}" -f (Get-Date -Format 'HH:mm:ss'), $m) }
L "configure start"
& $cmake -S 'D:\slot_src' -B 'D:\slot_build' -G 'Visual Studio 17 2022' -A Win32 2>&1 | ForEach-Object { L $_ }
L "configure exit $LASTEXITCODE"
if ($LASTEXITCODE -eq 0) {
  L "build start"
  & $cmake --build 'D:\slot_build' --config Release -- /m /verbosity:minimal 2>&1 | ForEach-Object { L $_ }
  L "build exit $LASTEXITCODE"
}
L "SLOT_BUILD_DONE"