# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\lobby_fe\frameworks\cocos2d-html5\extensions\spine\CCSkeleton.js'
d = open(p, encoding='utf-8').read()
old = 'getBlendFunc: function () {\n        var slot = this._skeleton.drawOrder[0];'
new = ('getBlendFunc: function () {\n'
       '        if (!this._skeleton) { return {src: cc.BLEND_SRC, dst: cc.BLEND_DST}; }\n'
       '        var slot = this._skeleton.drawOrder[0];')
if old in d:
    d = d.replace(old, new, 1)
    open(p, 'w', encoding='utf-8').write(d)
    print('getBlendFunc guarded')
else:
    print('pattern not found')