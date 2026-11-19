
from network.webserver import *
from network import dbghandler

sUrls = [
    (r"/service/", WSConnection),
    (r"/supop/", dbghandler.HDRDebug),
]