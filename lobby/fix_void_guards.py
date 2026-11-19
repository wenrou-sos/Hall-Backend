# -*- coding: utf-8 -*-
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
deps = ['deps_paikang52', 'deps_u-game-server', 'deps_colorgame', 'deps_fishshrimpcrab', 'deps_card']
for dep in deps:
    p = r'.\fish\%s\accounting\accounting.go' % dep
    lines = open(p, encoding='utf-8').read().split('\n')
    cur_void = False
    n = 0
    for i, ln in enumerate(lines):
        m = re.match(r'func \(a \*Accounting\) \w+\([^)]*\)\s*(\w*)\s*\{', ln)
        if m:
            cur_void = (m.group(1) == '')
        if 'if a.db == nil { return' in ln and cur_void:
            lines[i] = '    if a.db == nil { return } // dev: no DB'
            n += 1
    open(p, 'w', encoding='utf-8').write('\n'.join(lines))
    print(dep, 'void guards fixed:', n)