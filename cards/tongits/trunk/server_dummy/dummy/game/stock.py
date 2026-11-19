
import json
from utils import *
from redisassist import RDSPGuard
from definations import *

class StockError(Exception):
    pass

class Stock(object):
    sIns = None

    @classmethod
    def GetInstance(cls, attemper = None):
        if cls.sIns is None:
            cls.sIns = cls(attemper)
            cls.sIns.InitComponents()
        return cls.sIns

    def __init__(self, attemper):
        if Stock.sIns != None:
            raise StockError("Stock已被创建！")
        self.mAttemper = attemper

    def InitComponents(self):
        return True

    def GetStockValue(self):
        try:
            rp = RDSPGuard.RP("gamelist")
            nStockValue = rp.LibGrd.R.hget("sha@stock_"+ServiceOpt.sHashKey, "stock")
            if nStockValue is not None:
                if int(nStockValue) < -100000000 or int(nStockValue) > 100000000:
                    return -100000000  # 定義水庫負數極限，避免機器人輸到從水庫無窮小變成無窮大
                else:
                    return int(nStockValue)  # 正常取水庫值
        except:
            PrintEXC()
        return 0

    def ModifyStockValue(self, variation):
        try:
            if variation is not None \
                    and isinstance(variation, int) \
                    and variation != 0:
                rp = RDSPGuard.RP("gamelist")
                rp.LibGrd.R.hincrby("sha@stock_"+ServiceOpt.sHashKey, "stock", variation)
        except:
            PrintEXC()
