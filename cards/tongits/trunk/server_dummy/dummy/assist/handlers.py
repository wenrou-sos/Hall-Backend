
import json
import struct
import asyncio
import socket
import hashlib
from tornado.web import RequestHandler
from c_l_lobby_pb2 import *
from dbtask import TaskQueue
from gmproc import sProc
from utils import *

sRespErrOK = 0
sRespErrExc = -1
sRespErrNoneRP = -2
sRespErrARGVErr = -3

class RespData(object):

    @classmethod
    def Default(cls, data = None):
        return cls(data = data)

    def __init__(self, data = None):
        self.mMainData = {
            "err" : sRespErrOK
        }
        if data is not None:
            if isinstance(data, dict):
                self.mMainData.update(data)
            else:
                self.mMainData["ex"] = data
        self.mCtorTime = time.time()

    @property
    def Data(self):
        return self.mMainData

    def SetResult(self, ret):
        self.mMainData["use_time"] = "%.6fs" % (time.time() - self.mCtorTime)
        if isinstance(ret, str):
            self.mMainData["ret"] = ret
        else:
            self.mMainData["d"] = ret
            self.mMainData["ret"] = "ok"

    def OK(self):
        self.mMainData["err"] = sRespErrOK
        return self

    def Exc(self):
        self.mMainData["err"] = sRespErrExc
        return self

    def NoneRP(self):
        self.mMainData["err"] = sRespErrOutCtrl
        return self

    def ARGVErr(self):
        self.mMainData["err"] = sRespErrARGVErr
        return self

# Main
class HDRShutdownService(RequestHandler):
    def get(self):
        resp = RespData.Default()
        self.application.ShutdownService()
        resp.SetResult("ok")
        self.write(json.dumps(resp.Data))
        self.flush()
        self.finish()

class HDRDoTask(RequestHandler):
    async def get(self):
        Log("收到请求：", HDRDoTask)
        resp = RespData.Default()
        try:
            tasks = json.loads(self.get_argument("tasks"))
            task_resp = {}
            cache = {
                "task_count" : len(tasks),
                "task_resp" : task_resp
            }

            params_group = {}
            for i in range(len(tasks)):
                task = tasks[i]
                proxy_name = task["proxy_name"]
                task_type = task["task_type"]
                task_data = task["data"]
                sign = proxy_name + "|" + task_type + "|" + task_data
                if sign in params_group:
                    task_resp[sign + "(repeat:" + str(i) + ")"] = { "msg" : "repeat" }
                else:
                    params_group[sign] = (proxy_name, task_type, task_data, )

            for sign in params_group:
                params = params_group[sign]
                ret = TaskQueue.Push(params[0], params[1], params[2], hint_data = { "callback" : self.CheckComplete, "cache" : cache, "sign" : sign }, immed = True)
                if ret != 0:
                    task_resp[sign] = { "msg" : "Task push error -> " + str(ret) }

            if len(cache["task_resp"]) < cache["task_count"]:
                while "end" not in cache:
                    await asyncio.sleep(0.02)
                cache.pop("end")
            resp.SetResult(cache)
            self.write(json.dumps(resp.Data))
            self.flush()
            self.finish()
        except:
            PrintEXC()
            resp = resp.Exc()
            self.write(json.dumps(resp.Data))
            self.flush()
            self.finish()

    def CheckComplete(self, hint):
        Log("任务处理回调：", hint)
        cache = hint.pop("cache")
        sign = hint.pop("sign")
        task_resp = cache["task_resp"]
        task_resp[sign] = hint
        if len(task_resp) >= cache["task_count"]:
            cache["end"] = 0

class HDRGMProc(RequestHandler):
    async def post(self):
        Log("收到请求：", HDRGMProc)
        resp = RespData.Default()
        try:
            op = int(self.get_body_argument("op"))
            ex = json.loads(self.get_body_argument("ex"))
            if op in sProc:
                Log("GMProcID:", op)
                begin_time = time.time()
                ret = await sProc[op](ex)
                resp.SetResult(ret)
            else:
                Err("无效的GMProcID：", op)
                resp = resp.ARGVErr()
        except:
            PrintEXC()
            resp = resp.Exc()
        Info("GMProc响应：", resp.Data)
        self.write(json.dumps(resp.Data))
        self.flush()
        self.finish()