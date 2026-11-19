
import google.cloud.logging
import logging
import os
from google.cloud.logging.handlers import CloudLoggingHandler, setup_logging
import env_setting

if env_setting.LOCAL_SERVER:
    AUTH_PATH = "sd555-app-d05f05dacacb.json"
else:
    AUTH_PATH = os.path.dirname(os.path.abspath(__file__)) + "//sd555-app-d05f05dacacb.json"
'''
class log:
    def __init__(self):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = AUTH_PATH
        client = google.cloud.logging.Client()
        client.setup_logging()

    def warning(self,projectdata , logdata):
        text = projectdata + " " + logdata
        logging.warning(text)

    def error(self,projectdata,logdata):
        text = projectdata + " " + logdata
        logging.error(text)

    def info(self,projectdata,logdata):
        text = projectdata + " " + logdata
        logging.info(text)

'''
class log:
    def __init__(self):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = AUTH_PATH
        client = google.cloud.logging.Client()
        handler = CloudLoggingHandler(client)
        logging.getLogger().setLevel(logging.INFO)  # defaults to WARN
        setup_logging(handler)

        if env_setting.LOCAL_SERVER:
            self.localtext = 'localserver '
        else:
            self.localtext = ''

    def warning(self,projectdata , logdata):
        text = self.localtext + projectdata + " " + logdata
        logging.warning(text)


    def error(self,projectdata,logdata):
        text = self.localtext + projectdata + " " + logdata
        logging.error(text)


    def info(self,projectdata,logdata):
        text = self.localtext + projectdata + " " + logdata
        logging.info(text)
