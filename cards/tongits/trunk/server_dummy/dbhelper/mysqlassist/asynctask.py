
import asyncio
import threading
from queue import Queue
import time
from mysqlassist.utils import *

class AsyncDelegate(threading.Thread):
    def __init__(self, mysqlhdr_pool = None, queue_size = 128, sleep_time = 0.02, daemon = True):
        super().__init__()
        self.daemon = daemon
        self.mPool = mysqlhdr_pool
        self.mQueueSize = queue_size
        self.mQueue1st = Queue(maxsize = queue_size)
        self.mQueue2nd = Queue(maxsize = queue_size)
        self.mSleepTime = sleep_time
        self.mIsRunning = False

    def __repr__(self):
        return "<AsyncDelegate>[QueueSize:%d][SleepTime:%fs]" % (self.mQueueSize, self.mSleepTime)

    @property
    def IsEmpty(self):
        return self.mQueue1st.empty() and self.mQueue2nd.empty()

    def run(self):
        if self.mIsRunning:
            return
        Info("MySQL异步线程启动！")
        self.mIsRunning = True
        while self.mIsRunning:
            while not self.mQueue1st.empty():
                try:
                    task = self.mQueue1st.get(block = False)
                    conn = task[0]
                    sql = task[1]
                    hint = task[2]
                    cb = task[3]
                    if conn is None:
                        # Warn("不存在有效连接用于查询！")
                        self.mQueue2nd.put((conn, sql, hint, cb))
                    else:
                        self.mQueue2nd.put((conn, conn.Exec(sql), hint, cb, ))
                except:
                    PrintEXC()
                    break
            time.sleep(self.mSleepTime)

    def stop(self):
        self.mIsRunning = False

    def PushTask(self, sql = "", hint = None, callback = None): # CBtype : def fun(hint, results) 
        self.mQueue1st.put((self.mPool.GetConnection(), sql, hint, callback, ))

    def Update(self):
        while not self.mQueue2nd.empty():
            try:
                task_result = self.mQueue2nd.get(block = False)
                if task_result[0] is None:
                    self.PushTask(sql = task_result[1], hint = task_result[2], callback = task_result[3])
                    # Warn("任务再循环：", task_result[2], task_result[3], "活跃连接数：", self.mPool.ActiveCount)
                else:
                    conn = task_result[0]
                    sql_results = task_result[1]
                    hint = task_result[2]
                    cb = task_result[3]
                    if cb is not None:
                        cb(hint, sql_results)
                    self.mPool.ReleaseConnection(conn)
            except:
                PrintEXC()
            
    async def AsyncUpdate(self):
        while True:
            while not self.mQueue2nd.empty():
                try:
                    task_result = self.mQueue2nd.get(block = False)
                    if task_result[0] is None:
                        self.PushTask(sql = task_result[1], hint = task_result[2], callback = task_result[3])
                        # Warn("任务再循环：", task_result[2], task_result[3], "活跃连接数：", self.mPool.ActiveCount)
                    else:
                        conn = task_result[0]
                        sql_results = task_result[1]
                        hint = task_result[2]
                        cb = task_result[3]
                        if cb is not None:
                            cb(hint, sql_results)
                        self.mPool.ReleaseConnection(conn)
                except:
                    PrintEXC()
            await asyncio.sleep(0.02)