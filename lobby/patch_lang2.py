# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\pslobby_wc\trunk\src\core.js'
d = open(p, encoding='utf-8').read()
old = 'pslb.Language = function(){\n    var ret = pslb.LanguageGroup.eng;'
new = 'pslb.Language = function(){\n    var ret = (window.localStorage && localStorage.getItem("ps_lang")) || pslb.LanguageGroup.sch;'
assert old in d, 'lang pattern'
d = d.replace(old, new, 1)
old2 = '    return ret;\n}();\n\npslb.TextGroup = {};'
new2 = '    if (!(ret in pslb.LanguageGroup)) ret = pslb.LanguageGroup.sch;\n    return ret;\n}();\n\npslb.TextGroup = {};'
assert old2 in d, 'ret pattern'
d = d.replace(old2, new2, 1)
open(p, 'w', encoding='utf-8').write(d)
print('pslb.Language -> localStorage||sch')