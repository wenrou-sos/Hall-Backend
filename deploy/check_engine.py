# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmds = ['ls /data/playstar/www/g/PSF-ON-00001/frameworks/cocos2d-html5/ | head',
        'python3 -c "import json;d=json.load(open(\'/data/playstar/www/g/PSF-ON-00001/project.json\'));print(\'modules\',d.get(\'modules\'));print(\'jsList\',d.get(\'jsList\'));print(\'renderMode\',d.get(\'renderMode\'))"',
        'ls /data/playstar/www/g/PSC-ON-00007/frameworks/cocos2d-html5/ | head']
for cmd in cmds:
    i, o, e = c.exec_command(cmd)
    print('$', cmd); print((o.read().decode() + e.read().decode()).strip()[:400]); print()
c.close()