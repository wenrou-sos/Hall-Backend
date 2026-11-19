package accounting52

import (
	"52-game-server/application/gamesetting52"
	probability_proto "52-game-server/domain/probability/proto"
	"fmt"
	"math"
	"strconv"
	"strings"

	"gitlab.iplaystar.net/game-server/accounting"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/wallet"
)

type Accounting52 struct {
}

func (a52 *Accounting52) FluxActionHandler(action *flux.Action, a *accounting.Accounting, isOk chan bool) {
	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:
		isOk <- true

	case accounting.ActionAccountingStop:
		// do nothing

	case accounting.ActionAccountingDelete:
		//refundbet功能未開啟
		//if wallet.Service.WalletCategory(a.SecWebSocketKey) == wallet.CategoryHost {
		//	a.DeleteRefundLog()
		//}
		a.Delete()

	case accounting.ActionAccountingEnd:

		results := action.Payload()[0].(map[string]*probability_proto.PlayerData)
		//betCent := action.Payload()[1].(uint64)
		bankruptcy := action.Payload()[2].([]int32)
		newSecWebSocketKey := action.Payload()[3].(string)
		betamt := action.Payload()[4].(uint64)
		winamt := action.Payload()[5].(uint64)

		player := results[newSecWebSocketKey]

		playerGameResult := a52.ResultString(player, bankruptcy, wallet.Service.MemberName(newSecWebSocketKey), gamesetting52.Service.HostId(newSecWebSocketKey), gamesetting52.Service.Bet(newSecWebSocketKey))

		// Replace GameResult Cent
		playerGameResultArr := strings.Split(playerGameResult, "/")
		var end_cent uint64 = a.Start.InitCent - betamt + winamt
		playerGameResultArr[9] = strconv.FormatUint(uint64(end_cent), 10)
		playerGameResult = strings.Join(playerGameResultArr, "/")

		gameResult := fmt.Sprintf("%s", playerGameResult)

		gameData0, gameData1, gameData2, gameData3, gameData4 := "", "", "", "", ""

		for k, v := range results {
			if k != newSecWebSocketKey {
				name := wallet.Service.MemberName(k)
				hostId := gamesetting52.Service.HostId(k)
				if k == wallet.Service.MemberId(k) {
					hostId = "BOT"
				}
				bet := gamesetting52.Service.Bet(k)
				switch v.Seat {
				case 0:
					gameData0 = a52.ResultString(v, bankruptcy, name, hostId, bet)

				case 1:
					gameData1 = a52.ResultString(v, bankruptcy, name, hostId, bet)

				case 2:
					gameData2 = a52.ResultString(v, bankruptcy, name, hostId, bet)

				case 3:
					gameData3 = a52.ResultString(v, bankruptcy, name, hostId, bet)

				case 4:
					gameData4 = a52.ResultString(v, bankruptcy, name, hostId, bet)
				}
			}
		}

		gameData := ""

		switch {
		case gameData0 == "":
			gameData = fmt.Sprintf("%s", gameData1+"|"+gameData2+"|"+gameData3+"|"+gameData4)

		case gameData1 == "":
			gameData = fmt.Sprintf("%s", gameData2+"|"+gameData3+"|"+gameData4+"|"+gameData0)

		case gameData2 == "":
			gameData = fmt.Sprintf("%s", gameData3+"|"+gameData4+"|"+gameData0+"|"+gameData1)

		case gameData3 == "":
			gameData = fmt.Sprintf("%s", gameData4+"|"+gameData0+"|"+gameData1+"|"+gameData2)

		case gameData4 == "":
			gameData = fmt.Sprintf("%s", gameData0+"|"+gameData1+"|"+gameData2+"|"+gameData3)
		}

		a.End(betamt, 0, int64(winamt), 0, gameData, gameResult)

	}
}

func (a52 *Accounting52) RotationHandler(a *accounting.Accounting) {
	// do nothing
}
func (a52 *Accounting52) ResultString(result *probability_proto.PlayerData, bankruptcy []int32, name, hostId string, bet uint32) string {
	var s []string
	var handS []string
	var hitWinCardS []string
	var hitLoseCardS []string
	isBankruptcy := 0
	isShowDownWin := 0

	for _, h := range result.Cards.Hands {
		handS = append(handS, strconv.Itoa(int(h)))
	}
	for _, hc := range result.HitWinCards {
		var cardS []string
		for _, c := range hc.Cards {
			cardS = append(cardS, strconv.Itoa(int(c)))
		}
		hitWinCardS = append(hitWinCardS, "["+strings.Join(cardS, ",")+"]")
	}
	for _, hc := range result.HitLoseCards {
		var cardS []string
		for _, c := range hc.Cards {
			cardS = append(cardS, strconv.Itoa(int(c)))
		}
		hitLoseCardS = append(hitLoseCardS, "["+strings.Join(cardS, ",")+"]")
	}
	for _, v := range bankruptcy {
		if v == result.Seat {
			isBankruptcy = 1
			break
		}
	}
	if result.ShowdownScore > 0 {
		isShowDownWin = 1
	}
	s = append(s, name)
	s = append(s, strconv.Itoa(isBankruptcy))
	s = append(s, strconv.Itoa(int(result.HitWin)))
	s = append(s, strings.Join(hitWinCardS, ","))
	s = append(s, strconv.Itoa(int(result.HitLose)))
	s = append(s, strings.Join(hitLoseCardS, ","))
	s = append(s, strconv.Itoa(isShowDownWin))
	s = append(s, strconv.Itoa(int(math.Abs(float64(result.ShowdownScore)))))
	s = append(s, strings.Join(handS, ","))
	s = append(s, strconv.Itoa(int(result.Cent)))
	s = append(s, strconv.Itoa(int(result.AllWin)))
	s = append(s, strconv.Itoa(int(result.AllScore)))
	s = append(s, hostId)
	s = append(s, strconv.Itoa(int(bet)))
	return strings.Join(s, "/")
}
