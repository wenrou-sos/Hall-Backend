# -*- coding: utf-8 -*-
"""修 loading61%: LoadJackPotResource 不再推 PSImages; 补全大厅语言 res."""
import os, io, sys, re, tarfile, time, paramiko, concurrent.futures as cf
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
TRUNK = r'D:\pslobby_wc\trunk'
# 1) jp_resource no-op
for base in [TRUNK, r'D:\deploy_sub\lobby', r'D:\deploy_www\lobby']:
    p = os.path.join(base, 'src', 'jp', 'jp_resource.js')
    if os.path.exists(p):
        s = open(p, encoding='utf-8', errors='ignore').read()
        s2 = re.sub(r'function LoadJackPotResource\(g_resources\)\{.*?\n\}', 'function LoadJackPotResource(g_resources){\n    return; // PSImages publish pack absent; skip preload\n}', s, count=1, flags=re.S)
        if s2 != s:
            open(p, 'w', encoding='utf-8', newline='').write(s2)
            print('jp_resource noop', base)
# 2) tar full res
TAR = r'D:\lobby_res.tar'
P = chr(92) * 2 + '?' + chr(92)
with tarfile.open(TAR, 'w') as tf:
    tf.add(P + os.path.join(TRUNK, 'res'), arcname='res')
print('res tar MB', round(os.path.getsize(TAR) / 1e6, 1))
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=60)
sf = c.open_sftp()
sf.put(os.path.join(TRUNK, 'src', 'jp', 'jp_resource.js'), '/data/playstar/www/lobby/src/jp/jp_resource.js')
sf.close()
CH = 3
size = os.path.getsize(TAR); chunk = (size + CH - 1) // CH
parts = []
with open(TAR, 'rb') as f:
    for i in range(CH):
        d = f.read(chunk)
        if not d: break
        pp = TAR + '.r%d' % i; open(pp, 'wb').write(d); parts.append(pp)
def up(pp):
    for a in range(3):
        try:
            cc = paramiko.SSHClient(); cc.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            cc.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=60)
            t = cc.get_transport(); t.window_size = 2 ** 26; t.max_packet_size = 2 ** 18
            s = paramiko.SFTPClient.from_transport(t)
            s.put(pp, '/data/' + os.path.basename(pp)); s.close(); cc.close(); return
        except Exception as ex:
            print('retry', ex); time.sleep(3)
    raise RuntimeError(pp)
t0 = time.time()
with cf.ThreadPoolExecutor(max_workers=CH) as ex:
    list(ex.map(up, parts))
print('res upload', int(time.time() - t0), 's')
i, o, e = c.exec_command('cat ' + ' '.join('/data/' + os.path.basename(p) for p in parts) + ' > /data/lobby_res.tar && rm -f ' + ' '.join('/data/' + os.path.basename(p) for p in parts) + ' && tar -xf /data/lobby_res.tar -C /data/playstar/www/lobby && echo RES_EXTRACTED && ls /data/playstar/www/lobby/res')
print(o.read().decode()[-300:])
c.close()
print('LOADING_LANG_FIXED')