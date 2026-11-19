# -*- coding: utf-8 -*-
"""回退 89(PokDeng) 的 fix_poker_preload + fix_game_loader 改动, 恢复原可玩状态."""
import os, io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
PUSH = ('g_resources.push("res/common/anm/poker/unocards.png");\n'
        'g_resources.push("res/common/anm/poker/card.png");\n'
        'g_resources.push("res/common/anm/poker/card_back.png");\n\n')
FB = ("    var _psdone = false; var _pscb = cb;\n"
      "    cb = function(){ if (_psdone) return; _psdone = true; _pscb.apply(this, arguments); };\n"
      "    setTimeout(function(){ cb.call(target); }, 12000);\n")
def revert(base):
    r = os.path.join(base, 'src', 'resource.js')
    if os.path.exists(r):
        s = open(r, encoding='utf-8', errors='ignore').read()
        if PUSH in s:
            open(r, 'w', encoding='utf-8', newline='').write(s.replace(PUSH, '', 1))
            print('resource reverted', base)
    l = os.path.join(base, 'src', 'lib', 'loader', 'loader_scene.js')
    if os.path.exists(l):
        s = open(l, encoding='utf-8', errors='ignore').read()
        if FB in s:
            open(l, 'w', encoding='utf-8', newline='').write(s.replace(FB, '', 1))
            print('loader reverted', base)
revert(r'D:\psc00001_wc\trunk')
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
cmd = """python3 - <<'EOF'
PUSH=('g_resources.push("res/common/anm/poker/unocards.png");\\n'
      'g_resources.push("res/common/anm/poker/card.png");\\n'
      'g_resources.push("res/common/anm/poker/card_back.png");\\n\\n')
FB=("    var _psdone = false; var _pscb = cb;\\n"
    "    cb = function(){ if (_psdone) return; _psdone = true; _pscb.apply(this, arguments); };\\n"
    "    setTimeout(function(){ cb.call(target); }, 12000);\\n")
b='/data/playstar/www/g/PSC-ON-00001'
for rel,blk in [('src/resource.js',PUSH),('src/lib/loader/loader_scene.js',FB)]:
    p=b+'/'+rel
    s=open(p,encoding='utf-8',errors='ignore').read()
    if blk in s:
        open(p,'w',encoding='utf-8',newline='').write(s.replace(blk,'',1)); print('reverted',rel)
EOF"""
i, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode().strip(), e.read().decode()[-200:])
c.close()
print('REVERT89_DONE')