# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'.\fish\deps_card\wallet\wallet_dev.go'
d = open(p, 'rb').read().decode('utf-8')
old = 'cent:            0,'
new = 'cent:            b.balance,'
assert old in d
d = d.replace(old, new, 1)
open(p, 'wb').write(d.encode('utf-8'))
print('deps_card wallet dev cent = balance (fix 3100_2)')