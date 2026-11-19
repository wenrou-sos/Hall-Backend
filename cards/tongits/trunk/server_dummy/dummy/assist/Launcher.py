#!/bin/python

import sys
import os
import json

sys.path.append(('%s/../..' % (os.getcwd())))
sys.path.append(('%s/../../dbhelper'%(os.getcwd())))
sys.path.append(('%s/../../proto/dummy/client_center' % (os.getcwd())))
sys.path.append(('%s/../../proto/dummy/main_cmd' % (os.getcwd())))
sys.path.append(('%s/../../proto/dummy/subgame' % (os.getcwd())))
sys.path.append(('%s/../../utils' % (os.getcwd())))

from mainservice import MainService

if __name__ == "__main__":
    cfg_path = "cfg/main.json"
    cfg_data = {}
    with open(cfg_path, "r") as hd:
        cfg_data = json.loads(hd.read())
    MainService.StartService(**cfg_data)