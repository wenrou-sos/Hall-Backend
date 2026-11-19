#!/bin/python

import sys
import os
import json

sys.path.append(('%s/../..' % (os.getcwd())))
sys.path.append(('%s/../../utils'%(os.getcwd())))
sys.path.append(('%s/../../dbhelper'%(os.getcwd())))
sys.path.append(('%s/../../proto/dummy/client_center' % (os.getcwd())))
sys.path.append(('%s/../../proto/dummy/main_cmd' % (os.getcwd())))

from mainservice import MainService

if __name__ == "__main__":
    options = {}
    with open("cfg/main.json", "r") as hd:
        options = json.loads(hd.read())
    if len(sys.argv) >= 2:
        options["port"] = int(sys.argv[1])
    MainService.GetInstance().StartService(**options)