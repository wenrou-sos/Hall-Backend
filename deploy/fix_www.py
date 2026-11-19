# -*- coding: utf-8 -*-
"""修大厅 WS 为 location.host/ws/lobby; 恢复 res/PSImages(精简语言); 补传服务器。"""
import os, io, sys, subprocess, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
TRUNK = r'D:\pslobby_wc\trunk'
OLD = 'new WebSocket("ws://127.0.0.1:8084/lobby")'
NEW = 'new WebSocket("ws://" + window.location.host + "/ws/lobby")'
for base in [TRUNK, r'D:\deploy_sub\lobby', r'D:\deploy_www\lobby']:
    p = os.path.join(base, 'src', 'core.js')
    if os.path.exists(p):
        s = open(p, encoding='utf-8', errors='ignore').read()
        if OLD in s:
            open(p, 'w', encoding='utf-8', newline='').write(s.replace(OLD, NEW))
            print('patched', p)
# restore PSImages trimmed
KEEP = {'common', 'eng', 'sch'}
src = os.path.join(TRUNK, 'res', 'PSImages')
for dstbase in [r'D:\deploy_sub\lobby', r'D:\deploy_www\lobby']:
    dst = os.path.join(dstbase, 'res', 'PSImages')
    subprocess.run(['robocopy', src, dst, '/E', '/NFL', '/NDL', '/NJH', '/NJS', '/NP'], capture_output=True)
    for root, dirs, files in os.walk(dst):
        for d in list(dirs):
            # language dirs are numeric? PSImages/3/<lang>/... keep common/eng/sch at level2
            rel = os.path.relpath(os.path.join(root, d), dst).replace(os.sep, '/')
            parts = rel.split('/')
            if len(parts) == 2 and parts[1] not in KEEP:
                import shutil; shutil.rmtree(os.path.join(root, d), ignore_errors=True); dirs.remove(d)
    print('PSImages restored', dstbase)
# upload core.js + PSImages to server
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=60)
sf = c.open_sftp()
def put(local, remote):
    try:
        sf.stat(remote)
    except IOError:
        try: sf.mkdir(remote)
        except IOError: pass
    if os.path.isdir(local):
        for f in os.listdir(local):
            put(os.path.join(local, f), remote + '/' + f)
    else:
        sf.put(local, remote)
put(r'D:\deploy_sub\lobby\src\core.js', '/data/playstar/www/lobby/src/core.js')
put(r'D:\deploy_sub\lobby\res\PSImages', '/data/playstar/www/lobby/res/PSImages')
sf.close(); c.close()
print('WWW_FIX_UPLOADED')