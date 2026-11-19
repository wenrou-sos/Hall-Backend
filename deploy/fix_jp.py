# -*- coding: utf-8 -*-
import os, io, sys, paramiko, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
for base in [r'D:\pslobby_wc\trunk', r'D:\deploy_sub\lobby', r'D:\deploy_www\lobby']:
    p = os.path.join(base, 'src', 'jp', 'jp_ly_banner.js')
    if os.path.exists(p):
        s = open(p, encoding='utf-8', errors='ignore').read()
        if 'banner_json ||' not in s:
            s2 = re.sub(r'(ctor:function\(\)\{\s*this\._super\(\);)', r'\1\n        if (!jp_res.banner_json || !jp_res.banner_atlas) { return; }', s, count=1)
            if s2 != s:
                open(p, 'w', encoding='utf-8', newline='').write(s2)
                print('patched', p)
            else:
                print('nomatch', p)
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
sf = c.open_sftp()
sf.put(r'D:\deploy_sub\lobby\src\jp\jp_ly_banner.js', '/data/playstar/www/lobby/src/jp/jp_ly_banner.js')
sf.close(); c.close()
print('JP_GUARD_UPLOADED')