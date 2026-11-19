
import importlib
from definations import *
from dbexecution import sSqls
from mysqlassist import MYPGuard
from user import *
from utils import *
import numpy
import math

android_vip = False  # 設置機器人取得同桌是否有vip玩家

class AndroidServiceError(Exception):
    pass

class AndroidDelegate(object):
    def __init__(self):
        pass

    def OnAndroidSitDown(self, mTable):
        pass

    def OnAndroidReady(self):
        pass

    def OnConcludeGame(self):
        pass

    def OnUpdate(self):
        pass

class SvrAndtoidInfo(object):
    def __init__(self):
        self.nUUID = 0
        self.nLeaveRate = 0
        self.nMinPlayDraw = 0
        self.nMaxPlayDraw = 0
        self.nMinTakeScore = 0
        self.nMaxTakeScore = 0
        self.nMinResponseTime = 0
        self.nMaxResponseTime = 0
        self.nPlayTime = 0
        self.nSex = 0
        self.nFaceID = 0
        self.mNickName = ''

    def SetOption(self, mData):
        self.nUUID = mData["id"]
        self.nLeaveRate = mData["LeaveRate"]
        self.nMinPlayDraw = mData["MinPlayDraw"]
        self.nMaxPlayDraw = mData["MaxPlayDraw"]
        self.nMinTakeScore = mData["MinTakeScore"]
        self.nMaxTakeScore = mData["MaxTakeScore"]
        self.nMinResponseTime = mData["MinReposeTime"]
        self.nMaxResponseTime = mData["MaxReposeTime"]
        self.nPlayTime = mData["ServiceTime"]
        self.nSex = mData["Sex"]
        self.nFaceID = mData["FaceID"]
        self.mNickName = mData["NickName"]

class AndroidUserItem(object):
    def __init__(self, sAndroidInfo):
        self.mAndroidInfo = sAndroidInfo     # 机器人配置信息
        self.mAndroidSink = None
        self.nCreateTime = 0    # 创建时间
        self.nRepositTime = 0   # 复位时间
        self.nCurrRounds = 0    # 当前局数
        self.nRounds = 0        # 机器人退出当前桌子以后，随机赋予下次可玩的游戏局数
        self.nLeaveRate = 0     # 离开概率
        self.nInitScore = 0     # 初始金币
        self.nServiceTime = 0   # 服务时间
        self.nLeftPlayDraw = 0  # 剩余局数
        self.nLeaveTime = 0
        self.Inititlize()

    def Inititlize(self):
        self.mSvrUserItem = SvrUserItem()
        self.mSvrUserItem.mUserInfo = SvrUserInfo()
        self.mSvrUserItem.mUserInfo.mUUID = self.mAndroidInfo.nUUID
        self.mSvrUserItem.mUserInfo.mGameID = self.mAndroidInfo.nUUID
        self.mSvrUserItem.mUserInfo.mFaceID = self.mAndroidInfo.nFaceID
        self.mSvrUserItem.mUserInfo.mSex = self.mAndroidInfo.nSex
        self.mSvrUserItem.mUserInfo.mScore = self.mAndroidInfo.nMinTakeScore
        self.mSvrUserItem.mUserInfo.mNickName = self.mAndroidInfo.mNickName
        self.mSvrUserItem.SetSrvUserStatus(eUS.US_FREE, INVALID_TABLE, INVALID_CHAIR)
        self.mSvrUserItem.mAndroidTag = True
        # 异常配置检测
        if self.mAndroidInfo.nMinTakeScore > self.mAndroidInfo.nMaxTakeScore \
                or self.mAndroidInfo.nMinPlayDraw > self.mAndroidInfo.nMaxPlayDraw \
                or self.mAndroidInfo.nMinResponseTime > self.mAndroidInfo.nMaxResponseTime:
            Error("请检查机器人3个上下限配置")
            return
        self.nRounds = self.GetRndRound()
        self.nServiceTime = self.GetRndServiceTime()
        self.mSvrUserItem.mUserInfo.mScore = self.GetRndScore()
        self.nRepositTime = 0
        self.nLeaveRate = self.mAndroidInfo.nLeaveRate

    def GetTableID(self):
        return self.mSvrUserItem.TableID

    def GetChairID(self):
        return self.mSvrUserItem.ChairID

    def GetInfo(self):
        return self.mSvrUserItem.mUserInfo

    def GetUUID(self):
        return self.mSvrUserItem.mUserInfo.mUUID

    def GetUserStatus(self):
        return self.mSvrUserItem.mUserInfo.mStatus

    def SetUserStatus(self, mStatus):
        self.mSvrUserItem.mUserInfo.mStatus = mStatus

    def GetMeUserItem(self):
        return self.mSvrUserItem

    def OnAndroidReady(self):
        if self.mAndroidSink is not None:
            self.mAndroidSink.OnAndroidReady()

    def OnAndroidSitDown(self, mTableFrame, vip=False):
        if self.mAndroidSink is not None:
            self.mAndroidSink.OnAndroidSitDown(mTableFrame)
        # 重新分配機器人的攜帶金額
        # 機器人金額 = 准入 + [4.5~20.0] x 底注 - [0.42~4] x 底注
        self.mSvrUserItem.mUserInfo.mScore = mTableFrame.Dgt.mServiceOpt.sMinEnterScore \
                                             + self.GetRndScoreByCellScoreWithPlus() \
                                             - self.GetRndScoreByCellScoreWithSubtract()
        # 確認是否啟動同桌真人玩家vip禮遇
        global android_vip
        android_vip = vip

    def OnSecondAndroidSitDown(self, mTableFrame, vip=False):
        if self.mAndroidSink is not None:
            self.mAndroidSink.OnAndroidSitDown(mTableFrame)
        # 重新分配機器人的攜帶金額
        nScore = 0
        for wChair in range(ServiceAttr.sChairCnt):
            srvUserItem = mTableFrame.GetTableUserItem(wChair)
            if srvUserItem is not None and not srvUserItem.IsAndroidUser:
                # 取座號最小的真人玩家的錢包數目A
                nScore = srvUserItem.mUserInfo.mScore
                break
        # 取位移數的正負值C
        bJuge = 1 if GetRndInt(0, 1) > 0 else -1
        # 取位移數底注*[5.1~20.0]B
        self.mSvrUserItem.mUserInfo.mScore = self.GetRndScore()
        # 取位移數底注*[5.1~20.0]B * 正負數C
        nAddScore = self.mSvrUserItem.mUserInfo.mScore * bJuge
        self.mSvrUserItem.mUserInfo.mScore = nAddScore + nScore
        # 機器人攜帶金額E = A + B x C - (A + B x C) % 10
        self.mSvrUserItem.mUserInfo.mScore = self.mSvrUserItem.mUserInfo.mScore - (
                    self.mSvrUserItem.mUserInfo.mScore % 10)
        # 若低於准入則用准入值
        if self.mSvrUserItem.mUserInfo.mScore < mTableFrame.Dgt.mServiceOpt.sMinEnterScore:
            self.mSvrUserItem.mUserInfo.mScore = mTableFrame.Dgt.mServiceOpt.sMinEnterScore
        # 若高於房間允許最大攜入金額則用最大攜入金額
        elif self.mSvrUserItem.mUserInfo.mScore > mTableFrame.Dgt.mServiceOpt.sMaxScore:
            self.mSvrUserItem.mUserInfo.mScore = mTableFrame.Dgt.mServiceOpt.sMaxScore
        # 確認是否啟動同桌真人玩家vip禮遇
        global android_vip
        android_vip = vip

    def OnConcludeGame(self):
        if self.mAndroidSink is not None:
            self.mAndroidSink.OnConcludeGame()

    def OnTimerPulse(self):
        if self.mAndroidSink is not None:
            self.mAndroidSink.OnUpdate()

    def OnReposition(self):
        self.mSvrUserItem.mUserInfo.mStatus = eUS.US_NULL
        self.mSvrUserItem.mUserInfo.mTableID = INVALID_TABLE
        self.mSvrUserItem.mUserInfo.mChairID = INVALID_CHAIR
        self.mSvrUserItem.SetSrvUserStatus(eUS.US_NULL, INVALID_TABLE, INVALID_CHAIR)
        self.nServiceTime = self.GetRndServiceTime()
        self.mSvrUserItem.mUserInfo.mScore = self.GetRndScore()
        self.nRounds = self.GetRndRound()
        self.nCurrRounds = 0
        self.nRepositTime = GetServerTime()
        self.nLeaveRate = self.mAndroidInfo.nLeaveRate
        self.nLeaveTime = GetServerTime()

    def GetRndServiceTime(self):
        return GetRndInt(self.mAndroidInfo.nMinResponseTime, self.mAndroidInfo.nMaxResponseTime)

    def GetRndScore(self):
        return GetRndInt(self.mAndroidInfo.nMinTakeScore, self.mAndroidInfo.nMaxTakeScore)

    def GetRndScoreByCellScoreWithPlus(self):  # 取得隨機待相加的底注*倍率
        # 底注*4.5~底注*20之間取一個整數
        return GetRndInt(math.ceil(ServiceOpt.sCellScore * 4.5), math.floor(ServiceOpt.sCellScore * 20))

    def GetRndScoreByCellScoreWithSubtract(self):  # 取得隨機待相減的底注*倍率
        # 底注*0.42~底注*4之間取一個整數
        return GetRndInt(math.ceil(ServiceOpt.sCellScore * 0.42), math.floor(ServiceOpt.sCellScore * 4))

    def GetRndRound(self):
        return GetRndInt(self.mAndroidInfo.nMinPlayDraw, self.mAndroidInfo.nMaxPlayDraw)

class AndroidService(object):
    sIns = None

    @classmethod
    def GetInstance(cls, attemper = None):
        if cls.sIns is None:
            cls.sIns = cls(attemper)
            cls.sIns.InitComponents()
        return cls.sIns

    def __init__(self, attemper):
        if AndroidService.sIns != None:
            raise AndroidServiceError("AndroidService已被创建！")
        self.mAttemper = attemper
        self.mAndroidModule = None
        self.mAndroidModuleVip = None
        self.bReaded = False
        self.mUUIDGenerator = 1000000000
        self.mAndroids = {}  # 一般玩家下載的機器人
        self.mAndroidsVip = {}  # vip玩家下載的機器人
        self.vip = False  # 此桌是否有人為vip

    def GenNewUUID(self):
        self.mUUIDGenerator += 1
        return self.mUUIDGenerator

    def InitComponents(self):
        self.bReaded = False
        sqlp = MYPGuard.MYP("game")
        sqlp2 = MYPGuard.MYP("game")
        sql = sSqls["load_nickname"]
        sql2 = sSqls["load_android_vip_name"]
        sqlp.Exec(sql = sql.GetSQL(params = { "cnt" : 10 }), callback = self.OnMysql_ReadAndroids)
        sqlp2.Exec(sql = sql2.GetSQL(params = { "cnt" : 10 }), callback = self.OnMysql_ReadAndroidsVip)
        while True:
            sqlp.Update()
            sqlp2.Update()
            if self.bReaded:
                break
        Info("机器人列表加载完成")

    def OnMysql_ReadAndroids(self, hint, result):
        self.bReaded = True
        try:
            self.mAndroidModule = importlib.import_module("subgame." + ServiceOpt.sModuleName + ".androidsink")
        except:
            PrintEXC()
        if len(result) > 0:
            for mData in result:
                sAndroid = SvrAndtoidInfo()
                sAndroid.nUUID = self.GenNewUUID()
                sAndroid.nLeaveRate = 100
                sAndroid.nMinPlayDraw = 1
                sAndroid.nMaxPlayDraw = 1
                sAndroid.nMinTakeScore = int(ServiceOpt.sCellScore * 5.1)
                sAndroid.nMaxTakeScore = ServiceOpt.sCellScore * 20
                sAndroid.nFaceID = GetRndInt(0, 16)
                sAndroid.mNickName = mData["NickName"]
                self.AddAndroid(sAndroid)
        '''
        if len(result) > 0:
            for mData in result:
                sAndroid = SvrAndtoidInfo(mData)
                self.AddAndroid(sAndroid)
        '''

    def OnMysql_ReadAndroidsVip(self, hint, result):
        self.bReaded = True
        try:
            self.mAndroidModuleVip = importlib.import_module("subgame." + ServiceOpt.sModuleName + ".androidsink")
        except:
            PrintEXC()
        if len(result) > 0:
            for mData in result:
                sAndroid = SvrAndtoidInfo()
                sAndroid.nUUID = self.GenNewUUID()
                sAndroid.nLeaveRate = 100
                sAndroid.nMinPlayDraw = 1
                sAndroid.nMaxPlayDraw = 1
                sAndroid.nMinTakeScore = int(ServiceOpt.sCellScore * 5.1)
                sAndroid.nMaxTakeScore = ServiceOpt.sCellScore * 20
                sAndroid.nFaceID = GetRndInt(0, 16)
                sAndroid.mNickName = mData["NickName"]
                self.AddAndroidVip(sAndroid)
        '''
        if len(result) > 0:
            for mData in result:
                sAndroid = SvrAndtoidInfo(mData)
                self.AddAndroidVip(sAndroid)
        '''

    def AddAndroid(self, androidInfo):
        sAndrdUserItem = AndroidUserItem(androidInfo)
        mAndroidSink = self.mAndroidModule.Create()
        mAndroidSink.Initialization(sAndrdUserItem)
        sAndrdUserItem.mAndroidSink = mAndroidSink
        self.mAndroids[sAndrdUserItem.GetUUID()] = sAndrdUserItem

    def AddAndroidVip(self, androidInfo):
        sAndrdUserItem = AndroidUserItem(androidInfo)
        mAndroidSink = self.mAndroidModuleVip.Create()
        mAndroidSink.Initialization(sAndrdUserItem)
        sAndrdUserItem.mAndroidSink = mAndroidSink
        self.mAndroidsVip[sAndrdUserItem.GetUUID()] = sAndrdUserItem

    def GetThreeAndroid(self, vip):
        vAndroids = []
        if vip == False:  # 一般玩家取用一般機器人
            for id, android in self.mAndroids.items():
                if android is not None:
                    if android.GetUserStatus() == eUS.US_FREE \
                            or android.GetUserStatus() == eUS.US_NULL:
                        vAndroids.append(android)
        else:  # vip玩家取用vip機器人
            self.vip = True
            for id, android in self.mAndroidsVip.items():
                if android is not None:
                    if android.GetUserStatus() == eUS.US_FREE \
                            or android.GetUserStatus() == eUS.US_NULL:
                        vAndroids.append(android)
        if len(vAndroids) >= 3:  # 每桌4人，清單至少要有3個當前待機的機器人
            get_each_table_android = []  # 取得每桌機器人清單
            android_3_id = numpy.random.choice(range(len(vAndroids)), 3, replace=False)  # 抽3位機器人，取後不放回
            for i in android_3_id:
                # 因為取後不放回，每桌每位機器人都必須是不同的人
                get_each_table_android.append(vAndroids[i])
            return get_each_table_android
        # 机器人不足了，再分配50个机器人
        self.InitComponents()
        return None

    def GetTwoAndroid(self, vip):
        vAndroids = []
        if vip == False:  # 一般玩家取用一般機器人
            for id, android in self.mAndroids.items():
                if android is not None:
                    if android.GetUserStatus() == eUS.US_FREE \
                            or android.GetUserStatus() == eUS.US_NULL:
                        vAndroids.append(android)
        else:  # vip玩家取用vip機器人
            self.vip = True
            for id, android in self.mAndroidsVip.items():
                if android is not None:
                    if android.GetUserStatus() == eUS.US_FREE \
                            or android.GetUserStatus() == eUS.US_NULL:
                        vAndroids.append(android)
        if len(vAndroids) >= 2:  # 清單至少要有2個當前待機的機器人
            get_each_table_android = []  # 取得每桌機器人清單
            android_2_id = numpy.random.choice(range(len(vAndroids)), 2, replace=False)  # 抽2位機器人，取後不放回
            for i in android_2_id:
                # 因為取後不放回，每桌每位機器人都必須是不同的人
                get_each_table_android.append(vAndroids[i])
            return get_each_table_android
        # 机器人不足了，再分配50个机器人
        self.InitComponents()
        return None

    def GetFreeAndroid(self, vip):
        vAndroids = []
        if vip == False:  # 一般玩家取用一般機器人
            for id, android in self.mAndroids.items():
                if android is not None:
                    if android.GetUserStatus() == eUS.US_FREE \
                            or android.GetUserStatus() == eUS.US_NULL:
                        vAndroids.append(android)
        else:  # vip玩家取用vip機器人
            self.vip = True
            for id, android in self.mAndroidsVip.items():
                if android is not None:
                    if android.GetUserStatus() == eUS.US_FREE \
                            or android.GetUserStatus() == eUS.US_NULL:
                        vAndroids.append(android)
        if len(vAndroids) > 0:
            return vAndroids[GetRndInt(0, len(vAndroids) - 1)]
        # 机器人不足了，再分配50个机器人
        self.InitComponents()
        return None

    def GetAndroid(self, nUUID):
        if self.vip == False:
            if nUUID in self.mAndroids:
                return self.mAndroids[nUUID]
        else:
            if nUUID in self.mAndroidsVip:
                return self.mAndroidsVip[nUUID]
        return None

    def OnEventTimerPulse(self):
        for id, android in self.mAndroids.items():
            if android is not None \
                    and android.GetInfo().mStatus >= eUS.US_SIT:
                android.OnTimerPulse()
        for id, android in self.mAndroidsVip.items():
            if android is not None \
                    and android.GetInfo().mStatus >= eUS.US_SIT:
                android.OnTimerPulse()

    def OnConcludeGame(self, nUUID, nCurScore):
        sAndroid = self.GetAndroid(nUUID)
        if sAndroid is None:
            return
        sAndroid.OnConcludeGame()
        #修改
        #if self.mAttemper.mServiceAttr.sAllowMatch:
        #    sAndroid.OnReposition()
        #    return
        # 判断当前剩余的可玩游戏局数，剩余局数为0，则机器人退出桌子，进入自由队列
        sAndroid.nCurrRounds += 1
        # 判断本次离开概率
        nLeaveRate = GetRndInt(0, 99)

        # 达到最大可玩的游戏局数，则该机器人需要起立，退出桌子
        # 判断机器人身上金币不足
        if sAndroid.nRounds <= sAndroid.nCurrRounds \
                or nCurScore <= sAndroid.mAndroidInfo.nMinTakeScore \
                or (nLeaveRate <= sAndroid.nLeaveRate and sAndroid.nCurrRounds > sAndroid.mAndroidInfo.nMinPlayDraw):
            DEBUG("机器人[%s:%d]状态由PLAYING->EXIT, 当前金币：%d", sAndroid.GetInfo().mNickName, nUUID, nCurScore)
            sAndroid.SetUserStatus(eUS.US_EXIT)
            sAndroid.nLeaveTime = GetServerTime() + GetRndInt(10, 12)
        else:
            sAndroid.nLeaveRate += GetRndInt(10, 30)       # 本次未命中，下次离开概率 + N

        need_suicide = getattr(sAndroid, 'suicide', False)
        if need_suicide:
            self.kill_android(nUUID)

    def get_android_for_tester(self, amount):
        """取得測試人員使用的機器人

        直接建立新的機器人，並把最新的派出去
        設定 suicide 屬性，當牌局結束時作為刪除判斷

        Args:
            amount (int): 要使用的機器人數量
        Returns:
            list: 機器人物件

        """
        self.create_android_for_tester(amount)

        n = self.mUUIDGenerator # 最新的一隻機器人 uuid

        android_ls = []

        for i in range(amount):
            android = self.mAndroids[n-i]
            android.suicide = True

            android_ls.append(android)

        return android_ls

    def create_android_for_tester(self, amount):
        """建立測試人員用的機器人

        Args:
            amount (int): 要建立的機器人數量
        """
        self.bReaded = False
        sqlp = MYPGuard.MYP("game")
        sql = sSqls["load_nickname"]
        sqlp.Exec(sql = sql.GetSQL(params = { "cnt" : amount }), callback = self.OnMysql_ReadAndroids)
        while True:
            sqlp.Update()
            if self.bReaded:
                break
        Info("机器人列表加载完成")

    def kill_android(self, uuid):
        """殺掉機器人

        刪除物件，並從機器人清單中清除

        Args:
            uuid (int): 機器人的 uuid
        """
        del self.mAndroids[uuid]