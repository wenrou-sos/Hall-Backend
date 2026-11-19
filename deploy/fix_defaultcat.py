# -*- coding: utf-8 -*-
import os, io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
for base in [r'D:\pslobby_wc\trunk', r'D:\deploy_sub\lobby', r'D:\deploy_www\lobby']:
    p = os.path.join(base, 'src', 'gameWall.js')
    if os.path.exists(p):
        s = open(p, encoding='utf-8', errors='ignore').read()
        n = s.count('_clickButton(pslb.gameWall.TodaySpecial)')
        s = s.replace('_clickButton(pslb.gameWall.TodaySpecial)', '_clickButton(pslb.gameWall.HotGame !== undefined ? pslb.gameWall.HotGame : pslb.gameWall.TodaySpecial)')
        s = s.replace('this._btn_group[pslb.gameWall.TodaySpecial].setVisible(true);',
                      'this._btn_group[pslb.gameWall.TodaySpecial].setVisible(true);\n            if (this._btn_group[pslb.gameWall.HotGame]) this._btn_group[pslb.gameWall.HotGame].setVisible(true);\n            if (this._btn_group[pslb.gameWall.AllGame]) this._btn_group[pslb.gameWall.AllGame].setVisible(true);')
        open(p, 'w', encoding='utf-8', newline='').write(s)
        print('gamewall default HotGame', base, n)
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('82.158.228.38', username='root', password='t3S6GMuGwmWr', timeout=30)
sf = c.open_sftp()
sf.put(r'D:\deploy_sub\lobby\src\gameWall.js', '/data/playstar/www/lobby/src/gameWall.js')
sf.close(); c.close()
print('DEFAULT_CAT_FIXED')