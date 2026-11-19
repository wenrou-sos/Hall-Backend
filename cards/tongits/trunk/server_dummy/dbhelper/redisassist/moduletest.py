from redisassist.rdsproxyguard import *
from redisassist import utils as rdsutils
import threading
import asyncio

RDSProxyGuard.LoadByFile("redisassist/cfg/dbs.json")

rp1 = RDSProxyGuard.RP("game")

lib_grd1 = rp1.LibGrd
acc = "znq"
pho = 13950051001
nam = "Zeng"
# params = lib_grd1.Call("common.GenAcc", *(acc, pho, nam, ))
# print(params)
# uuid = params[1]
# game_id = params[2]
# params = lib_grd1.Call("common.OnRegAcc", *(uuid, acc, pho, nam, "123", "123"))
# print(params)
params = lib_grd1.Call("common.ReqLogin", *("pdOjqVZYxIbdlSYgYItztAXaURzUKmHX", ))
rdsutils.Log(params)

print("-----------分割线----------")
'''
from queue import Queue
q = Queue(maxsize = 2)

class WorkerThread(threading.Thread):
    def __init__(self, daemon=True):
        super(WorkerThread, self).__init__()
        self.daemon = daemon

    def run(self):
        while True:
            try:
                x = q.get(block = False)
                print(x)
            except:
                pass

    def stop(self):
        # stopping simply unsubscribes from all channels and patterns.
        # the unsubscribe responses that are generated will short circuit
        # the loop in run(), calling pubsub.close() to clean up the connection
        self.pubsub.unsubscribe()
        self.pubsub.punsubscribe()

worker = WorkerThread()
worker.start()

for i in range(50000):
    q.put(i)
'''
print("-----------分割线----------")

async_helper1 = rp1.AsyncHelper

async def DoTask(hint):
    print("Begin:", hint)
    print("End:", hint, (await async_helper1.Exec("GET", "var@uuid")))

tasks = [DoTask(val) for val in range(100)]

loop = asyncio.get_event_loop()
print("Loop begin!")
loop.run_until_complete(asyncio.wait(tasks))
# loop.close()
print("Loop end!")

tasks = [DoTask(val) for val in range(100)]

loop = asyncio.get_event_loop()
print("Loop begin!")
loop.run_until_complete(asyncio.wait(tasks))
print("Loop end!")

print("-----------分割线----------")
'''
tasks = [rp1.PubSub.AsyncUpdate(), rp1.LibGrd.AsyncUpdate()]
loop = asyncio.get_event_loop()
print("Loop begin!")
loop.run_until_complete(asyncio.wait(tasks))
loop.close()
print("Loop end!")
'''