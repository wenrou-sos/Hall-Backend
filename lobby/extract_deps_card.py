# -*- coding: utf-8 -*-
"""按 89-game-server go.mod 提取卡牌所需内部库到 deps_card（独立版本套），并加 replace。"""
import json, hashlib, subprocess, os, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.abspath(__file__))          # fish/lobby
FISH = os.path.dirname(ROOT)                              # fish
TAR = r'D:\BaiduNetdiskDownload\1684674626_2023_05_21_13.3.2_gitlab_backup.tar'
BUNDLES = os.path.join(FISH, 'bundles')
DEPS = os.path.join(FISH, 'deps_card')
SERVER = os.path.join(FISH, 'cards', '89-game-server')
os.makedirs(DEPS, exist_ok=True)
projects = json.load(open(os.path.join(FISH, '..', 'gitlab_backup_inspect', 'projects.json'), encoding='utf-8'))
by_path = {p['full_path']: p['id'] for p in projects}

def parse_reqs(gomod):
    out = {}
    if not os.path.exists(gomod):
        return out
    txt = open(gomod, encoding='utf-8').read()
    for m in re.finditer(r'(gitlab\.iplaystar\.net/[\w\-/]+)\s+(v[\w\.\-]+)', txt):
        out.setdefault(m.group(1), m.group(2))
    return out

def bundle_rel(pid):
    h = hashlib.sha256(str(pid).encode()).hexdigest()
    return 'repositories/@hashed/%s/%s/%s.bundle' % (h[:2], h[2:4], h)

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, (r.stdout or '') + (r.stderr or '')

wanted = parse_reqs(os.path.join(SERVER, 'go.mod'))
report = {}
for rnd in range(4):
    new = {p: v for p, v in wanted.items() if p not in report}
    if not new:
        break
    rels = []
    for path in new:
        pid = by_path.get(path.replace('gitlab.iplaystar.net/', ''))
        if pid is None:
            print('!! missing project', path); continue
        rels.append(bundle_rel(pid))
    fl = os.path.join(ROOT, 'card_filelist.txt')
    open(fl, 'w', encoding='utf-8').write('\n'.join(rels))
    run(['tar', '-xf', TAR, '-C', BUNDLES, '-T', fl])
    for path, ver in new.items():
        pid = by_path.get(path.replace('gitlab.iplaystar.net/', ''))
        if pid is None:
            continue
        name = path.split('/')[-1]
        dest = os.path.join(DEPS, name)
        b = os.path.join(BUNDLES, bundle_rel(pid).replace('/', os.sep))
        if not os.path.exists(dest):
            code, out = run(['git', '-c', 'core.longpaths=true', 'clone', '-q', b, dest])
            if code != 0:
                print('clone fail', name, out[:200]); continue
        code, tags = run(['git', '-C', dest, 'tag', '-l'])
        if ver in tags.split():
            run(['git', '-C', dest, 'checkout', '-q', ver]); used = ver
        else:
            used = 'master(no tag %s)' % ver
        if not os.path.exists(os.path.join(dest, 'go.mod')):
            open(os.path.join(dest, 'go.mod'), 'w', encoding='utf-8').write('module %s\n\ngo 1.15\n' % path)
        report[path] = {'dir': name, 'used': used}
        print('%-50s -> %s' % (path, used))
    for path, info in list(report.items()):
        for p2, v2 in parse_reqs(os.path.join(DEPS, info['dir'], 'go.mod')).items():
            wanted.setdefault(p2, v2)

gomod = os.path.join(SERVER, 'go.mod')
txt = open(gomod, encoding='utf-8').read()
if 'replace (' not in txt:
    lines = ['\nreplace (']
    for path, info in sorted(report.items()):
        lines.append('\t%s => ../../deps_card/%s' % (path, info['dir']))
    lines.append(')\n')
    open(gomod, 'a', encoding='utf-8').write('\n'.join(lines))
print('deps_card count', len(report), '; replace added')