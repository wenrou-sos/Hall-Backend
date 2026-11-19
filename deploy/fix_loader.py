# -*- coding: utf-8 -*-
import os, io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
OLD = "    _cc.loaderScene.initWithResources(resources, cb, target);"
NEW = ("    var _psdone = false; var _pscb = cb;\n"
       "    cb = function(){ if (_psdone) return; _psdone = true; _pscb.apply(this, arguments); };\n"
       "    setTimeout(function(){ cb.call(target); }, 12000);\n"
       "    _cc.loaderScene.initWithResources(resources, cb, target);")
for base in [r'D:\pslobby_wc\trunk', r'D:\deploy_sub\lobby', r'D:\deploy_www\lobby']:
    p = os.path.join(base, 'src', 'lib', 'loader', 'loader_scene.js')
    if os.path.exists(p):
        s = open(p, encoding='utf-8', errors='ignore').read()
        if OLD in s and '_psdone' not in s:
            open(p, 'w', encoding='utf-8', newline='').write(s.replace(OLD, NEW, 1))
            print('loader fallback', base)
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
sf = c.open_sftp()
sf.put(r'D:\deploy_sub\lobby\src\lib\loader\loader_scene.js', '/data/playstar/www/lobby/src/lib/loader/loader_scene.js')
sf.close(); c.close()
print('LOADER_FIXED')