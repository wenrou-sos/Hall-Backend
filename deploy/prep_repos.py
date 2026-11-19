# -*- coding: utf-8 -*-
"""准备 Hall-Frontend / Hall-Backend 两个 git 仓库 staging(代码+脚本, 素材走fetch)."""
import os, io, sys, subprocess, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
WS = os.getcwd()
FISH = os.path.join(WS, 'fish')
BE = r'D:\repo_backend'
FE = r'D:\repo_frontend'
def rob(src, dst, xd):
    subprocess.run(['robocopy', src, dst, '/E', '/XD'] + xd + ['/NFL', '/NDL', '/NJH', '/NJS', '/NP'], capture_output=True)
for d in [BE, FE]:
    if os.path.exists(d):
        shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
# backend: Go source + deps + cards + lobby stub/scripts + deploy scripts
XD = ['.git', '.svn', 'dist', 'bin', 'gocache', 'gopath', 'localappdata', 'tools', 'node_modules', '__pycache__', 'sd555-app-lobby']
for sub in ['Fish-Game-Server', 'deps', 'cards', 'lobby', 'deploy']:
    rob(os.path.join(FISH, sub), os.path.join(BE, sub), XD)
# remove big binaries/logs/tars
for dp, dn, fn in os.walk(BE):
    for f in fn:
        if f.endswith(('.exe', '.log', '.tar', '.pdb', '.obj', '.lib', '.dll', '.err', '.out')):
            os.remove(os.path.join(dp, f))
# frontend: lobby client code (no res/.svn/publish)
rob(r'D:\pslobby_wc\trunk', os.path.join(FE, 'lobby'), ['.svn', 'res', 'publish', 'node_modules', '.git'])
print('staged BE/FE')