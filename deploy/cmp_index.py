# -*- coding: utf-8 -*-
import paramiko, io, sys, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
loc = open(r'D:\games_wc\PSF-ON-00002\trunk\index.html', 'rb').read()
print('local index md5', hashlib.md5(loc).hexdigest(), len(loc))
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
i, o, e = c.exec_command('md5sum /data/playstar/www/g/PSF-ON-00002/index.html; wc -c < /data/playstar/www/g/PSF-ON-00002/index.html; grep -o "src=\\"[^\\"]*\\" /data/playstar/www/g/PSF-ON-00002/index.html | head')
print(o.read().decode())
i, o, e = c.exec_command('md5sum /data/playstar/www/g/PSF-ON-00002/main.js /data/playstar/www/g/PSF-ON-00002/project.json')
print(o.read().decode())
c.close()
print('local main md5', hashlib.md5(open(r'D:\games_wc\PSF-ON-00002\trunk\main.js', 'rb').read()).hexdigest())
print('local proj md5', hashlib.md5(open(r'D:\games_wc\PSF-ON-00002\trunk\project.json', 'rb').read()).hexdigest())