# -*- coding: utf-8 -*-
import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmd = r'''
cd /data/playstar/www/g
for gid in PSF-ON-00001 PSC-ON-00001; do
  if [ -d "$gid/publish/html5" ]; then
    rm -rf "${gid}_pub"; cp -a "$gid/publish/html5" "${gid}_pub"; rm -rf "$gid"; mv "${gid}_pub" "$gid";
  fi
done
python3 - <<'EOF'
import re
F=('new WebSocket("ws://127.0.0.1:8899/fish")','new WebSocket((location.hostname==="127.0.0.1"||location.hostname==="localhost")&&location.port!=="80"&&location.port!=="" ? "ws://127.0.0.1:8899/fish" : "ws://"+location.host+"/ws/fish")')
C=('new WebSocket("ws://127.0.0.1:8901/card")','new WebSocket((location.hostname==="127.0.0.1"||location.hostname==="localhost")&&location.port!=="80"&&location.port!=="" ? "ws://127.0.0.1:8901/card" : "ws://"+location.host+"/ws/card89")')
for gid,pr in [('PSF-ON-00001',F),('PSC-ON-00001',C)]:
    p='/data/playstar/www/g/%s/src/g_message.js'%gid
    try:
        s=open(p).read()
        if pr[0] in s:
            open(p,'w').write(s.replace(pr[0],pr[1])); print('patched',gid)
        else:
            print('no-old',gid, 'has location.host:', 'location.host' in s)
    except Exception as e: print('err',gid,e)
EOF
curl -s -o /dev/null -w "fish:%{http_code} " http://127.0.0.1/g/PSF-ON-00001/
curl -s -o /dev/null -w "pok:%{http_code}\n" http://127.0.0.1/g/PSC-ON-00001/
curl -s http://127.0.0.1/g/PSF-ON-00001/src/g_message.js | grep -c "ws/fish"
'''
i, o, e = c.exec_command(cmd, timeout=120)
print(o.read().decode(), e.read().decode()[-300:])
c.close()
print('SWAP_DONE')