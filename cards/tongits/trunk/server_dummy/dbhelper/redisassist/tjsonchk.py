
import os
import sys
import json
import redis
import time

db_index = "2"
if len(sys.argv) > 1:
    db_index = sys.argv[1]

r = redis.from_url("redis://:123456@192.168.1.106/" + db_index)

key_pt = "sha@sgjson_*"
items = r.keys(key_pt)

if len(items) > 0:
    err_map = {}
    for itm in items:
        uuid = itm[len(key_pt) - 1 :].decode()
        err_list = []
        data_map = r.hgetall(itm)
        for sid, jd in data_map.items():
            try:
                json.loads(jd)
            except:
                err_list.append(sid.decode())
        if len(err_list) > 0:
            err_map[uuid] = err_list
    if len(err_map) > 0:
        print("Found errors:\n", json.dumps(err_map, indent = 4))
    else:
        print("Do not find any errors!")
else:
    print("No item exists!")