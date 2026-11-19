package lottery

import (
	"52-game-server/domain/probability"
	"crypto/rand"
	"math/big"

	"52-game-server/application/gamesetting52"
	PSCM_00007_1 "52-game-server/domain/probability/PSCM-00007-1"
	probability_proto "52-game-server/domain/probability/proto"
	common52_proto "52-game-server/models/proto"
	"math"

	"gitlab.iplaystar.net/game-server/accounting"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/wallet"
)

const (
	NORMAL_WIN    = "NORMAL_WIN"
	PLAY_CARD_WIN = "PLAY_CARD_WIN"
	CALL_CARD_WIN = "CALL_CARD_WIN"
)

var Service = &service{
	Id: "LotteryService",
}

type service struct {
	Id string
}

func (s *service) Result(
	firstRound bool,
	betCent uint64,
	accountingSn map[string]uint64,
	secWebSocketKey string,
	playersResult map[string]*probability_proto.PlayerData,
	gameRoomUuid, gameRoomType, winType string,
	hitSeat int32,
	originalSecWebSocketKey map[string]string) *probability_proto.Result {

	payout := 1.0

	win := false
	nextStartSeat := -1
	winner := make(map[string]string)
	data := s.eResult(gameRoomUuid)

	originalAllScore := make(map[string]uint64)
	if secWebSocketKey != "" {
		calcPlayer := playersResult[secWebSocketKey]
		calcPlayer.ChangeScore = 0
		win = probability.Service.CalcCards(calcPlayer, playersResult)
		if win {
			for _, player := range playersResult {
				if calcPlayer.Seat != player.Seat {
					var score int64
					switch winType {
					case NORMAL_WIN:
						if firstRound {
							score = int64(PSCM_00007_1.Math52.PSC_ON_00007_1.ComparingPay[1]) * int64(betCent)
						} else {
							score = int64(PSCM_00007_1.Math52.PSC_ON_00007_1.ComparingPay[2]) * int64(betCent)
						}

					case PLAY_CARD_WIN:
						score = int64(PSCM_00007_1.Math52.PSC_ON_00007_1.ComparingPay[0]) * int64(betCent)

					case CALL_CARD_WIN:
						if hitSeat == player.Seat {
							score = int64(PSCM_00007_1.Math52.PSC_ON_00007_1.ComparingPay[0]) * int64(betCent)
						} else {
							score = int64(PSCM_00007_1.Math52.PSC_ON_00007_1.ComparingPay[2]) * int64(betCent)
						}

					default:
						panic("ERROR WIN TYPE")
					}

					calcPlayer.AllScore += score
					calcPlayer.ChangeWin = 1
					calcPlayer.ChangeScore += uint64(score)
					calcPlayer.ShowdownScore += score
					player.AllScore -= score
					player.ChangeWin = 0
					player.ChangeScore = uint64(score)
					player.ShowdownScore -= score
					if int64(player.Cent)+player.AllScore < 0 {
						p := math.Abs(float64(player.Cent)) / math.Abs(float64(player.AllScore))
						if p < payout {
							payout = p
						}
					}
				}
			}
		} else {
			for _, player := range playersResult {
				if calcPlayer.Seat != player.Seat {
					var score int64
					if firstRound {
						if player.Cards.SumPoint < calcPlayer.Cards.SumPoint {
							score = int64(PSCM_00007_1.Math52.PSC_ON_00007_1.ComparingPay[0]) * int64(betCent)
						} else {
							score = int64(PSCM_00007_1.Math52.PSC_ON_00007_1.ComparingPay[1]) * int64(betCent)
						}
					} else {
						if player.Cards.SumPoint < calcPlayer.Cards.SumPoint {
							score = int64(PSCM_00007_1.Math52.PSC_ON_00007_1.ComparingPay[1]) * int64(betCent)
						} else {
							score = int64(PSCM_00007_1.Math52.PSC_ON_00007_1.ComparingPay[2]) * int64(betCent)
						}
					}
					calcPlayer.AllScore -= score
					calcPlayer.ChangeWin = 0
					calcPlayer.ChangeScore += uint64(score)
					calcPlayer.ShowdownScore -= score
					player.AllScore += score
					player.ChangeWin = 1
					player.ChangeScore = uint64(score)
					player.ShowdownScore += score
				}
			}

			if int64(calcPlayer.Cent)+calcPlayer.AllScore < 0 {
				p := math.Abs(float64(calcPlayer.Cent)) / math.Abs(float64(calcPlayer.AllScore))
				if p < payout {
					payout = p
				}
			}
		}

		sumPoint := 100
		for k, p := range playersResult {
			fee := gamesetting52.Service.Fee(k)
			p.AllScore = int64(float64(p.AllScore) * payout)
			originalAllScore[k] = uint64(math.Abs(float64(p.AllScore)))
			if p.AllScore >= 0 {
				if sumPoint > int(p.Cards.SumPoint) {
					sumPoint = int(p.Cards.SumPoint)
					nextStartSeat = int(p.Seat)
				} else if sumPoint == int(p.Cards.SumPoint) {
					if n, err := rand.Int(rand.Reader, big.NewInt(2)); err == nil {
						if n.Uint64() == 0 {
							nextStartSeat = int(p.Seat)
						}
					} else {
						panic(err)
					}
				}
				winner[k] = k
				p.AllWin = 1
				p.AllScore = int64(math.Floor(float64(p.AllScore * int64(100-fee) / 100)))
				p.Cent += uint64(p.AllScore)
				wallet.Service.IncreaseCent(k, k, uint64(p.AllScore))
			} else {
				p.AllWin = 0
				p.AllScore = int64(math.Abs(float64(p.AllScore)))
				p.Cent -= uint64(p.AllScore)
				wallet.Service.DecreaseCent(k, k, uint64(p.AllScore))
				if p.Cent == 0 {
					data.Bankruptcy = append(data.Bankruptcy, p.Seat)
				}
			}
			data.PlayerData = append(data.PlayerData, p)

			logger.Service.Zap.Infow("Result",
				"GameUser", k,
				"GameRoomUuid", gameRoomUuid,
				"p", p,
			)
		}
	}

	for k := range playersResult {
		originalKey := k
		if key, ok := originalSecWebSocketKey[k]; ok {
			originalKey = key
		}
		var betamt, winamt, asn uint64
		if sn, ok := accountingSn[originalKey]; ok {
			player := playersResult[k]
			switch player.AllWin {
			case 0:
				betamt = originalAllScore[k]
				winamt = 0
			case 1:
				betamt = originalAllScore[k]
				winamt = betamt + uint64(player.AllScore)
			}
			asn = sn

			flux.Send(accounting.ActionAccountingEnd, s.Id, accounting.Service.HashId(originalKey, sn), playersResult, betCent, data.Bankruptcy, k, betamt, winamt)
		}
		if wallet.Service.WalletCategory(k) == wallet.CategoryHost {
			cent, _ := wallet.Service.Cent(k)
			wallet.Service.Withdraw(k, asn, cent, betamt, winamt)
		}
	}
	s.eBroadcastResult(data, winner, nextStartSeat)
	return data
}

func (s *service) EndResult(
	betCent uint64,
	accountingSn map[string]uint64,
	playersResult map[string]*probability_proto.PlayerData,
	gameRoomUuid, gameRoomType string,
	originalSecWebSocketKey map[string]string) *probability_proto.Result {

	payout := 1.0
	score := int64(PSCM_00007_1.Math52.PSC_ON_00007_1.ComparingPay[2]) * int64(betCent)
	var winPlayerCount int64 = 0
	var totalLoseScore int64 = 0
	var smallestSum int32 = 50

	data := s.eResult(gameRoomUuid)

	for _, player := range playersResult {
		if player.Cards.SumPoint < smallestSum {
			smallestSum = player.Cards.SumPoint
		}
	}

	for _, player := range playersResult {
		if player.Cards.SumPoint > smallestSum {
			player.AllScore -= score
			player.ChangeWin = 0
			player.ChangeScore = uint64(score)
			player.ShowdownScore -= score
			totalLoseScore += score
			if int64(player.Cent)+player.AllScore < 0 {
				p := math.Abs(float64(player.Cent)) / math.Abs(float64(player.AllScore))
				if p < payout {
					payout = p
				}
			}
		} else {
			winPlayerCount++
		}
	}

	winScore := math.Floor(float64(totalLoseScore) / float64(winPlayerCount))
	for _, player := range playersResult {
		if player.Cards.SumPoint == smallestSum {
			player.AllScore += int64(winScore)
			player.ChangeWin = 1
			player.ChangeScore = uint64(winScore)
			player.ShowdownScore += int64(winScore)
		}
	}

	sumPoint := 100
	nextStartSeat := -1
	winner := make(map[string]string)
	originalAllScore := make(map[string]uint64)
	for k, p := range playersResult {
		fee := gamesetting52.Service.Fee(k)
		p.AllScore = int64(float64(p.AllScore) * payout)
		originalAllScore[k] = uint64(math.Abs(float64(p.AllScore)))
		if p.AllScore >= 0 {
			if sumPoint > int(p.Cards.SumPoint) {
				sumPoint = int(p.Cards.SumPoint)
				nextStartSeat = int(p.Seat)
			} else if sumPoint == int(p.Cards.SumPoint) {
				if n, err := rand.Int(rand.Reader, big.NewInt(2)); err == nil {
					if n.Uint64() == 0 {
						nextStartSeat = int(p.Seat)
					}
				} else {
					panic(err)
				}
			}
			winner[k] = k
			p.AllWin = 1
			p.AllScore = int64(math.Floor(float64(p.AllScore * int64(100-fee) / 100)))
			p.Cent += uint64(p.AllScore)
			wallet.Service.IncreaseCent(k, k, uint64(p.AllScore))
		} else {
			p.AllWin = 0
			p.AllScore = int64(math.Abs(float64(p.AllScore)))
			p.Cent -= uint64(p.AllScore)
			wallet.Service.DecreaseCent(k, k, uint64(p.AllScore))
			if p.Cent == 0 {
				data.Bankruptcy = append(data.Bankruptcy, p.Seat)
			}
		}
		data.PlayerData = append(data.PlayerData, p)

		logger.Service.Zap.Infow("Result",
			"GameUser", k,
			"GameRoomUuid", gameRoomUuid,
			"p", p,
		)
	}
	for k := range playersResult {
		originalKey := k
		if key, ok := originalSecWebSocketKey[k]; ok {
			originalKey = key
		}
		var betamt, winamt, asn uint64
		if sn, ok := accountingSn[originalKey]; ok {
			player := playersResult[k]
			switch player.AllWin {
			case 0:
				betamt = originalAllScore[k]
				winamt = 0
			case 1:
				betamt = originalAllScore[k]
				winamt = betamt + uint64(player.AllScore)
			}
			asn = sn

			flux.Send(accounting.ActionAccountingEnd, s.Id, accounting.Service.HashId(originalKey, sn), playersResult, betCent, data.Bankruptcy, k, betamt, winamt)
		}
		if wallet.Service.WalletCategory(k) == wallet.CategoryHost {
			cent, _ := wallet.Service.Cent(k)
			wallet.Service.Withdraw(k, asn, cent, betamt, winamt)
		}
	}
	s.eBroadcastResult(data, winner, nextStartSeat)
	return data
}

func (s *service) SpecialResult(
	betCent uint64,
	accountingSn map[string]uint64,
	playersResult map[string]*probability_proto.PlayerData,
	gameRoomUuid, gameRoomType string,
	originalSecWebSocketKey map[string]string) *probability_proto.Result {

	payout := 1.0
	data := s.eResult(gameRoomUuid)

	var specialCalc []*probability_proto.PlayerData
	for _, p := range playersResult {
		sp := probability.Service.CalcSpecialCards(ToIntArr(p.Cards.Hands))
		if sp.Rule > 0 {
			specialCalc = append(specialCalc, p)
			p.Rule = int32(sp.Rule)
		}
	}
	if len(specialCalc) == 0 {
		return nil
	}
	index := 0
	if len(specialCalc) >= 1 {
		rule := 0
		for i, p := range specialCalc {
			sp := probability.Service.CalcSpecialCards(ToIntArr(p.Cards.Hands))
			if sp.Rule > rule {
				index = i
				rule = sp.Rule
			}
			if sp.Rule == rule {
				scle := specialCalc[index]
				ssp := probability.Service.CalcSpecialCards(ToIntArr(scle.Cards.Hands))
				if sp.Oder > ssp.Oder {
					index = i
					rule = sp.Rule
				}
				if sp.Oder == ssp.Oder {
					if sp.Oder2 > ssp.Oder2 {
						index = i
						rule = sp.Rule
					}
				}
			}
		}
	}
	scle := specialCalc[index]
	sp := probability.Service.CalcSpecialCards(ToIntArr(scle.Cards.Hands))
	score := int64(betCent) * int64(sp.Pay)
	for _, player := range playersResult {
		if player.Seat != scle.Seat {
			scle.AllScore += score
			scle.ChangeScore += uint64(score)
			scle.ShowdownScore += score
			player.AllScore -= score
			player.ChangeScore = uint64(score)
			player.ShowdownScore -= score
			if int64(player.Cent)+player.AllScore < 0 {
				p := math.Abs(float64(player.Cent)) / math.Abs(float64(player.AllScore))
				if p < payout {
					payout = p
				}
			}
		}
	}

	winner := make(map[string]string)
	nextStartSeat := -1
	originalAllScore := make(map[string]uint64)
	for k, p := range playersResult {
		fee := gamesetting52.Service.Fee(k)
		p.AllScore = int64(float64(p.AllScore) * payout)
		originalAllScore[k] = uint64(math.Abs(float64(p.AllScore)))
		if p.AllScore >= 0 {
			winner[k] = k
			nextStartSeat = int(p.Seat)
			p.ChangeWin = 1
			p.AllWin = 1
			p.AllScore = int64(math.Floor(float64(p.AllScore * int64(100-fee) / 100)))
			p.Cent += uint64(p.AllScore)
			wallet.Service.IncreaseCent(k, k, uint64(p.AllScore))
		} else {
			p.ChangeWin = 0
			p.AllWin = 0
			p.AllScore = int64(math.Abs(float64(p.AllScore)))
			p.Cent -= uint64(p.AllScore)
			wallet.Service.DecreaseCent(k, k, uint64(p.AllScore))
			if p.Cent == 0 {
				data.Bankruptcy = append(data.Bankruptcy, p.Seat)
			}
		}
		data.PlayerData = append(data.PlayerData, p)
		logger.Service.Zap.Infow("Special Result",
			"GameUser", k,
			"GameRoomUuid", gameRoomUuid,
			"p", p,
		)
	}
	for k := range playersResult {
		originalKey := k
		if key, ok := originalSecWebSocketKey[k]; ok {
			originalKey = key
		}
		var betamt, winamt, asn uint64
		if sn, ok := accountingSn[originalKey]; ok {
			player := playersResult[k]
			switch player.AllWin {
			case 0:
				betamt = originalAllScore[k]
				winamt = 0
			case 1:
				betamt = originalAllScore[k]
				winamt = betamt + uint64(player.AllScore)
			}
			asn = sn

			flux.Send(accounting.ActionAccountingEnd, s.Id, accounting.Service.HashId(originalKey, sn), playersResult, betCent, data.Bankruptcy, k, betamt, winamt)
		}
		if wallet.Service.WalletCategory(k) == wallet.CategoryHost {
			cent, _ := wallet.Service.Cent(k)
			wallet.Service.Withdraw(k, asn, cent, betamt, winamt)
		}
	}
	s.eBroadcastResult(data, winner, nextStartSeat)
	return data
}

func (s *service) eResult(gameRoomUuid string) *probability_proto.Result {
	return &probability_proto.Result{
		Msgid:      common52_proto.EMSGID_eResult,
		RoomUuid:   gameRoomUuid,
		PlayerData: nil,
		Charge:     5,
		Bankruptcy: make([]int32, 0),
	}
}

func (s *service) eBroadcastResult(result *probability_proto.Result, winner map[string]string, nextStartSeat int) {
	data := &probability_proto.BroadcastResult{
		Msgid:  common52_proto.EMSGID_eBroadcastResult,
		Result: result,
	}

	flux.Send(probability.EMSGID_eBroadcastResult, s.Id, result.RoomUuid, data, winner, nextStartSeat)
}

func (s *service) ShowDownLogic(firstRound bool, seat int32, playersResult map[string]*probability_proto.PlayerData, logicLevel []int) bool {
	var sum int32 = 0
	isSmallest := true

	for _, p := range playersResult {
		if p.Seat == seat {
			sum = p.Cards.SumPoint
		}
	}

	for _, p := range playersResult {
		if p.Seat == seat {
			continue
		}
		if sum >= p.Cards.SumPoint {
			isSmallest = false
		}
	}

	if n, err := rand.Int(rand.Reader, big.NewInt(100)); err == nil {
		if n.Uint64() < uint64(logicLevel[1]) {
			if !isSmallest {
				return false
			}
			if firstRound {
				if sum <= int32(logicLevel[2]) {
					return true
				}
			} else {
				if sum <= int32(logicLevel[3]) {
					return true
				}
			}
			return false
		} else {
			if firstRound {
				if sum <= int32(logicLevel[4]) {
					return true
				}
			} else {
				if sum <= int32(logicLevel[5]) {
					return true
				}
			}
			return false
		}
	} else {
		panic(err)
	}
	return false
}

func (s *service) PlayCardLogic(seat int32, playersResult map[string]*probability_proto.PlayerData, logicLevel []int) bool {
	var cards []int32
	var otherCards []int32
	for _, p := range playersResult {
		if p.Seat == seat {
			cards = p.Cards.Hands
		} else if p.Seat == (seat+1)%int32(len(playersResult)) {
			otherCards = p.Cards.Hands
		}
	}
	var isSameCards = func() bool {
		var same []bool
		sameCount := 0
		for _, c := range cards {
			for _, oc := range otherCards {
				if c%13 == oc%13 {
					same = append(same, true)
					break
				}
			}
		}
		for _, s := range same {
			if s == true {
				sameCount++
			}
		}
		if sameCount == len(cards) {
			return true
		}
		return false
	}

	if isSameCards() {
		return false
	}

	if n, err := rand.Int(rand.Reader, big.NewInt(100)); err == nil {
		if n.Uint64() < uint64(logicLevel[0]) {
			return true
		} else {
			return false
		}
	} else {
		panic(err)
	}
}

func ToIntArr(array []int32) []int {
	var arr []int
	for _, c := range array {
		arr = append(arr, int(c))
	}
	return arr
}

func (s *service) DrawCardLogic(data *probability_proto.PlayerData, cards []int) int {
	var cardList [13]bool
	for _, c := range data.Cards.Hands {
		cardList[c%13] = true
	}

	maxCard := -1
	maxIndex := -1
	for i, c := range cards {
		if !cardList[c%13] && c%13 > maxCard {
			maxCard = c % 13
			maxIndex = i
		}
	}

	if maxIndex == -1 {
		return 0
	}
	return maxIndex
}
