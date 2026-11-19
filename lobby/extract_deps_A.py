# -*- coding: utf-8 -*-
"""A 组：按各 server go.mod 提取私有依赖到 deps_<name>（独立版本套），checkout tag，缺 go.mod 合成，加 replace。
用法: python extract_deps_A.py [family ...]  默认 paikang52 fishshrimpcrab"""
import json, hashlib, subprocess, os, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
ROOT = os.path.dirname(os.path.abspath(__file__))
FISH = os.path.dirname(ROOT)
TAR = r'D:\BaiduNetdiskDownload\1684674626_2023_05_21_13.3.2_gitlab_backup.tar'
BUNDLES = os.path.join(FISH, 'bundles')
ALL = {'dummy': 'dummy', 'paikang52': 'paikang52', 'fishshrimpcrab': 'fishshrimpcrab'}
fams = sys.argv[1:] or ['paikang52', 'fishshrimpcrab']
projects = json.load(open(os.path.join(FISH, '..', 'gitlab_backup_inspect', 'projects.json'), encoding='utf-8'))
by_path = {p['full_path']: p['id'] for p in projects}

def parse_reqs(gomod):
    out = {}
    if not os.path.exists(gomod):
        return out
    txt = open(gomod, encoding='utf-8').read()
    txt = txt.split('replace (')[0]
    for m in re.finditer(r'(gitlab\.iplaystar\.net/[\w\-/]+)\s+(v[\w.\-]+)', txt):
        out.setdefault(m.group(1), m.group(2))
    return out

def bundle_rel(pid):
    h = hashlib.sha256(str(pid).encode()).hexdigest()
    return 'repositories/@hashed/%s/%s/%s.bundle' % (h[:2], h[2:4], h)

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, (r.stdout or '') + (r.stderr or '')

wanted = {f: parse_reqs(os.path.join(FISH, 'cards', ALL[f], 'go.mod')) for f in fams}
report = {f: {} for f in fams}
for rnd in range(5):
    new = {f: {p: v for p, v in wanted[f].items() if p not in report[f]} for f in fams}
    allnew = set()
    for f in fams:
        allnew |= set(new[f])
    if not allnew:
        break
    rels = []
    for path in sorted(allnew):
        pid = by_path.get(path.replace('gitlab.iplaystar.net/', ''))
        if pid is None:
            print('!! missing project', path); continue
        rel = bundle_rel(pid)
        if not os.path.exists(os.path.join(BUNDLES, rel.replace('/', os.sep))):
            rels.append(rel)
    if rels:
        fl = os.path.join(ROOT, 'depsA_filelist.txt')
        open(fl, 'w', encoding='utf-8').write('\n'.join(rels))
        code, out = run(['tar', '-xf', TAR, '-C', BUNDLES, '-T', fl])
        print('round', rnd, 'tar rc', code, out[:400])
    for f in fams:
        deps = os.path.join(FISH, 'deps_' + f)
        os.makedirs(deps, exist_ok=True)
        for path, ver in new[f].items():
            pid = by_path.get(path.replace('gitlab.iplaystar.net/', ''))
            if pid is None:
                report[f][path] = {'dir': None, 'used': 'MISSING_PROJECT'}
                continue
            name = path.split('/')[-1]
            dest = os.path.join(deps, name)
            b = os.path.join(BUNDLES, bundle_rel(pid).replace('/', os.sep))
            if not os.path.exists(b):
                print('!! bundle missing', f, path)
                report[f][path] = {'dir': None, 'used': 'MISSING_BUNDLE'}
                continue
            if not os.path.exists(dest):
                code, out = run(['git', '-c', 'core.longpaths=true', 'clone', '-q', b, dest])
                if code != 0:
                    print('clone fail', f, name, out[:200])
                    report[f][path] = {'dir': None, 'used': 'CLONE_FAIL'}
                    continue
            code, tags = run(['git', '-C', dest, 'tag', '-l'])
            if ver in tags.split():
                run(['git', '-C', dest, 'checkout', '-q', ver]); used = ver
            else:
                used = 'master(no tag %s)' % ver
            if not os.path.exists(os.path.join(dest, 'go.mod')):
                open(os.path.join(dest, 'go.mod'), 'w', encoding='utf-8').write('module %s\n\ngo 1.15\n' % path)
            report[f][path] = {'dir': name, 'used': used}
            print('%-14s %-50s -> %s' % (f, path, used))
        for path, info in list(report[f].items()):
            if info['dir']:
                for p2, v2 in parse_reqs(os.path.join(deps, info['dir'], 'go.mod')).items():
                    wanted[f].setdefault(p2, v2)
for f in fams:
    gomod = os.path.join(FISH, 'cards', ALL[f], 'go.mod')
    txt = open(gomod, encoding='utf-8').read()
    if 'replace (' not in txt:
        lines = ['\nreplace (']
        for path, info in sorted(report[f].items()):
            if info['dir']:
                lines.append('\t%s => ../../deps_%s/%s' % (path, f, info['dir']))
        lines.append(')\n')
        open(gomod, 'a', encoding='utf-8').write('\n'.join(lines))
    print(f, 'deps count', len([1 for i in report[f].values() if i['dir']]), '; replace added')
json.dump(report, open(os.path.join(ROOT, 'deps_A_report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('DEPS_A_DONE')