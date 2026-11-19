# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmds = ['head -c 260 /data/playstar/www/g/PSF-ON-00002/project.json',
        'curl -s -o /dev/null -w "main:%{http_code} " http://127.0.0.1:8888/g/PSF-ON-00002/publish/main.js',
        'curl -s -o /dev/null -w "loader:%{http_code} " http://127.0.0.1:8888/g/PSF-ON-00002/src/lib/loader/loader_scene.js',
        'curl -s -o /dev/null -w "idx:%{http_code}" http://127.0.0.1:8888/g/PSF-ON-00002/',
        'ls /data/playstar/www/g/PSF-ON-00002/ | head',
        'curl -s -o /dev/null -w "ccboot:%{http_code} " http://127.0.0.1:8888/g/PSF-ON-00002/frameworks/cocos2d-html5/CCBoot.js',
        'curl -s -o /dev/null -w "rootmain:%{http_code}" http://127.0.0.1:8888/g/PSF-ON-00002/main.js']
for cmd in cmds:
    i, o, e = c.exec_command(cmd)
    print('$', cmd); print(o.read().decode().strip()[:300]); print()
c.close()