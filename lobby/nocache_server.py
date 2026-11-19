# -*- coding: utf-8 -*-
"""no-cache 静态服务器：避免浏览器缓存补丁后的引擎 js。"""
import http.server, socketserver, os, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else r'D:\lobby_fe'
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8082

class H(http.server.SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    def log_message(self, *a):
        pass

socketserver.TCPServer.allow_reuse_address = True
with http.server.ThreadingHTTPServer(('127.0.0.1', PORT), H) as httpd:
    print('no-cache static server', PORT, ROOT, flush=True)
    httpd.serve_forever()