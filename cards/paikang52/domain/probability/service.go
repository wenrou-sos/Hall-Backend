package probability

import (
	PSC_ON_00007_1 "52-game-server/domain/probability/PSC-ON-00007-1"
	PSCM_00007_1 "52-game-server/domain/probability/PSCM-00007-1"
	probability_proto "52-game-server/domain/probability/proto"

	"gitlab.iplaystar.net/game-server/logger"
)

const (
	EMSGID_eResult          = "EMSGID_eResult"
	EMSGID_eBroadcastResult = "EMSGID_eBroadcastResult"
)

var Service = &service{}

type service struct {
}

func (s *service) CalcSpecialCards(card []int) *SpecialProbability {
	rule, oder, oder2, pay := PSC_ON_00007_1.Deck.RuleCards(card, PSCM_00007_1.Math52.PSC_ON_00007_1)

	logger.Service.Zap.Infow("CalcSpecialCards",
		"Oder", oder,
		"Oder2", oder2,
		"Pay", pay,
		"Rule", rule,
	)

	return &SpecialProbability{
		Pay:   pay,
		Rule:  rule,
		Oder:  oder,
		Oder2: oder2,
	}
}

func (s *service) CalcCards(calc *probability_proto.PlayerData, playersResult map[string]*probability_proto.PlayerData) bool {

	for _, p := range playersResult {
		if p.Cards.SumPoint < calc.Cards.SumPoint {
			return false
		}
	}

	return true
}

func (s *service) CallCards(cards []int, card int) []int {

	var callCardArray []int

	kind := card % 13

	for _, c := range cards {
		if c%13 == kind {
			callCardArray = append(callCardArray, c)
		}
	}
	return callCardArray
}

func (s *service) PlayCards(cards, otherCards []int, logic bool) []int {
	var playCardArray []int
	cardSum := [13]int{0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}

	for _, c := range cards {
		k := c % 13
		cardSum[k] = cardSum[k] + (k + 1)
	}

	/*max := 0
	maxPoint := cardSum[0]

	for i, s := range cardSum {
		if logic {
			otherNo := true
			for _, c := range otherCards {
				if s != 0 && c%13 == i {
					otherNo = false
				}
			}
			if otherNo && s > maxPoint {
				maxPoint = s
				max = i
			}
		} else {
			if s > maxPoint {
				maxPoint = s
				max = i
			}
		}
	}*/

	max := -1
	maxPoint := 0

	if logic {
		for i, s := range cardSum {
			otherNo := true
			for _, c := range otherCards {
				if s != 0 && c%13 == i {
					otherNo = false
					break
				}
			}
			if otherNo && s > maxPoint {
				maxPoint = s
				max = i
			}
		}
	}

	if max == -1 {
		for i, s := range cardSum {
			if s > maxPoint {
				maxPoint = s
				max = i
			}
		}
	}

	for _, c := range cards {
		if c%13 == max {
			playCardArray = append(playCardArray, c)
		}
	}

	return playCardArray
}

func (s *service) CardToIndex(card int) (index int) {
	for k, v := range PSCM_00007_1.Math52.PSC_ON_00007_1.Deck {
		if v == card {
			return k
		}
	}
	panic("ERROR CARD")
}
