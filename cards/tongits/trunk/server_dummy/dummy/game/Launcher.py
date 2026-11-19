#!/bin/python

import sys
import os

sys.path.append(('%s/../..' % (os.getcwd())))
sys.path.append(('%s/../../utils'%(os.getcwd())))
sys.path.append(('%s/../../dbhelper'%(os.getcwd())))
sys.path.append(('%s/../../proto/dummy/client_center' % (os.getcwd())))
sys.path.append(('%s/../../proto/dummy/main_cmd' % (os.getcwd())))
sys.path.append(('%s/../../proto/dummy/subgame' % (os.getcwd())))

from mainservice import MainService
import threading
import json
import synchronize

if __name__ == "__main__":
    if len(sys.argv) <= 3:
        Err("Usage：python -u -m Launcher `host_api_key` `subgame_id` `server_port`")
        exit()
    host_api_key = sys.argv[1]
    subgame_id = sys.argv[2]
    server_port = int(sys.argv[3])
    cfg = {}
    with open("cfg/main.json", "r") as hd:
        cfg = json.loads(hd.read())
    #multihost_redis = cfg["multihost_redis"]
    # t = threading.Thread(target=synchronize.synchronize_data, args=(
    # multihost_redis["host"], multihost_redis["port"], multihost_redis["db"], multihost_redis["password"],
    # host_api_key, subgame_id))
    # # 執行該子執行緒
    # t.start()
    MainService.GetInstance(host_api_key, subgame_id, server_port).StartService()