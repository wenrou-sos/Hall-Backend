# -*- coding: utf-8 -*-
"""B 组补充: 本地已有源码(如 D:\\server_wc\\git\\<name>)的 server -> 复制到 fish/cards/<name>, 复用 extract_servers_b.py 的 deps 管线。
用法: python extract_servers_b2.py <name>=<src_dir> [<name>=<src_dir> ...]
"""
import json, hashlib, subprocess, os, re, sys, io, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
ROOT = os.path.dirname(os.path.abspath(__file__))
FISH = os.path.dirname(ROOT)
TAR = r'D:\BaiduNetdiskDownload\1684674626_2023_05_21_13.3.2_gitlab_backup.tar'
BUNDLES = os.path.join(FISH, 'bundles')
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

def bundle_abs(pid):
    return os.path.join(BUNDLES, bundle_rel(pid).replace('/', os.sep))

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, (r.stdout or '') + (r.stderr or '')

def tar_extract(rels):
    rels = [r for r in rels if not os.path.exists(os.path.join(BUNDLES, r.replace('/', os.sep)))]
    if not rels:
        return
    fl = os.path.join(ROOT, 'b2_batch_filelist.txt')
    open(fl, 'w', encoding='utf-8').write('\n'.join(rels))
    code, out = run(['tar', '-xf', TAR, '-C', BUNDLES, '-T', fl])
    print('tar scan for %d bundles rc=%d %s' % (len(rels), code, out[:200]), flush=True)

pairs = []
for a in sys.argv[1:]:
    name, src = a.split('=', 1)
    pairs.append((name, src))
servers = {}
for name, src in pairs:
    dest = os.path.join(FISH, 'cards', name)
    if not os.path.exists(dest):
        if not os.path.isdir(src):
            print('!! src missing', name, src, flush=True); continue
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns('.svn'))
    if not os.path.exists(os.path.join(dest, 'go.mod')):
        print('!! no go.mod at root, skip deps:', name, flush=True)
        continue
    servers[name] = dest
    print('server ready:', name, flush=True)

wanted = {name: parse_reqs(os.path.join(dest, 'go.mod')) for name, dest in servers.items()}
reports = {name: {} for name in servers}
for rnd in range(5):
    need = {}
    for name in servers:
        for p, v in wanted[name].items():
            if p not in reports[name]:
                pid = by_path.get(p.replace('gitlab.iplaystar.net/', ''))
                if pid is None:
                    print('!! missing project', p, flush=True)
                    reports[name][p] = {'dir': p.split('/')[-1], 'used': 'NOPROJECT'}
                else:
                    need.setdefault(pid, p)
    if not need:
        break
    tar_extract([bundle_rel(pid) for pid in need])
    for name in servers:
        deps = os.path.join(FISH, 'deps_' + name)
        os.makedirs(deps, exist_ok=True)
        for p, v in list(wanted[name].items()):
            if p in reports[name]:
                continue
            pid = by_path.get(p.replace('gitlab.iplaystar.net/', ''))
            if pid is None:
                continue
            dname = p.split('/')[-1]
            dest = os.path.join(deps, dname)
            bb = bundle_abs(pid)
            if not os.path.exists(bb):
                print('!! bundle missing', name, p, flush=True)
                reports[name][p] = {'dir': dname, 'used': 'MISSING'}
                continue
            if not os.path.exists(dest):
                code, out = run(['git', '-c', 'core.longpaths=true', 'clone', '-q', bb, dest])
                if code != 0:
                    print('clone fail', name, dname, out[:200], flush=True)
                    continue
            code, tags = run(['git', '-C', dest, 'tag', '-l'])
            if v in tags.split():
                run(['git', '-C', dest, 'checkout', '-q', v]); used = v
            else:
                used = 'master(no tag %s)' % v
            if not os.path.exists(os.path.join(dest, 'go.mod')):
                open(os.path.join(dest, 'go.mod'), 'w', encoding='utf-8').write('module %s\n\ngo 1.15\n' % p)
            reports[name][p] = {'dir': dname, 'used': used}
        for p, info in list(reports[name].items()):
            for p2, v2 in parse_reqs(os.path.join(deps, info['dir'], 'go.mod')).items():
                wanted[name].setdefault(p2, v2)
    print('round', rnd, 'done', {n: len(r) for n, r in reports.items()}, flush=True)

for name, dest in servers.items():
    gomod = os.path.join(dest, 'go.mod')
    txt = open(gomod, encoding='utf-8').read()
    if 'replace (' not in txt:
        lines = ['\nreplace (']
        for p, info in sorted(reports[name].items()):
            if info['used'] in ('MISSING', 'NOPROJECT'):
                continue
            lines.append('\t%s => ../../deps_%s/%s' % (p, name, info['dir']))
        lines.append(')\n')
        open(gomod, 'a', encoding='utf-8').write('\n'.join(lines))
    json.dump(reports[name], open(os.path.join(ROOT, 'b_%s_deps.json' % name), 'w', encoding='utf-8'), indent=1)
    print('replace added:', name, 'deps', len(reports[name]), flush=True)
print('EXTRACT_B2_DONE', flush=True)