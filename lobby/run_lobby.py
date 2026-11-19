# -*- coding: utf-8 -*-
"""launcher:  bundled python 为隔离模式(不 prepend 脚本目录)，手动注入 sys.path 后运行 lobbyserver。"""
import sys, os, runpy
HERE = os.path.dirname(os.path.abspath(__file__))
SRV = os.path.join(HERE, 'lobbyserver')
sys.path.insert(0, SRV)
os.chdir(SRV)
runpy.run_path(os.path.join(SRV, 'lobbyserver.py'), run_name='__main__')