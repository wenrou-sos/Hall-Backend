# -*- coding: utf-8 -*-
"""本地化空实现：原版依赖 pyga 向远程 Google Analytics 上报，本地 stub 掉。"""
import env_setting

class PG_GA(object):
    def __init__(self, ip, memberid=0):
        self.ip = ip
        self.memberid = memberid
    def send_page_view(self, page, title):
        pass
    def send_event(self, *a, **kw):
        pass
