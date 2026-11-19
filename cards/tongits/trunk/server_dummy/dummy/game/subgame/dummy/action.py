# 机器人动作
from definations import *
from subgame.dummy.gamelogic import *
import android

class eActionResult(object):
    RUNNING = 0     #运行中
    FINISHED = 1    #完成

class eActionIDs(object):
    eDRAW = 1  # 摸牌
    ePICK = 2  # 捡牌
    eCOMBINE = 3  # 出牌
    eINSERT = 4  # 插牌
    eDROP = 5  # 弃牌
    Group = 6  # 組牌
    UnGroup = 7  # 解散組牌
    Fight = 8  # 發起比牌
    Challenge = 9  # 接受比牌
    Fold = 10  # 放棄比牌

class Action(object):
    def __init__(self):
        self.mOp = -1    #阶段
        self.mThinkEndTime = -1     #思考结束时间

    @property
    def Op(self):
        return self.mOp

    @property
    def ThinkEndTime(self):
        return self.mThinkEndTime

    def AddThinkTime(self, op, time, desc=">>>思考......"):
        self.mOp = op
        self.mThinkEndTime = time
        Info(desc)
    # 抽牌階段思考時間
    def GetDrawThinkTime(self):
        return GetServerTime() + GetRndInt(5, 7)
    # 撿牌階段思考時間
    def GetPickThinkTime(self):
        return GetServerTime() + GetRndInt(6, 7)
    # 出牌階段思考時間
    def GetCombineThinkTime(self):
        return GetServerTime() + GetRndInt(4, 5)
    # 插牌階段思考時間
    def GetInsertThinkTime(self):
        return GetServerTime() + GetRndInt(3, 4)
    # 棄牌階段思考時間
    def GetDropThinkTime(self):
        return GetServerTime() + GetRndInt(3, 4)
    # 機器人組牌、解散組牌、發起比牌、接受比牌、放棄比牌階段思考時間
    def GetCompareThinkTime(self):
        return GetServerTime() + 1

    def IsThinkEnd(self):
        return self.ThinkEndTime <= GetServerTime()

    def OnRun(self, mRunParams):
        return eActionResult.FINISHED

class ComboAction(object):
    def __init__(self):
        self.mIdx = 0
        self.mActions = []

    def OnRun(self, mRunParams):
        for idx in range(self.mIdx, len(self.mActions)):
            if self.mActions[idx].OnRun(mRunParams) == eActionResult.RUNNING:
                return eActionResult.RUNNING
            self.mIdx += 1
        return eActionResult.FINISHED

#抽牌
class DrawAction(Action):
    def OnRun(self, mRunParams):
        if mRunParams.mAndroidSink is None:
            return eActionResult.FINISHED
        sMePlayer = mRunParams.mAndroidSink.xLogic.Players[mRunParams.mAndroidSink.wMeChairID]
        if self.Op != eActionIDs.eDRAW:
            if sMePlayer.IsOpAllowed(EnumGameOperation.nDraw):
                self.AddThinkTime(eActionIDs.eDRAW, self.GetDrawThinkTime(), ">>>思考? 等待抽牌......")
        if self.Op == eActionIDs.eDRAW:
            if not self.IsThinkEnd():
                return eActionResult.RUNNING
            if mRunParams.nDrawIdx > 0:
                Log(">>> 自定义 抽牌")
                mRunParams.mAndroidSink.Operation(EnumGameOperation.nDraw, [mRunParams.nDrawIdx])
            else:
                Log(">>> 机器人，抽牌")
                vDrawIdx = []
                is_lucky_draw = GetRndInt(1, 100) <= ServiceOpt.sRobotDrawRate
                is_vip_lucky_draw = GetRndInt(1, 100) <= ServiceOpt.sRobotDrawRateVip
                # 如果機器人抽到幸運值，或vip房內機器人抽中vip幸運值
                if is_lucky_draw or (android.android_vip == True and is_vip_lucky_draw) or True:
                    # 開啟作弊抽牌規則
                    Log("幸運機率{}, vip幸運機率{}, 機器人座號{}抽中幸運值".format(
                        ServiceOpt.sRobotDrawRate, ServiceOpt.sRobotDrawRateVip, sMePlayer.nSeatIndex))
                    vRelates = mRunParams.mAndroidSink.GetDeckRelateOrIns()
                    if len(vRelates) > 0:
                        nDraw = vRelates[GetRndInt(0, len(vRelates)-1)]
                        vDrawIdx.append(nDraw)
                mRunParams.mAndroidSink.Operation(EnumGameOperation.nDraw, vDrawIdx)
        return eActionResult.FINISHED

#捡牌
class PickAction(Action):
    def OnRun(self, mRunParams):
        if mRunParams.mAndroidSink is None:
            return eActionResult.FINISHED
        sMePlayer = mRunParams.mAndroidSink.xLogic.Players[mRunParams.mAndroidSink.wMeChairID]
        if self.Op != eActionIDs.ePICK:
            if sMePlayer.IsOpAllowed(EnumGameOperation.nPick):
                self.AddThinkTime(eActionIDs.ePICK, self.GetPickThinkTime(), ">>>思考? 等待捡牌......")
        if self.Op == eActionIDs.ePICK:
            if not self.IsThinkEnd():
                return eActionResult.RUNNING
            if mRunParams.mPickCombo is not None and len(mRunParams.mPickCombo) > 0:
                Log(">>> 固定捡牌")
                combo = mRunParams.mPickCombo
                vpickcombo = list(combo[2].keys())
                if len(vpickcombo) > 5:
                    while len(vpickcombo) > 5:
                        if vpickcombo[-1] != combo[1]:
                            vpickcombo.pop(-1)
                    while len(vpickcombo) > 5:
                        if vpickcombo[0] != combo[1]:
                            vpickcombo.pop(0)
                mRunParams.mAndroidSink.Operation(EnumGameOperation.nPick, [combo[0]] + vpickcombo)
                #mRunParams.mAndroidSink.Operation(EnumGameOperation.nPick, [combo[0]] + list(combo[2].keys()))
            else:
                Log(">>> 随机捡牌")
                xLogic = mRunParams.mAndroidSink.xLogic
                vNfCombos = mRunParams.mAndroidSink.GetCanPickCombos()
                if len(vNfCombos) > 0:
                    combo = vNfCombos[0]
                    vpickcombo = list(combo[2].keys())
                    if len(vpickcombo) > 5:
                        while len(vpickcombo) > 5:
                            if vpickcombo[-1] != combo[1]:
                                vpickcombo.pop(-1)
                            else:
                                vpickcombo.pop(0)
                        while len(vpickcombo) > 5:
                            if vpickcombo[0] != combo[1]:
                                vpickcombo.pop(0)
                            else:
                                vpickcombo.pop(-1)
                    mRunParams.mAndroidSink.Operation(EnumGameOperation.nPick, [combo[0]] + vpickcombo)
        return eActionResult.FINISHED

#出牌
class CombineAction(Action):
    def OnRun(self, mRunParams):
        if mRunParams.mAndroidSink is None:
            return eActionResult.FINISHED
        sMePlayer = mRunParams.mAndroidSink.xLogic.Players[mRunParams.mAndroidSink.wMeChairID]
        if self.Op != eActionIDs.eCOMBINE:
            if sMePlayer.IsOpAllowed(EnumGameOperation.nCombine):
                self.AddThinkTime(eActionIDs.eCOMBINE, self.GetCombineThinkTime(), ">>>思考? 等待出牌......")
                return eActionResult.RUNNING
        if self.Op == eActionIDs.eCOMBINE:
            if not self.IsThinkEnd():
                return eActionResult.RUNNING
            # 看起來這個條件不會執行到
            if mRunParams.vCombines is not None and len(mRunParams.vCombines) > 0:
                Log(">>> 固定出牌")
                for combo in mRunParams.vCombines:
                    # 驗證數量是否 > 5 → 不合理出牌
                    if len(combo) > LogicConfig.nMaxContinuity:
                        while len(combo) > LogicConfig.nMaxContinuity:
                            lst = list(combo.keys()).pop(-1)
                            combo.pop(lst)

                    # 比對list(combo.keys())是否為list(sMePlayer.mInHand.keys())的子集
                    # 並驗證出牌是否有3張以上
                    if set(list(combo.keys())) < set(list(sMePlayer.mInHand.keys())) \
                            and len(list(combo.keys())) >= LogicConfig.nMinContinuity:
                        # 出牌
                        mRunParams.mAndroidSink.Operation(EnumGameOperation.nCombine, list(combo.keys()))
                        mRunParams.vCombines.remove(combo)
                        break

                    if len(mRunParams.vCombines) > 0:
                        self.AddThinkTime(eActionIDs.eCOMBINE, self.GetCombineThinkTime(), ">>>思考? 等待出牌......")
                        return eActionResult.RUNNING
                    break
            else:
                Log(">>> 随机出牌")
                if mRunParams.mAndroidSink.WhetherCombineOrPass():
                    one_list = []  # 全部為1的陣列
                    combos = []
                    combo = {}
    
                    # # 如果未開張一次清空不成立→取得所有出牌可能
                    # if mRunParams.mAndroidSink.AndroidNotOpenCanDummy() == None:
    
                    sMeSerial = CardSerializer()
                    sMeSerial.AddBatch(list(sMePlayer.mInHand.keys()))
                    combos = sMeSerial.GetAllCombo()
                    if sMePlayer.bIsOpened :
                        combo = mRunParams.mAndroidSink.CombosHasStraightBroken(combos)
                    else:
                        combo = mRunParams.mAndroidSink.CombosPointMin(combos)
                    Log("是否開張:{},combo:{}".format(sMePlayer.bIsOpened, combo))
    
                    # else:  # 如果未開張一次清空成立→指定出牌組合
                    #     for android_combo in mRunParams.mAndroidSink.AndroidNotOpenCanDummy()[1]:
                    #         for i in range(len(android_combo)):
                    #             one_list.append(1)
                    #         combos.append(dict(zip(android_combo, one_list)))
                    if len(combo) == 0:
                        return eActionResult.FINISHED
                    mRunParams.mAndroidSink.Operation(EnumGameOperation.nCombine, list(combo.keys()))

                    
                    
                    #for combo in combos:  # 走訪所有出牌組合
                    #    # 驗證數量是否 > 5 → 不合理出牌
                    #    if len(combo) > LogicConfig.nMaxContinuity:
                    #        while len(combo) > LogicConfig.nMaxContinuity:
                    #            lst = list(combo.keys()).pop(-1)
                    #            combo.pop(lst)
                    #    # if len(combo) == len(sMePlayer.mInHand):
                    #    #     lst = list(combo.keys()).pop(-1)
                    #    #     combo.pop(lst)
                    #
                    #    # 比對list(combo.keys())是否為list(sMePlayer.mInHand.keys())的子集
                    #    # 並驗證出牌是否有3張以上
                    #    if set(list(combo.keys())) <= set(list(sMePlayer.mInHand.keys())) \
                    #            and len(list(combo.keys())) >= LogicConfig.nMinContinuity:
                    #        # 出牌
                    #        mRunParams.mAndroidSink.Operation(EnumGameOperation.nCombine, list(combo.keys()))
                    #        break
                        
                    if sMePlayer.IsOpAllowed(EnumGameOperation.nCombine):
                        self.AddThinkTime(eActionIDs.eCOMBINE, self.GetCombineThinkTime(), ">>>思考? 等待出牌......")
                        return eActionResult.RUNNING
        return eActionResult.FINISHED

#插牌
class InsertAction(Action):
    def OnRun(self, mRunParams):
        if mRunParams.mAndroidSink is None:
            return eActionResult.FINISHED
        sMePlayer = mRunParams.mAndroidSink.xLogic.Players[mRunParams.mAndroidSink.wMeChairID]
        if self.Op != eActionIDs.eINSERT:
            if sMePlayer.IsOpAllowed(EnumGameOperation.nInsert):
                self.AddThinkTime(eActionIDs.eINSERT, self.GetInsertThinkTime(), ">>>思考? 等待插牌......")
                return eActionResult.RUNNING
        if self.Op == eActionIDs.eINSERT:
            if not self.IsThinkEnd():
                return eActionResult.RUNNING
            if mRunParams.vInsertIdxs is not None and len(mRunParams.vInsertIdxs) > 0:
                Log(">>> 自定义 插牌")
                serial = CardSerializer()

                for unq_index, combo in mRunParams.mAndroidSink.xLogic.mAllCombos.items():
                    matchedidx = -1
                    for idx in mRunParams.vInsertIdxs:
                        cindexlist = list(combo.keys())
                        cindexlist.append(idx)
                        serial.Clear()
                        serial.AddBatch(cindexlist)
                        if serial.HasFullMatch(cindexlist):
                            matchedidx = idx
                            mRunParams.mAndroidSink.Operation(EnumGameOperation.nInsert, [idx, unq_index])
                            break

                    if matchedidx != -1:
                        mRunParams.vInsertIdxs.remove(matchedidx)
                        break

                if len(mRunParams.vInsertIdxs) > 0:
                    self.AddThinkTime(eActionIDs.eINSERT, self.GetInsertThinkTime(), ">>>思考? 等待插牌......")
                    return eActionResult.RUNNING
            else:
                Log(">>> 随机 插牌")
                serial = CardSerializer()
                for unq_index, combo in mRunParams.mAndroidSink.xLogic.mAllCombos.items():
                    matched = False 
                    for cindex in mRunParams.mAndroidSink.get_hand_index_ls(sMePlayer): # 排除已經成為組牌區的牌
                        cindexlist = list(combo.keys())
                        cindexlist.append(cindex)
                        serial.Clear()
                        serial.AddBatch(cindexlist)
                        if serial.HasFullMatch(cindexlist):
                            matched = True
                            mRunParams.mAndroidSink.Operation(EnumGameOperation.nInsert, [cindex, unq_index])
                            break

                    if not matched:
                        return eActionResult.FINISHED

                if sMePlayer.IsOpAllowed(EnumGameOperation.nInsert):
                    self.AddThinkTime(eActionIDs.eINSERT, self.GetInsertThinkTime(), ">>>思考? 等待插牌......")
                    return eActionResult.RUNNING
        return eActionResult.FINISHED

#弃牌(26~30)
class DropAction(Action):
    def OnRun(self, mRunParams):
        if mRunParams.mAndroidSink is None:
            return eActionResult.FINISHED
        sMePlayer = mRunParams.mAndroidSink.xLogic.Players[mRunParams.mAndroidSink.wMeChairID]
        if self.Op != eActionIDs.eDROP:
            if sMePlayer.IsOpAllowed(EnumGameOperation.nDrop):
                self.AddThinkTime(eActionIDs.eDROP, self.GetDropThinkTime(), ">>>思考? 等待弃牌......")
                return eActionResult.RUNNING
        if self.Op == eActionIDs.eDROP:
            if not self.IsThinkEnd():
                return eActionResult.RUNNING
            Info(">>> 弃牌->弃差的牌")
            mDropIdxs = mRunParams.vDropIdxs if len(mRunParams.vDropIdxs) > 0 \
                else mRunParams.mAndroidSink.GetPriorDropIdxs()
            if len(mDropIdxs) > 0:
                mRunParams.mAndroidSink.Operation(
                    EnumGameOperation.nDrop, [mRunParams.mAndroidSink.choose_drop_card(mDropIdxs)])
        return eActionResult.FINISHED

class GroupAction(Action):
    def OnRun(self, mRunParams):
        if mRunParams.mAndroidSink is None:
            return eActionResult.FINISHED
        sMePlayer = mRunParams.mAndroidSink.xLogic.Players[mRunParams.mAndroidSink.wMeChairID]

        if self.Op != eActionIDs.Group:
            if sMePlayer.IsOpAllowed(EnumGameOperation.Group):
                self.AddThinkTime(eActionIDs.Group, self.GetCompareThinkTime(), ">>>思考? 等待組牌......")
                return eActionResult.RUNNING

        if self.Op == eActionIDs.Group:
            if not self.IsThinkEnd():
                return eActionResult.RUNNING
            Info(">>> 組牌")

            card_serial = CardSerializer()
            card_serial.AddBatch(mRunParams.mAndroidSink.get_hand_index_ls(sMePlayer))  # 排除已經成為組牌區的牌
            combos = card_serial.GetAllCombo()

            if len(combos) > 0:
                loop_interrupt = False  # 設置迴圈初始標籤是否中斷
                for combo in combos:
                    ## 驗證這組合適合組牌還是出牌，如果不適合組牌，適合出牌
                    #if not mRunParams.mAndroidSink.GroupOrCombine(combo):
                    #    continue  # 換下一組合驗證

                    # 驗證數量是否 > 5 → 不合理出牌
                    if len(combo) > LogicConfig.nMaxContinuity:
                        while len(combo) > LogicConfig.nMaxContinuity:
                            lst = list(combo.keys()).pop(-1)
                            combo.pop(lst)

                    # 確認組合不在已組牌內，並驗證出牌是否有3張以上
                    if combo not in sMePlayer.group_combination \
                            and len(combo) >= LogicConfig.nMinContinuity:
                        mRunParams.mAndroidSink.Operation(EnumGameOperation.Group, list(combo))
                        loop_interrupt = True  # 迴圈中斷，表示所有組牌組合還沒被驗證完是否適合組牌或適合出牌
                        break  # 就用這一組合去組牌，其他組合先不看

                if loop_interrupt:  # 迴圈中斷，表示所有組牌組合還沒被驗證完是否適合組牌或適合出牌，需要再一次等待組牌
                    if sMePlayer.IsOpAllowed(EnumGameOperation.Group):
                        self.AddThinkTime(eActionIDs.Group, self.GetCombineThinkTime(), ">>>思考? 等待組牌......")
                        return eActionResult.RUNNING

        return eActionResult.FINISHED

class UnGroupAction(Action):
    def OnRun(self, mRunParams):
        if mRunParams.mAndroidSink is None:
            return eActionResult.FINISHED
        sMePlayer = mRunParams.mAndroidSink.xLogic.Players[mRunParams.mAndroidSink.wMeChairID]

        if self.Op != eActionIDs.UnGroup:
            if sMePlayer.IsOpAllowed(EnumGameOperation.UnGroup):
                self.AddThinkTime(eActionIDs.UnGroup, self.GetCompareThinkTime(), ">>>思考? 等待解散組牌......")
                return eActionResult.RUNNING

        if self.Op == eActionIDs.UnGroup:
            if not self.IsThinkEnd():
                return eActionResult.RUNNING
            Info(">>> 解散組牌")

            if len(sMePlayer.group_combination) != 0:
                group = list(sMePlayer.group_combination[0])
                mRunParams.mAndroidSink.Operation(EnumGameOperation.UnGroup, group)

        return eActionResult.FINISHED

class FightAction(Action):
    def OnRun(self, mRunParams):
        if mRunParams.mAndroidSink is None:
            return eActionResult.FINISHED
        sMePlayer = mRunParams.mAndroidSink.xLogic.Players[mRunParams.mAndroidSink.wMeChairID]

        if self.Op != eActionIDs.Fight:
            if sMePlayer.IsOpAllowed(EnumGameOperation.Fight):
                self.AddThinkTime(eActionIDs.Fight, self.GetCompareThinkTime(), ">>>思考? 等待發起比牌......")
                return eActionResult.RUNNING

        if self.Op == eActionIDs.Fight:
            if not self.IsThinkEnd():
                return eActionResult.RUNNING
            Info(">>> 發起比牌")
            mRunParams.mAndroidSink.Operation(EnumGameOperation.Fight, [])
        return eActionResult.FINISHED

class ChallengeAction(Action):
    def OnRun(self, mRunParams):
        if mRunParams.mAndroidSink is None:
            return eActionResult.FINISHED
        sMePlayer = mRunParams.mAndroidSink.xLogic.Players[mRunParams.mAndroidSink.wMeChairID]

        if self.Op != eActionIDs.Challenge:
            if sMePlayer.IsOpAllowed(EnumGameOperation.Challenge):
                self.AddThinkTime(eActionIDs.Challenge, self.GetCompareThinkTime(), ">>>思考? 等待接受比牌......")
                return eActionResult.RUNNING

        if self.Op == eActionIDs.Challenge:
            if not self.IsThinkEnd():
                return eActionResult.RUNNING
            Info(">>> 接受比牌")
            mRunParams.mAndroidSink.Operation(EnumGameOperation.Challenge, [])

        return eActionResult.FINISHED

class FoldAction(Action):
    def OnRun(self, mRunParams):
        if mRunParams.mAndroidSink is None:
            return eActionResult.FINISHED
        sMePlayer = mRunParams.mAndroidSink.xLogic.Players[mRunParams.mAndroidSink.wMeChairID]

        if self.Op != eActionIDs.Fold:
            if sMePlayer.IsOpAllowed(EnumGameOperation.Fold):
                self.AddThinkTime(eActionIDs.Fold, self.GetCompareThinkTime(), ">>>思考? 等放棄比牌......")
                return eActionResult.RUNNING

        if self.Op == eActionIDs.Fold:
            if not self.IsThinkEnd():
                return eActionResult.RUNNING
            Info(">>> 放棄比牌")
            mRunParams.mAndroidSink.Operation(EnumGameOperation.Fold, [])

        return eActionResult.FINISHED

# 抽牌->出牌->插牌->棄牌
class DrawComboAction(ComboAction):
    def __init__(self):
        super(DrawComboAction, self).__init__()
        self.mActions.append(DrawAction())
        self.mActions.append(UnGroupAction())
        self.mActions.append(GroupAction())
        self.mActions.append(CombineAction())
        self.mActions.append(InsertAction())
        self.mActions.append(DropAction())

# 撿牌->出牌->插牌->棄牌
class PickComboAction(ComboAction):
    def __init__(self):
        super(PickComboAction, self).__init__()
        self.mActions.append(PickAction())
        self.mActions.append(UnGroupAction())
        self.mActions.append(GroupAction())
        self.mActions.append(CombineAction())
        self.mActions.append(InsertAction())
        self.mActions.append(DropAction())

# 出牌->插牌->棄牌
class CombineComboAction(ComboAction):
    def __init__(self):
        super(CombineComboAction, self).__init__()
        self.mActions.append(CombineAction())
        self.mActions.append(InsertAction())
        self.mActions.append(DropAction())

# 插牌->棄牌
class InsertComboAction(ComboAction):
    def __init__(self):
        super(InsertComboAction, self).__init__()
        self.mActions.append(InsertAction())
        self.mActions.append(DropAction())

# 棄牌
class DropComboAction(ComboAction):
    def __init__(self):
        super(DropComboAction, self).__init__()
        self.mActions.append(DropAction())

# 發起比牌
class FightComboAction(ComboAction):
    def __init__(self):
        super(FightComboAction, self).__init__()
        self.mActions.append(FightAction())

# 放棄比牌
class FoldComboAction(ComboAction):
    def __init__(self):
        super(FoldComboAction, self).__init__()
        self.mActions.append(FoldAction())

# 接受比牌
class ChallengeComboAction(ComboAction):
    def __init__(self):
        super(ChallengeComboAction, self).__init__()
        self.mActions.append(ChallengeAction())
