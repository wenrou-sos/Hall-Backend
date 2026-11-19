package accountingFS

import (
	"math"

	"fish-shrimp-crab-game-server/application/gamesettingFS"
	"fish-shrimp-crab-game-server/application/lobbysettingFS"
	lottery_proto "fish-shrimp-crab-game-server/application/lottery/proto"
	bet_proto "fish-shrimp-crab-game-server/domain/bet/proto"
	"fmt"
	"strconv"
	"strings"

	"gitlab.iplaystar.net/game-server/accounting"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/wallet"
)

type AccountingFS struct {
}

func (aFS *AccountingFS) FluxActionHandler(action *flux.Action, a *accounting.Accounting, isOk chan bool) {

	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:
		isOk <- true

	case accounting.ActionAccountingStop:
		// do nothing

	case accounting.ActionAccountingEnd:
		results := action.Payload()[0].(*lottery_proto.BroadcastResult)
		bets := action.Payload()[1].(map[string][]bet_proto.BetCall)
		dice := action.Payload()[2].(([3]int32))
		memberName := action.Payload()[3].(string)
		balance := action.Payload()[4].(uint64)

		gameData := fmt.Sprintf("%d,%d,%d|", dice[0], dice[1], dice[2])
		gameData += strings.Trim(strings.Replace(fmt.Sprint(results.WinIndexes), " ", ",", -1), "[]")
		gameData += "|" + strconv.FormatUint(balance, 10)

		for k, _ := range bets {
			if k == a.SecWebSocketKey { //過濾掉機器人
				gameRate := gamesettingFS.Service.Rate(k)
				gameData += "|" + strconv.FormatUint(uint64(gameRate), 10)
				break
			}
		}

		var totalBet uint32
		var playerBetState [11][24]uint32
		var allPlayerMemberNames [11]string
		for k, betCalls := range bets {
			for _, betCall := range betCalls {
				betCost := gamesettingFS.Service.Bet(k, betCall.BetIndex)
				gameRate := gamesettingFS.Service.Rate(k)
				playerBetState[betCall.Seat][int(betCall.BetType)] += betCost * gameRate
				if k == a.SecWebSocketKey { //過濾掉機器人
					totalBet += betCost * gameRate
				}
			}
			if len(betCalls) > 0 {
				allPlayerMemberNames[int(betCalls[0].Seat)] = wallet.Service.MemberName(k)
			}
		}

		var allPlayerResults [11]*lottery_proto.Result
		for _, result := range results.Results {
			allPlayerResults[int(result.Seat)] = result
		}

		playerSeat := bets[a.SecWebSocketKey][0].Seat
		//gameResult := fmt.Sprintf("%d/%d", allPlayerResults[playerSeat].Status, allPlayerResults[playerSeat].Pay)
		gameResult := memberName + "/" + strings.Trim(strings.Replace(fmt.Sprint(playerBetState[playerSeat]), " ", ",", -1), "[]")

		i := playerSeat + 1
		if i == 11 {
			i = 0
		}
		for i != playerSeat {
			if allPlayerResults[i] == nil {
				gameResult += "|-"
			} else {
				gameResult += "|" + allPlayerMemberNames[i] + "/" + strings.Trim(strings.Replace(fmt.Sprint(playerBetState[i]), " ", ",", -1), "[]")
			}
			i++
			if i == 11 {
				i = 0
			}
		}

		switch allPlayerResults[playerSeat].Status {
		case int32(lottery_proto.Result_WIN):
			fee := lobbysettingFS.Service.Fee(a.SecWebSocketKey)
			profit := uint32(allPlayerResults[playerSeat].Pay) //尚未抽水的利潤
			feePercent := float64(100-fee) / math.Floor(100)
			feeProfit := uint32(math.Round(float64(profit) * feePercent)) //抽水後的利潤
			totalWin := feeProfit + totalBet

			a.End(uint64(totalBet), 0, int64(totalWin), 0, gameData, gameResult)

		case int32(lottery_proto.Result_LOSE), int32(lottery_proto.Result_TIE): //平手或輸局
			lose := uint32(allPlayerResults[playerSeat].Pay) //輸多少
			totalWin := totalBet - lose                      //押注扣掉輸多少，就是只贏回多少

			a.End(uint64(totalBet), 0, int64(totalWin), 0, gameData, gameResult)
		}

		logger.Service.Zap.Infow("ActionAccountingEnd",
			"GameUser", a.SecWebSocketKey,
			"AccountingSn", a.Start.Sn,
			"totalBet", totalBet,
			"gameData", gameData,
			"gameResult", gameResult,
		)

	}
}

func (aFS *AccountingFS) RotationHandler(a *accounting.Accounting) {
	// do nothing
}
