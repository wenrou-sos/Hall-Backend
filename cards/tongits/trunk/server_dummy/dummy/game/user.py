
from definations import *
from utils import *

#分数变更信息
class stScoreVarInfo(object):
    def __init__(self):
        self.mScore = 0
        #self.mBankScore = 0
        self.mRevenue = 0   #税收
        self.mWinCnt = 0
        self.mLostCnt = 0
        self.mDrawCnt = 0
        self.mModify = False

    def Clean(self):
        self.mModify = False
        self.mScore = 0
        #self.mBankScore = 0
        self.mTax = 0
        self.mWinCnt = 0
        self.mLostCnt = 0
        self.mDrawCnt = 0

class SvrUserInfo(object):
    def __init__(self):
        self.mSource = ''
        self.mUUID = -1
        self.mChannel = "" #str
        self.mSdkUUID = "" #str
        self.mGameID = -1
        self.mNickName = b""
        self.mCanMatchPlayer = 1  # 可以匹配真人玩家的資格
        self.mFaceID = 0
        self.mSex = 0
        self.mTableID = 0
        self.mChairID = 0
        self.mStatus = eUS.US_NULL
        self.mScore = 0
        self.wallet_type = None
        #self.mBankScore = 0
        self.mRecharge = 0
        self.mExchange = 0
        self.mCtrlStatus = 0
        self.mCtrlScore = 0
        self.mLastDay = 0
        self.mTodayProfit = 0
        #self.mCardScore = 0
        self.mJson = {}         #全局Json
        self.mSubJson = "{}"    #子游戏Json
        #游戏信息
        self.mWinCnt = 0
        self.mLostCnt = 0
        self.mDrawCnt = 0
        self.mExp = 0
        self.mVarInfo = stScoreVarInfo()

class SvrUserItem(object):
    def __init__(self):
        self.mSocketID = 0
        self.mIpAddr = "127.0.0.1"
        self.mAndroidTag = False
        self.mUserInfo = None
        self.mLogonTime = 0
        self.mCliReady = False
        self.mOfflineStatus = 0
        self.mLastTableID = INVALID_TABLE
        self.mLastPlayTime = 0
        self.mExceptTableID = INVALID_TABLE
        #来自平台的验证信息
        self.mToken = ""
        #匹配信息
        self.bMate = False      #是否在匹配中
        self.nMateTime = 0      #开始匹配时间
        self.mAuto_operate_fail_times = 0;  # 系統自動操作失敗累計

    @property
    def UUID(self):
        return self.mUserInfo.mUUID

    @property
    def TableID(self):
        return self.mUserInfo.mTableID

    @property
    def ChairID(self):
        return self.mUserInfo.mChairID

    @property
    def Status(self):
        return self.mUserInfo.mStatus

    @property
    def IsAndroidUser(self):
        return self.mAndroidTag

    @property
    def IsCliReady(self):
        return self.mCliReady

    @property
    def SocketID(self):
        return self.mSocketID

    def SetSrvUserStatus(self, state, wTableID, wChairID):
        self.mUserInfo.mStatus = state
        self.mUserInfo.mTableID = wTableID
        self.mUserInfo.mChairID = wChairID

    def Detach(self):
        self.mCliReady = False
        self.mSocketID = 0

    def SetOfflineStatus(self, status):
        self.mOfflineStatus = status

    def ResetAutoOperateFailTimes(self):
        self.mAuto_operate_fail_times = 0

    def AddAutoOperateFailTimes(self):
        self.mAuto_operate_fail_times += 1

    def CheckAutoOperateFailTimesOverLimit(self):
        return self.mAuto_operate_fail_times >= 10


class SvrUsrMgr(object):
    sSvrUsrs = {}
    bModify = False

    @classmethod
    def AddSvrUserItem(cls, info, dwSocketID, sIpAddr)->SvrUserItem:
        svrUserItem = SvrUserItem()
        svrUserItem.mUserInfo = info
        svrUserItem.mLogonTime = GetServerTime()
        svrUserItem.mSocketID = dwSocketID
        svrUserItem.mAndroidTag = False
        svrUserItem.mIpAddr = sIpAddr
        cls.sSvrUsrs[info.mUUID] = svrUserItem
        bModify = True
        return svrUserItem

    @classmethod
    def GetSrvUserItem(cls, dwUUID):
        if dwUUID not in cls.sSvrUsrs:
            return None
        return cls.sSvrUsrs[dwUUID]

    @classmethod
    def DelSvrUserItem(cls, pSrvUserItem):
        bModify = True
        if pSrvUserItem is None \
                or pSrvUserItem.mUserInfo.mStatus != eUS.US_NULL:
            return False
        if pSrvUserItem.mUserInfo.mUUID == 0 \
                or pSrvUserItem.mUserInfo.mUUID not in cls.sSvrUsrs:
            return True
        del cls.sSvrUsrs[pSrvUserItem.mUserInfo.mUUID]
        return True

    @classmethod
    def GetUserItemCount(cls):
        return len(cls.sSvrUsrs)

    @classmethod
    def GetPlayerTotalScore(cls):
        nTotleScore = 0
        for nId, sPlayer in cls.sSvrUsrs.items():
            if sPlayer is not None:
                nTotleScore += sPlayer.mUserInfo.mScore     #nTotleScore += (sPlayer.mUserInfo.mScore + sPlayer.mUserInfo.mBankScore)
        return nTotleScore
