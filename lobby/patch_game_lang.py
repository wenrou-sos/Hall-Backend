# -*- coding: utf-8 -*-
"""让所有游戏客户端默认中文(读 localStorage.ps_lang||sch), URL lang 优先。"""
import os, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
roots = [r'D:\fish_frontend\srv\svn\game', r'D:\games_wc', r'D:\psc00001_wc']
JS = "(function(){var m=window.location.search.match(/[?&]lang=([^&]+)/);if(m)return m[1];return (window.localStorage&&localStorage.getItem('ps_lang'))||'sch';})()"
pats = [
    ("let RES_LANGUAGE = 'eng';", "let RES_LANGUAGE = %s;" % JS),
    ('let RES_LANGUAGE = "eng";', 'let RES_LANGUAGE = %s;' % JS),
    ("var RES_LANGUAGE = 'eng';", "var RES_LANGUAGE = %s;" % JS),
    ('var RES_LANGUAGE = "eng";', 'var RES_LANGUAGE = %s;' % JS),
    ("let JP_RES_LANGUAGE = 'eng';", "let JP_RES_LANGUAGE = %s;" % JS),
    ('var lan = "eng";', 'var lan = %s;' % JS),
    ("var lan = 'eng';", "var lan = %s;" % JS),
]
n = 0
for root in roots:
    for dp, dn, fn in os.walk(root):
        if '.svn' in dp or 'node_modules' in dp or 'frameworks' in dp or 'publish' in dp:
            continue
        for f in fn:
            if not f.endswith('.js'):
                continue
            p = os.path.join(dp, f)
            try:
                d = open(p, encoding='utf-8', errors='replace').read()
            except Exception:
                continue
            orig = d
            for old, new in pats:
                if old in d:
                    d = d.replace(old, new)
            if d != orig:
                open(p, 'w', encoding='utf-8').write(d)
                n += 1
                print('patched', p)
print('GAME_LANG_DONE files', n)