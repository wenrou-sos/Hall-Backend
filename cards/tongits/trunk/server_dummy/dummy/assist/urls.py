
from handlers import *
from network import dbghandler

sMainUrls = [
    (r"/downservice/", HDRShutdownService),
    (r"/dotask/", HDRDoTask),
    (r"/gmproc/", HDRGMProc),
    (r"/supop/", dbghandler.HDRDebug),
]