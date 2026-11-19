# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmds = ['for g in PSF-ON-00001 PSC-ON-00007; do echo "== $g"; ls /data/playstar/www/g/$g/frameworks/cocos2d-html5/moduleConfig.js 2>&1; ls /data/playstar/www/g/$g/frameworks/cocos2d-html5/ | wc -l; done',
        'curl -s -o /dev/null -w "fishmod:%{http_code} " http://127.0.0.1:8888/g/PSF-ON-00001/frameworks/cocos2d-html5/moduleConfig.js',
        'curl -s -o /dev/null -w "cardmod:%{http_code}" http://127.0.0.1:8888/g/PSC-ON-00007/frameworks/cocos2d-html5/moduleConfig.js']
for cmd in cmds:
    i, o, e = c.exec_command(cmd)
    print('$', cmd); print((o.read().decode() + e.read().decode()).strip()[:400]); print()
c.close()