
import asyncio
import threading
import time
from queue import Queue
from utils import *

class AsyncWorker(threading.Thread):
    def __init__(self, queue_size = 128, sleep_time = 0.02, daemon = True):
        super().__init__()
        self.daemon = daemon
        self.mQueueSize = queue_size
        self.mQueue1st = Queue(maxsize = queue_size)
        self.mSleepTime = sleep_time
        self.mIsRunning = False

    def __repr__(self):
        return "<AsyncWorker>[QueueSize:%d][SleepTime:%fs]" % (self.mQueueSize, self.mSleepTime)

    @property
    def IsEmpty(self):
        return self.mQueue1st.empty()

    def GetCount(self):
        return self.mQueue1st.qsize()

    def run(self):
        if self.mIsRunning:
            return
        Info("公用异步任务线程启动！")
        self.mIsRunning = True
        while self.mIsRunning:
            while not self.mQueue1st.empty():
                try:
                    proc, hint = self.mQueue1st.get(block = False)
                    hint["result"] = proc(*(hint["args"]), **(hint["kwargs"]))
                except:
                    PrintEXC()
                    break
            time.sleep(self.mSleepTime)

    def stop(self):
        self.mIsRunning = False

    def PushTask(self, proc, hint):
        if not callable(proc):
            return False
        if not isinstance(hint, dict):
            return False
        if "args" not in hint:
            hint["args"] = tuple()
        if "kwargs" not in hint:
            hint["kwargs"] = {}
        self.mQueue1st.put((proc, hint, ))
        return True

class AsyncGuard(object):
    def __init__(self, worker_cnt = 1, *args, **kwargs):
        self.mWorkerCnt = worker_cnt
        self.mCounter = 0
        self.mWorkers = [
            AsyncWorker(*args, **kwargs) for i in range(worker_cnt)
        ]
        for worker in self.mWorkers:
            worker.start()
        Log("AsyncGuard创建：", self.mWorkers)

    def IsEmpty(self):
        for worker in self.mWorkers:
            if not worker.IsEmpty:
                return False
        return True

    def GetCount(self):
        nCount = 0
        for worker in self.mWorkers:
            nCount += worker.GetCount()
        return nCount

    async def DoAsync(self, proc, *args, **kwargs):
        hint = {
            "args" : args,
            "kwargs" : kwargs
        }
        worker = self.NextWorker()
        if worker.PushTask(proc, hint):
            while "result" not in hint:
                await asyncio.sleep(0.01)
            return hint["result"]
        else:
            Err("Push async task error:", proc, hint)
        return None

    def NextWorker(self):
        worker = self.mWorkers[self.mCounter % self.mWorkerCnt]
        self.mCounter += 1
        return worker