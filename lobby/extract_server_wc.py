# -*- coding: utf-8 -*-
"""定向流式提取 svn.tar.gz: srv/svn/server/git/**(含 .git) 与 srv/svn/server/tongits-server/**(去 .svn) -> D:\\server_wc"""
import tarfile, sys, os, time, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
SRC = r'D:\BaiduNetdiskDownload\svn.tar.gz'
OUT = r'D:\server_wc'
PFX_GIT = 'srv/svn/server/git/'
PFX_TON = 'srv/svn/server/tongits-server/'
P = chr(92) * 2 + '?' + chr(92)
seen = set()
children = set()
ext = 0
t0 = time.time()
n = 0
with tarfile.open(SRC, 'r|gz') as tf:
    for m in tf:
        n += 1
        name = m.name
        if name.startswith(PFX_GIT):
            seen.add('git')
            rel = name[len(PFX_GIT):]
            c = rel.split('/')[0]
            if c and c not in children:
                children.add(c)
                print('GITCHILD', c, 'at entry', n, 'elapsed', int(time.time() - t0), flush=True)
            if not rel or rel.startswith('.svn') or '/.svn' in rel:
                continue
            dst = os.path.join(OUT, 'git', rel.replace('/', os.sep))
            if m.isdir():
                os.makedirs(P + dst, exist_ok=True)
            elif m.isfile():
                os.makedirs(P + os.path.dirname(dst), exist_ok=True)
                open(P + dst, 'wb').write(tf.extractfile(m).read())
                ext += 1
        elif name.startswith(PFX_TON):
            seen.add('ton')
            rel = name[len(PFX_TON):]
            if not rel or rel.startswith('.svn') or '/.svn' in rel:
                continue
            dst = os.path.join(OUT, 'tongits-server', rel.replace('/', os.sep))
            if m.isdir():
                os.makedirs(P + dst, exist_ok=True)
            elif m.isfile():
                os.makedirs(P + os.path.dirname(dst), exist_ok=True)
                open(P + dst, 'wb').write(tf.extractfile(m).read())
                ext += 1
        elif len(seen) == 2 and name > 'srv/svn/server/tongits-server-APP~':
            print('past targets, break at', name, flush=True)
            break
        if ext and ext % 2000 == 0:
            print('ext', ext, 'entry', n, 'elapsed', int(time.time() - t0), flush=True)
print('SERVERWC_DONE extracted', ext, 'seen', sorted(seen), 'git children', sorted(children), 'elapsed', int(time.time() - t0), flush=True)