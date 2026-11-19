package probability

import (
	"crypto/rand"
	"math/big"
	"sort"
	PSC_ON_00013 "u-game-server/domain/probability/PSC-ON-00013"
	probability_proto "u-game-server/domain/probability/proto"
)

const (
	EMSGID_eBroadcastResult  = "EMSGID_eBroadcastResult"
	EMSGID_eBroadcastRanking = "EMSGID_eBroadcastRanking"
)

var Service = &service{}

type service struct {
}

func (s *service) DrawBot(cards []int, lastCard, lastColor, percent int) int {
	if n, err := rand.Int(rand.Reader, big.NewInt(100)); err == nil {
		if int(n.Uint64()) >= percent {
			return -1
		}
	} else {
		panic(err)
	}

	for _, c := range cards {
		if s.CheckCardNormal(c, lastCard, -1, lastColor, -1) {
			return c
		}
	}

	return -1
}

func (s *service) PlayCardsBot(cards []int, lastCard, lastColor, penalty int, blackFirst, numberFirst, canPlus2 bool) (playCards []int, playColor int) {
	var validCards []int
	var validColorCards []int
	var validPointCards []int
	var validBlackCards []int
	lp, _, ln := PSC_ON_00013.Deck.CardInfo(lastCard)

	for _, card := range cards {
		p, c, n := PSC_ON_00013.Deck.CardInfo(card)
		if penalty > 0 {
			if n == "WD" {
				validBlackCards = append(validBlackCards, card)
			} else if n == "D" && canPlus2 {
				if c == lastColor {
					validColorCards = append(validColorCards, card)
				} else if p == lp && n == ln {
					validPointCards = append(validPointCards, card)
				}
			}
		} else {
			if n == "W" || n == "WD" {
				validBlackCards = append(validBlackCards, card)
			} else if n == "D" {
				if canPlus2 {
					if c == lastColor {
						validColorCards = append(validColorCards, card)
					} else if p == lp && n == ln {
						validPointCards = append(validPointCards, card)
					}
				}
			} else if c == lastColor {
				validColorCards = append(validColorCards, card)
			} else if p == lp && n == ln {
				validPointCards = append(validPointCards, card)
			}
		}
	}

	if blackFirst && len(validBlackCards) > 0 {
		validCards = validBlackCards
	} else if len(validColorCards) > 0 {
		validCards = validColorCards
	} else if len(validPointCards) > 0 {
		validCards = validPointCards
	} else {
		validCards = validBlackCards
	}

	order := -1
	name := "default"
	for _, card := range validCards {
		if numberFirst {
			_, _, n := PSC_ON_00013.Deck.CardInfo(card)
			if (n == "" && name == "") || (n != "" && name != "") { // (數字 && 前數字) || (功能 && 前功能) -> 要看order
				if o := card % 27; o > order {
					order = o
					name = n
					playCards = append([]int{}, card)
					playColor = card / 27
				}
			} else if n == "" && name != "" { // 數字 && 前功能 -> 直接覆蓋
				order = card % 27
				name = n
				playCards = append([]int{}, card)
				playColor = card / 27
			}
		} else {
			if o := card % 27; o > order {
				order = o
				playCards = append([]int{}, card)
				playColor = card / 27
			}
		}
	}

	return playCards, playColor
}

func (s *service) PlayCardsPlayer(cards []int, lastCard, lastColor, penalty int) (playCards []int, playColor int) {
	var validCards []int
	var validColorCards []int
	var validPointCards []int
	var validSpecialCards [2][]int // 0:返回/跳過下一位/抽2張 ; 1:換色/抽四張

	lp, _, ln := PSC_ON_00013.Deck.CardInfo(lastCard)

	for _, card := range cards {
		p, c, n := PSC_ON_00013.Deck.CardInfo(card)
		if penalty > 0 {
			if n == "WD" {
				playCards = append([]int{}, card)
				return playCards, playColor
			} else if n == "D" {
				if c == lastColor {
					validColorCards = append(validColorCards, card)
				} else if p == lp && n == ln {
					validPointCards = append(validPointCards, card)
				}
			}
		} else {
			if n == "" {
				if c == lastColor {
					validColorCards = append(validColorCards, card)
				} else if p == lp && n == ln {
					validPointCards = append(validPointCards, card)
				}
			} else {
				if n == "W" || n == "WD" { //換色/抽四張
					validSpecialCards[1] = append(validSpecialCards[1], card)
				} else if c == lastColor || (p == lp && n == ln) { //返回/跳過下一位/抽2張
					validSpecialCards[0] = append(validSpecialCards[0], card)				
				}
			}
		}
	}
	if len(validColorCards) > 0 {
		validCards = validColorCards
	} else if len(validPointCards) > 0 {
		validCards = validPointCards
	} else if len(validSpecialCards[1]) > 0 {
		return randomChooseCard(validSpecialCards[1]) 
	} else if len(validSpecialCards[0]) > 0 {
		return randomChooseCard(validSpecialCards[0]) 
	}

	order := -1
	for _, card := range validCards {
		if o := card % 27; o > order {
			order = o
			playCards = append([]int{}, card)
			playColor = card / 27
		}
	}

	return playCards, playColor
}

func (s *service) CheckCardNormal(card, lastCard, lastDraw, lastColor, penalty int) bool {
	if lastDraw != -1 && card != lastDraw {
		return false
	} else if penalty > 0 {
		if _, _, n := PSC_ON_00013.Deck.CardInfo(card); n == "D" || n == "WD" {
			return true
		}
	} else {
		if p, c, n := PSC_ON_00013.Deck.CardInfo(card); n == "W" || n == "WD" {
			return true
		} else {
			if lp, _, ln := PSC_ON_00013.Deck.CardInfo(lastCard); lastColor == c || (lp == p && ln == n) {
				return true
			}
		}
	}
	return false
}

func (s *service) CheckCardTwin(card, lastCard, lastDraw, lastColor, penalty int) bool {
	if lastDraw != -1 && card != lastDraw {
		return false
	} else if penalty > 0 {
		return false
	} else {
		if p, c, n := PSC_ON_00013.Deck.CardInfo(card); n == "" {
			if lp, _, _ := PSC_ON_00013.Deck.CardInfo(lastCard); lastColor == c || lp == p {
				return true
			}
		}
	}
	return false
}

func (s *service) ChooseColor(data *probability_proto.PlayerData, playerData map[string]*probability_proto.PlayerData) int {
	maxPoint := -1
	n, err := rand.Int(rand.Reader, big.NewInt(4))
	color := int(n.Int64())
	onlyBlack := true

	if err != nil {
		panic(err)
	}
	for _, c := range data.Cards.Hands {
		if p, co, name := PSC_ON_00013.Deck.CardInfo(int(c)); name != "W" && name != "WD" {
			if p > maxPoint {
				onlyBlack = false
				maxPoint = p
				color = co
			}
		}
	}

	var minSum int32 = 1000
	var winner *probability_proto.PlayerData = nil
	if onlyBlack {
		for _, p := range playerData {
			if p.Seat == data.Seat {
				continue
			}
			if p.Cards.SumPoint < minSum {
				minSum = p.Cards.SumPoint
				winner = p
			}
		}

		minPoint := 100
		for _, c := range winner.Cards.Hands {
			if p, co, name := PSC_ON_00013.Deck.CardInfo(int(c)); name != "W" && name != "WD" {
				if p < minPoint {
					minPoint = p
					color = co
				}
			}
		}
	}

	return color
}

func (s *service) InitialCard(cards []int) int {
	n, err := rand.Int(rand.Reader, big.NewInt(int64(len(cards))))

	if err != nil {
		panic(err)
	}

	card := cards[n.Uint64()]

	if _, _, n := PSC_ON_00013.Deck.CardInfo(card); n == "" {
		return card
	} else {
		return s.InitialCard(cards)
	}
}

func (s *service) LuckyCard(cards []int, count, maxCount, percent int) int {
	n, err := rand.Int(rand.Reader, big.NewInt(100))

	if err != nil {
		panic(err)
	}

	card := cards[0]

	if percent < 0 {
		return card
	}

	for _, c := range cards {
		_, _, name := PSC_ON_00013.Deck.CardInfo(c)
		if int(n.Uint64()) < percent && count < maxCount {
			if name != "" {
				card = c
				break
			}
		} else {
			if name == "" {
				card = c
				break
			}
		}
	}

	return card
}

func (s *service) UnluckyDrawCard(cards []int, lastCard, lastColor int) int {
	var cardIndex [109]int

	for i, c := range cards {
		cardIndex[c] = i
	}

	d := make([]int, len(cards))
	copy(d, cards)
	sort.Slice(d, func(i, j int) bool {
		type_i, type_j := 0, 0
		//9 > 8 > 7 > SK&RE > 6 > 5 > 4 > 3 > 2 > 1 > 0 > D&W&WD
		switch d[i] % 27 {
		case 0:
			type_i = 1
		case 1, 2:
			type_i = 2
		case 3, 4:
			type_i = 3
		case 5, 6:
			type_i = 4
		case 7, 8:
			type_i = 5
		case 9, 10:
			type_i = 6
		case 11, 12:
			type_i = 7
		case 13, 14:
			type_i = 9
		case 15, 16:
			type_i = 10
		case 17, 18:
			type_i = 11
		case 19, 20, 21, 22:
			type_i = 8
		}
		switch d[j] % 27 {
		case 0:
			type_j = 1
		case 1, 2:
			type_j = 2
		case 3, 4:
			type_j = 3
		case 5, 6:
			type_j = 4
		case 7, 8:
			type_j = 5
		case 9, 10:
			type_j = 6
		case 11, 12:
			type_j = 7
		case 13, 14:
			type_j = 9
		case 15, 16:
			type_j = 10
		case 17, 18:
			type_j = 11
		case 19, 20, 21, 22:
			type_j = 8
		}
		return type_i > type_j
	})

	for _, c := range d {
		if !s.CheckCardNormal(c, lastCard, -1, lastColor, 0) {
			return cardIndex[c]
		}
	}
	return 0
}

func randomChooseCard(validCards []int) (playCards []int, playColor int) {
	index := random(len(validCards))
	card := validCards[index]
	playCards = append([]int{}, card)
	playColor = card / 27
	return playCards, playColor
}

func random(value int) int {
    n, err := rand.Int(rand.Reader, big.NewInt(int64(value)))
    if err != nil {
        panic(err)
    }

    return int(n.Uint64())
}
