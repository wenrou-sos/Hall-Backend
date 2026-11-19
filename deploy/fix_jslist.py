# -*- coding: utf-8 -*-
"""fish bundle: jsList 把 loader_scene.js 提到最前, 保证 cc.LoaderScene 先定义."""
import os, io, sys, json, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
def fix(p):
    try:
        d = json.load(open(p, encoding='utf-8'))
    except Exception:
        return False
    jl = d.get('jsList') or []
    hit = [x for x in jl if 'loader_scene.js' in x]
    if hit and jl[0] != hit[0]:
        jl = hit + [x for x in jl if x not in hit]
        d['jsList'] = jl
        json.dump(d, open(p, 'w', encoding='utf-8'), indent=4)
        return True
    return False
n = 0
for i in range(1, 8):
    gid = 'PSF-ON-0000%d' % i
    for base in [r'D:\deploy_www\g', r'D:\deploy_sub\g']:
        p = os.path.join(base, gid, 'project.json')
        if os.path.exists(p) and fix(p):
            n += 1
print('local jsList reordered', n)
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmd = """python3 - <<'EOF'
import json,os
n=0
for i in range(1,8):
    p='/data/playstar/www/g/PSF-ON-0000%d/project.json'%i
    if not os.path.exists(p): continue
    d=json.load(open(p))
    jl=d.get('jsList') or []
    hit=[x for x in jl if 'loader_scene.js' in x]
    if hit and jl[0]!=hit[0]:
        d['jsList']=hit+[x for x in jl if x not in hit]
        json.dump(d,open(p,'w'),indent=4); n+=1
print('server jsList reordered',n)
EOF"""
i, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode().strip(), e.read().decode()[-200:])
c.close()
print('JSLIST_FIXED')