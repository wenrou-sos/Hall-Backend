# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\pslobby_wc\trunk\src\gameWall.js'
d = open(p, encoding='utf-8').read()
old = '            this._btn_group[i].setPosition(pslb.ButtonPos[BK.DEVICE_MODE][i]);'
new = '            if (this._btn_group[i] && pslb.ButtonPos[BK.DEVICE_MODE]) { this._btn_group[i].setPosition(pslb.ButtonPos[BK.DEVICE_MODE][i]); }'
if old in d:
    d = d.replace(old, new, 1)
    open(p, 'w', encoding='utf-8').write(d)
    print('gameWall reset_position guarded')
else:
    print('pattern not found')