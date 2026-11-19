# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\pslobby_wc\trunk\src\core.js'
d = open(p, encoding='utf-8').read()
old = 'if (game_id === "PSF-ON-00001") { return "http://127.0.0.1:8080/?access_token=dev&subid=" + subgame_id; }'
new = old + '\n    if (game_id === "PSC-ON-00001") { return "http://127.0.0.1:8085/?access_token=dev&subid=" + subgame_id; }'
assert old in d
d = d.replace(old, new, 1)
open(p, 'w', encoding='utf-8').write(d)
print('BuildLaunchURL + PSC-ON-00001 -> 8085')