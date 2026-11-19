
import math
import hashlib
import json
import time
from copy import deepcopy
from definations import *
from main_cmd_pb2 import *
from error_pb2 import *
from dummy_pb2 import *
from c_l_lobby_pb2 import *
from c_g_game_pb2 import *
from center_game_pb2 import *
from data_struct_pb2 import *
from utils import *
from subgame.dummy.gamelogic import *
from subgame.dummy import gamelogic
from mysqlassist import MYPGuard
from mysqlassist.myp_object import ServerMYP
from redisassist import RDSPGuard, EventRP
from redisassist.rdsproxyguard import EventRP, UserRP
from tableframe import TableDelegate
from requesthelper import *
import random
import numpy

class EnumGamePeriod(object):
    nIdle = 0  # 空閒等待階段
    nStart = 1  # 遊戲開始階段
    nAction = 2  # 回合操作階段
    nFinish = 3  # 遊戲結束階段
    nChallenge = 4  # 接受比牌思考階段

class GameConfig(object):
    vPeriodTime = None
    nInTax = 0
    nOutTax = 5
    vNextDeck = None
    mBroadCastTable = None

    @classmethod
    def Reset2Default(cls):
        cls.vPeriodTime = [0, 5, 20, 0, 9]
        cls.nInTax = 0
        cls.nOutTax = 5
        cls.vNextDeck = None
        cls.mBroadCastTable = { 79 : 50000 }

class ScoreRecords(object):
    def __init__(self):
        self.nGained = 0
        self.nLost = 0
        self.nGainedTax = 0
        self.nLostTax = 0

def GetServiceAttr(sServiceAttr = None):
    if sServiceAttr is not None:
        sServiceAttr.sChairCnt = 3
        sServiceAttr.sMinPlayer = 3
        sServiceAttr.sStartMode = eGSM.SM_ATLEAST_2_READY
        sServiceAttr.sAllowMatch = True
        sServiceAttr.sWaitStartTime = 20
        return True
    return False

def Create():
    return TableFrameSink()

def LoadConfig(servname):
    GameConfig.Reset2Default()
    LogicConfig.Reset2Default()
    return True

class PrivateConfig(object):
    def __init__(self):
        self.nCellScore = 100
        self.vPeriodTime = None
        self.nInTax = None
        self.nOutTax = None
        self.vNextDeck = None
        self.mBroadCastTable = None

    def Reload(self):
        self.nCellScore = 100
        self.vPeriodTime = deepcopy(GameConfig.vPeriodTime)
        self.nInTax = GameConfig.nInTax
        self.nOutTax = GameConfig.nOutTax
        self.vNextDeck = GameConfig.vNextDeck
        self.mBroadCastTable = GameConfig.mBroadCastTable

class TableFrameSink(TableDelegate):
    def __init__(self):
        self.mTableFrame = None
        self.mServiceOpt = None
        self.mServiceAttr = None

        self.xLogic = GameLogic()
        self.mUsers = {}
        self.nMainTimerID = -1
        self.nPeriod = EnumGamePeriod.nIdle
        self.nPeriodEndTime = 0
        self.challenge_end_time = 0  # 玩家接受比牌的思考終止時間
        self.strRoundSign = None
        self.mLastScore = {}
        self.xPrivateCfg = PrivateConfig()
        self.bReloaded = False
        self.strBeginTime = ""
        # self.real_player_can_not_open_can_dummy = False  # 玩家是否按下了未開張一次清空的dummy

    def InitDgt(self, t):
        self.mTableFrame = t
        self.mServiceOpt = self.mTableFrame.Attemper.ServiceOpt
        self.mServiceAttr = self.mTableFrame.Attemper.ServiceAttr
        return True

    def OnActionUserSitDown(self, wChairID, pSvrUserItem, bLookonUser = False)->bool:
        if pSvrUserItem is None or bLookonUser \
                or self.mTableFrame is None:
            return False
        if wChairID in self.mUsers:
            return True
        elif self.xLogic.PlayerJoinIn(wChairID, pSvrUserItem.IsAndroidUser):
            self.mUsers[wChairID] = pSvrUserItem
            return True
        return False

    def OnActionUserStandUp(self, wChairID, pSvrUserItem, bLookonUser = False)->bool:
        if pSvrUserItem is None:
            return False
        if wChairID in self.mUsers:
            if self.xLogic.PlayerLeave(wChairID):
                self.mUsers.pop(wChairID, None)
                return True
            else:
                return False
        return True

    def OnActionUserOnReady(self, wChairID, pSvrUserItem, pMsg)->bool:
        return True

    def OnActionUserEnterTable(self, wChairID, pSvrUserItem)->bool:
        if wChairID not in self.mUsers:
            return False
        self.SyncScene(wChairID)
        if self.xLogic.IsGaming:
            Log("SyncPeriod in OnActionUserEnterTable")
            self.SyncPeriod(wChairID, is_reconn = True)
            self.SyncAllScoreEvents(wChairID)
        return True

    def OnEventGameStart(self, vDeck):
        if self.nPeriod != EnumGamePeriod.nIdle:
            return
        if self.xLogic.GameStart(vDeck):
            cur_time = GetServerTime()
            self.strRoundSign = "%.10d%.3d%.11d%.3d" % (GetServerTime(), self.mServiceOpt.sSubGameId, self.mServiceOpt.sIndex, self.mTableFrame.TableID)
            ShowStatus(self.xLogic, self.strRoundSign, self.mUsers)
            period = EnumGamePeriod.nStart
            self.strBeginTime = GetServerTimeStr()
            self.nPeriod = period
            self.nPeriodEndTime = cur_time + self.xPrivateCfg.vPeriodTime[period]
            for chair_id, user_item in self.mUsers.items():
                self.SyncScene(chair_id)
                self.SyncPeriod(chair_id)
            self.nMainTimerID = self.mTableFrame.AddTimer(1, self.GameMainLoop, None)
        else:
            Err("尝试开启对局失败，未知的错误！")

    # def release_android_in_table(self):
    #     """釋放桌子中所有的機器人
    #
    #     為了連續遊戲，機器人狀態會被設定為準備中
    #     但可能在遊戲開始時判斷無法開局，要將這些機器人釋放回去
    #     """
    #     for _, user_item in self.mUsers.items():
    #         if user_item.IsAndroidUser:
    #             uuid = user_item.UUID
    #             android = self.mTableFrame.Attemper.AndroidService.GetAndroid(uuid)
    #             android.OnReposition()

    def OnInitialize(self, nCellScore, nThinkTime, nNoticeScore):  # , nChallengeTime):
        self.xPrivateCfg.Reload()
        self.xPrivateCfg.nCellScore = int(nCellScore)
        self.xPrivateCfg.vPeriodTime[EnumGamePeriod.nAction] = int(nThinkTime)  # 回合操作時間
        # self.xPrivateCfg.vPeriodTime[EnumGamePeriod.nChallenge] = int(nChallengeTime)  # 接受比牌思考時間  # TODO DO
        self.xPrivateCfg.mBroadCastTable[79] = int(nNoticeScore)
        #self.xPrivateCfg.vNextDeck = vDeck
        #self.strRoundSign = "%.10d%.7d%.3d" % (GetServerTime(), self.mServiceOpt.sSubGameId, self.mTableFrame.TableID)
        #self.strBeginTime = GetServerTimeStr()
        return True

    def OnReposition(self):
        pass

    def OnDisMissGame(self):  # 解散時，相關的flag重置
        # if self.nMainTimerID != -1:
        self.mTableFrame.RemoveTimer(self.nMainTimerID)
        self.nMainTimerID = -1
        self.xLogic.GameEnd()
        self.nPeriod = EnumGamePeriod.nIdle
        self.nPeriodEndTime = 0
        self.challenge_end_time = 0  # 玩家接受比牌的思考終止時間
        self.strRoundSign = None
        self.bReloaded = False
        return True

    def cancel_isgaming(self):  # 解散後isgaming flag仍在遊戲中
        self.xLogic.bIsGaming = False  # 解散後bIsGaming就不在遊戲中了

    def cancel_isfinished(self):  # 解散後isfinished flag仍未結束遊戲
        self.xLogic.bIsFinished = False  # 解散後isfinished就結束了

    def cancel_hasandroid(self):  # 解散後hasandroid flag仍存在
        self.xLogic.bHasAndroid = False  # 解散後hasandroid就不在了

    def OnGameMessage(self, wCmdID, pMsg, pSvrUserItem)->bool:
        if wCmdID == cg_msgid_game_op:
            if self.nPeriod != EnumGamePeriod.nAction:
                return True
            recv_msg = msg_game_op()
            if recv_msg.ParseFromString(pMsg):
                # if recv_msg.op_type == 64:  # if op_type = 0x40
                #     # 玩家按下了未開張一次清空的dummy
                #     self.real_player_can_not_open_can_dummy = True
                #     self.nPeriodEndTime = GetServerTime()  # 結束時間 = 就是現在，因此開始強制自動出牌
                # else:  # if op_type != 0x40
                params = [v for v in recv_msg.params]
                # 也有可能操作整牌者(自動組牌)非輪到該回合的玩家
                self.DoPlayerOperate(recv_msg.op_type, params, pSvrUserItem)

        return True

    def DoPlayerOperate(self, op_type, params, pSvrUserItem, android_round=False):  # params 1D
        # 若操作訊號為整牌鍵(自動組牌)
        if op_type == 8192:  # EnumGameOperation.GroupReorganize
            # 驗證操作者是否非自己回合按下整牌鍵(自動組牌)
            seat_index, params = self.xLogic.who_has_these_cards(params)  # params 2D
        # 若操作訊號為接受比牌或放棄比牌，而且是真人玩家操作  # EnumGameOperation.Challenge or EnumGameOperation.Fold
        elif (op_type == 1024 or op_type == 2048) and android_round == False:
            for i in params:  # params 1D and only with one int
                seat_index = i  # 操作者決不是輪到她回合，因此封包會夾帶操作座號進來
        else:
            seat_index = pSvrUserItem.ChairID  # 操作者為輪到她回合的玩家或機器人

        # 參數不使用pSvrUserItem.ChairID，因為有可能操作的玩家並不是輪到自己回合的人
        # android_round=True : 識別為機器人操作回合

        if self.xLogic.PlayerOperate(seat_index, op_type, params,
                                     android_round=android_round):
            ShowStatus(self.xLogic)
            bankruptcy_player_list = None   # 新增輸入破產玩家列表
            leverage_player_list = None     # 新增以小博大玩家列表
            final_rank = None    # 新增座號排序[2, 1, 0, 3]
            auto_operate_dc = {}
            member_grade_overall = None

            if self.xLogic.IsFinished:  # 如果遊戲結束
                # 新增輸入破產玩家列表、以小博大玩家列表、座號排序列表、整桌會員等級資訊
                bankruptcy_player_list, leverage_player_list, final_rank, member_grade_overall, auto_operate_dc = self.GameFinished()
            if op_type == 32:  # 0x20棄牌等同換人，下一位回合秒數重新倒計時
                self.nPeriodEndTime = GetServerTime() + self.xPrivateCfg.vPeriodTime[self.nPeriod]
            if op_type == 512:  # 0x200發起比牌時，接受比牌思考時間開始倒計時，回合時間也同步延長
                self.challenge_end_time = GetServerTime() + self.xPrivateCfg.vPeriodTime[EnumGamePeriod.nChallenge]
                self.nPeriodEndTime = GetServerTime() + self.xPrivateCfg.vPeriodTime[self.nPeriod]

            self.NotifyPlayerOperation(seat_index, op_type, params,
                                       bankruptcy_player_list=bankruptcy_player_list,
                                       leverage_player_list=leverage_player_list, final_rank=final_rank,
                                       member_grade_overall=member_grade_overall,
                                       auto_operate_dc=auto_operate_dc)

    def WriteUserScore(self, wChairID, nModScore, nCost, tableID=None, nScore=None):
        scoreInfo = stScoreInfo()
        scoreInfo.mScore = nScore
        scoreInfo.mModScore = nModScore
        scoreInfo.mCost = nCost
        scoreInfo.mRevenue = 0
        scoreInfo.mScoreType = eST.ST_DRAW if nModScore == 0 \
            else (eST.ST_WIN if nModScore > 0 else eST.ST_LOSE)
        member_grade_calculation = self.mTableFrame.WriteUserScore(wChairID, scoreInfo, tableID=tableID)
        return member_grade_calculation  # 回傳會員等級資訊

    def GameMainLoop(self, params):
        """
        因為未開張拉密也會執行此 method，但邏輯上應該是玩家操作，所以要 not 並以此作為判斷
            系統強制執行 -> is_not_dummy = True
            玩家未開張拉密 -> is_not_dummy = False
        """
        cur_time = GetServerTime()

        if self.xLogic.is_fight:  # 若場上為比牌階段
            if self.challenge_end_time <= cur_time:  # 有人發起比牌後第N次進入，接受比牌的時間到
                for seat_index in range(len(self.xLogic.Players)):  # 3人遊玩
                    # 強制放棄比牌
                    seat_index, op_type, op_data = self.xLogic.GetPlayerForceFold(seat_index)
                    if seat_index != None and op_type != None and op_data != None:
                        if self.xLogic.PlayerOperate(seat_index, op_type, op_data, auto_operate=True):  # 強制操作
                            if self.xLogic.IsFinished:
                                # 回傳破產玩家、以小博大玩家、座號排名列表、整桌會員等級資訊
                                bankruptcy_player_list, leverage_player_list, final_rank, member_grade_overall, auto_operate_dc = self.GameFinished()
                                # 新增輸入破產玩家、以小博大玩家、座號排名列表
                                self.NotifyPlayerOperation(seat_index, op_type, op_data,
                                                           bankruptcy_player_list=bankruptcy_player_list,
                                                           leverage_player_list=leverage_player_list,
                                                           final_rank=final_rank,
                                                           member_grade_overall=member_grade_overall,
                                                           auto_operate_dc=auto_operate_dc)

        if self.nPeriod == EnumGamePeriod.nFinish:  # 場上為結束階段
            self.xLogic.GameEnd()
            self.mTableFrame.ConcludeGame()
            self.nMainTimerID = -1
            self.nPeriod = EnumGamePeriod.nIdle
            self.nPeriodEndTime = 0  # 回合操作時間歸零
            self.challenge_end_time = 0  # 接受比牌時間歸零
            self.strRoundSign = None
            self.bReloaded = False
            return False

        if self.nPeriodEndTime <= cur_time:  # 場上為回合正常操作階段，回合操作時間到時
            if self.nPeriod == EnumGamePeriod.nStart:
                self.nPeriod = EnumGamePeriod.nAction
                # 啟動玩家回合操作倒計時時間
                self.nPeriodEndTime = cur_time + self.xPrivateCfg.vPeriodTime[self.nPeriod]

                for chair_id, player_info in self.xLogic.Players.items():
                    if player_info.IsJoined:
                        self.SyncPeriod(chair_id)  # 傳遞倒計時啟動資訊

            elif self.nPeriod == EnumGamePeriod.nAction:
                cur_turn = self.xLogic.CurrentTurn
                while True:
                    # 時間到，強制讓真人玩家進入自動操作()
                    seat_index, op_type, op_data = self.xLogic.GetPlayerForceOp()

                    if self.xLogic.PlayerOperate(seat_index, op_type, op_data, auto_operate=True):
                        self.mUsers[seat_index].ResetAutoOperateFailTimes()  # 重置自動操作失敗次數
                        ShowStatus(self.xLogic)

                        if self.xLogic.IsFinished:
                            # 回傳破產玩家、以小博大玩家、座號排名列表、整桌會員等級資訊
                            bankruptcy_player_list, leverage_player_list, final_rank, member_grade_overall, auto_operate_dc = self.GameFinished()
                            # 新增輸入破產玩家、以小博大玩家、座號排名列表
                            self.NotifyPlayerOperation(seat_index, op_type, op_data,
                                                       bankruptcy_player_list=bankruptcy_player_list,
                                                       leverage_player_list=leverage_player_list,
                                                       final_rank=final_rank,
                                                       member_grade_overall=member_grade_overall,
                                                       auto_operate_dc=auto_operate_dc)
                            break
                        elif cur_turn != self.xLogic.CurrentTurn:
                            self.nPeriodEndTime = cur_time + self.xPrivateCfg.vPeriodTime[self.nPeriod]
                            self.NotifyPlayerOperation(seat_index, op_type, op_data)
                            break
                        else:
                            self.nPeriodEndTime += 2
                            self.NotifyPlayerOperation(seat_index, op_type, op_data)
                            break
                    else:
                        if seat_index != None:
                            Err("玩家 {} 強制操作失敗".format(self.mTableFrame.mUserItemArr[seat_index].UUID))
                            self.mUsers[seat_index].AddAutoOperateFailTimes() # 累加自動操作失敗次數

                            if self.mUsers[seat_index].CheckAutoOperateFailTimesOverLimit(): # 檢查自動操作失敗次數超過限制
                                self.mTableFrame.DisMissGame(manual_dismiss=True) #解散游戏-强制终止游戏
                                return  False
                        break
            elif self.nPeriod == EnumGamePeriod.nFinish:
                self.xLogic.GameEnd()
                self.mTableFrame.ConcludeGame()
                self.nMainTimerID = -1
                self.nPeriod = EnumGamePeriod.nIdle
                self.nPeriodEndTime = 0  # 回合操作時間歸零
                self.challenge_end_time = 0  # 接受比牌時間歸零
                self.strRoundSign = None
                self.bReloaded = False
                return False
        return True

    def scoreRate(self, all_players_score_offset):  # 含有以小博大，計算所有人的最小比例
        player_calc_order = self.xLogic.Level  # 分數排名, 低到高
        min_scoreRate = None
        bankruptcy_player_list = []  # 破產座號(顯示一位)
        leverage_player_list = []  # 以小博大座號(顯示一位)
        all_bankruptcy = []  # 破產座號(不顯示)
        all_leverage = []  # 以小博大座號(不顯示)
        use_the_bankruptcy_player_carry_money = []  # 多位觸發破產的玩家所攜帶的錢
        use_the_leverage_player_carry_money = []  # 多位觸發以小博大的玩家所攜帶的錢
        cnt = len(player_calc_order)  # 玩家人數
        for i in range(cnt):
            player_info = player_calc_order[i]
            seat_index = player_info.SeatIndex
            user = self.mUsers[seat_index]
            ownScore = user.mUserInfo.mScore  # 自己帶的錢
            # (自己的遊戲分數 - 位移分數) * 底注
            original_score = (player_info.GetTotalScore()-(all_players_score_offset * (1/cnt))) * self.xPrivateCfg.nCellScore
            if player_info.GetTotalScore() == 0:
                scoreRate = 1  # 正常比例
            elif abs(original_score) == 0:
                scoreRate = 1  # 正常比例
            else:
                scoreRate = ownScore / abs(original_score)  # 計算比例
                if ownScore < abs(original_score):
                    if original_score < 0:
                        if min_scoreRate == None:  # 最小比例不存在時
                            min_scoreRate = scoreRate
                            # 加入目前觸發破產的玩家(還沒走訪完)
                            bankruptcy_player_list.append(seat_index)
                            all_bankruptcy.append(seat_index)
                            # 這一位觸發破產的玩家所攜帶的錢
                            use_the_bankruptcy_player_carry_money.append(ownScore)
                        elif scoreRate < min_scoreRate:  # 比例比上一個最小比例，還要小
                            min_scoreRate = scoreRate  # 取代上一位成為最小比例
                            del bankruptcy_player_list[:]  # 刪除破產座號(顯示一位)
                            del leverage_player_list[:]  # 刪除以小博大座號列表(顯示一位)
                            del all_bankruptcy[:]  # 刪除多位破產座號(不顯示)
                            del all_leverage[:]  # 刪除多位以小博大座號(不顯示)
                            del use_the_bankruptcy_player_carry_money[:]  # 刪除多位破產玩家攜帶的錢
                            del use_the_leverage_player_carry_money[:]  # 刪除多位以小博大玩家攜帶的錢
                            # 加入唯一一位真正觸發破產的玩家
                            bankruptcy_player_list.append(seat_index)
                            all_bankruptcy.append(seat_index)
                            # 這一位觸發破產的玩家所攜帶的錢
                            use_the_bankruptcy_player_carry_money.append(ownScore)
                        elif scoreRate == min_scoreRate:
                            # 加入第2位「最小比例」的破產玩家
                            all_bankruptcy.append(seat_index)
                            # 第2位觸發玩家所攜帶的錢
                            use_the_bankruptcy_player_carry_money.append(ownScore)
                    # 自己帶的錢*其他人數倍數 < 自己贏的錢 = 達成以小博大條件
                    elif ownScore * (cnt - 1) < abs(original_score):
                        # 重新計算以小博大專屬的scoreRate
                        scoreRate = ownScore * (cnt - 1) / abs(original_score)
                        if min_scoreRate == None:  # 最小比例不存在時
                            min_scoreRate = scoreRate
                            # 加入目前觸發以小搏大的玩家(還沒走訪完)
                            leverage_player_list.append(seat_index)
                            all_leverage.append(seat_index)
                            # 這一位觸發以小搏大的玩家所攜帶的錢的倍數(2人桌1倍、3人桌2倍、4人桌3倍)
                            use_the_leverage_player_carry_money.append(ownScore*(cnt-1))
                        elif scoreRate < min_scoreRate:  # 比例比上一個最小比例，還要小
                            min_scoreRate = scoreRate  # 取代上一位成為最小比例
                            del bankruptcy_player_list[:]  # 刪除破產座號列表
                            del leverage_player_list[:]  # 刪除以小博大座號列表
                            del all_bankruptcy[:]  # 刪除多位破產玩家列表
                            del all_leverage[:]  # 刪除多位以小博大座號(不顯示)
                            del use_the_bankruptcy_player_carry_money[:]  # 刪除多位破產玩家攜帶的錢
                            del use_the_leverage_player_carry_money[:]  # 刪除多位以小博大玩家攜帶的錢
                            # 加入唯一一位真正觸發以小博大的玩家
                            leverage_player_list.append(seat_index)
                            all_leverage.append(seat_index)
                            # 這一位觸發以小博大的玩家所攜帶的錢的倍數(2人桌1倍、3人桌2倍、4人桌3倍)
                            use_the_leverage_player_carry_money.append(ownScore*(cnt-1))
                        elif scoreRate == min_scoreRate:
                            # 加入第2位「最小比例」的以小博大玩家
                            all_leverage.append(seat_index)
                            # 第2位觸發玩家所攜帶的錢的倍數(2人桌1倍、3人桌2倍、4人桌3倍)
                            use_the_leverage_player_carry_money.append(ownScore*(cnt-1))
        # 如果從頭到尾所有玩家都沒觸發以小博大或破產
        if min_scoreRate == None:
            return 1, [], [], [], [], [], []
        elif min_scoreRate >= 1:
            return 1, [], [], [], [], [], []
        else:
            return min_scoreRate, bankruptcy_player_list, leverage_player_list, all_bankruptcy, all_leverage, use_the_bankruptcy_player_carry_money, use_the_leverage_player_carry_money

    def scoreRateWithoutLeverage(self, all_players_score_offset):  # 不含以小博大，計算所有人的最小比例
        player_calc_order = self.xLogic.Level  # 分數排名, 低到高
        min_scoreRate = None
        bankruptcy_player_list = []  # 破產座號(顯示一位)
        all_bankruptcy = []  # 破產座號(不顯示)
        use_the_bankruptcy_player_carry_money = []  # 多位觸發破產的玩家所攜帶的錢
        cnt = len(player_calc_order)  # 遊戲人數
        for i in range(cnt):
            player_info = player_calc_order[i]
            seat_index = player_info.SeatIndex
            user = self.mUsers[seat_index]
            ownScore = user.mUserInfo.mScore  # 自己帶的錢
            # (自己的遊戲分數 - 位移分數) * 底注
            original_score = (player_info.GetTotalScore()-(all_players_score_offset * (1/cnt))) * self.xPrivateCfg.nCellScore
            if player_info.GetTotalScore() == 0:
                scoreRate = 1  # 正常比例
            elif abs(original_score) == 0:
                scoreRate = 1  # 正常比例
            else:
                if original_score < 0:
                    scoreRate = ownScore / abs(original_score)  # 計算比例
                    if ownScore < abs(original_score):
                        if min_scoreRate == None:  # 最小比例不存在時
                            min_scoreRate = scoreRate
                            # 加入目前觸發破產的玩家(還沒走訪完)
                            bankruptcy_player_list.append(seat_index)
                            all_bankruptcy.append(seat_index)
                            # 這一位觸發破產的玩家所攜帶的錢
                            use_the_bankruptcy_player_carry_money.append(ownScore)
                        elif scoreRate < min_scoreRate:  # 比例比上一個最小比例，還要小
                            min_scoreRate = scoreRate  # 取代上一位成為最小比例
                            del bankruptcy_player_list[:]  # 刪除破產座號(顯示一位)
                            del all_bankruptcy[:]  # 刪除多位破產座號(不顯示)
                            del use_the_bankruptcy_player_carry_money[:]  # 刪除多位破產玩家攜帶的錢
                            # 加入唯一一位真正觸發破產的玩家
                            bankruptcy_player_list.append(seat_index)
                            all_bankruptcy.append(seat_index)
                            # 這一位觸發破產的玩家所攜帶的錢
                            use_the_bankruptcy_player_carry_money.append(ownScore)
                        elif scoreRate == min_scoreRate:
                            # 加入第2位「最小比例」的破產玩家
                            all_bankruptcy.append(seat_index)
                            # 第2位觸發玩家所攜帶的錢
                            use_the_bankruptcy_player_carry_money.append(ownScore)
        # 如果從頭到尾所有玩家都沒觸發以小博大或破產
        if min_scoreRate == None:
            return 1, [], [], []
        elif min_scoreRate >= 1:
            return 1, [], [], []
        else:
            return min_scoreRate, bankruptcy_player_list, all_bankruptcy, use_the_bankruptcy_player_carry_money

    def _get_redis_log_mode_for_tester(self, player_calc_order):
        """
        如果玩家中有人的名稱是 play_star_tester 代表此局不需要記錄到 redis 中
        """
        tester_mode = False

        for tmp in player_calc_order:
            information_seat_index = tmp.SeatIndex  # 個人資訊提取個人座號
            user_name = self.mUsers[information_seat_index].mUserInfo.mSdkUUID

            if user_name == 'play_star_tester':
                tester_mode = True
                break

        return tester_mode

    def _get_day_interval_and_nowtime(self, login_time):
        """取得玩家登入天數差距

        Args:
            login_time (int): 時間戳

        Returns:
            int: 天數差距
            int: 現在時間戳
        """
        tz = datetime.timezone(datetime.timedelta(hours=+7))

        nowtime = datetime.datetime.now(tz)
        lastlogintime = datetime.datetime.fromtimestamp(login_time).astimezone(tz)  # int to datetime

        # 去掉時間，用日期做天數計算
        nowtime_date = datetime.datetime(nowtime.year, nowtime.month, nowtime.day)
        lastlogintime_date = datetime.datetime(lastlogintime.year,
                                               lastlogintime.month,
                                               lastlogintime.day)

        return (nowtime_date - lastlogintime_date).days, nowtime

    def _add_water_balloon(self, user_item, player_info):
        uuid = user_item.mUserInfo.mUUID  # 多代理商uuid
        host_api_key = user_item.mUserInfo.mChannel  # 撈取玩家代理商

        rp = RDSPGuard.RP("game")
        hostuuid = None  # 先預設單代理模式下沒有hostuuid
        # if self.mServiceOpt.sMultiHost == 1:  # 若遊戲為多代理商模式
        #     # ===取得redis base資訊===
        #     account_base_ss = rp.LibGrd.R.hget(
        #         "sha@data_" + str(user_item.mUserInfo.mUUID), "base")
        #     if account_base_ss is not None:
        #         account_base = db_data_user()
        #         account_base.ParseFromString(account_base_ss)
        #         hostuuid = account_base.hostuuid  # 同步單代理商uuid
        # 取得潑水節2倍水球起始日
        date_redis = rp.LibGrd.R.hget("sha@chl_" + self.mServiceOpt.sHostApiKey, "date")
        songkran_start = None
        two_times_date = None
        songkran_end = None
        if date_redis != None:
            date_redis = json.loads(date_redis.decode())
            songkran_start = date_redis["songkran_start"]  # 取得活動起始日
            two_times_date = date_redis["two_times_date"]  # 取得2倍水球加碼日
            songkran_end = date_redis["songkran_end"]  # 取得潑水節活動結束日

        water_balloon = player_info.WaterBalloon  # 預設一倍
        if two_times_date != None and songkran_end != None:  # 檢查是否要雙倍且活動是否結束
            # two_times_date_int = int(time.mktime(time.strptime(two_times_date, "%Y-%m-%d")))
            # 若2倍水球活動設定起始日與潑水節活動早就開始了
            if two_times_date <= int(time.time()) and songkran_end >= int(time.time()):
                water_balloon = player_info.WaterBalloon * 2
            # 若活動未結束，才要寫入任務次數、水球數與抽獎券
            if songkran_start <= int(time.time()) and songkran_end >= int(time.time()):
                EventRP.add_point(uuid, water_balloon)

                event_data = EventRP.get_event_data(uuid)  # 獲取玩家登入活動所需資料
                day_interval, nowtime = self._get_day_interval_and_nowtime(event_data["login_time"])

                # 給抽獎券
                lottery_ticket_num = EventRP.room_lottery_ticket_dc[str(self.mServiceOpt.sSubGameId)]
                event_data["lottery_ticket"] = event_data.get("lottery_ticket", 0) + lottery_ticket_num

                # 判斷是否需要重製每日水球上限
                if day_interval == 1 and event_data.get("reset_point_in_game", 0) == 0:
                    event_data["daily_point"] = 0
                    event_data["reset_point_in_game"] = 1

                EventRP.update_event_data(uuid, event_data, hostuuid, host_api_key,
                                          ServiceOpt.sSubGameId)

    def GameFinished(self):
        self.mLastScore.clear()
        self.real_player_can_not_open_can_dummy = False  # 遊戲結束0x40訊號回歸初始值
        player_calc_order = self.xLogic.Level  # 分數排名, 低到高
        # 增加座號array，排序由第4名至第1名
        final_rank = []
        for i in player_calc_order:
            final_rank.append(i.SeatIndex)  # 呈現結果範例：[2, 1, 3, 0]，2號為第4名
        all_players_score_offset = 0  # 所有玩家的分數距離0的差距offset(有正負)
        for player_info in player_calc_order:
            self.mLastScore[player_info.SeatIndex] = ScoreRecords()
            # 將所有玩家的分數加總(用來判斷是否等於0或有位移)
            all_players_score_offset += player_info.GetTotalScore()
        in_tax = self.xPrivateCfg.nInTax
        out_tax = self.xPrivateCfg.nOutTax  # 5%
        cnt = len(player_calc_order)
        bankruptcy_player_list = []  # 破產座號(顯示一位)
        leverage_player_list = []  # 以小博大座號(顯示一位)
        all_bankruptcy = []  # 破產座號(不顯示)
        all_leverage = []  # 以小博大座號(不顯示)
        use_the_bankruptcy_player_carry_money = []  # 多位觸發破產的玩家所攜帶的錢
        use_the_leverage_player_carry_money = []  # 多位觸發以小博大的玩家所攜帶的錢

        if self.mServiceOpt.sAllowLeverage != 0:  # 以小博大機制結算開啟
            scoreRate, bankruptcy_player_list, leverage_player_list, all_bankruptcy, all_leverage, use_the_bankruptcy_player_carry_money, use_the_leverage_player_carry_money = self.scoreRate(all_players_score_offset)
        else:  # 以小博大機制結算關閉，不計算以小博大
            scoreRate, bankruptcy_player_list, all_bankruptcy, use_the_bankruptcy_player_carry_money = self.scoreRateWithoutLeverage(all_players_score_offset)

        for i in range(cnt):  # cnt = 玩家N人
            player_info = player_calc_order[i]
            total_score = player_info.GetTotalScore()  # 自己的遊戲分數
            # total_cost = 0 # 跟其他玩家遊戲分數差異的總合
            # for j in [1, 2, 3]:
            #     total_cost += player_calc_order[j].GetTotalScore() - total_score
            #
            # if total_cost < 1:
            #     continue
            seat_index = player_info.SeatIndex
            # cost_user_score = total_cost * self.xPrivateCfg.nCellScore  # 總共要給其他玩家的總賠分
            # 自己的賠分(負的表示不用賠) = 自己遊戲分數的負值 * 底注 * 以小搏大比例
            seif_lose_points = -(total_score - (all_players_score_offset * (1 / cnt))) * self.xPrivateCfg.nCellScore * scoreRate

            if seif_lose_points > 0:  # 如果4個人不存在有玩家破產，而自己要賠錢
                # 自己要賠的錢
                seif_lose_points_append = seif_lose_points
                # 未稅以前，自己可得到的錢
                self.mLastScore[seat_index].nGained += 0
                # 未稅以前，自己必須失去的錢
                self.mLastScore[seat_index].nLost += int(math.floor(seif_lose_points_append))
            else:  # 自己不用賠錢
                # 自己要賠的錢是負值，等於不用賠，所以取絕對值，加到下面的nGained清單
                seif_lose_points_append = -seif_lose_points
                # 未稅以前，自己可得到的錢
                self.mLastScore[seat_index].nGained += int(math.floor(seif_lose_points_append))
                # 未稅以前，自己必須失去的錢
                self.mLastScore[seat_index].nLost += 0
            if len(all_bankruptcy) > 0:
                # 如果有人觸發破產最小比例，不管前面做什麼，就將觸發破產的那一位玩家的金額完整扣到0.00
                for j in range(len(all_bankruptcy)):
                    # 此玩家直接視為得到0元
                    self.mLastScore[all_bankruptcy[j]].nGained = 0
                    # 此玩家失去的錢，就會是自己攜帶進來的錢
                    self.mLastScore[all_bankruptcy[j]].nLost = use_the_bankruptcy_player_carry_money[j]
            elif len(all_leverage) > 0:
                # 如果有人觸發以小博大最小比例，不管前面做什麼，就將觸發以小博大的那一位玩家的金額完整加到自己攜帶的金額
                for j in range(len(all_leverage)):
                    # 此玩家得到的錢，就會是自己攜帶進來的錢的倍數(2人桌1倍、3人桌2倍、4人桌3倍)
                    self.mLastScore[all_leverage[j]].nGained = use_the_leverage_player_carry_money[j]
                    # 此玩家直接視為失去0元
                    self.mLastScore[all_leverage[j]].nLost = 0
        # 如果全場最小比例是以小博大
        if len(all_leverage) > 0:
            # 最後再把所有人的賠付總和，統一計算給最後1名
            pay_for_the_first = 0  # 預設所有人要賠給最後1名的錢
            for seat_index in final_rank:  # 走訪所有名次
                if seat_index != final_rank[0]:  # 走訪到最後1名不用進去，直接離開
                    sc_rec = self.mLastScore[seat_index]
                    tot = sc_rec.nGained - sc_rec.nLost
                    # tot是各自的最終分數，所以加上tot才是最後1名要賠的錢
                    pay_for_the_first = pay_for_the_first + tot
            # 結算最後1名可拿到的錢
            self.mLastScore[final_rank[0]].nGained = 0
            # 結算最後1名失去的錢
            self.mLastScore[final_rank[0]].nLost = pay_for_the_first
        else:  # 如果全場最小比例是破產，或者乾脆沒有最小比例的話
            # 最後再把所有人的賠付總和，統一計算給第1名
            pay_for_the_first = 0  # 預設所有人要賠給第1名的錢
            for seat_index in final_rank:  # 走訪所有名次
                if seat_index != final_rank[-1]:  # 走訪到第1名不用進去，直接離開
                    sc_rec = self.mLastScore[seat_index]
                    tot = sc_rec.nGained - sc_rec.nLost
                    # tot是各自的最終分數，所以減掉tot才是要賠給第1名的錢
                    pay_for_the_first = pay_for_the_first - tot
            # 結算第1名可拿到的錢
            self.mLastScore[final_rank[-1]].nGained = pay_for_the_first
            # 結算第1名失去的錢
            self.mLastScore[final_rank[-1]].nLost = 0
        # 開始計算含稅後可得到的錢與失去的錢
        member_grade_overall = []  # 儲存每個人的等級資訊
        for seat_index in self.mLastScore:
            sc_rec = self.mLastScore[seat_index]
            tot = sc_rec.nGained - sc_rec.nLost
            if tot > 0:
                tot = int(math.floor(tot))
                sc_rec.nOutTax = int(math.ceil(tot * (out_tax / 100)))
                real_tot = tot - sc_rec.nOutTax
                # 各別進入寫入遊戲積分並回傳等級資訊
                member_grade_calculation = self.WriteUserScore(seat_index, real_tot, 0, tableID=self.mTableFrame.TableID)
                member_grade_overall.append(member_grade_calculation)  # 各別加入每個人的等級資訊
                if self.xLogic.HasAndroid and \
                        not self.mUsers[seat_index].IsAndroidUser:
                    self.mTableFrame.ModifyStockValue(-tot)
                bc_table = self.xPrivateCfg.mBroadCastTable
                tids = list(bc_table.keys())
                tids.sort()
                for tid in tids:
                    cond = bc_table[tid]
                    if tot >= cond:
                        argv = []
                        nam = self.mUsers[seat_index].mUserInfo.mSdkUUID
                        if not nam:
                            nam = self.mUsers[seat_index].mUserInfo.mNickName
                        if isinstance(nam, bytes):
                            nam = nam.decode()
                        argv.append(nam)
                        argv.append(str(self.mServiceOpt.sSubGameId))
                        argv.append(str(real_tot))
                        argv.append(str(self.mServiceOpt.sIndex))
                        self.mTableFrame.SendAwardNoticeMsg(0, tid, argv)
                        break
            elif tot < 0:
                tot = int(math.ceil(tot))
                sc_rec.nInTax = int(math.floor(-tot * (in_tax / 100)))
                # 各別進入寫入遊戲積分並回傳等級資訊
                member_grade_calculation = self.WriteUserScore(seat_index, tot, 0, tableID=self.mTableFrame.TableID)
                member_grade_overall.append(member_grade_calculation)  # 各別加入每個人的等級資訊
                if self.xLogic.HasAndroid and \
                        not self.mUsers[seat_index].IsAndroidUser:
                    self.mTableFrame.ModifyStockValue(-tot - sc_rec.nInTax)
            else:
                # 各別進入寫入遊戲積分並回傳等級資訊
                member_grade_calculation = self.WriteUserScore(seat_index, 0, 0, tableID=self.mTableFrame.TableID)
                member_grade_overall.append(member_grade_calculation)  # 各別加入每個人的等級資訊

        member_grade_overall = self.member_grade_transform(member_grade_overall)  # 轉換等級資訊格式
        players = {}
        fixed_multi_game_id = ""  # 固定遊戲代號，供機器人抓取不到base，能隨意給他同桌真人玩家的遊戲代號
        fixed_multi_channel = ""  # 固定商戶代號，供機器人抓取不到base，能隨意給他同桌真人玩家的商戶代號
        if fixed_multi_game_id == "" or fixed_multi_channel == "":  # 若固定遊戲代號或固定商戶代號都沒資料
            for every_player_info in player_calc_order:
                seat_index = every_player_info.SeatIndex
                if not self.mUsers[seat_index].IsAndroidUser:
                    # ===取得redis base資訊===
                    rp = RDSPGuard.RP("game")
                    account_base_ss = rp.LibGrd.R.hget("sha@data_" + str(self.mUsers[seat_index].mUserInfo.mUUID), "base")
                    if account_base_ss is not None:
                        account_base = db_data_user()
                        account_base.ParseFromString(account_base_ss)
                        # 塞入遊戲代號，供同桌機器人使用
                        fixed_multi_game_id = account_base.game_id
                        # 塞入商戶代號，供同桌機器人使用
                        fixed_multi_channel = account_base.channel
                        break
                # =======================
        all_table_confirm_vip = False  # 是否達成vip自動化條件
        all_table_info = {}  # 取得整桌每個人的{名稱: [商戶代號, 遊戲代號, vip為0或1, uuid]}
        for player_info in player_calc_order:
            seat_index = player_info.SeatIndex
            player_rec = {}
            nam = self.mUsers[seat_index].mUserInfo.mSdkUUID
            if not nam:
                 nam = self.mUsers[seat_index].mUserInfo.mNickName
            if isinstance(nam, bytes):
                nam = nam.decode()
            player_rec["nam"] = nam
            # player_rec["hand"] = list(player_info.InHand.keys())
            player_rec["gsc"] = player_info.GainedScore
            player_rec["lsc"] = player_info.LostScore
            player_rec["opn"] = player_info.IsOpened
            player_rec["point"] = player_info.compare_point

            # 取得真人玩家或機器人的等級、頭像、頭框(遊戲紀錄資料半成品, uuid, 座號)
            player_rec = self.GetLvFaceidFrame(player_rec, self.mUsers[seat_index].mUserInfo.mUUID, seat_index)

            sc_rec = self.mLastScore[seat_index]
            tot = sc_rec.nGained - sc_rec.nLost
            if tot > 0:
                tot = int(math.floor(tot))
                tot_without_outtax = tot  # 未含抽水的贏分
                tot -= int(math.ceil(sc_rec.nOutTax))
            elif tot < 0:
                tot = int(math.ceil(tot))
                tot_without_outtax = tot  # 未含抽水的輸分
            else:
                tot_without_outtax = 0  # 未含抽水的平手，統一視為0
            player_rec["tot"] = tot
            player_rec["twt"] = tot_without_outtax
            player_rec["twin"] = abs(player_rec["tot"] + tot_without_outtax) if tot_without_outtax > 0 else 0
            player_rec["gold"] = self.mUsers[seat_index].mUserInfo.mScore
            if all_table_confirm_vip == False:  # 走訪玩家過程尚未達成vip自動化條件，才需要確認
                # 確認是否達成自動化vip條件
                all_table_confirm_vip = self.confirm_vip(tot)
            rp = RDSPGuard.RP("game")
            chl_resp = rp.LibGrd.Call("channel.GetInfo", *(self.mServiceOpt.sHostApiKey,))

            if self.mUsers[seat_index].IsAndroidUser == False and not self.mServiceOpt.IsEducateSvr():  # 如果不是機器人帳號
                account_res = rp.LibGrd.Call("common.GetInfoBySYS", *(self.mUsers[seat_index].mUserInfo.mUUID,))

                wallet_type = self.mUsers[seat_index].mUserInfo.wallet_type

                if account_res[0] != 0:
                    continue

                account_base = db_data_user()
                account_base.ParseFromString(account_res[1])

                # 檢查玩家是否贏太多需要通知風控
                self.prize_notice(account_base, player_rec, tot_without_outtax)

                single_host_api_key = account_base.sin_channel
                multi_inf = rp.LibGrd.R.hget("multi@inf_" + account_base.channel, single_host_api_key)
                multi_inf = json.loads(multi_inf)

                # if chl_resp[0] == 0:
                #     tmp = OnRedisResultParser(chl_resp[1])
                #     ctm_data = json.loads(tmp["extra"])
                #     if int(self.mServiceOpt.sMultiHost) == 1:  # 多代理商
                #         gs_url = ctm_data["gs_url"]
                #         host_chl = "CARD_" + account_base.channel
                #         if host_chl in gs_url:
                #             gs_url = gs_url[host_chl]
                # if int(self.mServiceOpt.sMultiHost) == 1:  # 多代理商
                #     if wallet_type == 1:
                #         host_url = RequestHelper.DoPost(gs_url + "/hosturl", {"host_api_key": account_base.channel})
                #         host_url = host_url["data"]
                #         self.BetResult(account_base, account_res, host_url, player_rec, seat_index, tot_without_outtax)
                # else:  # 單代理商
                if wallet_type == 1:
                    host_url = multi_inf["host_url"]
                    self.BetResult(account_base, account_res, host_url, player_rec, seat_index, tot_without_outtax)
            '''
            combos = player_info.Combos
            player_combos = {}
            for combo_index in combos:
                combo = combos[combo_index]
                player_combos[combo_index] = list(combo.keys())
            player_rec["cbs"] = player_combos
            '''
            sc_records = player_info.ScoreRecords
            player_sc_records = []
            for rec_info in sc_records:
                main_type = rec_info[0]
                ev = {}
                ev["mt"] = main_type
                if main_type == EnumScoreBaseType.nNormal:
                    ev["st"] = rec_info[1]
                    ev["cl"] = rec_info[2]
                    ev["sc"] = rec_info[3]
                elif main_type == EnumScoreBaseType.nSpecial:
                    ev["st"] = rec_info[1]
                    ev["sc"] = rec_info[2]
                elif main_type == EnumScoreBaseType.nFinish:
                    ev["cl"] = rec_info[1]
                    ev["sc"] = rec_info[2]
                    ev["st"] = rec_info[3]
                player_sc_records.append(ev)
            player_rec["sce"] = player_sc_records
            players[player_info.SeatIndex] = player_rec
            player_rec["bot"] = self.mUsers[seat_index].IsAndroidUser  # 新增bot，確認此座號為機器人座號
            # 不是機器人帳號時，塞入固定的遊戲代號
            if self.mUsers[seat_index].IsAndroidUser == False:
                # ===取得redis base資訊===
                rp = RDSPGuard.RP("game")
                account_base_ss = rp.LibGrd.R.hget("sha@data_" + str(self.mUsers[seat_index].mUserInfo.mUUID), "base")
                if account_base_ss is not None:
                    account_base = db_data_user()
                    account_base.ParseFromString(account_base_ss)
                    # 遊戲紀錄增加一欄game：供後臺歷史紀錄抓取game_id
                    # 避免多代理商後台紀錄只顯示在多代理商server所屬遊戲代號的區域內
                    player_rec["game"] = account_base.game_id
                    # 給PS抓取各自的商戶
                    player_rec["htk"] = account_base.channel
                    # 不管這局結束前是不是vip，都先加入all_table_info
                    # 取得整桌每個人的{名稱: [商戶代號, 遊戲代號, vip為0或1, uuid]}
                    all_table_info.update({nam: [account_base.game_id, account_base.channel, account_base.VIP,
                                                 self.mUsers[seat_index].mUserInfo.mUUID]})
            # 是機器人帳號時，將fixed_multi_game_id、fixed_multi_channel塞入紀錄，視為機器人的遊戲代號與商戶
            else:
                player_rec["game"] = fixed_multi_game_id
                player_rec["htk"] = fixed_multi_channel
        if all_table_confirm_vip == True:  # 若vip條件達成
            self.insert_vip(all_table_info)  # 將所有人寫入VIP_player資料表
        ending_time_str = GetServerTimeStr()
        gc = []
        send_log_host = []

        for player_info in player_calc_order:
            seat_index = player_info.SeatIndex
            if seat_index not in self.mUsers:
                continue
            user_item = self.mUsers[seat_index]
            sc_rec = self.mLastScore[seat_index]
            player_log = stPlayerLog()
            player_log.nUUID = user_item.mUserInfo.mUUID
            player_log.sMemberID = user_item.mUserInfo.mSdkUUID
            player_log.sChannel = user_item.mUserInfo.mChannel
            if player_log.sChannel not in send_log_host:
                send_log_host.append(player_log.sChannel)
            nam = user_item.mUserInfo.mSdkUUID
            if not nam:
                 nam = self.mUsers[seat_index].mUserInfo.mNickName
            if isinstance(nam, bytes):
                nam = nam.decode()
            player_log.mNickName = nam
            tot = sc_rec.nGained - sc_rec.nLost
            if tot > 0:
                tot = int(math.floor(tot))
                player_log.nCalScore = tot - int(math.ceil(sc_rec.nOutTax))
                player_log.nTax = sc_rec.nOutTax
            else:
                tot = int(math.ceil(tot))
                player_log.nCalScore = tot
                player_log.nTax = 0
            player_log.nCurrentScore = user_item.mUserInfo.mScore
            player_log.sTime = ending_time_str
            player_log.sRoundID = self.strRoundSign
            player_log.nTableID = self.mTableFrame.TableID
            player_log.nChairID = seat_index
            self.mTableFrame.WritePlayerLog(player_log)

        auto_operate_dc = {}  # 記錄每位玩家是否由自動操作，傳給前端使用

        for player_info in player_calc_order:
            seat_index = player_info.SeatIndex
            player_rec = players[seat_index]

            auto_operate_dc[str(seat_index)] = player_info.auto_operate
            player_rec["auto_operate"] = player_info.auto_operate
            player_info.set_auto_operate(False)  # 避免影響到下一局，狀態設定回預設

            user_item = self.mUsers[seat_index]
            member_id = user_item.mUserInfo.mSdkUUID
            player_rec["mid"] = member_id
            # 走訪每一個座號，將水球數更新至redis event

            if not self.mUsers[seat_index].IsAndroidUser:
                self._add_water_balloon(user_item, player_info)

        table_rec = {}
        table_rec["p"] = players
        table_rec["gc"] = gc
        table_rec["bt"] = self.strBeginTime
        table_rec["cell"] = self.xPrivateCfg.nCellScore
        table_rec["bankruptcy"] = bankruptcy_player_list  # 遊戲紀錄顯示破產玩家列表
        table_rec["leverage"] = leverage_player_list  # 遊戲紀錄顯示以小博大玩家列表
        table_rec["finalrank"] = final_rank  # 遊戲紀錄顯示座號排序列表
        table_log = stTableLog()
        table_log.nTableID = self.mTableFrame.TableID
        table_log.sRoundID = self.strRoundSign
        table_log.sTime = ending_time_str
        table_log.sDetailInfo = table_rec
        android_civil_war = True  # 新增機器人內戰標籤
        for information in player_calc_order:  # 走訪所有人的資訊
            information_seat_index = information.SeatIndex  # 個人資訊提取個人座號
            if not self.mUsers[information_seat_index].IsAndroidUser:  # 如果遊戲桌只要有一位真人玩家
                android_civil_war = False  # 那就不是機器人內戰
                break

        is_tester_mode = self._get_redis_log_mode_for_tester(player_calc_order)
        # android_civil_war = False 代表不會同步回去 DB
        # 測試帳號不會同步，把這個變數拿來用
        android_civil_war = True if is_tester_mode else android_civil_war

        # 寫DB時多帶入android_civil_war，確保機器人內戰不寫入PS DB
        self.mTableFrame.WriteTableLog(table_log, send_log_host, android_civil_war)
        # 還要再多寫accounting與accounting_robot至ps_db
        self.write_table_log_to_ps_db(table_log, len(player_calc_order))

        self.nPeriod = EnumGamePeriod.nFinish

        # self.nPeriodEndTime = GetServerTime() + self.xPrivateCfg.vPeriodTime[self.nPeriod]

        # 將破產玩家列表、以小博大玩家列表、座號排序列表回傳DoPlayerOperate()與GameMainLoop()
        return bankruptcy_player_list, leverage_player_list, final_rank, member_grade_overall, auto_operate_dc

    def write_table_log_to_ps_db(self, table_log, player_amounts):  # 從gs寫入遊戲紀錄至ps_db
        if self.mServiceOpt.IsEducateSvr():
            return  # 試玩房不用寫遊戲紀錄，亦不用同步至ps_db

        table_log.sDetailInfo["p"] = self.AccountingJsonCut(table_log.sDetailInfo["p"])

        for i in range(player_amounts):  # 走訪當局遊戲人數
            # 向redis的sha@chl取得玩家所屬來源的商戶名稱
            host_api_key = table_log.sDetailInfo["p"][i]["htk"] \
                if "htk" in table_log.sDetailInfo["p"][i] else self.mServiceOpt.sHostApiKey
            rp = RDSPGuard.RP("game")
            if not table_log.sDetailInfo["p"][i]["bot"]:  # 真人玩家的遊戲紀錄
                account_base = UserRP.get_account_base(str(self.mUsers[i].mUserInfo.mUUID))
                multi_inf = rp.LibGrd.R.hget("multi@inf_" + host_api_key, account_base.sin_channel)
                multi_inf = json.loads(multi_inf)
                robot_host_id = multi_inf["host_id"]
                robot_db_id = multi_inf["db_id"]
                break
        for i in range(player_amounts):  # 走訪當局遊戲人數
            parameters = {}  # 為下一位準備寫入的欄位內容
            parameters["machine_id"] = -1

            rp = RDSPGuard.RP("game")
            name = rp.LibGrd.R.hget("sha@chl_" + host_api_key, "name")
            # 確認name不為none後再進行decode解析
            parameters["host_id"] = str(name.decode()) if name else ""

            parameters["host_level"] = 0
            parameters["begin_time"] = table_log.sDetailInfo["bt"]
            parameters["game_time"] = table_log.sTime
            parameters["game_id"] = table_log.sDetailInfo["p"][i]["game"]
            parameters["subgame_id"] = self.mServiceOpt.sSubGameId
            parameters["member_id"] = table_log.sDetailInfo["p"][i]["nam"]
            parameters["init_cent"] = table_log.sDetailInfo["p"][i]["gold"] - table_log.sDetailInfo["p"][i]["tot"]
            parameters["bet"] = abs(table_log.sDetailInfo["p"][i]["twt"])
            parameters["denom"] = 1
            parameters["total_win"] = table_log.sDetailInfo["p"][i]["twin"]
            parameters["bonus_win"] = 0
            parameters["gamble_win"] = 0
            parameters["jackpot_win"] = 0

            # 整理gs的game_table_log給ps的accounting的game_data
            # 整段game_table_log.Log無p物件
            jLog = {}  # {}
            jLog["hashkey"] = self.mServiceOpt.sHashKey
            jLog["hostapikey"] = self.mServiceOpt.sHostApiKey
            jLog["subgameid"] = self.mServiceOpt.sSubGameId
            jLog["tabid"] = table_log.nTableID
            jLog["roundid"] = table_log.sRoundID
            jLog["time"] = table_log.sTime
            detail_info = deepcopy(table_log.sDetailInfo)
            jLog["detail"] = detail_info
            del jLog["detail"]["p"]
            # 將json string空格全部拿掉以縮減寫入空間
            a = json.dumps([jLog]).replace(" ", "")
            # 但是日期時間不可以沒有空格
            b = a.find("-", a.find("-") + 1)
            c = a[:b + 2 + 1] + " " + a[b + 2 + 1:]
            d = c.find("-", c.find("-", c.find("-", c.find("-") + 1) + 1) + 1)
            e = c[:d + 2 + 1] + " " + c[d + 2 + 1:]
            parameters["game_data"] = e  # [{}]

            # 整理gs的game_table_log給ps的accounting的game_result
            # 只有roundid與p物件
            kLog = {}
            kLog["roundid"] = table_log.sRoundID
            kLog["p"] = table_log.sDetailInfo["p"]
            # 將json string空格全部拿掉以縮減寫入空間
            kLog_string = json.dumps([kLog]).replace(" ", "")
            parameters["game_result"] = kLog_string  # [{}]

            parameters["end_cent"] = table_log.sDetailInfo["p"][i]["gold"]
            parameters["bonus"] = 0
            parameters["gamble"] = 0
            parameters["game_module"] = 0
            parameters["game_end"] = 1
            parameters["test_account"] = 0

            if not table_log.sDetailInfo["p"][i]["bot"]:  # 真人玩家的遊戲紀錄
                account_base = UserRP.get_account_base(str(self.mUsers[i].mUserInfo.mUUID))
                multi_inf = rp.LibGrd.R.hget("multi@inf_" + host_api_key, account_base.sin_channel)
                multi_inf = json.loads(multi_inf)
                name = multi_inf["host_id"]
                parameters["host_id"] = name
                if account_base.sn:  # 若有auto_increment單號
                    parameters["sn"] = account_base.sn
                    self.mTableFrame.SlotGame("update_ps_db_accounting",
                                              parameters, multi_inf["db_id"])  # 現有紀錄更新
                    # 在玩家 betresult 之後清除 sn，否則會在下一次 bet 時影響到流程
                    # 不寫在 BetResult 是因為會太早清掉 sn 影響流程
                    account_base.sn = 0
                    UserRP.set_account_base(account_base)

                else:  # 若沒有auto_increment
                    self.mTableFrame.SlotGame("insert_ps_db_accounting",
                                              parameters, multi_inf["db_id"])  # 新增新紀錄
            else:  # 機器人的遊戲紀錄
                parameters["host_id"] = robot_host_id
                self.mTableFrame.SlotGame("insert_ps_db_accounting_robot",
                                          parameters,  robot_db_id)

    def AccountingJsonCut(self, klog_p):  # json瘦身 : 存取雲端不再需要key，以避免ps db資料溢位
        for key, values in klog_p.items():
            new_sce_array = []
            for values_sce in values["sce"]:
                new_sce = []
                new_sce.append(values_sce.get("mt"))  # 主事件編號
                new_sce.append(values_sce.get("st"))  # 副事件編號
                new_sce.append(values_sce.get("cl", []))  # 牌面序號
                new_sce.append(values_sce.get("sc"))  # 分數加減
                new_sce_array.append(new_sce)
            klog_p[key]["sce"] = new_sce_array
        return klog_p

    def GetLvFaceidFrame(self, player_rec, uuid, seat_index):  # 取得真人玩家或機器人的等級、頭像、頭框
        account_base = UserRP.get_account_base(uuid)  # 取得base
        if account_base:  # 真人玩家
            player_rec["lv"] = account_base.lv  # 等級
            player_rec["faceid"] = account_base.faceid  # 頭像
            player_rec["frame"] = account_base.frame  # 頭框
        else:  # 機器人
            # 取得商戶名稱
            host_name = UserRP.get_host_name(self.mServiceOpt.sHostApiKey)
            # 取得等級資訊
            android_info = UserRP.get_account_android(self.mServiceOpt.sSubGameId,
                                                      self.mTableFrame.TableID, seat_index, host_name)
            # 取得完就刪除
            UserRP.delete_account_android(self.mServiceOpt.sSubGameId, self.mTableFrame.TableID, seat_index, host_name)
            if android_info == None:
                player_rec["lv"] = 0  # 等級
                player_rec["faceid"] = 0  # 頭像
                player_rec["frame"] = 0  # 頭框
            else:
                player_rec["lv"] = android_info["MemberLv"]  # 等級
                player_rec["faceid"] = android_info["FaceID"]  # 頭像
                player_rec["frame"] = android_info["CurHeadFrame"]  # 頭框
        return player_rec

    def member_grade_transform(self, member_grade_overall):  # [ {0} , {1} , {2} , {3} ]
        # 取得所有等級所需的勝場數
        upgrade_needs_win = ServerMYP.upgrade_threshold_list
        overall_transform = []  # 桌內所有人的等級資訊
        lv = []  # 等級陣列(排名序)
        play_times = []  # 生涯遊玩次數陣列(排名序)
        all_win_times = []  # 生涯獲勝次數陣列(排名序)
        chair_id = []  # 座號(排名序)
        for i in range(len(member_grade_overall)):
            lv.append(member_grade_overall[i]["lv"])
            play_times.append(member_grade_overall[i]["play_times"])
            all_win_times.append(member_grade_overall[i]["all_win_times"])
            chair_id.append(member_grade_overall[i]["chair_id"])

        # [ [等級依排名序] , [遊玩數依排名序] , [勝場數依排名序] , [對應表] , [座號依排名序] ]
        overall_transform.append(lv)
        overall_transform.append(play_times)
        overall_transform.append(all_win_times)
        overall_transform.append(upgrade_needs_win)
        overall_transform.append(chair_id)
        return overall_transform

    def confirm_vip(self, tot):  # 確認vip自動化條件
        if tot > self.xPrivateCfg.nCellScore * self.mServiceOpt.sWinTimes:  # 如果有人贏分超過底注*設定倍率
            return True  # 整桌所有玩家變成vip
        return False  # 未達成

    def insert_vip(self, all_table_info):  # 整桌所有人加入vip名單
        for i, j in all_table_info.items():  # 走訪整桌的{名稱: [商戶代號, 遊戲代號, vip為0或1, uuid]}
            if i != None and j != None and len(j) >= 2:  # 如果內容結構完整(遊戲內有2~4人)
                if j[2] == 0:  # 如果此玩家不是vip
                    self.mTableFrame.WriteVipPlayer(i, j[0], j[1])  # 寫入VIP_player資料表
                    self.mTableFrame.WriteVipLog(i, j[0], j[1], GetServerTimeStr())  # 寫入vip_log資料表
                    # 寫入redis的vip
                    rp = RDSPGuard.RP("game")
                    account_base_ss = rp.LibGrd.R.hget("sha@data_" + str(j[3]), "base")
                    if account_base_ss is not None:
                        account_base = db_data_user()
                        account_base.ParseFromString(account_base_ss)
                        account_base.VIP = 1
                        account_buffer = account_base.SerializeToString()
                        rp.LibGrd.R.hset("sha@data_" + str(j[3]), "base", account_buffer)
                        # if int(self.mServiceOpt.sMultiHost) == 1:  # 如果是多代理商模式
                        #     # 公開發佈同步至單代理商的account_base
                        #     self.mTableFrame.Attemper.SyncBase(account_base.hostuuid, account_base, account_base.channel)

    # 是否大獎通知訊息：玩家10場內是否平均RTP達標[[-1, -1], [-1, -1], ..., [winamt, betamt]]
    def prize_notice(self, account_base, player_rec, tot_without_outtax):
        # 不管錢包類型，本局此玩家的winamt與betamt
        winamt = abs(player_rec["tot"] + tot_without_outtax) if tot_without_outtax > 0 else 0
        betamt = abs(tot_without_outtax)

        if not account_base.ten_amt:  # 如果最近10場沒有任何1場winamt與betamt紀錄
            ten_amt = [[-1, -1] for _ in range(10)]  # 產生[[-1, -1], [-1, -1], ..., [-1, -1]]結構
            ten_amt[-1] = [winamt, betamt]  # 最後一個位置取代最新的紀錄
            account_base.ten_amt = json.dumps(ten_amt)  # 將ten_amt以str儲存至base

        else:  # 有過去的winamt與betamt紀錄
            ten_amt = json.loads(account_base.ten_amt)
            del ten_amt[0]  # 為了寫新的紀錄，第一個位置為時間最近的第11筆紀錄，必須刪除
            ten_amt.append([winamt, betamt])  # 最後一個位置寫入最新的紀錄
            account_base.ten_amt = json.dumps(ten_amt)  # 將ten_amt以str儲存至base

            if ten_amt[0][0] != -1 or ten_amt[0][1] != -1:  # 若累計遊玩滿10次
                # 計算10場的RTP與RTP差值
                winamt_list = []  # 10場winamt
                betamt_list = []  # 10場betamt
                for i in ten_amt:
                    winamt_list.append(i[0])
                    betamt_list.append(i[1])

                # if int(self.mServiceOpt.sMultiHost) == 1:  # 如果是多代理商模式
                #     single_uuid = account_base.hostuuid  # uuid單多有別
                #     multi_uuid = account_base.uuid
                # else:  # 如果是單代理商模式
                single_uuid = account_base.uuid  # uuid一樣
                multi_uuid = account_base.uuid

                # 若10場RTP大於120%
                rtp = (numpy.sum(winamt_list) / numpy.sum(betamt_list)) if numpy.sum(
                    betamt_list) != 0 else 0
                # 或10場netwin大於2萬
                netwin = numpy.sum(winamt_list) - numpy.sum(betamt_list)
                # 準備telegram bot通知的路徑
                telegram_urls = self.mTableFrame.mAttemper.App.mConfigs["telegram_urls"]
                if rtp > 1.5 and netwin > 2000000:  # 兩者皆是
                    telegram_params = {"title": "{}".format(account_base.game_id),
                                       "message": "{} ({} , {}) , {} and {} are out of standard".format(
                                           account_base.nickname, single_uuid,
                                           multi_uuid, "RTP" + " " + str(int(rtp * 100)) + "%",
                                           "NETWIN" + " " + str(netwin)
                                       ),
                                       "token": self.mTableFrame.mAttemper.App.mConfigs["telegram_token"]}
                    RequestHelper.DoPost(telegram_urls + "/", telegram_params)
                elif rtp > 1.5:  # 10場RTP大於120%
                    telegram_params = {"title": "{}".format(account_base.game_id),
                                       "message": "{} ({} , {}) , {} is out of standard".format(
                                           account_base.nickname, single_uuid,
                                           multi_uuid, "RTP" + " " + str(int(rtp * 100)) + "%"
                                       ),
                                       "token": self.mTableFrame.mAttemper.App.mConfigs["telegram_token"]}
                    RequestHelper.DoPost(telegram_urls + "/", telegram_params)
                elif netwin > 2000000:  # 10場netwin大於2萬
                    telegram_params = {"title": "{}".format(account_base.game_id),
                                       "message": "{} ({} , {}) , {} is out of standard".format(
                                           account_base.nickname, single_uuid,
                                           multi_uuid, "NETWIN" + " " + str(netwin)
                                       ),
                                       "token": self.mTableFrame.mAttemper.App.mConfigs["telegram_token"]}
                    RequestHelper.DoPost(telegram_urls + "/", telegram_params)

        rp = RDSPGuard.RP("game")
        uuid = account_base.uuid  # 遊戲內game server的uuid
        account_buffer = account_base.SerializeToString()
        rp.LibGrd.R.hset("sha@data_" + str(uuid), "base", account_buffer)  # 儲存，離開遊戲會自動同步至單代理商

    def BetResult(self, account_base, account_res, host_url, player_rec, seat_index, tot_without_outtax):
        try:
            rp = RDSPGuard.RP("game")
            multi_inf = rp.LibGrd.R.hget("multi@inf_" + account_base.channel, account_base.sin_channel)
            multi_inf = json.loads(multi_inf)
            host_url = multi_inf["host_url"]
            txn_id = account_base.txn_id
            dl_url = host_url["base_url"] + "/" + host_url["result"]
            err_msg = ", total_win: " + str(player_rec["gold"]) + ", memberid: " + str(account_base.sdk_uuid)
            data = {"txn": txn_id, "host": account_base.sin_channel, "type": 2, "action": 2,
                    "err_code": 1, "err_descr": "response error" + err_msg, "time": GetServerTimeStr()}
            self.mTableFrame.TradeLog("add_hosterrlog", data, account_base.channel)
            # 計算winamt：獲勝且沒有抽水的tot + 獲勝且抽過水的tot，如果輸了，則統一為0
            winamt = abs(player_rec["tot"] + tot_without_outtax) if tot_without_outtax > 0 else 0
            Log("玩家{}商戶{}暱稱{}的winamt是{}".format(account_base.uuid, account_base.channel, account_base.nickname, winamt))
            # 計算betamt：沒有抽水的tot的絕對值
            betamt = abs(tot_without_outtax)  # tot有可能為輸分負值
            Log("玩家{}商戶{}暱稱{}的betamt是{}".format(account_base.uuid, account_base.channel, account_base.nickname, betamt))
            response = RequestHelper.DoGet(dl_url, {"access_token": account_res[4].decode(), "txn_id": account_base.sn,
                                                    "total_win": player_rec["gold"], "bonus_win": 0,
                                                    "game_id": account_base.game_id, "subgame_id": self.mServiceOpt.sSubGameId,
                                                    "ts": int(time.time()), "winamt": winamt, "betamt": betamt})
            self.mTableFrame.TradeLog("delete_hosterrlog", data, account_base.channel)
            if response == None:
                # 沒回應，先從sha@chl抓取retry_times重複請求次數
                rp_re = RDSPGuard.RP("game")
                retry_times = rp_re.LibGrd.R.hget("sha@chl_" + self.mServiceOpt.sHostApiKey, "retry_times")
                # 序列化，若無法序列化則預設重複請求3次
                retry_times = int(retry_times.decode()) if retry_times else 3
                # 然後根據retry_times次數重複請求共享result，每次timeout為60秒，直到成功為止
                response2 = {}
                for _ in range(retry_times):
                    response2 = RequestHelper.DoGet(dl_url, {"access_token": account_res[4].decode(), "txn_id": account_base.sn,
                                                            "total_win": player_rec["gold"], "bonus_win": 0,
                                                            "game_id": account_base.game_id,
                                                            "subgame_id": self.mServiceOpt.sSubGameId,
                                                            "ts": int(time.time()), "winamt": winamt, "betamt": betamt})
                    if response2 and response2["status_code"] == 0:
                        break  # 只要成功一次就離開
                # 若走訪數次仍未果
                if not response2 or response2["status_code"] != 0:
                    # 準備共享result錯誤資訊存入資料表
                    share_result_data = {"txn_id": txn_id, "uuid": account_base.uuid,
                                         "member_id": str(account_base.sdk_uuid),
                                         "host_api_key": account_base.sin_channel,
                                         "gold": player_rec["gold"], "winamt": winamt, "betamt": betamt,
                                         "game_id": account_base.game_id, "subgame_id": self.mServiceOpt.sSubGameId,
                                         "status_code": -100 if not response2 else response2["status_code"],
                                         "date": GetServerTimeStr()}
                    # 寫入game_result_error_log資料表
                    self.mTableFrame.TradeLog("insert_share_result_error", share_result_data, account_base.channel)

                    err_msg = ", memberid: " + str(account_base.sdk_uuid) + ", total_win: " + str(player_rec["gold"])
                    data = {"txn": txn_id, "host": account_base.sin_channel, "type": 2, "action": 2,
                            "err_code": 4,
                            "err_descr": "results == None, " + err_msg,
                            "time": GetServerTimeStr()}
                    self.mTableFrame.TradeLog("add_hosterrlog", data, account_base.channel)
                    Warn("--- BetResult Game to PS Failed member_id=", self.mUsers[seat_index].mUserInfo.mSdkUUID, " score=", player_rec["gold"], " - ", player_rec["gold"], " response=None")

            elif response["status_code"] != 0:
                # 有回應，但回應不是正常訊號，準備共享result錯誤資訊存入資料表
                share_result_data = {"txn_id": txn_id, "uuid": account_base.uuid,
                                     "member_id": str(account_base.sdk_uuid),
                                     "host_api_key": account_base.sin_channel,
                                     "gold": player_rec["gold"], "winamt": winamt, "betamt": betamt,
                                     "game_id": account_base.game_id, "subgame_id": self.mServiceOpt.sSubGameId,
                                     "status_code": response["status_code"], "date": GetServerTimeStr()}
                # 寫入game_result_error_log資料表
                self.mTableFrame.TradeLog("insert_share_result_error", share_result_data, account_base.channel)

                err_msg = ", memberid: " + str(account_base.sdk_uuid) + ", total_win: " + str(player_rec["gold"])
                data = {"txn": txn_id, "host": account_base.sin_channel, "type": 2, "action": 2,
                        "err_code": 4,
                        "err_descr": "response_status_code: " + str(response["status_code"]) + err_msg,
                        "time": GetServerTimeStr()}
                self.mTableFrame.TradeLog("add_hosterrlog", data, account_base.channel)
                Warn("--- BetResult Game to PS Failed member_id=", self.mUsers[seat_index].mUserInfo.mSdkUUID, " score=", player_rec["gold"], " - ", player_rec["gold"], " status_code=", response["status_code"])

            else:
                Warn("--- BetResult Game to PS member_id=", self.mUsers[seat_index].mUserInfo.mSdkUUID, " score=", player_rec["gold"], " - ", player_rec["gold"])

            account_base.score = 0
            data = {"txn": txn_id, "host": account_base.sin_channel, "type": 2, "memberid": account_base.sdk_uuid,
                    "amount": player_rec["gold"], "time": GetServerTimeStr()}
            self.mTableFrame.TradeLog("add_sharingtradelog", data, account_base.channel)
            account_base.txn_id = "0"
            account_buffer = account_base.SerializeToString()
            rp.LibGrd.Call("common.SetInfoBySYS", *(self.mUsers[seat_index].mUserInfo.mUUID, account_buffer))
        except:
            PrintEXC()

    def SyncScene(self, chair_id = INVALID_CHAIR):
        send_msg = msg_scene_sync()
        send_msg.cell_score = self.xPrivateCfg.nCellScore
        if self.strRoundSign is not None:
            send_msg.round_sign = self.strRoundSign.encode()
        send_msg.out_tax = self.xPrivateCfg.nOutTax
        for idx in range(len(self.xPrivateCfg.vPeriodTime)):
            if idx != e_gameperiod_finish:
                send_msg.period_times.append(self.xPrivateCfg.vPeriodTime[idx])
            else:
                send_msg.period_times.append(ServiceAttr.sWaitStartTime)
        self.mTableFrame.SendData(e_msgid_dummy, cg_msgid_scene_sync, send_msg, chair_id)

    # 確認是否達到水球極限，是否遊戲中播出任務達成動畫
    def _check_point_limit(self, uuid):
        rp = RDSPGuard.RP("game")
        date_redis = rp.LibGrd.R.hget("sha@chl_" + self.mServiceOpt.sHostApiKey, "date")
        if date_redis == None:
            return 1  # 未設定活動時程，動畫不播

        date_redis = json.loads(date_redis.decode())  # 反序列化與解析
        songkran_start = date_redis["songkran_start"]  # 取得活動起始日
        songkran_end = date_redis["songkran_end"]  # 取得潑水節活動結束日
        if songkran_start > int(time.time()) or songkran_end < int(time.time()):
            return 1  # 超出活動時程，動畫不播

        event = EventRP.get_event_data(uuid)
        if "daily_point" in event and "total_point" in event:
            if event["daily_point"] >= EventRP.point_limit:
                return 1  # 水球已達上限，動畫不播
            if event["total_point"] >= EventRP.total_point_limit:
                return 1  # 水球已達上限，動畫不播

        return 0  # 水球未達上限，動畫要播

    # 新增輸入破產玩家列表、以小博大玩家列表、座號排序列表
    def SyncPeriod(self, chair_id, send_msg=None, is_reconn=True, bankruptcy_player_list=None,
                   leverage_player_list=None, final_rank=None, member_grade_overall=None,
                   auto_operate=0):
        """

        Args:
            auto_operate (int): 該名玩家最後是否由系統操作
        """
        if chair_id not in self.mUsers:
            return
        ignore_send = True
        if send_msg is None:
            ignore_send = False
            send_msg = msg_period_sync()

        # 如果遊戲結束了
        if self.xLogic.IsFinished:
            # 在msg_period_sync()這一層的protocol buffers新增破產玩家資訊
            if bankruptcy_player_list != [] and bankruptcy_player_list != None:
                send_msg.bankruptcy_player.extend(bankruptcy_player_list)
            # 在msg_period_sync()這一層的protocol buffers新增以小博大玩家資訊
            if leverage_player_list != [] and leverage_player_list != None:
                send_msg.leverage_player.extend(leverage_player_list)
            # 在msg_period_sync()這一層的protocol buffers新增座號排序資訊
            if final_rank != [] and final_rank != None:
                send_msg.final_rank.extend(final_rank)
            # 在msg_period_sync()這一層的protocol buffers新增玩家同桌玩了多少局
            if self.mTableFrame.continue_game_count != None:
                send_msg.continue_game_count = self.mTableFrame.continue_game_count

            send_msg.auto_operate = auto_operate

        send_msg.period = self.nPeriod

        dtime = 0
        curTime = GetServerTime()
        if self.nPeriodEndTime > curTime:
            dtime = self.nPeriodEndTime - curTime
        send_msg.period_end_time = int(dtime)

        # 其他玩家(非發起者)接受比牌的剩餘思考時間
        if self.xLogic.is_fight:  # 如果場上是比牌狀態
            send_msg.challenge_end_time = self.challenge_end_time - curTime \
                if self.challenge_end_time - curTime > 0 else 0

        if self.nPeriod == EnumGamePeriod.nAction:
            send_msg.op_chair_id = self.xLogic.CurrentTurn

        if self.nPeriod != EnumGamePeriod.nIdle:
            send_msg.deck_remain = len(self.xLogic.Deck)
            for card_index in self.xLogic.SeaBottom:
                send_msg.sea_bottom.append(card_index)

            for player_info in self.xLogic.Players.values():
                if not player_info.IsJoined:
                    continue
                msg_player = send_msg.players.add()
                msg_player.chair_id = player_info.SeatIndex

                # 組牌1成功與0失敗
                msg_player.can_group = 0 if self.xLogic.is_fight else 1
                # 目前是否有特殊組合
                msg_player.secret_melds = 1 if player_info.has_special_combine() else 0
                # 玩家是否允許比牌操作
                msg_player.op_allow_fight = player_info.op_allow_fight
                # 玩家的比牌點數
                msg_player.compare_point = player_info.compare_point
                # 玩家的組牌區有什麼牌[{},{}] → [[],[]]
                for group in player_info.group_combination:  # 走訪玩家組牌區取得每個組合
                    for i in group:  # 走訪每個組合取得單張牌index
                        msg_player.group_cards.append(i)  # [49, 50, 51, 52, 19, 20, 21]
                    msg_player.group_length.append(len(group))  # [4, 3]

                # 取得玩家的event
                uuid = self.mUsers[player_info.SeatIndex].mUserInfo.mUUID
                msg_player.animation_activity = self._check_point_limit(uuid)

                if player_info.SeatIndex == chair_id or self.nPeriod == EnumGamePeriod.nFinish:
                    for card_index in player_info.InHand:
                        msg_player.cards.append(card_index)
                else:
                    msg_player.cards.append(len(player_info.InHand))
                for combo_index, combo in player_info.Combos.items():
                    msg_combo = msg_player.combos.add()
                    msg_combo.combo_index = combo_index
                    msg_combo.unique_index = self.xLogic.GetComboUniqueIndex(player_info.SeatIndex, combo_index)
                    for card_index in combo:
                        msg_combo.cards.append(card_index)

                msg_player.gained = player_info.GainedScore
                msg_player.lost = player_info.LostScore
                msg_player.is_opened = player_info.IsOpened

                # 在msg_period_sync()的player這一層的protocol buffers新增...
                if member_grade_overall != None:
                    # [ [等級依排名序] , [遊玩數依排名序] , [勝場數依排名序] , [對應表] , [座號依排名序] ]
                    # 利用排名順位，取出[4]群組裡的座號所屬的索引別
                    # 新增整桌等級(座號序)
                    msg_player.MemberLv = member_grade_overall[0][member_grade_overall[4].index(msg_player.chair_id)]
                    # 新增整桌生涯遊玩次數(座號序)
                    msg_player.play_times = member_grade_overall[1][member_grade_overall[4].index(msg_player.chair_id)]
                    # 新增整桌生涯勝場數(座號序)
                    msg_player.all_win_times = member_grade_overall[2][member_grade_overall[4].index(msg_player.chair_id)]
                    # 新增等級勝場對應表(等級低至高1~80)
                    msg_player.upgrade_needs_win.extend(member_grade_overall[3])

                # 若座號與輪到回合的人一致
                if self.xLogic.CurrentTurn == player_info.SeatIndex:
                    msg_player.op_allow = player_info.OpAllow  # 只有輪到回合的人允許操作

                # if player_info.NotOpenCanDummy != None:  # 如果未開張一次清空有內容，達成條件
                #     # 如果[出牌]2維陣列有東西
                #     if player_info.NotOpenCanDummy[1] != []:
                #         temp = None
                #         temp2 = None
                #         temp3 = None
                #         # 分別塞入出牌的3包臨時的陣列
                #         for i in range(len(player_info.NotOpenCanDummy[1])):
                #             if temp == None:
                #                 temp = player_info.NotOpenCanDummy[1][i]
                #             elif temp2 == None:
                #                 temp2 = player_info.NotOpenCanDummy[1][i]
                #             elif temp3 == None:
                #                 temp3 = player_info.NotOpenCanDummy[1][i]
                #         # 3包各別有東西才塞入proto，否則視為空
                #         if temp != None:
                #             msg_player.not_open_can_combine1.extend(temp)
                #         if temp2 != None:
                #             msg_player.not_open_can_combine2.extend(temp2)
                #         if temp3 != None:
                #             msg_player.not_open_can_combine3.extend(temp3)
                #     # 如果[插牌]1維陣列有東西
                #     if player_info.NotOpenCanDummy[2] != []:
                #         msg_player.not_open_can_insert.extend(player_info.NotOpenCanDummy[2])
                #     # 如果[棄牌]1維陣列有東西
                #     if player_info.NotOpenCanDummy[3] != []:
                #         msg_player.not_open_can_drop.extend(player_info.NotOpenCanDummy[3])
            if is_reconn:  # 斷線重新進入房間與桌子
                dt_info = send_msg.dt_info
                sea_bottom = self.xLogic.SeaBottom

                for card_info in sea_bottom.values():
                    cinfo = dt_info.cardinfos.add()
                    if card_info.Owner is not None:
                        cinfo.owner = card_info.Owner.SeatIndex
                    else:
                        cinfo.owner = -1
                    drop_order = card_info.DropOrder
                    if len(drop_order) > 1:
                        last_drop_info = drop_order[-1]
                        cinfo.dropper = last_drop_info[0].SeatIndex
                    else:
                        cinfo.dropper = -1
                    cinfo.card_index = card_info.Poker.Index

                all_combos = self.xLogic.AllCombos
                for combo in all_combos.values():
                    for card_info in combo.values():
                        cinfo = dt_info.cardinfos.add()
                        cinfo.owner = card_info.FinalOwner.SeatIndex
                        drop_order = card_info.DropOrder
                        if len(drop_order) > 1:
                            last_drop_info = drop_order[-1]
                            cinfo.dropper = last_drop_info[0].SeatIndex
                        else:
                            cinfo.dropper = -1
                        cinfo.card_index = card_info.Poker.Index

        if not ignore_send:
            self.mTableFrame.SendData(e_msgid_dummy, cg_msgid_period_sync, send_msg, chair_id)
    # 新增輸入破產玩家列表、以小博大玩家列表、座號排序列表
    def NotifyPlayerOperation(self, chair_id, op_type, params, bankruptcy_player_list=None, leverage_player_list=None,
                              final_rank=None, member_grade_overall=None,
                              auto_operate_dc={}):
        send_msg = msg_op_notify()
        send_msg.chair_id = chair_id
        send_msg.op_type = op_type

        if op_type == 8192:  # EnumGameOperation.GroupReorganize
            for i in params:  # 2D to 1D list
                for j in i:
                    send_msg.params.append(j)
                send_msg.params.append(99)
        else:  # 其他訊號
            for v in params:  # 1D list
                send_msg.params.append(v)

        rec_map = self.xLogic.GetRecords()
        for seat_index in rec_map:
            for rec_info in rec_map[seat_index]:
                main_type = rec_info[0]
                ev = send_msg.events.add()
                ev.chair_id = seat_index
                ev.main_type = main_type
                if main_type == EnumScoreBaseType.nNormal:
                    ev.sub_type = rec_info[1]
                    ev.score = rec_info[3]
                elif main_type == EnumScoreBaseType.nSpecial:
                    ev.sub_type = rec_info[1]
                    ev.score = rec_info[2]
                elif main_type == EnumScoreBaseType.nFinish:
                    ev.score = rec_info[2]

        for tmp_chair_id, player_info in self.xLogic.Players.items():
            if not player_info.IsJoined:
                continue
            tmp_send_msg = msg_op_notify()
            tmp_send_msg.CopyFrom(send_msg)

            auto_operate = auto_operate_dc.get(str(tmp_chair_id), 0)
            # 新增輸入破產玩家列表、以小博大玩家列表、座號排序列表
            self.SyncPeriod(tmp_chair_id, tmp_send_msg.data, bankruptcy_player_list=bankruptcy_player_list,
                            leverage_player_list=leverage_player_list, final_rank=final_rank,
                            member_grade_overall=member_grade_overall, auto_operate=auto_operate)
            self.mTableFrame.SendData(e_msgid_dummy, cg_msgid_op_notify, tmp_send_msg, tmp_chair_id)

    def SyncAllScoreEvents(self, chair_id):
        send_msg = msg_score_event()
        for player_info in self.xLogic.Players.values():
            if not player_info.IsJoined:
                continue
            seat_index = player_info.SeatIndex
            for rec_info in player_info.ScoreRecords:
                main_type = rec_info[0]
                ev = send_msg.events.add()
                ev.chair_id = seat_index
                ev.main_type = main_type
                if main_type == EnumScoreBaseType.nNormal:
                    ev.sub_type = rec_info[1]
                    ev.score = rec_info[3]
                elif main_type == EnumScoreBaseType.nSpecial:
                    ev.sub_type = rec_info[1]
                    ev.score = rec_info[2]
                elif main_type == EnumScoreBaseType.nFinish:
                    ev.score = rec_info[2]
        self.mTableFrame.SendData(e_msgid_dummy, cg_msgid_score_event, send_msg, chair_id)

    def CanBotAction(self):
        return self.nPeriod == EnumGamePeriod.nAction
