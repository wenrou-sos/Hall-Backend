# -*- coding: utf-8 -*-
"""补 PSImages 素材(从 svn art 仓库 checkout) 到本地+服务器; 上传 resource.js(367修)."""
import os, io, sys, shutil, tarfile, time, paramiko, concurrent.futures as cf
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
WC = r'D:\psimages_wc'
for base in [r'D:\pslobby_wc\trunk', r'D:\deploy_sub\lobby', r'D:\deploy_www\lobby']:
    dst = os.path.join(base, 'res', 'PSImages')
    os.makedirs(dst, exist_ok=True)
    for item in os.listdir(WC):
        if item == '.svn':
            continue
        s = os.path.join(WC, item); d = os.path.join(dst, item)
        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d, ignore_errors=True)
            shutil.copytree(s, d)
        else:
            shutil.copy(s, d)
    print('PSImages copied', base)
TAR = r'D:\psimages.tar'
P = chr(92) * 2 + '?' + chr(92)
with tarfile.open(TAR, 'w') as tf:
    tf.add(P + os.path.join(r'D:\deploy_sub\lobby', 'res', 'PSImages'), arcname='res/PSImages')
print('tar MB', round(os.path.getsize(TAR) / 1e6, 1))
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=60)
sf = c.open_sftp()
sf.put(r'D:\deploy_sub\lobby\src\resource.js', '/data/playstar/www/lobby/src/resource.js')
sf.close()
CH = 3
size = os.path.getsize(TAR); chunk = (size + CH - 1) // CH
parts = []
with open(TAR, 'rb') as f:
    for i in range(CH):
        d = f.read(chunk)
        if not d: break
        pp = TAR + '.i%d' % i; open(pp, 'wb').write(d); parts.append(pp)
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
print('upload', int(time.time() - t0), 's')
i, o, e = c.exec_command('cat ' + ' '.join('/data/' + os.path.basename(p) for p in parts) + ' > /data/psimages.tar && rm -f ' + ' '.join('/data/' + os.path.basename(p) for p in parts) + ' && tar -xf /data/psimages.tar -C /data/playstar/www/lobby && echo PSIMG_EXTRACTED && ls /data/playstar/www/lobby/res/PSImages')
print(o.read().decode()[-300:])
c.close()
print('PSIMAGES_DEPLOYED')