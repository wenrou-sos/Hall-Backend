# -*- coding: utf-8 -*-
"""概率/鱼路径 .go 的 runtime.Caller(0) 绝对路径 -> 相对路径字面量(跨平台部署必需)。
var _, bs, _, _ = runtime.Caller(0)  ->  var bs = "domain/probability/.../x.go"
并移除不再使用的 runtime import。"""
import os, re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # fish
SERVERS = [os.path.join(ROOT, 'Fish-Game-Server')] + [os.path.join(ROOT, 'cards', d) for d in ['89-game-server', 'paikang52', 'u-game-server', 'colorgame', 'fishshrimpcrab']]
PAT = re.compile(r'var (_+), (\w+), _, _ = runtime\.Caller\(0\)')
n = 0
for srv in SERVERS:
    dom = os.path.join(srv, 'domain')
    if not os.path.isdir(dom):
        continue
    for dp, dn, fn in os.walk(dom):
        for f in fn:
            if not f.endswith('.go'):
                continue
            p = os.path.join(dp, f)
            lp = chr(92) * 2 + '?' + chr(92) + p
            s = open(lp, encoding='utf-8', errors='ignore').read()
            if 'runtime.Caller(0)' not in s:
                continue
            rel = os.path.relpath(p, srv).replace(os.sep, '/')
            s2 = PAT.sub(lambda m: 'var %s = "%s"' % (m.group(2), rel), s)
            if s2 != s:
                s2 = re.sub(r'^\s*"runtime"\s*\n', '', s2, flags=re.M)
                open(lp, 'w', encoding='utf-8', newline='').write(s2)
                n += 1
print('patched', n, 'files')