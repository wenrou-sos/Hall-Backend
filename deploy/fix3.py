# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
def sh(cmd, t=180):
    i, o, e = c.exec_command(cmd, timeout=t)
    return o.read().decode(), e.read().decode()
o, e = sh('pip3 install --break-system-packages -q "protobuf>=5.27" 2>&1 | tail -1; python3 -c "import google.protobuf; print(google.protobuf.__version__)"')
print('protobuf:', o.strip()[-100:])
o, e = sh('ls /data/playstar/srv/fish/domain/probability/PSFM-00013-1/ | head; echo ---; ls /data/playstar/srv/fish/domain/probability/ | head -20')
print(o)
o, e = sh('systemctl restart playstar-lobby playstar-fish; sleep 4; systemctl is-active playstar-fish playstar-lobby; ss -lnt | grep -E ":(8084|8899)"')
print(o, e[-200:])
o, e = sh('journalctl -u playstar-fish -n 4 --no-pager')
print(o[-500:])
c.close()
print('FIX3_DONE')