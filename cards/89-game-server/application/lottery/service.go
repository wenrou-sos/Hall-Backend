package lottery

import (
	"89-game-server/application/lobbysetting89"
	"89-game-server/domain/probability"
	probability_proto "89-game-server/domain/probability/proto"
	common89_proto "89-game-server/models/proto"
	"math"
	"time"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/accounting"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/wallet"
)

const (
	lose = probability_proto.Card_LOSE
	win  = probability_proto.Card_WIN
	tie  = probability_proto.Card_TIE
	fee  = 0.95
)

var Service = &service{
	Id: "LotteryService",
}

type service struct {
	Id string
}

func (s *service) Result(
	results map[string]*probability_proto.Card,
	betCent map[string]uint64,
	accountingSn map[string]uint64,
	bankerUuid, gameRoomUuid, gameRoomType string) *probability_proto.Result {

	if betCent != nil {
		time.Sleep(1 * time.Second) // for web client animation
	}

	banker := results[bankerUuid]

	logger.Service.Zap.Debugw("Result",
		"ResultsMap", results,
		"BankerUuid", bankerUuid,
		"GameRoomUuid", gameRoomUuid,
		"Banker", banker,
	)

	logger.Service.Zap.Debugw("Result",
		"betCentMap", betCent,
		"BankerUuid", bankerUuid,
		"GameRoomUuid", gameRoomUuid,
		"Banker", banker,
	)

	logger.Service.Zap.Debugw("Result",
		"AccountingSnMap", accountingSn,
		"BankerUuid", bankerUuid,
		"GameRoomUuid", gameRoomUuid,
		"Banker", banker,
	)

	data := s.eResult(gameRoomUuid)

	var bankerWinCent uint64 = 0
	var bankerLoseCent uint64 = 0

	for k, v := range results {
		isCheck := false

		if v.Seat != banker.Seat {

			if s.rule_1_2(v.Rule) && s.rule_1_2(banker.Rule) {
				v.Status = tie
				v.Cent = 0
				isCheck = true
			}

			if s.rule_3_4(v.Rule) && s.rule_3_4(banker.Rule) && !isCheck {
				v.Status = tie
				v.Cent = 0
				isCheck = true
			}

			if s.rule_48_49_50_51_52(v.Rule) && s.rule_48_49_50_51_52(banker.Rule) && !isCheck {
				switch {
				case v.SumPoint > banker.SumPoint: // player win
					v.Status = win

					// win cent cannot be bigger than wallet cent
					if v.Cent*v.Pay >= v.PlayerCent {
						bankerLoseCent += v.PlayerCent
						v.Cent = s.discount5(v.PlayerCent)
					} else {
						bankerLoseCent += v.Cent * v.Pay
						v.Cent = s.discount5(v.Cent * v.Pay)
					}

					if betCent != nil {
						wallet.Service.IncreaseCent(k, bankerUuid, v.Cent)
					}

				case v.SumPoint == banker.SumPoint:
					v.Status = tie
					v.Cent = 0

				case v.SumPoint < banker.SumPoint: // banker win
					v.Status = lose
					v.Cent = v.Cent * banker.Pay

					if v.Cent >= v.PlayerCent {
						v.Cent = v.PlayerCent
					}

					bankerWinCent += v.Cent

					if betCent != nil {
						wallet.Service.DecreaseCent(k, bankerUuid, v.Cent)
					}
				}
				isCheck = true
			}

			if !isCheck {
				switch {
				case v.Rule < banker.Rule: // player win
					v.Status = win

					// win cent cannot be bigger than wallet cent
					if v.Cent*v.Pay >= v.PlayerCent {
						bankerLoseCent += v.PlayerCent
						v.Cent = s.discount5(v.PlayerCent)
					} else {
						bankerLoseCent += v.Cent * v.Pay
						v.Cent = s.discount5(v.Cent * v.Pay)
					}

					if betCent != nil {
						wallet.Service.IncreaseCent(k, bankerUuid, v.Cent)
					}
				case v.Rule == banker.Rule && v.Suit > banker.Suit: // player win
					v.Status = win

					// win cent cannot be bigger than wallet cent
					if v.Cent*v.Pay >= v.PlayerCent {
						bankerLoseCent += v.PlayerCent
						v.Cent = s.discount5(v.PlayerCent)
					} else {
						bankerLoseCent += v.Cent * v.Pay
						v.Cent = s.discount5(v.Cent * v.Pay)
					}

					if betCent != nil {
						wallet.Service.IncreaseCent(k, bankerUuid, v.Cent)
					}
				case v.Rule == banker.Rule && v.Suit < banker.Suit: // banker win
					v.Status = lose
					v.Cent = v.Cent * banker.Pay

					if v.Cent >= v.PlayerCent {
						v.Cent = v.PlayerCent
					}

					bankerWinCent += v.Cent

					if betCent != nil {
						wallet.Service.DecreaseCent(k, bankerUuid, v.Cent)
					}
				case v.Rule == banker.Rule && v.Suit == banker.Suit:
					v.Status = tie
					v.Cent = 0

				case v.Rule > banker.Rule: // banker win
					v.Status = lose
					v.Cent = v.Cent * banker.Pay

					if v.Cent >= v.PlayerCent {
						v.Cent = v.PlayerCent
					}

					bankerWinCent += v.Cent

					if betCent != nil {
						wallet.Service.DecreaseCent(k, bankerUuid, v.Cent)
					}

				}
				isCheck = true
			}

			if betCent != nil {
				// end cent
				cent, err := wallet.Service.Cent(k)
				balance, err := wallet.Service.BalanceCache(k)

				if err != nil {
					panic("cent error") // TODO JOHNNY  壓測進來過  錢包提前關了
				}
				if lobbysetting89.Service.AutoATM(k) {
					v.PlayerCent = cent + balance
				} else {
					v.PlayerCent = cent
				}

			}

			data.Cards = append(data.Cards, v)
		}
	}

	if bankerWinCent > bankerLoseCent {
		banker.Cent = s.discount5(bankerWinCent - bankerLoseCent)
		banker.Status = win

		if betCent != nil {
			wallet.Service.IncreaseCent(bankerUuid, bankerUuid, banker.Cent)
		}
	}

	if bankerLoseCent > bankerWinCent {
		banker.Cent = bankerLoseCent - bankerWinCent
		banker.Status = lose

		if betCent != nil {
			wallet.Service.DecreaseCent(bankerUuid, bankerUuid, banker.Cent)
		}
	}

	if bankerLoseCent == bankerWinCent {
		banker.Cent = 0
		banker.Status = tie
	}

	if betCent != nil {
		// end cent
		cent, err := wallet.Service.Cent(bankerUuid)

		banker.PlayerCent = cent

		if err != nil {
			panic("cent error")
		}
	}

	data.Cards = append(data.Cards, banker)

	if betCent != nil {
		for k, v := range results {
			if sn, ok := accountingSn[k]; ok {
				logger.Service.Zap.Infow("Result",
					"GameUser", k,
					"BankerUuid", bankerUuid,
					"GameRoomUuid", gameRoomUuid,
					"AccountingSn", sn,
					"Seat", v.Seat,
					"Hand", v.Hand,
					"Point", v.SumPoint,
					"Rule", v.Rule,
					"Status", v.Status,
					"Cent", v.Cent,
					"Pay", v.Pay,
					"PlayerCent", v.PlayerCent,
				)

				// TODO JOHNNY HARD CODE
				if gameRoomType == "FRIEND_ROOM" {
					flux.Send(accounting.ActionAccountingEnd, s.Id, gameRoomUuid, results, betCent, bankerUuid, k, v.Seat, sn)
				} else {
					flux.Send(accounting.ActionAccountingEnd, s.Id, accounting.Service.HashId(k, sn), results, betCent, bankerUuid)
				}
			}
		}
		s.eBroadcastResult(data)
	}
	return data
}

func (s *service) discount5(cent uint64) uint64 {
	discountCent := uint64(math.Round(float64(cent) * fee))

	if discountCent > math.MaxUint64 {
		// TODO JOHNNY  要做錯誤處理
		panic("CENT OUT OF RANGE")
	}

	return discountCent
}

func (s *service) rule_1_2(rule int32) bool {
	switch rule {
	case 1, 2:
		return true

	default:
		return false
	}
}

func (s *service) rule_3_4(rule int32) bool {
	switch rule {
	case 3, 4:
		return true

	default:
		return false
	}
}

func (s *service) rule_48_49_50_51_52(rule int32) bool {
	switch rule {
	case 48, 49, 50, 51, 52:
		return true

	default:
		return false
	}
}

func (s *service) eResult(gameRoomUuid string) *probability_proto.Result {
	return &probability_proto.Result{
		Msgid:    common89_proto.EMSGID_eResult,
		RoomUuid: gameRoomUuid,
		Action:   probability_proto.Result_SETTLEMENT,
		Cards:    nil,
	}
}

func (s *service) eBroadcastResult(result *probability_proto.Result) {
	data := &probability_proto.BroadcastResult{
		Msgid:  common89_proto.EMSGID_eBroadcastResult,
		Result: result,
	}

	dataByte, _ := proto.Marshal(data)

	flux.Send(probability.EMSGID_eBroadcastResult, s.Id, result.RoomUuid, dataByte)
}
