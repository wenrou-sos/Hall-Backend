
from definations import *
from main_cmd_pb2 import *
from error_pb2 import *
from c_l_lobby_pb2 import *
from c_g_game_pb2 import *
from center_game_pb2 import *
from data_struct_pb2 import *
from utils import *
from user import *
from redisassist import RDSPGuard
from dbexecution import sSqls
from mysqlassist import MYPGuard
import json
import redis

TIME_OFF_LINE = 3
TIME_WAIT_START = 15

class TableDelegate(object):
    def __init__(self):
        pass

    def InitDgt(self, t):
        self.mTableFrame = t
        return True

    def OnActionUserSitDown(self, wChairID, pSvrUserItem, bLookonUser = False)->bool:
        return True

    def OnActionUserStandUp(self, wChairID, pSvrUserItem, bLookonUser = False)->bool:
        return True

    def OnActionUserOnReady(self, wChairID, pSvrUserItem, pMsg)->bool:
        return True

    def OnActionUserEnterTable(self, wChairID, pSvrUserItem)->bool:
        return True

    def OnGameMessage(self, wCmdID, pMsg, pSvrUserItem)->bool:
        return True

    def OnEventGameStart(self, vDeck):
        return True

    def OnInitialize(self, nCellScore, nThinkTime, nNoticeScore):
        return True

    def OnReposition(self):
        return True

    def OnDisMissGame(self):
        return True

class TableFrame(object):
    def __init__(self):
        self.mChairCnt = 0
        self.mTableID = -1
        self.mAttemper = None
        self.mDgt = None
        self.mStarted = False       # 对局中
        self.mStatus = 0            # 游戏状态
        self.mUserItemArr = []
        self.mTableTime = GetServerTime()
        self.mLastAndroidTime = GetServerTime()
        self.mOfflineUserTime = {}      # 座位号->掉线时间
        self.mDrawStartTime = 0         # 对局开始时间
        self.mStartMode = 0             # 游戏开始模式
        self.mAuthCode = b""            # 进入密码
        self.mOwnerChairID = INVALID_CHAIR          # 房主
        self.mStartTimer = None
        self.mWaitStartTimeEnd = 0         # 下一对局开始时间
        self.mcontinue_game_count = 0  # 第N次遊戲；第N-1次繼續遊戲

    def Init(self, table_id, attemper):
        self.mTableID = table_id
        self.mAttemper = attemper
        self.mChairCnt = self.mAttemper.ServiceAttr.sChairCnt
        self.mStartMode = self.mAttemper.ServiceAttr.sStartMode
        self.mDgt = self.mAttemper.GModule.Create()
        self.mUserItemArr = [None for i in range(self.mChairCnt)]
        if not self.mDgt.InitDgt(self):
            return False
        return True

    def OnReposition(self):
        if len(self.mAuthCode) > 0:
            self.mAttemper.DelAuthCode(self.mAuthCode)
        self.mAuthCode = b""
        self.mOwnerChairID = INVALID_CHAIR
        if self.mStartTimer is not None:
            self.RemoveTimer(self.mStartTimer)
        self.mStartTimer = None
        self.mWaitStartTimeEnd = 0

    @property
    def continue_game_count(self):
        return self.mcontinue_game_count

    @property
    def TableID(self):
        return self.mTableID

    @property
    def Attemper(self):
        return self.mAttemper

    @property
    def Dgt(self):
        return self.mDgt

    @property
    def AuthCode(self):
        return self.mAuthCode

    @property
    def OwnerChairID(self):
        return self.mOwnerChairID

    def GetLastAndroidTime(self):
        return self.mLastAndroidTime

    def GetStartLeftTime(self):
        if self.mWaitStartTimeEnd > 0:
            return self.mWaitStartTimeEnd - GetServerTime()
        return -1

    def GetStockValue(self):
        return self.mAttemper.Stock.GetStockValue()

    def ModifyStockValue(self, v):
        if not ServiceOpt.IsEducateSvr():
            self.mAttemper.Stock.ModifyStockValue(v)

    def AddTimer(self, interval, cb, params):
        return self.mAttemper.mTEngine.AddTimer(interval, cb, params)

    def RemoveTimer(self, id):
        self.mAttemper.mTEngine.RemoveTimer(id)

    def GetTableUserItem(self, wChairID):
        if wChairID < 0 or wChairID >= self.mChairCnt:
            return None
        return self.mUserItemArr[wChairID]

    #获取机器人数量
    def GetAndroidCount(self):
        nAndroidNum = 0
        for wChairID in range(self.mChairCnt):
            if self.mUserItemArr[wChairID] is not None \
                    and self.mUserItemArr[wChairID].IsAndroidUser:
                nAndroidNum += 1
        return nAndroidNum

    #获得桌子上真实玩家数量
    def GetUserCount(self):
        nCount = 0
        for wChairID in range(self.mChairCnt):
            if self.mUserItemArr[wChairID] is not None \
                    and not self.mUserItemArr[wChairID].IsAndroidUser:
                nCount += 1
        return nCount

    #获取游戏内玩家总数量（机器人+真人）
    def GetAllUserCount(self):
        nCount = 0
        for wChairID in range(self.mChairCnt):
            if self.mUserItemArr[wChairID] is not None:
                nCount += 1
        return nCount
    #一次獲取2個空位
    def GetTwoNullChairID(self):
        two_null_chair = []
        null_chair_count = 0  # 取得空座計數器
        for wChairID in range(self.mChairCnt):
            if self.mUserItemArr[wChairID] is None:  # 如果該座位沒有人佔位
                two_null_chair.append(wChairID)
                null_chair_count += 1
                if null_chair_count >= 2:  # 如果取得了2個空座位
                    break
        if two_null_chair != []:
            return two_null_chair  # 有2個空位回傳空位座號列表
        else:
            return INVALID_CHAIR  # 沒有空位回傳65535
    #获取空位
    def GetNullChairID(self):
        for wChairID in range(self.mChairCnt):
            if self.mUserItemArr[wChairID] is None:
                return wChairID
        return INVALID_CHAIR
    #一次獲取所有空位
    def GetMoreNullChairID(self):
        all_null_chair = []
        for wChairID in range(self.mChairCnt):
            if self.mUserItemArr[wChairID] is None:  # 如果該座位沒有人佔位
                all_null_chair.append(wChairID)
        if all_null_chair != []:
            return all_null_chair  # 有空位不管數量多少回傳空位座號列表
        else:
            return INVALID_CHAIR  # 沒有空位回傳65535
    #随机空位
    def GetRandNullChairID(self):
        wIndex = random.randint(0, self.mChairCnt - 1)
        for wChairID in range(wIndex, self.mChairCnt + wIndex):
            if self.mUserItemArr[wChairID % self.mChairCnt ] is None:
                return wChairID
        return INVALID_CHAIR

    def GetWaitCount(self):
        if self.mStarted \
                or (self.mStatus >= eGS.GS_PLAY and self.mStatus < eGS.GS_WAIT):
            return 0
        return self.mChairCnt - self.GetAllUserCount()

    def GetReadyCount(self):
        nCount = 0
        for wChairID in range(self.mChairCnt):
            srvUserItem = self.GetTableUserItem(wChairID)
            if srvUserItem is not None:
                if not srvUserItem.IsCliReady and not srvUserItem.IsAndroidUser:
                    Info("GetReadyCount srvUserItem.IsCliReady", srvUserItem.IsCliReady)
                    return 0
                if srvUserItem.Status != eUS.US_READY:
                    Info("GetReadyCount srvUserItem.Status", srvUserItem.Status)
                    return 0
                nCount += 1
        return nCount

    def IsStarted(self):
        if self.mStarted \
                or (self.mStatus >= eGS.GS_PLAY and self.mStatus < eGS.GS_WAIT):
            return True
        return False

    def IsCreateTable(self):
        if len(self.mAuthCode) > 0 \
                and self.mOwnerChairID != INVALID_CHAIR:
            return True
        return False

    def OnEventSocketGame(self, wSubCmdID, data, pSvrUserItem):
        if self.mDgt is not None:
            self.mDgt.OnGameMessage(wSubCmdID, data, pSvrUserItem)

    #发送消息
    def SendData(self, wMainCmdID, wSubCmdID, pbMsg, wChairID = INVALID_CHAIR)->bool:
        if wChairID is INVALID_CHAIR:
            for chairID in range(self.mChairCnt):
                srvUserItem = self.mUserItemArr[chairID]
                if srvUserItem is not None and not srvUserItem.IsAndroidUser:
                     self.mAttemper.SendToClient(srvUserItem.SocketID, wMainCmdID, wSubCmdID, pbMsg)
        else:
            srvUserItem = self.mUserItemArr[wChairID]
            if srvUserItem is not None and not srvUserItem.IsAndroidUser:
                self.mAttemper.SendToClient(srvUserItem.SocketID, wMainCmdID, wSubCmdID, pbMsg)
        return True

    #发送数据,除了wChairID外，其他全部发送
    def SendDataDebar(self, wMainCmdID, wSubCmdID, pbMsg, wDebarChairID)->bool:
        for wChairID in range(self.mChairCnt):
            if wChairID is wDebarChairID:
                continue
            srvUserItem = self.mUserItemArr[wChairID]
            if srvUserItem is None or srvUserItem.IsAndroidUser:
                continue
            self.mAttemper.SendToClient(srvUserItem.SocketID, wMainCmdID, wSubCmdID, pbMsg)

    def StartGame(self, nStatus=eGS.GS_PLAY)->bool:
        if self.mStarted \
                or (self.mStatus >= eGS.GS_PLAY and self.mStatus < eGS.GS_WAIT) \
                or (nStatus < eGS.GS_PLAY or nStatus > eGS.GS_WAIT):
            return False
        self.mStarted = True
        self.mStatus = nStatus
        self.mDrawStartTime = GetServerTime()
        for wChairID in range(self.mChairCnt):
            srvUserItem = self.GetTableUserItem(wChairID)
            if srvUserItem is not None \
                    and srvUserItem.Status == eUS.US_READY:
                srvUserItem.SetSrvUserStatus(eUS.US_PLAYING, self.mTableID, wChairID)
                srvUserItem.mLastTableID = self.mTableID
                srvUserItem.mExceptTableID = INVALID_TABLE
                srvUserItem.mLastPlayTime = self.mDrawStartTime
                srvUserItem.bMate = False
                srvUserItem.nMateTime = 0
        if self.mDgt is not None:
            self.mDgt.OnEventGameStart(self.mAttemper.AllokcCardShoe())
            # 寫入玩家當前新局號
            rp = RDSPGuard.RP("game")
            for wChairID in range(self.mChairCnt):
                srvUserItem = self.GetTableUserItem(wChairID)
                if srvUserItem is not None and srvUserItem.Status == eUS.US_PLAYING:
                    account_base_ss = rp.LibGrd.R.hget("sha@data_" + str(srvUserItem.mUserInfo.mUUID), "base")
                    if account_base_ss is not None:
                        account_base = db_data_user()
                        account_base.ParseFromString(account_base_ss)

                        account_base.current_game_uuid = self.mDgt.xLogic.StrRoundSign
                        account_base.last_game_starttime = GetServerTime()
                        account_base.last_svr_id = ServiceOpt.sSvrUUID
                        account_buffer = account_base.SerializeToString()
                        rp.LibGrd.Call("common.SetInfoBySYS", *(srvUserItem.mUserInfo.mUUID, account_buffer))

        if self.mStartTimer is not None:
            self.RemoveTimer(self.mStartTimer)

        self.mStartTimer = None
        return True

    def ConcludeGame(self)->bool:
        if not self.mStarted \
                or (self.mStatus < eGS.GS_PLAY or self.mStatus >= eGS.GS_WAIT):
            return False
        self.mStarted = False
        self.mStatus = eGS.GS_FREE
        for wChairID in range(self.mChairCnt):
            srvUserItem = self.GetTableUserItem(wChairID)
            if srvUserItem is None:
                continue
            if srvUserItem.Status != eUS.US_SIT:
                srvUserItem.SetSrvUserStatus(eUS.US_SIT, self.mTableID, wChairID)
            if srvUserItem.IsAndroidUser:
                self.mAttemper.mAndroidService.OnConcludeGame(srvUserItem.mUserInfo.mUUID,
                                                              srvUserItem.mUserInfo.mScore)
        '''
        #匹配规则修改：2020-05-08
        #匹配游戏每一局退出桌子到房间
        if self.mAttemper.mServiceAttr.sAllowMatch:
            for wChairID in range(self.mChairCnt):
                srvUserItem = self.GetTableUserItem(wChairID)
                if srvUserItem is None:
                    continue
                bOffline = False
                if wChairID in self.mOfflineUserTime:
                    bOffline = True
                if self.PerformStandUpAction(srvUserItem):
                    if bOffline:
                        self.mAttemper.OnEventUserLogout(srvUserItem, logout_offline, True)
                else:
                    Warn("PerformStandUpAction failed")
        '''
        for wChairID in range(self.mChairCnt):
            srvUserItem = self.GetTableUserItem(wChairID)
            if srvUserItem is None:
                continue
            bOffline = False
            if wChairID in self.mOfflineUserTime:
                bOffline = True
            if bOffline:
                if self.PerformStandUpAction(srvUserItem):
                    self.mAttemper.OnEventUserLogout(srvUserItem, logout_offline, True)
                else:
                    Warn("PerformStandUpAction failed")
            if not bOffline:
                if (ServiceOpt.sMinEnterScore != 0 and srvUserItem.mUserInfo.mScore < ServiceOpt.sMinEnterScore) \
                        or (ServiceOpt.sMaxEnterScore != 0 and srvUserItem.mUserInfo.mScore > ServiceOpt.sMaxEnterScore):
                    if not self.PerformStandUpAction(srvUserItem, False, enoughmoney_standup_op):
                        Warn("PerformStandUpAction failed 222")
        # 重置桌子
        if self.mDgt is not None:
            self.mDgt.OnReposition()

        # 是否維護
        rp = RDSPGuard.RP("game")
        api_key = ServiceOpt.sHostApiKey
        channel_res = rp.LibGrd.Call("channel.GetInfo", *(api_key,))
        if channel_res[0] == 0:
            chl_data = OnRedisResultParser(channel_res[1])
            ctm_data = json.loads(chl_data["extra"])
            if "status" in ctm_data:
                status = ctm_data["status"]
                if status == 1:  # 維護
                    return True

        #继续开始下一局
        if self.GetAllUserCount() >= 1:
            Log("继续等待下一局")
            self.mStartTimer = self.AddTimer(ServiceAttr.sWaitStartTime, self.OnTMEvt_WaitStart, None)
            self.mWaitStartTimeEnd = GetServerTime() + ServiceAttr.sWaitStartTime
        return True

    def OnTMEvt_WaitStart(self, params):
        try:
            self.mStartTimer = None
            self.mWaitStartTimeEnd = -1

            check_leave = False
            if self.GetAllUserCount() < 3:  # 未達tongits規定的3人遊戲
                check_leave = True
            for wChairID in range(self.mChairCnt):
                srvUserItem = self.GetTableUserItem(wChairID)
                if srvUserItem is None:
                    continue
                if srvUserItem.Status != eUS.US_READY:
                    check_leave = True

            if check_leave == True:
                for wChairID in range(self.mChairCnt):
                    srvUserItem = self.GetTableUserItem(wChairID)
                    if srvUserItem is None:
                        continue
                    if not self.PerformStandUpAction(srvUserItem, False, noready_standup):
                        Warn("OnTMEvt_WaitStart PerformStandUpAction failed")

            # if self.GetUserCount() > 0:
            #     if not self.IsCreateTable():
            #         if self.GetAllUserCount() == 1:
            #             if ServiceOpt.sAllowAndroid:
            #                 if not self.mAttemper.DistributeOneAndroid(self, True):
            #                     return
            #         for wChair in range(ServiceAttr.sChairCnt):
            #             srvUserItem = self.GetTableUserItem(wChair)
            #             if srvUserItem is not None \
            #                     and srvUserItem.IsAndroidUser:
            #                 self.OnEventReady(srvUserItem)
        except:
            PrintEXC()

    #解散游戏-强制终止游戏
    def DisMissGame(self, manual_dismiss=False):  # 手動解散True，建置或維護時False
        if not self.mStarted \
                or (self.mStatus < eGS.GS_PLAY or self.mStatus >= eGS.GS_WAIT):
            return False
        self.mStarted = False
        self.mStatus = eGS.GS_FREE

        Log(f"DisMissGame manual_dismiss={manual_dismiss} TableID={self.mTableID}")

        if self.mDgt is not None:
            self.mDgt.OnDisMissGame()
        for wChairID in range(self.mChairCnt):
            srvUserItem = self.GetTableUserItem(wChairID)
            if srvUserItem is None:
                continue
            if srvUserItem.Status != eUS.US_SIT:
                srvUserItem.SetSrvUserStatus(eUS.US_SIT, self.mTableID, wChairID)
            if srvUserItem.IsAndroidUser:
                self.mAttemper.mAndroidService.OnConcludeGame(srvUserItem.mUserInfo.mUUID,
                                                              srvUserItem.mUserInfo.mScore)
        for wChairID in range(self.mChairCnt):
            srvUserItem = self.GetTableUserItem(wChairID)
            if srvUserItem is None:
                continue
            bOffline = False
            if wChairID in self.mOfflineUserTime:
                bOffline = True
            # 手動強制解散流程
            if manual_dismiss == True:
                # 取消isgaming、isfinish、hasandroid的flag，避免下一次開啟系統仍舊判斷遊戲中
                self.mDgt.cancel_isgaming()
                self.mDgt.cancel_isfinished()
                self.mDgt.cancel_hasandroid()
                # 起立時，為了進入def OnActionUserStandUp將ChairID給pop，故帶入False參數
                if self.PerformStandUpAction(srvUserItem, False, logout_kicked):
                    # 事件登出
                    self.mAttemper.OnEventUserLogout(srvUserItem, logout_offline, True, True)
                    self.OnReposition()
                    Log("解散後 {} 不在遊戲中了".format(srvUserItem.mUserInfo.mUUID))
            # 正常解散流程
            elif self.PerformStandUpAction(srvUserItem, True, logout_kicked):
                if bOffline:
                    self.mAttemper.OnEventUserLogout(srvUserItem, logout_offline, True)
            else:
                Info("DisMissGame PerformStandUpAction failed")
        if self.mDgt is not None:
            self.mDgt.OnReposition()
        return True

    def PerformSitDownAction(self, wChairID, pSvrUserItem):
        if pSvrUserItem is None or wChairID == INVALID_CHAIR:
            return False
        self.mUserItemArr[wChairID] = pSvrUserItem
        if wChairID in self.mOfflineUserTime:
            del self.mOfflineUserTime[wChairID]
        self.mDgt.OnActionUserSitDown(wChairID, pSvrUserItem)
        pSvrUserItem.SetSrvUserStatus(eUS.US_SIT, self.mTableID, wChairID)
        if pSvrUserItem.IsAndroidUser:
            self.mLastAndroidTime = GetServerTime()
        return True

    def PerformStandUpAction(self, pSvrUserItem, bSkipDgt = False, reason = 0, bNotClient = True):
        if pSvrUserItem is None or pSvrUserItem.ChairID == INVALID_CHAIR:
            return True
        wChairID = pSvrUserItem.ChairID
        if pSvrUserItem.mUserInfo.mStatus == eUS.US_PLAYING:
            return False
        # 事件通知
        if not bSkipDgt:
            if self.mDgt is not None:
                if not self.mDgt.OnActionUserStandUp(wChairID, pSvrUserItem, False):
                    return False
        if bNotClient:
            self.OnEventUserStandUp(pSvrUserItem, reason)
        self.OnEventOwnerChange(pSvrUserItem.ChairID)
        pSvrUserItem.SetSrvUserStatus(eUS.US_FREE, INVALID_TABLE, INVALID_CHAIR)
        pSvrUserItem.mCliReady = False
        if pSvrUserItem.IsAndroidUser:
            self.mLastAndroidTime = GetServerTime()
        self.mUserItemArr[wChairID] = None
        if wChairID in self.mOfflineUserTime:
            del self.mOfflineUserTime[wChairID]
        nCount = self.GetAllUserCount()
        if nCount == 0:
            self.OnReposition()
        if nCount > 0:
            if not self.IsCreateTable():
                if self.EfficacyStartGame():
                    self.StartGame()
        return True

    def OnEventOwnerChange(self, wChairID):
        if wChairID == self.OwnerChairID:
            for wChair in range(self.mChairCnt):
                srvUserItem = self.GetTableUserItem(wChair)
                if srvUserItem is not None \
                        and srvUserItem.ChairID != wChairID:
                    self.mOwnerChairID = srvUserItem.ChairID
                    sendmsg = msg_ownerchange_ret()
                    sendmsg.table_owner = self.mOwnerChairID
                    self.SendData(e_msgid_game_action, e_cg_msgid_ownerchange, sendmsg)
                    return

    def OnEventUserStandUp(self, pSvrUserItem, reason):
        if pSvrUserItem is None or pSvrUserItem.ChairID == INVALID_CHAIR:
            return
        sendmsg = msg_standup_ret()
        sendmsg.chair_id = pSvrUserItem.ChairID
        sendmsg.ret = 0
        sendmsg.reason = reason
        self.mAttemper.SendToTableClient(pSvrUserItem.TableID,
                                         e_msgid_game_action, e_cg_msgid_standup, sendmsg)

    def OnEventUserReconnect(self, pSvrUserItem):
        if pSvrUserItem is not None:
            if pSvrUserItem.ChairID in self.mOfflineUserTime:
                del self.mOfflineUserTime[pSvrUserItem.ChairID]

    def OnEventUserOffLine(self, pSvrUserItem):
        if pSvrUserItem is not None:
            pSvrUserItem.SetOfflineStatus(logout_quit_game)
            if 0 != pSvrUserItem.mOfflineStatus \
                    and not pSvrUserItem.IsAndroidUser:
                self.mOfflineUserTime[pSvrUserItem.ChairID] = self.mTableTime

    def OnCheckOfflineUser(self, nowTime):
        self.mTableTime = nowTime
        if len(self.mOfflineUserTime) > 0:
            mRunUserTime = self.mOfflineUserTime.copy()     #运行过程中要修改值
            for wChair, nTime in mRunUserTime.items():
                if nTime == 0 or self.mTableTime - nTime < TIME_OFF_LINE:
                    continue
                svrUserItem = self.GetTableUserItem(wChair)
                if svrUserItem is None \
                        or svrUserItem.mUserInfo.mStatus >= eUS.US_PLAYING:
                    continue
                if self.PerformStandUpAction(svrUserItem, False, 0):
                    svrUserItem.SetSrvUserStatus(eUS.US_NULL, INVALID_TABLE, INVALID_CHAIR)
                    self.mAttemper.OnEventUserLogout(svrUserItem, logout_offline, True)

    def OnEventReady(self, pSvrUserItem):
        if self.mStatus >= eGS.GS_PLAY:
            return False
        if pSvrUserItem.mUserInfo.mScore < ServiceOpt.sMinEnterScore:
            return False
        if ServiceOpt.sMaxEnterScore != 0 and pSvrUserItem.mUserInfo.mScore > ServiceOpt.sMaxEnterScore:
            return False
        if pSvrUserItem.Status != eUS.US_SIT:
            return False
        if self.mDgt.OnActionUserOnReady(pSvrUserItem.ChairID, pSvrUserItem, None):
            pSvrUserItem.SetSrvUserStatus(eUS.US_READY, self.mTableID, pSvrUserItem.ChairID)
            #发送准备消息
            sendmsg = msg_ready_ret()
            sendmsg.ret = e_error_ok
            sendmsg.chair_id = pSvrUserItem.ChairID
            sendmsg.state = 1
            self.mAttemper.SendToTableClient(self.mTableID, e_msgid_game_action, e_cg_msgid_ready, sendmsg)
            #检测游戏开始
            if not self.IsCreateTable():
                if self.EfficacyStartGame():
                    self.StartGame()
        return True

    def OnEventEnterTable(self, pSvrUserItem):
        if pSvrUserItem is not None:
            pSvrUserItem.mCliReady = True
            self.mDgt.OnActionUserEnterTable(pSvrUserItem.ChairID, pSvrUserItem)
            if not self.IsCreateTable():
                if self.EfficacyStartGame():
                    self.StartGame()
        return True

    def IsCustomTable(self):
        if len(self.mAuthCode) > 0 and self.OwnerChairID != INVALID_CHAIR:
            return True
        return False

    def DoCreateTable(self, pSvrUserItem, sbAuthCode):
        if pSvrUserItem is None or sbAuthCode is None \
                or len(sbAuthCode) == 0:
            return False
        if not self.PerformSitDownAction(self.GetNullChairID(), pSvrUserItem):
            return False
        #self.mStartMode = eGSM.SM_CONTROL
        self.mAuthCode = sbAuthCode
        self.mOwnerChairID = pSvrUserItem.ChairID
        return True

    def DoJoinTable(self, pSvrUserItem, sbAuthCode):
        if pSvrUserItem is None or sbAuthCode is None \
                or sbAuthCode != self.mAuthCode or self.mStatus >= eUS.US_PLAYING\
                or pSvrUserItem.ChairID == self.OwnerChairID:
            return False
        return self.PerformSitDownAction(self.GetNullChairID(), pSvrUserItem)

    #检测游戏开始
    def EfficacyStartGame(self):
        #if self.mStarted or self.mStartMode == eGSM.SM_CONTROL:
        if self.mStarted:
            Info("self.mStarted", self.mStarted)
            return False
        #准备人数
        nCount = 0
        for wChairID in range(self.mChairCnt):
            srvUserItem = self.GetTableUserItem(wChairID)
            if srvUserItem is not None:
                if not srvUserItem.IsCliReady and not srvUserItem.IsAndroidUser:
                    # Info("srvUserItem.IsCliReady", srvUserItem.IsCliReady)
                    return False
                if srvUserItem.Status != eUS.US_READY:
                    Info("srvUserItem.Status", srvUserItem.Status)
                    return False
                nCount += 1

        self.mcontinue_game_count += 1  # 計數器+1：玩家進行下一局
        return nCount == ServiceAttr.sMinPlayer

    '''
        //登出类型
        logout_kicked                       = 3;//踢出,工具或者系统
        logout_relogin                      = 6;//重登
        logout_kick_timeout                 = 7;//游戏内部超时踢人,长时间不玩或者不准备
    '''
    def KickUser(self, wChairID, nReason = logout_kicked):
        srvUserItem = self.GetTableUserItem(wChairID)
        if srvUserItem is None:
            return
        if srvUserItem.mUserInfo.mStatus >= eUS.US_PLAYING \
                or not self.PerformStandUpAction(srvUserItem):
            srvUserItem.mOfflineStatus = nReason
            #通知被踢
            self.mAttemper.OnEventUserKick(srvUserItem, nReason, False)
            #断开连接
            dwSocketID = srvUserItem.SocketID
            pNetParams = self.mAttemper.GetNetBindParams(dwSocketID)
            if pNetParams is not None:
                del self.mAttemper.mID2Conn[dwSocketID]
            self.mAttemper.mServer.SafeClose(dwSocketID)
            srvUserItem.Detach()
            return
        srvUserItem.SetSrvUserStatus(eUS.US_NULL, INVALID_TABLE, INVALID_CHAIR)
        self.mAttemper.OnEventUserKick(srvUserItem, nReason)

    #广播大奖消息(模板ID 和 参数列表)
    def SendAwardNoticeMsg(self, nUUID, nTempID, vArgs):
        json_data = {}
        json_data["tid"] = nTempID
        json_data["nid"] = str(GetServerTimeMS()) + str(nUUID).zfill(6)
        json_data["type"] = 2   #1、系统维护  2、大奖公告
        json_data["args"] = []
        for arg in vArgs:
            if isinstance(arg, float) or isinstance(arg, int):
                arg = str(arg)
            if not isinstance(arg, bytes) and not isinstance(arg, str):
                continue
            bytesArg = arg if isinstance(arg, str) else arg.decode('utf-8')
            json_data["args"].append(bytesArg)
        self.mAttemper.WriteNotice(ServiceOpt.sHostApiKey, json.dumps(json_data))

        #发给自己
        sendmsg = msg_game_broadcast()
        sendmsg.msg_type = 2    #1、系统维护  2、大奖公告
        sendmsg.msg_template_id = nTempID
        for arg in vArgs:
            if isinstance(arg, float) or isinstance(arg, int):
                arg = str(arg)
            if not isinstance(arg, bytes) and not isinstance(arg, str):
                continue
            bytesArg = arg if isinstance(arg, bytes) else arg.encode('utf-8')
            sendmsg.param_list.append(bytesArg)
        srvUserItem = SvrUsrMgr.GetSrvUserItem(nUUID)
        if srvUserItem is None or srvUserItem.IsAndroidUser:
            return
        self.mAttemper.SendToClient(srvUserItem.SocketID, e_msgid_game_action, e_cg_msgid_broadcast, sendmsg)

    # 写入积分
    def WriteUserScore(self, wChairID, scoreInfo:stScoreInfo, tableID=None)->bool:
        srvUserItem = self.GetTableUserItem(wChairID)
        if srvUserItem is None:
            return False
        if wChairID >= self.mChairCnt \
                or scoreInfo.mScoreType == eST.ST_NULL:
            return False

        srvUserItem.mUserInfo.mVarInfo.bModify = True
        if scoreInfo.mScore is not None:
            srvUserItem.mUserInfo.mScore = scoreInfo.mScore
        else:
            srvUserItem.mUserInfo.mScore += scoreInfo.mModScore

        if srvUserItem.mUserInfo.mLastDay + 86400 < GetServerTime():
            srvUserItem.mUserInfo.mTodayProfit = 0
            srvUserItem.mUserInfo.mLastDay = GetServerZeroTime()
        srvUserItem.mUserInfo.mTodayProfit += scoreInfo.mModScore
        #srvUserItem.mUserInfo.mCardScore -= scoreInfo.mCost
        #srvUserItem.mUserInfo.mCardScore = srvUserItem.mUserInfo.mCardScore if srvUserItem.mUserInfo.mCardScore >= 0 else 0

        # 变更信息
        srvUserItem.mUserInfo.mVarInfo.mScore += scoreInfo.mModScore
        srvUserItem.mUserInfo.mVarInfo.mRevenue += scoreInfo.mRevenue
        #负分处理
        if srvUserItem.mUserInfo.mScore < 0:
            srvUserItem.mUserInfo.mVarInfo.mScore -= srvUserItem.mUserInfo.mScore
            srvUserItem.mUserInfo.mScore = 0
        member_grade_calculation = self.mAttemper.WriteUserScore(
            wChairID, srvUserItem, self.mDgt.xLogic.StrRoundSign, tableID=tableID, modscore=scoreInfo.mModScore)
        return member_grade_calculation  # 回傳會員等級資訊
    
    def WriteLog(self, colname, jsonstr):  # 寫入dmgamelog資料庫
        if self.mAttemper is not None:
            self.mAttemper.WriteLog(colname, jsonstr)

    def WriteVipLogFromTableFrame(self, colname, jsonstr):  # 寫入dmgamelog的vip_log
        if self.mAttemper is not None:
            self.mAttemper.WriteVipLogFromAttempter(colname, jsonstr)

    def WriteVipPlayerFromTableFrame(self, colname, jsonstr):  # 寫入dmgame的VIP_player
        if self.mAttemper is not None:
            self.mAttemper.WriteVipPlayerFromAttempter(colname, jsonstr)

    def WriteTableLog(self, stLog, send_log_host, android_civil_war):
        try:
            jLog = {}
            rLog = {}
            jLog["hashkey"] = ServiceOpt.sHashKey
            jLog["hostapikey"] = ServiceOpt.sHostApiKey
            jLog["subgameid"] = ServiceOpt.sSubGameId
            jLog["tabid"] = stLog.nTableID
            jLog["roundid"] = stLog.sRoundID
            jLog["time"] = stLog.sTime
            jLog["detail"] = stLog.sDetailInfo
            # 判斷是否機器人內戰
            if android_civil_war == False:
                jLog["status"] = 1  # 正常，寫入紀錄
            else:
                jLog["status"] = 0  # 異常，機器人內戰，不寫紀錄
            self.WriteLog("game_table_log", json.dumps(jLog))
            Log(f"write table log, tabid={stLog.nTableID} rount_id={stLog.sRoundID}")

            # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
            #     jLog["status"] = 0
            #     rLog = jLog
            #     for host in send_log_host:
            #         if host != "":
            #             rp = RDSPGuard.RP("gamelog")
            #             publish_data = {"fnc": "WriteTableLog", "type": "game_table_log", "data": rLog}
            #             rp.LibGrd.R.publish(host + "_" + str(ServiceOpt.sSubGameId), json.dumps(publish_data))
        except:
            PrintEXC()

    def WritePlayerLog(self, stLog):
        try:
            srvUserItem = self.GetTableUserItem(stLog.nChairID)
            if srvUserItem is None or srvUserItem.IsAndroidUser:
                return

            is_tester_mode = srvUserItem.mUserInfo.mSdkUUID == "play_star_tester"

            jLog = {}
            rLog = {}
            jLog["roundID"] = stLog.sRoundID
            jLog["subgameid"] = ServiceOpt.sSubGameId
            jLog["hashkey"] = ServiceOpt.sHashKey
            jLog["uuid"] = stLog.nUUID
            jLog["hostapikey"] = stLog.sChannel
            jLog["memberID"] = stLog.sMemberID
            if isinstance(stLog.mNickName, bytes):
                jLog["nickName"] = stLog.mNickName.decode('utf-8')
            else:
                jLog["nickName"] = stLog.mNickName
            jLog["tableID"] = stLog.nTableID
            jLog["chairID"] = stLog.nChairID
            jLog["calScore"] = stLog.nCalScore
            jLog["tax"] = stLog.nTax
            jLog["curScore"] = stLog.nCurrentScore
            jLog["time"] = stLog.sTime
            jLog["status"] = 0 if is_tester_mode else 1

            self.WriteLog("game_play_log", json.dumps(jLog))
            Log(f"write player log uuid={stLog.nUUID} rount_id={stLog.sRoundID}")

            # if int(ServiceOpt.sMultiHost) == 1:  # 多代理商
            #     jLog["status"] = 0
            #     rLog = jLog
            #     rp = RDSPGuard.RP("game")
            #     account_base_ss = rp.LibGrd.R.hget("sha@data_" + str(stLog.nUUID), "base")
            #     if account_base_ss is not None:
            #         account_base = db_data_user()
            #         account_base.ParseFromString(account_base_ss)
            #         rp = RDSPGuard.RP("gamelog")
            #         rLog["uuid"] = account_base.hostuuid
            #         publish_data = {"fnc": "WriteTableLog", "type": "game_play_log", "data": rLog}
            #         rp.LibGrd.R.publish(stLog.sChannel + "_" + str(ServiceOpt.sSubGameId), json.dumps(publish_data))
            #     else:
            #         Log("WritePlayerLog(multihost) uuid err")
        except:
            PrintEXC()

    def WriteVipLog(self, nickname, game_id, host_api_key, add_time):  # 準備寫入vip_log的資料
        try:
            jLog = {}
            jLog["apikey"] = host_api_key  # 玩家來源商戶代號
            jLog["game_id"] = game_id  # 遊戲代號
            jLog["member_id"] = nickname  # 玩家名稱
            jLog["add_time"] = add_time  # 加入成為vip的時間
            self.WriteVipLogFromTableFrame("vip_log", jLog)  # 資料格式為str不是jsonstr不需要dumps
            # if int(ServiceOpt.sMultiHost) == 1:  # 如果是多代理商模式
            #     # 準備同步
            #     rp = RDSPGuard.RP("gamelog")
            #     publish_data = {"fnc": "VipLog", "type": "vip_log", "data": jLog}
            #     # 公開發布讓單代理商與多代理服務器雙向監聽
            #     rp.LibGrd.R.publish(str(host_api_key) + "_" + str(ServiceOpt.sSubGameId), json.dumps(publish_data))
        except:
            PrintEXC()

    def WriteVipPlayer(self, nickname, game_id, host_api_key):  # 準備寫入VIP_player的資料
        try:
            jLog = {}
            jLog["apikey"] = host_api_key  # 玩家來源商戶代號
            jLog["game_id"] = game_id  # 遊戲代號
            jLog["member_id"] = nickname  # 玩家名稱
            self.WriteVipPlayerFromTableFrame("VIP_player", jLog)  # 資料格式為str不是jsonstr不需要dumps
        #     if int(ServiceOpt.sMultiHost) == 1:  # 如果是多代理商模式
        #         # 準備同步
        #         rp = RDSPGuard.RP("gamelog")
        #         publish_data = {"fnc": "VipPlayer", "type": "VIP_player", "data": jLog}
        #         # 公開發布讓單代理商與多代理服務器雙向監聽
        #         rp.LibGrd.R.publish(str(host_api_key) + "_" + str(ServiceOpt.sSubGameId), json.dumps(publish_data))
        except:
            PrintEXC()

    def TradeLog(self, type, data, channel):
        try:
            sqlp = MYPGuard.MYP("log")
            sql = sSqls[type]
            sqlp.Exec(sql=sql.GetSQL(params=data), callback=None)
            # # 如果是多代理商模式
            # if int(ServiceOpt.sMultiHost) == 1:
            #     # 準備同步
            #     rp = RDSPGuard.RP("gamelog")
            #     publish_data = {"fnc": "TradeLog", "type": type, "data": data}
            #     # 公開發布讓單代理商與多代理服務器雙向監聽
            #     rp.LibGrd.R.publish(str(channel) + "_" + str(ServiceOpt.sSubGameId), json.dumps(publish_data))
        except:
            PrintEXC()

    def SlotGame(self, type, data, db_id):
        try:
            sqlp = MYPGuard.MYP(db_id)
            sql = sSqls[type]
            return sqlp.Exec(sql=sql.GetSQL(params=data), callback=None)
        except:
            PrintEXC()
