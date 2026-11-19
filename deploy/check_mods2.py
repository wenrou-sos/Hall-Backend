# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmds = ['python3 -c "import json;print(\'card\',json.load(open(\'/data/playstar/www/g/PSC-ON-00007/project.json\')).get(\'modules\'),json.load(open(\'/data/playstar/www/g/PSC-ON-00007/project.json\')).get(\'renderMode\'))"',
        'ls /data/playstar/www/g/PSF-ON-00001/frameworks/cocos2d-html5/',
        'ls /data/playstar/www/g/PSF-ON-00001/frameworks/cocos2d-html5/extensions/ 2>&1 | head']
for cmd in cmds:
    i, o, e = c.exec_command(cmd)
    print('$', cmd); print((o.read().decode() + e.read().decode()).strip()[:500]); print()
c.close()