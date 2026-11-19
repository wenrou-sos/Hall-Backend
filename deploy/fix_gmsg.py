# -*- coding: utf-8 -*-
"""g_message.js Connect: 本地直连服务端端口, 公网走 nginx /ws/ 路径。服务器+本地同步。"""
import os, io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
FISH_OLD = 'new WebSocket("ws://127.0.0.1:8899/fish")'
FISH_NEW = 'new WebSocket((location.hostname==="127.0.0.1"||location.hostname==="localhost")&&location.port!=="80"&&location.port!=="" ? "ws://127.0.0.1:8899/fish" : "ws://"+location.host+"/ws/fish")'
CARD_OLD = 'new WebSocket("ws://127.0.0.1:8901/card")'
CARD_NEW = 'new WebSocket((location.hostname==="127.0.0.1"||location.hostname==="localhost")&&location.port!=="80"&&location.port!=="" ? "ws://127.0.0.1:8901/card" : "ws://"+location.host+"/ws/card89")'
pairs = [(FISH_OLD, FISH_NEW), (CARD_OLD, CARD_NEW)]
# local
for base in [r'D:\deploy_sub', r'D:\deploy_www']:
    for gid in ['PSF-ON-00001', 'PSC-ON-00001']:
        p = os.path.join(base, 'g', gid, 'src', 'g_message.js')
        if os.path.exists(p):
            s = open(p, encoding='utf-8', errors='ignore').read()
            for a, b in pairs:
                s = s.replace(a, b)
            open(p, 'w', encoding='utf-8', newline='').write(s)
print('local patched')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
sf = c.open_sftp()
for gid in ['PSF-ON-00001', 'PSC-ON-00001']:
    lp = os.path.join(r'D:\deploy_sub', 'g', gid, 'src', 'g_message.js')
    sf.put(lp, '/data/playstar/www/g/' + gid + '/src/g_message.js')
sf.close()
i, o, e = c.exec_command('curl -s http://127.0.0.1/g/PSF-ON-00001/src/g_message.js | grep -c "ws/fish"; curl -s http://127.0.0.1/g/PSC-ON-00001/src/g_message.js | grep -c "ws/card89"')
print('server grep:', o.read().decode().strip())
c.close()
print('GMSG_FIXED')