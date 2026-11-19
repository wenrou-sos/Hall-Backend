# -*- coding: utf-8 -*-
"""dev 无 DB: 给 accounting 所有用到 a.db 的方法加 nil 守卫, 避免 gorm nil panic。"""
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
deps = ['deps_paikang52', 'deps_u-game-server', 'deps_colorgame', 'deps_fishshrimpcrab', 'deps_card']
for dep in deps:
    p = r'.\fish\%s\accounting\accounting.go' % dep
    try:
        lines = open(p, 'rb').read().decode('utf-8').split('\n')
    except FileNotFoundError:
        print(dep, 'missing'); continue
    out = []
    cur_func = None
    guarded = set()
    ret = 'false'
    for i, ln in enumerate(lines):
        out.append(ln)
        m = re.match(r'func \(a \*Accounting\) (\w+)\(', ln)
        if m:
            cur_func = m.group(1)
            ret = 'false' if cur_func == 'create' else 'true'
        if cur_func and cur_func not in guarded and 'a.db.' in ln:
            # insert guard after the opening brace line of current func: find it backwards
            # simpler: insert guard immediately before first a.db usage is unsafe; insert at func open
            # locate func open index in out
            for j in range(len(out) - 1, -1, -1):
                if re.match(r'func \(a \*Accounting\) %s\(' % cur_func, out[j]):
                    # opening brace may be same line or next; insert after line ending '{'
                    k = j
                    while not out[k].rstrip().endswith('{'):
                        k += 1
                    out.insert(k + 1, '    if a.db == nil { return %s } // dev: no DB' % ret)
                    guarded.add(cur_func)
                    break
    open(p, 'wb').write('\n'.join(out).encode('utf-8'))
    print(dep, 'guarded methods:', sorted(guarded))