# -*- coding: utf-8 -*-
import os, io, sys, paramiko, concurrent.futures as cf, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
ROOT = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(ROOT, 'bin')
HOST = '82.158.228.38'
names = ['fish', 'card89', 'card52', 'cardu4', 'cardcg', 'cardfsc']
def up(n):
    for a in range(3):
        try:
            cc = paramiko.SSHClient(); cc.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            cc.connect(HOST, username='root', password='t3S6GMuGwmWr', timeout=60)
            t = cc.get_transport(); t.window_size = 2 ** 26; t.max_packet_size = 2 ** 18
            sf = paramiko.SFTPClient.from_transport(t)
            sf.put(os.path.join(BIN, n), '/data/playstar/bin/' + n + '.new')
            sf.close(); cc.close(); return n
        except Exception as ex:
            print('retry', n, ex); time.sleep(3)
    raise RuntimeError(n)
t0 = time.time()
with cf.ThreadPoolExecutor(max_workers=3) as ex:
    print('uploaded:', list(ex.map(up, names)))
print('bins upload', int(time.time() - t0), 's')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username='root', password='t3S6GMuGwmWr', timeout=30)
i, o, e = c.exec_command('cd /data/playstar/bin && for n in fish card89 card52 cardu4 cardcg cardfsc; do mv -f $n.new $n; done; chmod +x /data/playstar/bin/*; systemctl restart playstar-fish playstar-card89; sleep 4; systemctl is-active playstar-fish playstar-card89 playstar-lobby; ss -lnt | grep -E ":(8084|8899|8901)"')
print(o.read().decode(), e.read().decode()[-200:])
c.close()
print('BINS_DEPLOYED')