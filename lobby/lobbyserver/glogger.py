# -*- coding: utf-8 -*-
"""本地化 glogger：原版依赖 google.cloud.logging，stub 为本地 logging。"""
import logging
import env_setting

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

class log:
    def __init__(self):
        self.localtext = 'localserver ' if env_setting.LOCAL_SERVER else ''
    def warning(self, projectdata, logdata):
        logging.warning(self.localtext + str(projectdata) + ' ' + str(logdata))
    def error(self, projectdata, logdata):
        logging.error(self.localtext + str(projectdata) + ' ' + str(logdata))
    def info(self, projectdata, logdata):
        logging.info(self.localtext + str(projectdata) + ' ' + str(logdata))