# -*- coding: utf-8 -*-
"""给所有游戏客户端 loader_scene.js 加 12s 兜底(服务器+本地)."""
import os, io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
OLD = "    _cc.loaderScene.initWithResources(resources, cb, target);"
NEW = ("    var _psdone = false; var _pscb = cb;\n"
       "    cb = function(){ if (_psdone) return; _psdone = true; _pscb.apply(this, arguments); };\n"
       "    setTimeout(function(){ cb.call(target); }, 12000);\n"
       "    _cc.loaderScene.initWithResources(resources, cb, target);")
def patch(p):
    try:
        s = open(p, encoding='utf-8', errors='ignore').read()
    except Exception:
        return False
    if OLD in s and '_psdone' not in s:
        open(p, 'w', encoding='utf-8', newline='').write(s.replace(OLD, NEW, 1))
        return True
    return False
n = 0
for root in [r'D:\deploy_www\g', r'D:\deploy_sub\g', r'D:\games_wc', r'D:\psc00001_wc', r'D:\fish_frontend']:
    for dp, dn, fn in os.walk(root):
        if '.svn' in dp:
            continue
        if 'loader_scene.js' in fn and dp.endswith(os.path.join('lib', 'loader')):
            if patch(os.path.join(dp, 'loader_scene.js')):
                n += 1
print('local patched', n)
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmd = """python3 - <<'EOF'
import os
OLD="    _cc.loaderScene.initWithResources(resources, cb, target);"
NEW=("    var _psdone = false; var _pscb = cb;\\n"
     "    cb = function(){ if (_psdone) return; _psdone = true; _pscb.apply(this, arguments); };\\n"
     "    setTimeout(function(){ cb.call(target); }, 12000);\\n"
     "    _cc.loaderScene.initWithResources(resources, cb, target);")
n=0
for dp,dn,fn in os.walk('/data/playstar/www/g'):
    if 'loader_scene.js' in fn and dp.endswith('lib/loader'):
        p=os.path.join(dp,'loader_scene.js')
        s=open(p,encoding='utf-8',errors='ignore').read()
        if OLD in s and '_psdone' not in s:
            open(p,'w',encoding='utf-8',newline='').write(s.replace(OLD,NEW,1)); n+=1
print('server patched',n)
EOF"""
i, o, e = c.exec_command(cmd, timeout=120)
print(o.read().decode().strip(), e.read().decode()[-200:])
c.close()
print('GAME_LOADER_FIXED')