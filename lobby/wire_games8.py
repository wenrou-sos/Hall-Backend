# -*- coding: utf-8 -*-
"""把 6 个捕鱼变体客户端 WS 指向本地 8899/fish，各起静态服务，并接大厅跳转。"""
import os, re, io, sys, subprocess, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.abspath(__file__))
PSF = ['PSF-ON-00002', 'PSF-ON-00003', 'PSF-ON-00004', 'PSF-ON-00005', 'PSF-ON-00006', 'PSF-ON-00007']
ports = {}
for i, gid in enumerate(PSF):
    trunk = os.path.join(r'D:\games_wc', gid, 'trunk')
    port = 8086 + i
    ports[gid] = port
    patched = False
    for fn in ['src/lkmessage.js', 'src/g_message.js', 'src/core.js']:
        p = os.path.join(trunk, fn)
        if not os.path.exists(p):
            continue
        d = open(p, encoding='utf-8', errors='replace').read()
        d2, n = re.subn(r'(const SocketTarget\s*=\s*")[^"]*(")', r'\g<1>ws://127.0.0.1:8899/fish\g<2>', d)
        d2, n2 = re.subn(r'(new WebSocket\(")ws://[^"]*(/fish"\))', r'\g<1>ws://127.0.0.1:8899\g<2>', d2)
        if n or n2:
            open(p, 'w', encoding='utf-8').write(d2)
            patched = True
    print(gid, 'port', port, 'ws patched', patched)
    subprocess.Popen([sys.executable, os.path.join(ROOT, 'nocache_server.py'), trunk, str(port)],
                     stdout=open(os.path.join(ROOT, 'fe_%s.log' % gid), 'w'),
                     stderr=subprocess.STDOUT)
# lobby BuildLaunchURL map
core = r'D:\pslobby_wc\trunk\src\core.js'
d = open(core, encoding='utf-8').read()
anchor = '    return "./AutoClosePage/";'
add = ''
for gid, port in ports.items():
    line = '    if (game_id === "%s") { return "http://127.0.0.1:%d/?access_token=dev&subid=" + subgame_id; }\n' % (gid, port)
    if gid not in d:
        add += line
if add:
    d = d.replace(anchor, add + anchor, 1)
    open(core, 'w', encoding='utf-8').write(d)
print('lobby BuildLaunchURL added', len(ports), 'mappings')