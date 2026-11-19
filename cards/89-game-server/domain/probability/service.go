package probability

import (
	PSC_ON_00001_1 "89-game-server/domain/probability/PSC-ON-00001-1"
	PSCM_00001_1 "89-game-server/domain/probability/PSCM-00001-1"

	"gitlab.iplaystar.net/game-server/logger"
)

const (
	EMSGID_eResult          = "EMSGID_eResult"
	EMSGID_eBroadcastResult = "EMSGID_eBroadcastResult"
)

var Service = &service{}

type service struct {
}

func (s *service) Calc2Cards(card1, card2 int) *Probability {
	pay, rule, point := PSC_ON_00001_1.Deck.Rule2Cards(card1, card2, PSCM_00001_1.Math89.PSC_ON_00001_1)

	logger.Service.Zap.Debugw("Calc 2 Cards",
		"Card1", card1,
		"Card2", card2,
		"SumPoint", point,
		"Pay", pay,
		"Rule", rule,
	)

	return &Probability{
		Card1: card1,
		Card2: card2,
		Card3: -1,
		Pay:   pay,
		Rule:  rule,
		Point: point,
	}
}

func (s *service) Calc3Cards(card1, card2, card3 int) *Probability {
	pay, rule, point, suit := PSC_ON_00001_1.Deck.Rule3Cards(card1, card2, card3, PSCM_00001_1.Math89.PSC_ON_00001_1)

	logger.Service.Zap.Debugw("Calc 3 Cards",
		"Card1", card1,
		"Card2", card2,
		"Card3", card3,
		"SumPoint", point,
		"Pay", pay,
		"Rule", rule,
	)

	return &Probability{
		Card1: card1,
		Card2: card2,
		Card3: card3,
		Pay:   pay,
		Rule:  rule,
		Point: point,
		Suit:  suit,
	}
}

func (s *service) CardToIndex(card int) (index int) {
	for k, v := range PSCM_00001_1.Math89.PSC_ON_00001_1.Deck {
		if v == card {
			return k
		}
	}
	panic("ERROR CARD")
}
