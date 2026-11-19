# -*- coding: utf-8 -*-
"""protobuf-3.0-beta hash.h 适配现代 MSVC: 用 std::unordered_map/set 替代 stdext::hash_compare。"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'D:\slot_src\lib\protobuf-3.0.0-beta-1\src\google\protobuf\stubs\hash.h'
d = open(p, encoding='utf-8', errors='replace').read()
old = '#  define GOOGLE_PROTOBUF_HAS_CXX11_HASH\n#  define GOOGLE_PROTOBUF_HASH_COMPARE std::hash_compare'
new = ('#  define GOOGLE_PROTOBUF_HAS_CXX11_HASH\n'
       '#  define GOOGLE_PROTOBUF_HASH_NAMESPACE std\n'
       '#  include <unordered_map>\n'
       '#  define GOOGLE_PROTOBUF_HASH_MAP_CLASS unordered_map\n'
       '#  include <unordered_set>\n'
       '#  define GOOGLE_PROTOBUF_HASH_SET_CLASS unordered_set')
assert old in d, 'msvc macro'
d = d.replace(old, new, 1)
old2 = '#elif defined(_MSC_VER) && !defined(_STLPORT_VERSION)\n\ntemplate <typename Key>\nstruct hash : public GOOGLE_PROTOBUF_HASH_COMPARE<Key> {'
new2 = '#elif defined(_MSC_VER) && !defined(_STLPORT_VERSION) && (_MSC_VER < 1600)\n\ntemplate <typename Key>\nstruct hash : public GOOGLE_PROTOBUF_HASH_COMPARE<Key> {'
assert old2 in d, 'msvc branch'
d = d.replace(old2, new2, 1)
open(p, 'w', encoding='utf-8').write(d)
print('protobuf hash.h patched for modern MSVC')