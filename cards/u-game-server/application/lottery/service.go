package lottery

import (
	"sort"
	"u-game-server/application/gamesettingU"
	"u-game-server/domain/probability"
	PSC_ON_00013 "u-game-server/domain/probability/PSC-ON-00013"
	PSCM_00013 "u-game-server/domain/probability/PSCM-00013"

	"gitlab.iplaystar.net/game-server/accounting"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/wallet"

	"math"
	probability_proto "u-game-server/domain/probability/proto"
	commonU_proto "u-game-server/models/proto"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/flux"
)

var Service = &service{
	Id: "LotteryService",
}

type service struct {
	Id string
}

func (s *service) Ranking2(seat int32, playerData map[string]*probability_proto.PlayerData) {
	cardHand := make(map[int32][]int)
	cardNum := make(map[int32]int)
	ranking := make(map[int32]int32)

	for _, p1 := range playerData {
		ranking[p1.Seat] = 1
		cardNum[p1.Seat] = len(p1.Cards.Hands)
		cardHand[p1.Seat] = []int{}
		for _, c := range p1.Cards.Hands {
			point, _, _ := PSC_ON_00013.Deck.CardInfo(int(c))
			cardHand[p1.Seat] = append(cardHand[p1.Seat], point)
		}
		sort.Ints(cardHand[p1.Seat])
		for _, p2 := range playerData {
			if p1.Cards.SumPoint > p2.Cards.SumPoint {
				// order 1
				ranking[p1.Seat]++
			}
		}
	}

	for i, n1 := range cardNum {
		for j, n2 := range cardNum {
			if i == j {
				continue
			}
			if ranking[i] == ranking[j] {
				// order 2
				if n1 > n2 {
					ranking[i]++
				} else if n1 < n2 {
					ranking[j]++
				} else {
					// order 3
					for k := len(cardHand[i]) - 1; k >= 0; k-- {
						if cardHand[i][k] > cardHand[j][k] {
							ranking[i]++
							break
						} else if cardHand[i][k] < cardHand[j][k] {
							ranking[j]++
							break
						}
					}

					// order 4
					if ranking[i] == ranking[j] {
						if i == seat {
							ranking[j]++
						} else {
							ranking[i]++
						}
					}
				}
			}
		}
	}

	for _, p := range playerData {
		if v, ok := ranking[p.Seat]; ok {
			p.Rank = v
		}
	}
}

func (s *service) Ranking3(seat int32, playerData map[string]*probability_proto.PlayerData) {
	cardHand := make(map[int32][]int)
	cardNum := make(map[int32]int)
	ranking := make(map[int32]int32)

	for _, p1 := range playerData {
		ranking[p1.Seat] = 1
		cardNum[p1.Seat] = len(p1.Cards.Hands)
		cardHand[p1.Seat] = []int{}
		for _, c := range p1.Cards.Hands {
			point, _, _ := PSC_ON_00013.Deck.CardInfo(int(c))
			cardHand[p1.Seat] = append(cardHand[p1.Seat], point)
		}
		sort.Ints(cardHand[p1.Seat])
		for _, p2 := range playerData {
			if p1.Cards.SumPoint > p2.Cards.SumPoint {
				// order 1
				ranking[p1.Seat]++
			}
		}
	}

	for i, n1 := range cardNum {
		for j, n2 := range cardNum {
			if i == j {
				continue
			}
			if ranking[i] == ranking[j] {
				// order 2
				if n1 > n2 {
					ranking[i]++
				} else if n1 < n2 {
					ranking[j]++
				} else {
					// order 3
					for k := len(cardHand[i]) - 1; k >= 0; k-- {
						if cardHand[i][k] > cardHand[j][k] {
							ranking[i]++
							break
						} else if cardHand[i][k] < cardHand[j][k] {
							ranking[j]++
							break
						}
					}

					// order 4
					if ranking[i] == ranking[j] {
						if i > j {
							if i > seat && j < seat {
								ranking[j]++
							} else {
								ranking[i]++
							}
						} else {
							if j > seat && i < seat {
								ranking[i]++
							} else {
								ranking[j]++
							}
						}
					}
				}
			}
		}
	}

	for _, p := range playerData {
		if v, ok := ranking[p.Seat]; ok {
			p.Rank = v
		}
	}
}

func (s *service) Ranking4(seat int32, playerData map[string]*probability_proto.PlayerData) {
	cardHand := make(map[int32][]int)
	cardNum := make(map[int32]int)
	ranking := make(map[int32]int32)

	for _, p1 := range playerData {
		ranking[p1.Seat] = 1
		cardNum[p1.Seat] = len(p1.Cards.Hands)
		cardHand[p1.Seat] = []int{}
		for _, c := range p1.Cards.Hands {
			point, _, _ := PSC_ON_00013.Deck.CardInfo(int(c))
			cardHand[p1.Seat] = append(cardHand[p1.Seat], point)
		}
		sort.Ints(cardHand[p1.Seat])
		for _, p2 := range playerData {
			if p1.Cards.SumPoint > p2.Cards.SumPoint {
				// order 1
				ranking[p1.Seat]++
			}
		}
	}

	for i, n1 := range cardNum {
		for j, n2 := range cardNum {
			if i == j {
				continue
			}
			if ranking[i] == ranking[j] {
				// order 2
				if n1 > n2 {
					ranking[i]++
				} else if n1 < n2 {
					ranking[j]++
				} else {
					// order 3
					for k := len(cardHand[i]) - 1; k >= 0; k-- {
						if cardHand[i][k] > cardHand[j][k] {
							ranking[i]++
							break
						} else if cardHand[i][k] < cardHand[j][k] {
							ranking[j]++
							break
						}
					}

					// order 4
					if ranking[i] == ranking[j] {
						if i > j {
							if (i > seat && j < seat) || i == seat {
								ranking[j]++
							} else {
								ranking[i]++
							}
						} else {
							if j > seat && i < seat || j == seat {
								ranking[i]++
							} else {
								ranking[j]++
							}
						}
					}
				}
			}
		}
	}

	for _, p := range playerData {
		if v, ok := ranking[p.Seat]; ok {
			p.Rank = v
		}
	}
}

func (s *service) Result(
	betCent uint64,
	accountingSn map[string]uint64,
	seat int32,
	playerData map[string]*probability_proto.PlayerData,
	gameRoomUuid, gameRoomType, bankerUuid string,
	mathTest bool,
	originalSecWebSocketKey map[string]string) {

	data := s.eResult(gameRoomUuid)
	payout := 1.0
	maxWin := 1
	hasMaxWin := false
	hasBankruptcy := false

	if seat != -1 {
		switch len(playerData) {
		case 2:
			s.Ranking2(seat, playerData)
			payout, maxWin, hasMaxWin, hasBankruptcy = s.Result2(betCent, playerData)
		case 3:
			s.Ranking3(seat, playerData)
			payout, maxWin, hasMaxWin, hasBankruptcy = s.Result3(betCent, playerData)
		case 4:
			s.Ranking4(seat, playerData)
			payout, maxWin, hasMaxWin, hasBankruptcy = s.Result4(betCent, playerData)
		}

		if mathTest {
			return
		}

		if hasMaxWin && len(playerData) == 4 {
			var pd [4]*probability_proto.PlayerData
			for _, p := range playerData {
				pd[p.Rank-1] = p
			}
			pd[0].AllScore = int64(math.Round(float64(pd[0].AllScore) * payout))
			pd[1].AllScore = int64(math.Round(float64(pd[1].AllScore) * payout))
			pd[2].AllScore = int64(math.Round(float64(pd[2].AllScore) * payout))
			pd[3].AllScore = -(pd[0].AllScore + pd[1].AllScore + pd[2].AllScore)
		} else if hasBankruptcy && len(playerData) == 4 {
			var pd [4]*probability_proto.PlayerData
			for _, p := range playerData {
				pd[p.Rank-1] = p
			}
			pd[1].AllScore = int64(math.Round(float64(pd[1].AllScore) * payout))
			pd[2].AllScore = int64(math.Round(float64(pd[2].AllScore) * payout))
			pd[3].AllScore = int64(math.Round(float64(pd[3].AllScore) * payout))
			pd[0].AllScore = -(pd[1].AllScore + pd[2].AllScore + pd[3].AllScore)
		} else {
			for _, p := range playerData {
				p.AllScore = int64(math.Round(float64(p.AllScore) * payout))
			}
		}

		originalAllScore := make(map[string]uint64)
		for k, p := range playerData {
			fee := gamesettingU.Service.Fee(k)
			p.MaxWin = 0
			if p.AllScore >= 0 {
				p.AllWin = 1
				if p.AllScore >= int64(p.Cent)*int64(maxWin) {
					p.AllScore = int64(p.Cent) * int64(maxWin)
					p.MaxWin = 1
				}
				originalAllScore[k] = uint64(p.AllScore)
				p.AllScore = int64(math.Floor(float64(p.AllScore * int64(100-fee) / 100)))
				p.Cent += uint64(p.AllScore)
				wallet.Service.IncreaseCent(k, k, uint64(p.AllScore))
			} else {
				p.AllWin = 0
				p.AllScore = int64(math.Abs(float64(p.AllScore)))
				originalAllScore[k] = uint64(p.AllScore)
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
		for k := range playerData {
			originalKey := k
			if key, ok := originalSecWebSocketKey[k]; ok {
				originalKey = key
			}
			var betamt, winamt, asn uint64
			if sn, ok := accountingSn[originalKey]; ok {
				player := playerData[k]
				switch player.AllWin {
				case 0:
					betamt = originalAllScore[k]
					winamt = 0
				case 1:
					betamt = originalAllScore[k]
					winamt = betamt + uint64(player.AllScore)
				}
				asn = sn

				flux.Send(accounting.ActionAccountingEnd, s.Id, accounting.Service.HashId(originalKey, sn), playerData, betCent, data.Bankruptcy, bankerUuid, k, betamt, winamt)
			}
			if wallet.Service.WalletCategory(k) == wallet.CategoryHost {
				cent, _ := wallet.Service.Cent(k)
				if cent > 0 {
					wallet.Service.Withdraw(k, asn, cent, betamt, winamt)
				}
			}
		}
	} else {
		for k := range playerData {
			originalKey := k
			if key, ok := originalSecWebSocketKey[k]; ok {
				originalKey = key
			}
			if sn, ok := accountingSn[originalKey]; ok {
				if wallet.Service.WalletCategory(k) == wallet.CategoryHost {
					wallet.Service.Refund(k, sn, true)
				} else {
					cent, _ := wallet.Service.Cent(k)
					wallet.Service.Withdraw(k, sn, cent, 0, 0)
				}
			}
		}
	}

	s.eBroadcastResult(data)
}

func (s *service) Result2(betCent uint64, playerData map[string]*probability_proto.PlayerData) (payout float64, maxWin int, hasMaxWin, hasBankruptcy bool) {
	level := 0
	payout = 1.0
	extraPay := make(map[int32]int)
	totalExtra := 0
	for _, p := range playerData {
		extraPay[p.Seat] = 0

		if p.Rank == 2 {
			base := PSCM_00013.MathU.PSC_ON_00013.Pay2[level][p.Rank-1]
			if int(p.Cards.SumPoint) > base {
				extraPay[p.Seat] = int(p.Cards.SumPoint) - base
				totalExtra += int(p.Cards.SumPoint) - base
			}
		}
	}

	for _, p := range playerData {
		if p.Rank == 1 {
			extraPay[p.Seat] += totalExtra
		}
	}

	hasMaxWin = false
	hasBankruptcy = false
	for _, p := range playerData {
		score := int64(PSCM_00013.MathU.PSC_ON_00013.Pay2[level][p.Rank-1]+extraPay[p.Seat]) * int64(betCent)

		if p.Rank == 1 {
			p.AllScore += score
		} else {
			p.AllScore -= score
		}

		maxWinCent := int64(p.Cent) * int64(PSCM_00013.MathU.PSC_ON_00013.MaxWin[0])
		if int64(p.Cent)+p.AllScore < 0 {
			newPayout := math.Abs(float64(p.Cent)) / math.Abs(float64(p.AllScore))
			if newPayout < payout {
				payout = newPayout
				hasBankruptcy = true
				hasMaxWin = false
			}
		} else if p.AllScore > maxWinCent {
			newPayout := math.Abs(float64(maxWinCent)) / math.Abs(float64(p.AllScore))
			if newPayout < payout {
				payout = newPayout
				hasMaxWin = true
				hasBankruptcy = false
			}
		}
	}

	return payout, PSCM_00013.MathU.PSC_ON_00013.MaxWin[0], hasMaxWin, hasBankruptcy
}

func (s *service) Result3(betCent uint64, playerData map[string]*probability_proto.PlayerData) (payout float64, maxWin int, hasMaxWin, hasBankruptcy bool) {
	level := 0
	payout = 1.0
	extraPay := make(map[int32]int)
	totalExtra := 0
	for _, p := range playerData {
		extraPay[p.Seat] = 0

		if p.Rank == 2 || p.Rank == 3 {
			base := PSCM_00013.MathU.PSC_ON_00013.Pay3[level][p.Rank-1]
			if int(p.Cards.SumPoint) > base {
				extraPay[p.Seat] = int(p.Cards.SumPoint) - base
				totalExtra += int(p.Cards.SumPoint) - base
			}
		}
	}

	for _, p := range playerData {
		if p.Rank == 1 {
			extraPay[p.Seat] += totalExtra
		}
	}

	hasMaxWin = false
	hasBankruptcy = false
	for _, p := range playerData {
		score := int64(PSCM_00013.MathU.PSC_ON_00013.Pay3[level][p.Rank-1]+extraPay[p.Seat]) * int64(betCent)

		if p.Rank == 1 {
			p.AllScore += score
		} else {
			p.AllScore -= score
		}

		maxWinCent := int64(p.Cent) * int64(PSCM_00013.MathU.PSC_ON_00013.MaxWin[1])
		if int64(p.Cent)+p.AllScore < 0 {
			newPayout := math.Abs(float64(p.Cent)) / math.Abs(float64(p.AllScore))
			if newPayout < payout {
				payout = newPayout
				hasBankruptcy = true
				hasMaxWin = false
			}
		} else if p.AllScore > maxWinCent {
			newPayout := math.Abs(float64(maxWinCent)) / math.Abs(float64(p.AllScore))
			if newPayout < payout {
				payout = newPayout
				hasMaxWin = true
				hasBankruptcy = false
			}
		}
	}

	return payout, PSCM_00013.MathU.PSC_ON_00013.MaxWin[1], hasMaxWin, hasBankruptcy
}

func (s *service) Result4(betCent uint64, playerData map[string]*probability_proto.PlayerData) (payout float64, maxWin int, hasMaxWin, hasBankruptcy bool) {
	var first int32 = 0
	var second int32 = 0
	for _, p := range playerData {
		if p.Rank == 1 {
			first = p.Cards.SumPoint
		} else if p.Rank == 2 {
			second = p.Cards.SumPoint
		}
	}

	level := -1
	if offset := int(second - first); offset <= PSCM_00013.MathU.PSC_ON_00013.LevelOffset[0] {
		level = 0
	} else if offset <= PSCM_00013.MathU.PSC_ON_00013.LevelOffset[1] {
		level = 1
	} else if offset <= PSCM_00013.MathU.PSC_ON_00013.LevelOffset[2] {
		level = 2
	} else if offset <= PSCM_00013.MathU.PSC_ON_00013.LevelOffset[3] {
		level = 3
	} else {
		level = 4
	}

	payout = 1.0
	extraPay := make(map[int32]int)
	totalExtra := 0
	for _, p := range playerData {
		extraPay[p.Seat] = 0

		if p.Rank == 3 || p.Rank == 4 {
			base := PSCM_00013.MathU.PSC_ON_00013.Pay4[level][p.Rank-1]
			if int(p.Cards.SumPoint) > base {
				extraPay[p.Seat] = int(p.Cards.SumPoint) - base
				totalExtra += int(p.Cards.SumPoint) - base
			}
		}
	}

	for _, p := range playerData {
		if p.Rank == 1 {
			extraPay[p.Seat] += totalExtra - (totalExtra / 2)
		} else if p.Rank == 2 {
			extraPay[p.Seat] += totalExtra / 2
		}
	}

	hasMaxWin = false
	hasBankruptcy = false
	for _, p := range playerData {
		score := int64(PSCM_00013.MathU.PSC_ON_00013.Pay4[level][p.Rank-1]+extraPay[p.Seat]) * int64(betCent)

		if p.Rank == 1 || p.Rank == 2 {
			p.AllScore += score
		} else {
			p.AllScore -= score
		}

		maxWinCent := int64(p.Cent) * int64(PSCM_00013.MathU.PSC_ON_00013.MaxWin[2])
		if int64(p.Cent)+p.AllScore < 0 {
			newPayout := math.Abs(float64(p.Cent)) / math.Abs(float64(p.AllScore))
			if newPayout < payout {
				payout = newPayout
				hasBankruptcy = true
				hasMaxWin = false
			}
		} else if p.AllScore > maxWinCent {
			newPayout := math.Abs(float64(maxWinCent)) / math.Abs(float64(p.AllScore))
			if newPayout < payout {
				payout = newPayout
				hasMaxWin = true
				hasBankruptcy = false
			}
		}
	}

	return payout, PSCM_00013.MathU.PSC_ON_00013.MaxWin[2], hasMaxWin, hasBankruptcy
}

func (s *service) eResult(gameRoomUuid string) *probability_proto.Result {
	return &probability_proto.Result{
		Msgid:      commonU_proto.EMSGID_eResult,
		RoomUuid:   gameRoomUuid,
		PlayerData: nil,
		Charge:     5,
		Bankruptcy: make([]int32, 0),
	}
}

func (s *service) eBroadcastResult(result *probability_proto.Result) {
	data := &probability_proto.BroadcastResult{
		Msgid:  commonU_proto.EMSGID_eBroadcastResult,
		Result: result,
	}

	flux.Send(probability.EMSGID_eBroadcastResult, s.Id, result.RoomUuid, data)
}

func (s *service) BroadcastRanking(roomUuid string, playerData map[string]*probability_proto.PlayerData, rankingType int32) {
	data := &probability_proto.BroadcastRanking{
		Msgid:      commonU_proto.EMSGID_eBroadcastRanking,
		PlayerData: make([]*probability_proto.PlayerData, 0),
		Type:       rankingType,
	}
	for _, p := range playerData {
		d := &probability_proto.PlayerData{
			Seat:        p.Seat,
			PokerNumber: p.PokerNumber,
			Cent:        p.Cent,
			Rank:        p.Rank,
		}
		data.PlayerData = append(data.PlayerData, d)
	}
	dataByte, _ := proto.Marshal(data)
	flux.Send(probability.EMSGID_eBroadcastRanking, s.Id, roomUuid, dataByte)
}
