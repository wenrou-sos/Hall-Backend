# -*- coding: utf-8 -*-
"""为6个捕鱼变体构建 webpack publish（复用00001 node_modules junction）。"""
import os, sys, io, subprocess, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
FISH_NM = r'D:\fish_frontend\srv\svn\game\PSF-ON-00001\trunk\node_modules'
PSF = ['PSF-ON-00002', 'PSF-ON-00003', 'PSF-ON-00004', 'PSF-ON-00005', 'PSF-ON-00006', 'PSF-ON-00007']
env = dict(os.environ)
env['NODE_OPTIONS'] = '--openssl-legacy-provider'
for gid in PSF:
    trunk = os.path.join(r'D:\games_wc', gid, 'trunk')
    nm = os.path.join(trunk, 'node_modules')
    if not os.path.exists(nm):
        subprocess.run(['cmd', '/c', 'mklink', '/J', nm, FISH_NM], capture_output=True)
    t0 = time.time()
    r = subprocess.run(['cmd', '/c', 'npx', 'webpack', '--config', 'webpack.dev.js'],
                       cwd=trunk, env=env, capture_output=True, text=True, errors='replace')
    ok = r.returncode == 0
    print(gid, 'webpack exit', r.returncode, 'elapsed', int(time.time() - t0))
    if not ok:
        print((r.stdout or r.stderr)[-800:])
        continue
    exe = os.path.join(trunk, 'tools', 'replace_atlas_plist.exe')
    if os.path.exists(exe):
        subprocess.run([exe, os.path.join(trunk, 'publish', 'assets')], cwd=trunk, capture_output=True)
    print(gid, 'publish files:', len(os.listdir(os.path.join(trunk, 'publish'))))
print('VARIANTS_BUILD_DONE')