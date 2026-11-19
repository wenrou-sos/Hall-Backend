# -*- coding: utf-8 -*-
import os, io, sys, json, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
MODS = ['cocos2d', 'spine', 'extensions']
def fix(p):
    try:
        d = json.load(open(p, encoding='utf-8'))
    except Exception:
        return False
    if d.get('modules') != MODS:
        d['modules'] = MODS
        json.dump(d, open(p, 'w', encoding='utf-8'), indent=4)
        return True
    return False
n = 0
for i in range(1, 8):
    for base in [r'D:\deploy_www\g', r'D:\deploy_sub\g']:
        p = os.path.join(base, 'PSF-ON-0000%d' % i, 'project.json')
        if os.path.exists(p) and fix(p):
            n += 1
print('local modules', n)
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmd = """python3 - <<'EOF'
import json
n=0
for i in range(1,8):
    p='/data/playstar/www/g/PSF-ON-0000%d/project.json'%i
    d=json.load(open(p))
    if d.get('modules')!=['cocos2d','spine','extensions']:
        d['modules']=['cocos2d','spine','extensions']
        json.dump(d,open(p,'w'),indent=4); n+=1
print('server modules',n)
EOF"""
i, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode().strip(), e.read().decode()[-200:])
c.close()
print('MODULES_FIXED')