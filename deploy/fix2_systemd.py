# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
def sh(cmd, t=120):
    i, o, e = c.exec_command(cmd, timeout=t)
    return o.read().decode(), e.read().decode()
units = {
    'playstar-fish': ('/data/playstar/srv/fish', '/data/playstar/bin/fish', '8899', 'fish'),
    'playstar-card89': ('/data/playstar/srv/89-game-server', '/data/playstar/bin/card89', '8901', 'card89'),
}
for name, (wd, exe, port, sn) in units.items():
    unit = '[Unit]\nDescription=%s\nAfter=network.target\n\n[Service]\nWorkingDirectory=%s\nEnvironment=HTTP_PORT=%s SERVER_NAME=%s LOG_LEVEL=0 POOL_SIZE=100 CHAN_SIZE=102400 VERSION=dev\nExecStart=%s\nRestart=always\nRestartSec=2\n\n[Install]\nWantedBy=multi-user.target\n' % (name, wd, port, sn, exe)
    sh("cat > /etc/systemd/system/%s.service <<'EOF'\n%sEOF" % (name, unit))
stub_unit = '[Unit]\nDescription=playstar-lobby-stub\nAfter=network.target\n\n[Service]\nWorkingDirectory=/data/playstar/lobby_stub\nExecStart=/usr/bin/python3 /data/playstar/lobby_stub/pslobby_ws_stub.py\nRestart=always\nRestartSec=2\n\n[Install]\nWantedBy=multi-user.target\n'
sh("cat > /etc/systemd/system/playstar-lobby.service <<'EOF'\n%sEOF" % stub_unit)
o, e = sh('systemctl daemon-reload && systemctl enable --now playstar-fish playstar-card89 playstar-lobby 2>&1 | tail -2 && sleep 3 && systemctl is-active playstar-fish playstar-card89 playstar-lobby && ss -lnt | grep -E ":(8084|8899|8901)"')
print(o, e[-300:])
c.close()
print('SYSTEMD_DONE')