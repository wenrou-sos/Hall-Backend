# -*- coding: utf-8 -*-
"""把牌图集 png 加入 g_resources 预加载, 消除公网慢网络下 addSpriteFrames 竞态(自己的牌黑)."""
import os, io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
ANCHOR = 'var PreparationRes = function(){'
ADD = ('g_resources.push("res/common/anm/poker/unocards.png");\n'
       'g_resources.push("res/common/anm/poker/card.png");\n'
       'g_resources.push("res/common/anm/poker/card_back.png");\n\n')
def patch(p):
    try:
        s = open(p, encoding='utf-8', errors='ignore').read()
    except Exception:
        return False
    if 'unocards.png");' in s:
        return False
    if ANCHOR in s:
        open(p, 'w', encoding='utf-8', newline='').write(s.replace(ANCHOR, ADD + ANCHOR, 1))
        return True
    return False
n = 0
for root in [r'D:\games_wc', r'D:\psc00001_wc', r'D:\deploy_www\g', r'D:\deploy_sub\g']:
    for dp, dn, fn in os.walk(root):
        if '.svn' in dp or 'frameworks' in dp or 'publish' in dp:
            continue
        if 'resource.js' in fn and dp.endswith('src'):
            if patch(os.path.join(dp, 'resource.js')):
                n += 1
print('local patched', n)
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmd = """python3 - <<'EOF'
import os
ANCHOR='var PreparationRes = function(){'
ADD=('g_resources.push("res/common/anm/poker/unocards.png");\\n'
     'g_resources.push("res/common/anm/poker/card.png");\\n'
     'g_resources.push("res/common/anm/poker/card_back.png");\\n\\n')
n=0
for gid in os.listdir('/data/playstar/www/g'):
    if not gid.startswith('PSC'): continue
    p='/data/playstar/www/g/%s/src/resource.js'%gid
    if not os.path.exists(p): continue
    s=open(p,encoding='utf-8',errors='ignore').read()
    if 'unocards.png");' in s: continue
    if ANCHOR in s:
        open(p,'w',encoding='utf-8',newline='').write(s.replace(ANCHOR,ADD+ANCHOR,1)); n+=1
print('server patched',n)
EOF"""
i, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode().strip(), e.read().decode()[-200:])
c.close()
print('POKER_PRELOAD_FIXED')