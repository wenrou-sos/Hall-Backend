# -*- coding: utf-8 -*-
"""最小 Redis 协议(RESP2)服务，供本地化平台大厅使用（打桩替代远程 GCP Redis）。
支持 pg_redis 用到的命令: get/setex/set/keys/del/dbsize/expire/ttl/flushdb/lpush/rpop/llen/lrange/ltrim/ping/select/info。
"""
import asyncio, time, fnmatch

STORE = {}      # key -> (value_bytes, expire_ts or None)
LISTS = {}      # key -> list of bytes

def enc_simple(s): return b'+' + s.encode() + b'\r\n'
def enc_err(s): return b'-' + s.encode() + b'\r\n'
def enc_int(n): return b':' + str(n).encode() + b'\r\n'
def enc_bulk(b):
    if b is None: return b'$-1\r\n'
    return b'$' + str(len(b)).encode() + b'\r\n' + b + b'\r\n'
def enc_arr(items):
    out = b'*' + str(len(items)).encode() + b'\r\n'
    for it in items: out += it
    return out

def alive(key):
    if key in STORE:
        v, exp = STORE[key]
        if exp is not None and time.time() > exp:
            del STORE[key]; return None
        return v
    return None

def handle(cmd):
    if not cmd: return enc_err('ERR empty')
    name = cmd[0].decode().lower()
    args = cmd[1:]
    if name == 'ping': return enc_simple('PONG')
    if name == 'select': return enc_simple('OK')
    if name == 'info': return enc_bulk(b'# Server\r\nredis_version:5.0.14-local-stub\r\n')
    if name == 'flushdb':
        STORE.clear(); LISTS.clear(); return enc_simple('OK')
    if name == 'dbsize': return enc_int(len(STORE) + len(LISTS))
    if name == 'set':
        STORE[args[0]] = (args[1], None); return enc_simple('OK')
    if name == 'setex':
        STORE[args[0]] = (args[2], time.time() + int(args[1])); return enc_simple('OK')
    if name == 'get':
        return enc_bulk(alive(args[0]))
    if name == 'del' or name == 'delete':
        n = 0
        for k in args:
            if k in STORE: del STORE[k]; n += 1
            if k in LISTS: del LISTS[k]; n += 1
        return enc_int(n)
    if name == 'expire':
        if args[0] in STORE:
            v, _ = STORE[args[0]]; STORE[args[0]] = (v, time.time() + int(args[1])); return enc_int(1)
        return enc_int(0)
    if name == 'ttl':
        if args[0] in STORE:
            v, exp = STORE[args[0]]
            return enc_int(-1 if exp is None else max(0, int(exp - time.time())))
        return enc_int(-2)
    if name == 'keys':
        pat = args[0].decode() if args else '*'
        ks = [k for k in list(STORE) + list(LISTS) if fnmatch.fnmatch(k.decode(), pat)]
        return enc_arr([enc_bulk(k) for k in ks])
    if name == 'lpush':
        L = LISTS.setdefault(args[0], [])
        for v in args[1:]: L.insert(0, v)
        return enc_int(len(L))
    if name == 'rpop':
        L = LISTS.get(args[0], [])
        return enc_bulk(L.pop() if L else None)
    if name == 'llen': return enc_int(len(LISTS.get(args[0], [])))
    if name == 'lrange':
        L = LISTS.get(args[0], []); s = int(args[1]); e = int(args[2])
        e = len(L) - 1 if e == -1 else e
        return enc_arr([enc_bulk(v) for v in L[s:e + 1]])
    if name == 'ltrim':
        L = LISTS.get(args[0], []); s = int(args[1]); e = int(args[2])
        e = len(L) - 1 if e == -1 else e
        LISTS[args[0]] = L[s:e + 1]; return enc_simple('OK')
    return enc_simple('OK')   # 其余命令一律回 OK，保证客户端不报错

async def client(reader, writer):
    buf = b''
    try:
        while True:
            data = await reader.read(65536)
            if not data: break
            buf += data
            # 解析 RESP 数组命令
            while buf:
                if not buf.startswith(b'*'):
                    # inline command
                    idx = buf.find(b'\r\n')
                    if idx < 0: break
                    line = buf[:idx]; buf = buf[idx + 2:]
                    cmd = line.split()
                    if cmd: writer.write(handle(cmd))
                    continue
                idx = buf.find(b'\r\n')
                if idx < 0: break
                try: n = int(buf[1:idx])
                except ValueError: buf = b''; break
                pos = idx + 2; parts = []; ok = True
                for _ in range(n):
                    if pos >= len(buf) or buf[pos:pos + 1] != b'$': ok = False; break
                    j = buf.find(b'\r\n', pos)
                    if j < 0: ok = False; break
                    ln = int(buf[pos + 1:j]); pos = j + 2
                    if pos + ln + 2 > len(buf): ok = False; break
                    parts.append(buf[pos:pos + ln]); pos += ln + 2
                if not ok: break
                buf = buf[pos:]
                writer.write(handle(parts))
            await writer.drain()
    except (ConnectionResetError, asyncio.CancelledError):
        pass
    finally:
        writer.close()

async def main():
    srv = await asyncio.start_server(client, '127.0.0.1', 6379)
    print('local-stub-redis listening 127.0.0.1:6379', flush=True)
    async with srv: await srv.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())