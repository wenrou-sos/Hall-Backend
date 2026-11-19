from definations import *
from android import AndroidDelegate
from subgame.dummy.gamelogic import *
from subgame.dummy.action import *
from copy import deepcopy
import math

def Create():
    return AndroidSink()

class AiRunParams(object):
    def __init__(self, androidsink):
        self.mAndroidSink = androidsink
        self.vDropIdxs = []                 #随机弃牌
        self.vCombines = []                 #出牌数据：[[牌组1],[牌组2],...]
        self.vInsertIdxs = []               #插牌数据,顺序
        self.mPickCombo = {}                #捡牌数据
        self.nDrawIdx = -1                  #摸牌数据

    def Cleanup(self):
        self.vDropIdxs.clear()
        self.vCombines.clear()
        self.vInsertIdxs.clear()
        self.mPickCombo.clear()
        self.nDrawIdx = -1

class AndroidSink(AndroidDelegate):
    def __init__(self):
        self.mAndrdUserItem = None
        self.mTableFrame = None
        self.mTableFrameSink = None
        self.xLogic = None
        self.wMeChairID = INVALID_CHAIR
        self.mAction = None
        self.mRunParams = AiRunParams(self)
        #金牌关联牌
        self.mGoldRelates = { 0x12:1, 0x22:1, 0x32:1, 0x03:1, 0x04:1,
                              0x0C:1, 0x1C:1, 0x2C:1, 0x3A:1, 0x3B:1, 0x3D:1, 0x31:1}

    def Initialization(self, sAndrdUserItem):
        self.mAndrdUserItem = sAndrdUserItem

    def OnAndroidSitDown(self, mTable):
        self.mTableFrame = mTable
        self.mTableFrameSink = self.mTableFrame.mDgt
        self.xLogic = self.mTableFrameSink.xLogic
        self.wMeChairID = self.mAndrdUserItem.GetMeUserItem().ChairID
        self.mAction = None

    def OnAndroidReady(self):
        pass

    def OnConcludeGame(self):
        pass

    def OnUpdate(self):
        if self.mTableFrameSink.CanBotAction():
            if self.wMeChairID != self.xLogic.CurrentTurn:
                # 若不是在比牌階段不可操作
                if not self.mTableFrameSink.xLogic.is_fight:
                    return
            #执行动作
            if self.mAction is not None:
                eResult = self.mAction.OnRun(self.mRunParams)
                if eResult == eActionResult.FINISHED:
                    self.mAction = None
                return
            self.TryMakeAction()

    def TryMakeAction(self):
        self.mRunParams.Cleanup()
        sMePlayer = self.xLogic.Players[self.wMeChairID]

        if self.mTableFrameSink.xLogic.is_fight:  # 場上有玩家發起比牌時
            if sMePlayer.IsOpAllowed(EnumGameOperation.Challenge):
                if self.AndroidLucky(sMePlayer):
                    if self.PeepPoint():
                        Log("=====偷看完自己是點數是全場最小 接受比牌")
                        self.mAction = ChallengeComboAction()
                    else:
                        Log("=====偷看完自己是點數不是全場最小 放棄比牌")
                        self.mAction = FoldComboAction()
                else:
                    if self.WhetherFightOrChallenge():  # 如果機器人計算後決定接受比牌:
                        Log(f'{self.wMeChairID}比牌但要回復')
                        self.mAction = ChallengeComboAction()  # 機器人接受比牌
                    else:
                        self.mAction = FoldComboAction()  # 機器人放棄比牌
            else:
                Log(f'{self.wMeChairID}比牌但不用回復')
                self.mAction = FoldComboAction()  # 機器人放棄比牌
            return

        if sMePlayer.IsOpAllowed(EnumGameOperation.Fight):
            Log("=====未被插牌{}".format(sMePlayer.odd_turn_inserted_mark == 0 and sMePlayer.even_turn_inserted_mark == 0))
            if sMePlayer.odd_turn_inserted_mark == 0 and sMePlayer.even_turn_inserted_mark == 0:
                if self.AndroidLucky(sMePlayer):
                    if self.PeepPoint():
                        Log("=====偷看完自己是點數是全場最小 發起比牌")
                        self.mAction = FightComboAction()
                        return  # 進行發起比牌
                    else:
                        Log("=====偷看完自己是點數不是全場最小 不發起比牌")
                else:
                    if self.WhetherFightOrChallenge():
                        self.mAction = FightComboAction() # 如果機器人計算後決定發起比牌
                        return  # 進行發起比牌
            else:
                if self.WhetherFightOrChallenge():
                    self.mAction = FightComboAction() # 如果機器人計算後決定發起比牌
                    return  # 進行發起比牌

        # if sMePlayer.IsOpAllowed(EnumGameOperation.UnGroup):
        #     self.mAction = UnGroupAction()
        #     return  # 進行解散組牌

        if sMePlayer.IsOpAllowed(EnumGameOperation.nPick):
            if self.WhetherPickOrPass():  # 機器人是否撿牌
                Log("撿牌")
                self.mAction = PickComboAction()
                return  # 進行撿牌
            Log("不撿牌")

        if sMePlayer.IsOpAllowed(EnumGameOperation.nDraw):
            self.mAction = DrawComboAction()
            return  # 進行抽牌

        #if sMePlayer.IsOpAllowed(EnumGameOperation.Group):
        #    self.mAction = GroupAction()
        #    return  # 進行組牌

        if self.WhetherCombineOrPass():  # 機器人是否出牌或扣牌
            if sMePlayer.IsOpAllowed(EnumGameOperation.nCombine):
                self.mAction = CombineComboAction()
                return  # 進行出牌

        if sMePlayer.IsOpAllowed(EnumGameOperation.nInsert):
            self.mAction = InsertComboAction()
            return  # 進行插牌

        if sMePlayer.IsOpAllowed(EnumGameOperation.nDrop):
            self.mAction = DropComboAction()
            return  # 進行棄牌

    def Operation(self, op, params):
        # android_round=True : 識別為機器人操作
        self.mTableFrameSink.DoPlayerOperate(op, params, self.mAndrdUserItem.GetMeUserItem(), android_round=True)

    #获取玩家座位号
    def GetPlayerChairID(self):
        for wChair, _ in self.xLogic.Players.items():
            if wChair != INVALID_CHAIR and wChair != self.wMeChairID:
                return wChair
        return INVALID_CHAIR

    def GetCount(self):
        if self.wMeChairID in self.xLogic.Players:
            nC = len(self.xLogic.Players[self.wMeChairID].mInHand)
            return nC
        return 0

    def AndroidLucky(self ,sMePlayer):#機器人抽到幸運值       
        is_lucky_draw = GetRndInt(1, 100) <= ServiceOpt.sRobotDrawRate
        is_vip_lucky_draw = GetRndInt(1, 100) <= ServiceOpt.sRobotDrawRateVip
        Log("幸運機率{}, vip幸運機率{}, 機器人座號{}抽幸運值".format(
                    ServiceOpt.sRobotDrawRate, ServiceOpt.sRobotDrawRateVip, sMePlayer.nSeatIndex))
            # 如果機器人抽到幸運值，或vip房內機器人抽中vip幸運值
        if is_lucky_draw or (android.android_vip == True and is_vip_lucky_draw):
            Log("☆☆☆抽中幸運值☆☆☆")
            return True
        else:
            Log("▼▼▼沒抽中幸運值▼▼▼")
            return False

    # def AndroidNotOpenCanDummy(self):
    #     sMePlayer = self.xLogic.Players[self.wMeChairID]
    #     return sMePlayer.android_pick_combine_insert_drop

    # 定義手上雜牌剩下幾張
    # def inhand_badcard_amounts(self, vCombines, mAllCombos):
    #     sMePlayer = self.xLogic.Players[self.wMeChairID]  # 取得該玩家資訊
    #     vMeIndexs = list(sMePlayer.mInHand.keys())  # 取得該玩家手上所有的牌
    #     inhand_amounts = len(vMeIndexs)  # 手上的牌共N張
    #     temps = []  # 顯示目前算過一次的牌，加進去的牌就不重複算第2次
    #     # 以下計算所有出牌的可能
    #     for i in vCombines:  # 所有可出牌的組合：vCombines is list, i is dict
    #         for j in list(i.keys()):  # 將單一組合過濾values()，組成list()，在清單內取出單一張牌
    #             if j not in temps:  # 如果該張牌還沒被算過一次
    #                 inhand_amounts -= 1  # 計算手上的牌 - 1 = 手上雜牌剩N張
    #                 temps.append(j)  # 將此牌加入不可再次計算的清單內
    #     # 以下計算所有插牌的可能
    #     serial = CardSerializer()
    #     for unq_index, combo in mAllCombos.items():
    #         for cindex in sMePlayer.mInHand.keys():
    #             cindexlist = list(combo.keys())
    #             cindexlist.append(cindex)
    #             serial.Clear()
    #             serial.AddBatch(cindexlist)
    #             if serial.HasFullMatch(cindexlist):
    #                 if cindex not in temps:  # 如果該張牌還沒被算過一次
    #                     inhand_amounts -= 1  # 計算手上的牌 - 1 = 手上雜牌剩N張
    #                     temps.append(cindex)  # 將此牌加入不可再次計算的清單內
    #     return inhand_amounts  # 回傳手上剩下多少沒用的雜牌

    def get_hand_index_ls(self, sMePlayer):
        """排除掉已經組成牌組的卡，回傳剩餘手牌

        Args:
            sMePlayer (PlayerInfo): 玩家物件

        Returns:
            list: 卡牌 index [1, 2, 43, ...]
        """
        card_index_ls = list(sMePlayer.mInHand.keys())
        output_card_index_ls = [i for i in card_index_ls]

        for group in sMePlayer.group_combination:
            for index in group:
                if index in card_index_ls:
                    output_card_index_ls.remove(index)

        return output_card_index_ls

    def GroupOrCombine(self, combo):  # 機器人是否組牌或出牌
        for i in combo.keys():
            if len(combo) == 5:  # 5張同花順
                return True  # 組合適合組牌

            if i % 16 == 1:  # 組合中有一張A加分牌
                return False  # 組合適合出牌

            if i % 16 == 13:  # 組合中有一張K加分牌
                return False  # 組合適合出牌

            if len(combo) == 4:  # 4張，但不確定是否為鐵支
                card_index_ls = [card_index for card_index in combo]
                for j in range(3):  # 最多4張，index0123
                    if abs(card_index_ls[j] - card_index_ls[j + 1]) % 16 == 0:  # 驗證為鐵支
                        return True  # 組合適合組牌

        return True  # 組合適合組牌

    def WhetherFightOrChallenge(self):  # 機器人是否發起比牌或接受比牌
        # 條件一: 其他人都沒開張!!!
        condition_1 = 0  # 有多少人達成條件1
        for seat_index in self.xLogic.vPlayersOrder:  # 走訪所有人
            if self.wMeChairID != seat_index:  # 若座號不是自己
                if self.xLogic.Players[seat_index].bIsOpened:  # 其他家有人開張了
                    condition_1 += 1
        if condition_1 == 0:  # 其他家都沒開張
            Log("=====達成條件一")
            return True  # 發起比牌且接受比牌

        if condition_1 >= 1:
            for seat_index in self.xLogic.vPlayersOrder:
                Log("=====座號{}{}開張".format(seat_index, "已" if self.xLogic.Players[seat_index].bIsOpened else "未"))
                Log("=====座號{}消耗點數{}".format(seat_index, self.xLogic.Players[seat_index].consume_point))
                Log("=====座號{}最小棄牌{}".format(seat_index, self.xLogic.Players[seat_index].drop_first_min_card))
                Log("=====座號{}第2小棄牌{}".format(seat_index, self.xLogic.Players[seat_index].drop_second_min_card))

        # 條件二: 自己消耗(撿牌、出牌、插牌)遠大於所有對手消耗20點以上!!!
        condition_2 = 0  # 有多少人達成條件2
        for seat_index in self.xLogic.vPlayersOrder:
            if self.xLogic.Players[seat_index].consume_point + 20 <= \
                    self.xLogic.Players[self.wMeChairID].consume_point:
                condition_2 += 1
        if condition_2 >= 2:  # 若2家都達成條件2
            if self.opened_count() == 1:
                Log("=====達成條件二")
                return True  # 發起比牌且接受比牌

        # 條件三: 自己比牌點數小於15點，所有對手剩餘手牌7張以上!!!
        min_inhand_count = 13  # 預設全場其他人最少手牌數
        if self.xLogic.Players[self.wMeChairID].compare_point < 15:  # 自己比牌點數不到15點
            for seat_index in self.xLogic.vPlayersOrder:
                if self.wMeChairID != seat_index:
                    # 取出手牌
                    inhand = list(self.xLogic.Players[seat_index].mInHand.keys())
                    if len(inhand) < min_inhand_count:  # 手牌數比全場其他人最少手牌數還少
                        min_inhand_count = len(inhand)  # 取代為全場其他人最少手牌數
            if min_inhand_count >= 7:  # 其他人7張以上
                Log("=====達成條件三")
                Log("=====手牌點數<15時，對方最少手牌數>=7 手牌:{} :對方最少手牌數{}".format(self.xLogic.Players[self.wMeChairID].compare_point, min_inhand_count))
                return True  # 發起比牌且接受比牌

        # 條件四: 自己消耗點數比所有對手消耗點數多2倍以上!!!
        condition_4 = 0  # 有多少人達成條件4
        for seat_index in self.xLogic.vPlayersOrder:
            if self.xLogic.Players[seat_index].consume_point * 2 < self.xLogic.Players[self.wMeChairID].consume_point:
                condition_4 += 1
        if condition_4 >= 2:  # 若2家都達成條件4
            Log("=====達成條件四")
            return True  # 發起比牌且接受比牌

        # 條件五:梯形公式比對手小!!!
        # 先算自己機器人的!
        trapezoid_myself = self.xLogic.Players[self.wMeChairID].compare_point
        # inhand_count_myself = len(list(self.xLogic.Players[self.wMeChairID].mInHand.keys()))
        # 補正: 最小棄牌 + 5 <= 第2小棄牌 == 以第2小棄牌 - 1 作為上底
        # if self.xLogic.Players[self.wMeChairID].drop_first_min_card + 5 <= \
        #         self.xLogic.Players[self.wMeChairID].drop_second_min_card:
        #     trapezoid_myself = \
        #         (self.xLogic.Players[self.wMeChairID].drop_second_min_card - 1 + 1) * inhand_count_myself / 2
        # else:
        #     trapezoid_myself = \
        #         (self.xLogic.Players[self.wMeChairID].drop_first_min_card + 1) * inhand_count_myself / 2

        # 再算對手的!
        min_trapezoid = 999  # 先預設最小梯形值
        trapezoid = 999  # 先預設其他人的梯形值
        Log("=====算點=====")
        for seat_index in self.xLogic.vPlayersOrder:
            if self.wMeChairID != seat_index:
                inhand_count = len(list(self.xLogic.Players[seat_index].mInHand.keys()))
                # 補正: 最小棄牌 + 5 <= 第2小棄牌 == 以第2小棄牌 - 1 作為上底
                if self.xLogic.Players[seat_index].drop_first_min_card + 5 <= \
                    self.xLogic.Players[seat_index].drop_second_min_card:
                    trapezoid = (self.xLogic.Players[seat_index].drop_second_min_card - 1 + 1) * inhand_count / 2
                else:
                    trapezoid = (self.xLogic.Players[seat_index].drop_first_min_card + 1) * inhand_count / 2
                Log("=====座號{}手牌數{}梯形值{}".format(seat_index, inhand_count, trapezoid))   
                # 保守補正梯形值
                if inhand_count >= 7 or trapezoid >= 34:
                    Log("=====若對方手牌數>=7，或梯形公式推算對方點數>34，則保守估計對方有一暗搭-20點")
                    trapezoid -= 20
                elif (inhand_count > 4 and inhand_count < 7) or (trapezoid >= 10 and trapezoid <= 34):
                    Log("=====若4<對方手牌數<7，或梯形公式推算10<=對方點數<=34，則保守補正將點數X(對方手牌數/10)")
                    trapezoid *= (inhand_count / 10)
                elif inhand_count <= 4 or trapezoid <= 10:
                    Log("=====若對方手牌數<=4，或梯形公式算完對方點數<=10，則保守補正為-對方手牌數")
                    trapezoid -= inhand_count
                Log("=====座號{}手牌數{}保守補正{}".format(seat_index, inhand_count, trapezoid))    

                # 看看是否比最小梯形值還小
                if min_trapezoid > trapezoid:
                    min_trapezoid = trapezoid
                    
        Log("=====自己{}點數{}".format(self.wMeChairID,trapezoid_myself)) 
        Log("=====算點=====")
        
        # 最後來比較雙方的!
        if trapezoid_myself < trapezoid:
            Log("=====達成條件五")
            return True  # 發起比牌且接受比牌
        Log("=====未達成發起比牌與接受比牌條件")
        return False  # 不發起比牌且不接受比牌

    def GetStockValue(self):
        return self.mTableFrame.GetStockValue()

    def GetPriorDropIdxs(self):
        '''
            選擇最大廢物值棄牌
            雜牌或中洞聽搭: 牌面數 + 0.5分
            組成連續聽搭或對子聽搭後，場上可聽1嵌: -0.1分
            組成連續聽搭或對子聽搭後，場上可聽2嵌: -1.6分
        '''
        sMePlayer = self.xLogic.Players[self.wMeChairID]
        vMeIndexs = list(sMePlayer.mInHand.keys())
        vMeIndexs.sort()
        # 廢物值初始值
        sIdxScore = {}
        for idx in vMeIndexs:
            poker_type, poker_point = Poker.Index2TypePoint(idx)
            card_point = poker_point if poker_point <= 10 else 10
            sIdxScore[idx] = card_point
        # 整理海底被棄過，與檯面牌的所有序號
        seabottom_and_mesa_cards_index = []
        for unq_index, combo in self.xLogic.mAllCombos.items():
            seabottom_and_mesa_cards_index.extend(list(combo.keys()))
        seabottom_and_mesa_cards_index.extend(self.xLogic.vSeaBottomOrder)

        for idx in vMeIndexs:
            for idx2 in vMeIndexs:
                if idx != idx2 and idx < idx2:
                    # 判斷2張牌是否連續聽搭或對子聽搭
                    kind_related = self.TryContinueRelateCombo(idx, idx2)
                    if kind_related != 0:
                        #Log("=====連續聽搭算前點數={:>2}:{:>4} , {:>2}:{:>4}".format(idx, sIdxScore[idx], idx2, sIdxScore[idx2]))
                        ready_hand = 2
                        if kind_related == 3:  # 不同花色對子
                            for idx3 in seabottom_and_mesa_cards_index:
                                if self.TryContinueRelateCombo(idx, idx3) == 3:  # 海底或檯面有此組搭
                                    ready_hand -= 1

                        elif kind_related == 1:  # 同花色順子
                            for idx3 in seabottom_and_mesa_cards_index:
                                if self.TryContinueRelateCombo(idx, idx3) == 1:  # 海底或檯面有此組搭
                                    ready_hand -= 1
                                if self.TryContinueRelateCombo(idx2, idx3) == 1:  # 海底或檯面有此組搭
                                    ready_hand -= 1
                        

                        elif kind_related == 2:  # 同花色順子中洞
                            ready_hand = 1
                            for idx3 in seabottom_and_mesa_cards_index:
                                if (self.TryContinueRelateCombo(idx, idx3) == 1) and (self.TryContinueRelateCombo(idx2, idx3)== 1):  # 海底或檯面有此組搭
                                    ready_hand -= 1

                        if ready_hand == 2:  # 聽2嵌: -1.6
                            #Log("聽雙頭")
                            sIdxScore[idx] -= 1.6
                            sIdxScore[idx2] -= 1.6
                        elif ready_hand == 1:  # 聽1嵌: -0.1
                            #Log("聽單吊")
                            sIdxScore[idx] -= 0.1
                            sIdxScore[idx2] -= 0.1
                        
                        sIdxScore[idx] = round(sIdxScore[idx], 1)
                        sIdxScore[idx2] = round(sIdxScore[idx2], 1)
                        #Log("=====連續聽搭算後點數={:>2}:{:>4} , {:>2}:{:>4}".format(idx, sIdxScore[idx], idx2, sIdxScore[idx2]))
                        #Log("")
        for idx in vMeIndexs:
            sIdxScore[idx] = sIdxScore[idx] if type(sIdxScore[idx]) == float else sIdxScore[idx] + 0.5 # 手上沒變化過的都是雜牌

        Log("手牌", vMeIndexs)
        Log("廢物點數", sIdxScore)
        group_combination_ls = self.get_hand_index_ls(sMePlayer)
        Log("排除掉已經組成牌組的卡", group_combination_ls)
        # 計算最優棄牌，tongits優先棄掉廢物點數大的
        nMaxScore = 0
        vIdxs = []
        for idx, score in sIdxScore.items():
            if score >= nMaxScore and idx in group_combination_ls:
                nMaxScore = score
                vIdxs.clear()
                vIdxs.append(idx)
        
        vMaxIdxs = []
        for idx, score in sIdxScore.items():
            if score == nMaxScore and idx in group_combination_ls:
                nMaxScore = score
                vMaxIdxs.append(idx)

        if len(vMaxIdxs) > 1:
            vIdxs.clear()
            Log("比大小決定", self.choose_drop_card(vMaxIdxs))
            vIdxs.append(self.choose_drop_card(vMaxIdxs))

        return  vIdxs

    # 機器人棄牌值還挑不出唯一一張棄牌，那就比大小決定
    def choose_drop_card(self, drop_indexs):
        max_card = [0, 0, 0]  # 設置最大雜牌[牌面序號, 牌面數字, 牌面花色]
        for card_index in drop_indexs:
            drop_card_number = int(card_index % 16)  # 牌面數字
            drop_card_flower = int(math.floor(card_index / 16))  # 牌面花色，0梅花1方塊2愛心3黑桃

            if drop_card_number > max_card[1]:  # 若牌面數字比原來的大
                max_card = [card_index, drop_card_number, drop_card_flower]  # 取代成為最大雜牌
            elif drop_card_number == max_card[1]:  # 若牌面數字比原來的相等
                if drop_card_flower > max_card[2]:  # 若牌面花色比原來的大
                    max_card = [card_index, drop_card_number, drop_card_flower]  # 取代成為最大雜牌

        return max_card[0]  # 選擇最大雜牌的序號丟棄之

    #判断2张牌是否听搭
    def TryRelateCombo(self, idx1, idx2):
        color1, value1 = Poker.Index2TypePoint(idx1)
        color2, value2 = Poker.Index2TypePoint(idx2)
        if value1 == value2:
            return True
        if color1 != color2:
            return False
        value1 = value1 if value1 != EnumPokerPoint.nAce else EnumPokerPoint.nSpecAce
        value2 = value2 if value2 != EnumPokerPoint.nAce else EnumPokerPoint.nSpecAce
        if abs(value1 - value2) <= 2:
            return True
        return False

    # 判斷2張牌是否連續聽搭或對子聽搭
    def TryContinueRelateCombo(self, idx1, idx2):
        color1, value1 = Poker.Index2TypePoint(idx1)
        color2, value2 = Poker.Index2TypePoint(idx2)
        if value1 == value2:
            return 3
        if color1 != color2:
            return 0
        if abs(value1 - value2) == 1:
            return 1
        if abs(value1 - value2) == 2:
            return 2
        return 0

    # 判断底牌与手牌 听搭、可插的牌
    def GetDeckRelateOrIns(self):
        sMePlayer = self.xLogic.Players[self.wMeChairID]
        vMeIndexs = list(sMePlayer.mInHand.keys())  # 手牌
        SeaBottomOrder = self.xLogic.vSeaBottomOrder  # 海底牌
        vDeckRemain = self.xLogic.vDeckOrder[self.xLogic.nDeckCursor:]  # 剩餘的牌組
        mRelates = []  # 準備一個作弊抽牌區

        for nTryIdx in vDeckRemain:  # 走訪剩餘牌組
            # 手牌聽搭或海底關聯
            for idx in (vMeIndexs + [SeaBottomOrder[-1]]):  # 走訪手牌+海底末張牌
                if self.TryRelateCombo(nTryIdx, idx):  # 牌組與手牌+海底牌是否關聯
                    # 加入此張至作弊抽牌區，計算幾次則累進2倍，關聯越大抽中機率越高
                    if nTryIdx not in mRelates:
                        mRelates.append(nTryIdx)
                    # 1次權重才1倍，但是2次3倍、3次5倍、4次7倍、5次9倍
                    else:
                        mRelates.append(nTryIdx)
                        mRelates.append(nTryIdx)
        # 可插
        serial = CardSerializer()
        for unq_index, combo in self.xLogic.mAllCombos.items():
            for nTryIdx in vDeckRemain:
                cindexlist = list(combo.keys())
                cindexlist.append(nTryIdx)
                serial.Clear()
                serial.AddBatch(cindexlist)
                if serial.HasFullMatch(cindexlist):
                    # 加入此張至作弊抽牌區，計算幾次則加幾次，關聯越大抽中機率越高
                    if nTryIdx not in mRelates:
                        mRelates.append(nTryIdx)
                    # 1次權重才1倍，但是2次3倍、3次5倍、4次7倍、5次9倍
                    else:
                        mRelates.append(nTryIdx)
                        mRelates.append(nTryIdx)
        return mRelates

    def WhetherPickOrPass(self):

        sMePlayer = self.xLogic.Players[self.wMeChairID]
        vMeIndexs = list(sMePlayer.mInHand.keys())  # 玩家手牌
        vpickCombos = self.GetCanPickCombos()
        repeat_combos = self.combos_repeat(vpickCombos, vMeIndexs)

        if len(repeat_combos) == 0:
            Log("=====基本邏輯:沒有拆搭，能撿則撿")
            return True
        Log("=====撿牌組合 {}".format(vpickCombos[0][2]))
        Log("=====可搭組合 {}".format(repeat_combos))
        pick_in_hand = [i for i in vMeIndexs]#排除手牌檢完可搭剩餘手牌
        pick_index_ls = list(vpickCombos[0][2].keys())
        for index in pick_index_ls:
            if index in vMeIndexs:
                pick_in_hand.remove(index)

        group_in_hand = [i for i in vMeIndexs]#排除手牌可搭剩餘手牌
        for index in repeat_combos.keys():
            if index in vMeIndexs:
                group_in_hand.remove(index)
                    
        group_point = 0
        pick_point = 0

        Log("=====撿牌後手牌 {}".format(pick_in_hand))
        Log("=====出搭後手牌 {}".format(group_in_hand))
        
        for card_index in group_in_hand:
            _, card_point = Poker.Index2TypePoint(card_index)
            group_point += card_point if card_point <= 10 else 10
        for card_index in pick_in_hand:
            _, card_point = Poker.Index2TypePoint(card_index)
            pick_point += card_point if card_point <= 10 else 10
        Log("=====拆搭邏輯:可拆搭情況下，選擇消耗點數比較多的搭 可搭剩餘:{} , 撿牌剩餘:{}".format( group_point, pick_point))

        return group_point > pick_point


    def combos_repeat(self, pickCombos, inHand):
        """手牌可搭跟撿牌組合是否有重複

        Args:
            pickCombos : 撿牌組合
            groupCombos : 玩家手牌

        Returns:
            list
        """
        card_serial = CardSerializer()
        card_serial.AddBatch(inHand)
        groupCombos = card_serial.GetAllCombo()

        pick_index_ls = []
        group_index_ls = []
        repeat_combos = {}

        pick_index_ls = list(pickCombos[0][2].keys())

        for combo in groupCombos:
            for index in combo:
                group_index_ls.append(index)
        
        visited = list(set(pick_index_ls) & set(group_index_ls))

        if len(visited):
            for combo in groupCombos:
                for index in combo:
                    if index in visited:
                        repeat_combos.update(combo)
                        break

        return repeat_combos

    def WhetherCombineOrPass(self):  # 機器人是否出牌或扣牌
        Log("=====機器人是否出牌或扣牌")
        # 條件三: 已開張的情況下，一律扣搭，順子搭有斷上張時出搭!!!
        if self.xLogic.Players[self.wMeChairID].bIsOpened:
            Log("=====已開張扣搭 順子搭有斷上張時出搭")
            return True
        # 條件一: 其他人都沒開張!!!
        elif self.opened_count() == 0  :
            Log("=====其他家都沒開張 不主動開張 扣搭")
            return False
        else :
            # 條件二: 有人開張時，若自己尚未開張，則出一搭跟進開張!!!
            Log("=====有人開張時，若自己尚未開張 出一搭跟進")
            return True

    def PeepPoint(self):  # 開天眼
        Log("=====偷看中")
        vminpoint =999
        vminseat =-1
        for seat_index in self.xLogic.vPlayersOrder:  # 走訪所有人
            Log("=====座號{}點數{}".format(seat_index, self.xLogic.Players[seat_index].compare_point))
            self.xLogic.Players[seat_index].compare_point
            if self.xLogic.Players[seat_index].compare_point < vminpoint:
                vminpoint = self.xLogic.Players[seat_index].compare_point
                vminseat = seat_index
        Log("=====自己[座號{}]是點數是否為全場最小{}".format(self.wMeChairID, self.wMeChairID == vminseat))      
        Log("=====偷看中")
        return self.wMeChairID == vminseat #自己是點數最少的

    def CombosHasStraightBroken(self, groupCombos):
        sMePlayer = self.xLogic.Players[self.wMeChairID]
        seabottom_and_mesa_cards_index = []
        vcombo = {}
        for unq_index, combo in self.xLogic.mAllCombos.items():
            seabottom_and_mesa_cards_index.extend(list(combo.keys()))
        seabottom_and_mesa_cards_index.extend(self.xLogic.vSeaBottomOrder)
        for combo in groupCombos:  # 走訪所有出牌組合
                        # 驗證數量是否 > 5 → 不合理出牌
            if len(combo) > LogicConfig.nMaxContinuity:
                while len(combo) > LogicConfig.nMaxContinuity:
                    lst = list(combo.keys()).pop(-1)
                    combo.pop(lst)
                        # 比對list(combo.keys())是否為list(sMePlayer.mInHand.keys())的子集
                        # 並驗證出牌是否有3張以上
            if set(list(combo.keys())) <= set(list(sMePlayer.mInHand.keys())) \
                and len(list(combo.keys())) >= LogicConfig.nMinContinuity:
                if self.ComboType(combo) == 1:
                    vcombo = {}
                    color1, value1 = Poker.Index2TypePoint(sorted(combo.keys())[-1])
                    Log("=====combo最後一張:{},{}".format(sorted(combo.keys())[-1],color1))
                    for idx2 in seabottom_and_mesa_cards_index:
                        color2, value2 = Poker.Index2TypePoint(idx2)
                        if color1 != color2:
                            continue
                        Log("=====combo最後一張是否聽搭:{},{}".format(idx2, abs(value1 - value2) == 1) or ( (value1 == 13) and (value2 == 1)))
                        if (abs(value1 - value2) == 1) or ( (value1 == 13) and (value2 == 1)):
                            vcombo = combo
                        if len(vcombo) > 0:
                            break
            if len(vcombo) > 0:
                return vcombo
                
        return vcombo

    def CombosPointMin(self, groupCombos):
        sMePlayer = self.xLogic.Players[self.wMeChairID]
        vcombo = {}
        min_point = 999
        for combo in groupCombos:  # 走訪所有出牌組合
                        # 驗證數量是否 > 5 → 不合理出牌
            if len(combo) > LogicConfig.nMaxContinuity:
                while len(combo) > LogicConfig.nMaxContinuity:
                    lst = list(combo.keys()).pop(-1)
                    combo.pop(lst)
                        # 比對list(combo.keys())是否為list(sMePlayer.mInHand.keys())的子集
                        # 並驗證出牌是否有3張以上
            if set(list(combo.keys())) <= set(list(sMePlayer.mInHand.keys())) \
                and len(list(combo.keys())) >= LogicConfig.nMinContinuity:
                point = self.ComboPoint(combo)
                if point < min_point:
                    min_point = point
                    vcombo = combo
                elif point == min_point:
                    if self.ComboType(combo) > self.ComboType(vcombo):
                        min_point = point
                        vcombo = combo
                    elif self.ComboType(combo) == self.ComboType(vcombo):
                         if self.ComboColor(combo) > self.ComboColor(vcombo):
                            min_point = point
                            vcombo = combo
                        
        return vcombo
    
    def ComboPoint(self, combo):
        point = 0
        for card_index in combo:
            _, card_point = Poker.Index2TypePoint(card_index)
            point += card_point if card_point <= 10 else 10
        return point
    
    def ComboType(self, combo): 
        vtype = 1

        if len(combo) == 4:  # 4張，但不確定是否為鐵支
            card_index_ls = [card_index for card_index in combo]
            for j in range(3):  # 最多4張，index0123
                if abs(card_index_ls[j] - card_index_ls[j + 1]) % 16 == 0:  # 驗證為鐵支
                    vtype = 3 

        elif len(combo) == 3:  # 3張，但不確定是否為三條
            card_index_ls = [card_index for card_index in combo]
            for j in range(2):  # 最多3張，index012
                if abs(card_index_ls[j] - card_index_ls[j + 1]) % 16 == 0:  # 驗證為三條
                   vtype = 2 
                    
        return vtype
    
    def ComboColor(self, combo):
        card_flower = 0
        for card_index in combo:
            color, _ = Poker.Index2TypePoint(card_index)
            card_flower = color
        return card_flower

    def opened_count(self):
        opened_count = 0 
        for seat_index in self.xLogic.vPlayersOrder:  # 走訪所有人
            if self.wMeChairID != seat_index:  # 若座號不是自己
                if self.xLogic.Players[seat_index].bIsOpened:  # 其他家有人開張了
                    opened_count += 1
        return opened_count

    # 海底有需要的牌(海底) 可捡牌
    def GetCanPickCombos(self):
        sMePlayer = self.xLogic.Players[self.wMeChairID]
        sMeIndexs = list(sMePlayer.mInHand.keys())
        vSBOrder = deepcopy(self.xLogic.vSeaBottomOrder[-1])  # 海底只有最後一張牌

        serializer = CardSerializer()
        vPickCombos = []  # [海底位置,海底牌索引值,和组成组合]

        serializer.Clear()
        serializer.AddBatch(sMeIndexs)
        serializer.Add(vSBOrder)
        combos = serializer.GetAllCombo(vSBOrder, sMePlayer.mInHand)
        if len(combos) > 0:
            vPickCombos.append([len(self.xLogic.vSeaBottomOrder) - 1, self.xLogic.vSeaBottomOrder[-1], combos[0]])

        return vPickCombos
