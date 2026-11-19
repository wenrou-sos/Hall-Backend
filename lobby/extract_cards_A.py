# -*- coding: utf-8 -*-
"""A 组：提取 dummy(199)/paikang52(114)/fishshrimpcrab(126) server bundle 并 clone 到 fish/cards/<name>。"""
import json, hashlib, subprocess, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
ROOT = os.path.dirname(os.path.abspath(__file__))
FISH = os.path.dirname(ROOT)
TAR = r'D:\BaiduNetdiskDownload\1684674626_2023_05_21_13.3.2_gitlab_backup.tar'
BUNDLES = os.path.join(FISH, 'bundles')
FAMILIES = {'dummy': 199, 'paikang52': 114, 'fishshrimpcrab': 126}

def bundle_rel(pid):
    h = hashlib.sha256(str(pid).encode()).hexdigest()
    return 'repositories/@hashed/%s/%s/%s.bundle' % (h[:2], h[2:4], h)

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, (r.stdout or '') + (r.stderr or '')

rels = []
for name, pid in FAMILIES.items():
    rel = bundle_rel(pid)
    if not os.path.exists(os.path.join(BUNDLES, rel.replace('/', os.sep))):
        rels.append(rel)
if rels:
    fl = os.path.join(ROOT, 'cardsA_filelist.txt')
    open(fl, 'w', encoding='utf-8').write('\n'.join(rels))
    code, out = run(['tar', '-xf', TAR, '-C', BUNDLES, '-T', fl])
    print('tar rc', code, out[:500])
for name, pid in FAMILIES.items():
    dest = os.path.join(FISH, 'cards', name)
    b = os.path.join(BUNDLES, bundle_rel(pid).replace('/', os.sep))
    if not os.path.exists(b):
        print('!! bundle missing', name, b); continue
    if not os.path.exists(dest):
        code, out = run(['git', '-c', 'core.longpaths=true', 'clone', '-q', b, dest])
        print('clone', name, 'rc', code, out[:300])
    code, out = run(['git', '-C', dest, 'log', '--oneline', '-1'])
    print(name, 'HEAD:', out.strip())
    gm = os.path.join(dest, 'go.mod')
    print(name, 'go.mod at root:', os.path.exists(gm))
    if not os.path.exists(gm):
        for dp, dn, fn in os.walk(dest):
            if '.git' in dp: continue
            if 'go.mod' in fn:
                print('  go.mod found:', os.path.relpath(os.path.join(dp, 'go.mod'), dest))
print('SERVERS_A_DONE')