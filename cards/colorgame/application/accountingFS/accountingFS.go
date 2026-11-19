package accountingFS

import (
	"math"
	"runtime/debug"

	"colorgame-game-server/application/gamesettingFS"
	"colorgame-game-server/application/lobbysettingFS"
	lottery_proto "colorgame-game-server/application/lottery/proto"
	"colorgame-game-server/domain/bet"
	bet_proto "colorgame-game-server/domain/bet/proto"
	"fmt"
	"strconv"
	"strings"

	errorcode "gitlab.iplaystar.net/game-server/error-code"

	"gitlab.iplaystar.net/game-server/accounting"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/wallet"
)

type AccountingFS struct {
}

func (aFS *AccountingFS) FluxActionHandler(action *flux.Action, a *accounting.Accounting, isOk chan bool) {
	defer func() {
		if err := recover(); err != nil {
			logger.Service.Zap.Fatalw("999",
				"err", err,
				"stacktrace", string(debug.Stack()),
			)
		}
	}()

	logger.Service.Zap.Infow(action.Key().Name(),
		"GameUser", action.Key().From(),
	)

	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:
		isOk <- true

	case accounting.ActionAccountingStop:
		// do nothing

	case accounting.ActionAccountingDelete:
		//accountingSn := action.Payload()[0].(uint64)
		if wallet.Service.WalletCategory(a.SecWebSocketKey) == wallet.CategoryHost {
			a.DeleteRefundLog()
		}
		a.Delete()

	case accounting.ActionAccountingEnd:
		results := action.Payload()[0].(*lottery_proto.BroadcastResult)
		bets := action.Payload()[1].(map[string][]bet_proto.BetCall)
		dice := action.Payload()[2].(([3]int32))
		memberName := action.Payload()[3].(string)
		balance := action.Payload()[4].(uint64)
		gameRoomUuid := action.Payload()[5].(string)

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

		gameData += "|" + gameRoomUuid

		var totalBet uint32
		var playerBetState [11][6]uint32
		var allPlayerMemberNames [11]string

		for k, betCalls := range bets {
			k_memberName := wallet.Service.MemberName(k)

			for idx, betCall := range betCalls {
				betCost := gamesettingFS.Service.Bet(k, betCall.BetIndex) //uint32
				gameRate := gamesettingFS.Service.Rate(k)                 // uint32
				cost := betCost * gameRate

				if betCall.BetType < 0 || betCall.BetType >= 6 ||
					betCall.Seat < 0 || betCall.Seat >= 11 ||
					cost < 0 {

					logger.Service.Zap.Errorw(bet.Bet_PROTO_BET_CALL_INVAILD,
						"GameUser", k,
						"MemberName", k_memberName,
						"BetIndex", betCall.BetIndex,
						"betCost", betCost,
						"gameRate", gameRate,
						"cost", cost,
						"Seat", betCall.Seat,
						"BetType", betCall.BetType,
					)

					// 異常資料 歸零
					betCall.BetType = 0
					betCall.Seat = 0
					cost = 0
					betCalls[idx] = betCall

					if memberName == k_memberName {
						flux.Send(bet.ActionClearBetStatus, k, k)
						errorcode.Service.Fatal(k, bet.Bet_PROTO_BET_CALL_INVAILD)
						return
					}
				}

				playerBetState[betCall.Seat][int(betCall.BetType)] += cost
				if k == a.SecWebSocketKey { //過濾掉機器人
					totalBet += cost
				}
			}

			if len(betCalls) > 0 {
				allPlayerMemberNames[int(betCalls[0].Seat)] = k_memberName
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

		var totalWin int64
		feeProfit := uint32(0)
		status := allPlayerResults[playerSeat].Status
		totalPay := uint32(allPlayerResults[playerSeat].Pay) //尚未抽水的利潤

		switch status {
		case int32(lottery_proto.Result_WIN):
			fee := lobbysettingFS.Service.Fee(a.SecWebSocketKey)
			profit := totalPay //尚未抽水的利潤
			feePercent := float64(100-fee) / math.Floor(100)
			feeProfit = uint32(math.Round(float64(profit) * feePercent)) //抽水後的利潤
			totalWin = int64(feeProfit + totalBet)

			if a.End(uint64(totalBet), 0, totalWin, gameData, gameResult) {
				if wallet.Service.WalletCategory(a.SecWebSocketKey) == wallet.CategoryHost {
					a.DeleteRefundLog()
				}
			}

		case int32(lottery_proto.Result_LOSE), int32(lottery_proto.Result_TIE): //平手或輸局
			lose := totalPay                         //輸多少
			totalWin = int64(totalBet) - int64(lose) //押注扣掉輸多少，就是只贏回多少

			if a.End(uint64(totalBet), 0, totalWin, gameData, gameResult) {
				if wallet.Service.WalletCategory(a.SecWebSocketKey) == wallet.CategoryHost {
					a.DeleteRefundLog()
				}
			}
		}

		logger.Service.Zap.Infow("ActionAccountingEnd",
			"GameRoomUuid", gameRoomUuid,
			"GameUser", a.SecWebSocketKey,
			"AccountingSn", a.Start.Sn,
			"status", status,
			"totalBet", totalBet,
			"totalPay", totalPay,
			"totalWin", totalWin,
			"feeProfit", feeProfit,
			"gameData", gameData,
			"gameResult", gameResult,
		)

	}
}

func (aFS *AccountingFS) RotationHandler(a *accounting.Accounting) {
	// do nothing
}
