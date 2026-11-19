
import asyncio

class Timer(object):
    def __init__(self, timer_id, interval, cb, params):
        self.mID = timer_id
        self.mInterval = float(interval)
        self.mCallBack = cb
        self.mParams = params
        self.mIsDisposed = False

    def SetInterval(self, interval):
        self.mInterval = interval

    def SetCallBack(self, cb):
        self.mCallBack = cb

    def SetParams(self, params):
        self.mParams = params

    def Dispose(self):
        self.mIsDisposed = True

    async def Loop(self):
        while True:
            await asyncio.sleep(self.mInterval)
            if self.mIsDisposed:
                return
            else:
                need_continue = self.mCallBack(self.mParams)
                if not need_continue:
                    TimerEngine.GetInstance().RemoveTimer(self.mID)
                    return

class TimerEngineError(Exception):
    pass

class TimerEngine(object):
    sIns = None
    @classmethod
    def GetInstance(cls, attemper = None):
        if cls.sIns is None:
            cls.sIns = cls(attemper)
            cls.sIns.InitComponents()
        return cls.sIns

    def __init__(self, attemper):
        if TimerEngine.sIns != None:
            raise TimerEngineError("TimerEngine已被创建！")
        self.mAttemper = attemper
        self.mID2Timer = {}
        self.mIDCounter = 0

    def InitComponents(self):
        pass

    def AddTimer(self, interval, cb, params):
        timer_id = self.mIDCounter
        self.mIDCounter += 1
        tr = Timer(timer_id, interval, cb, params)
        self.mID2Timer[timer_id] = tr
        self.mAttemper.App.CreateTask(tr.Loop())
        return timer_id

    def RemoveTimer(self, timer_id):
        tr = self.mID2Timer.pop(timer_id, None)
        if tr is not None:
            tr.Dispose()

    def GetTimerObject(self, timer_id):
        if timer_id in self.mID2Timer:
            return self.mID2Timer[timer_id]
        else:
            return None
