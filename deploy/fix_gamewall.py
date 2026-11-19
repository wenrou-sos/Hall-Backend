# -*- coding: utf-8 -*-
"""ButtonPos 扩到12 + gameWall 越界保护; 上传服务器."""
import os, io, sys, re, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
NEWPOS = "pslb.ButtonPos = {\n    0 : [\n" + ",\n".join("        cc.p(51,%d)" % y for y in [595, 509, 423, 337, 251, 595, 509, 423, 337, 251, 595, 509]) + "\n    ],\n    1 : [\n" + ",\n".join("        cc.p(61,%d)" % (976 - 103 * i) for i in range(12)) + "\n    ],\n};"
for base in [r'D:\pslobby_wc\trunk', r'D:\deploy_sub\lobby', r'D:\deploy_www\lobby']:
    p = os.path.join(base, 'src', 'filterAndLayout.js')
    if os.path.exists(p):
        s = open(p, encoding='utf-8', errors='ignore').read()
        s2 = re.sub(r'pslb\.ButtonPos = \{.*?\n\};', NEWPOS, s, count=1, flags=re.S)
        if s2 != s:
            open(p, 'w', encoding='utf-8', newline='').write(s2)
            print('buttonpos12', base)
    g = os.path.join(base, 'src', 'gameWall.js')
    if os.path.exists(g):
        s = open(g, encoding='utf-8', errors='ignore').read()
        old = "if (this._btn_group[i] && pslb.ButtonPos[BK.DEVICE_MODE]) { this._btn_group[i].setPosition(pslb.ButtonPos[BK.DEVICE_MODE][i]); }"
        new = "var _bp = pslb.ButtonPos[BK.DEVICE_MODE] && pslb.ButtonPos[BK.DEVICE_MODE][i]; if (this._btn_group[i] && _bp) { this._btn_group[i].setPosition(_bp); }"
        if old in s:
            open(g, 'w', encoding='utf-8', newline='').write(s.replace(old, new))
            print('gamewall guard', base)
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
sf = c.open_sftp()
for f in ['filterAndLayout.js', 'gameWall.js']:
    sf.put(os.path.join(r'D:\deploy_sub\lobby', 'src', f), '/data/playstar/www/lobby/src/' + f)
sf.close(); c.close()
print('GAMEWALL_FIXED')