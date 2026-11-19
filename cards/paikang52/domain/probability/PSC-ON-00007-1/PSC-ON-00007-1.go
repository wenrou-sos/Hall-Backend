package PSC_ON_00007_1

import (
	"sort"
	"strconv"
)

var Deck = &deck{
	diamond: 0,
	club:    13,
	heart:   26,
	spade:   39,
}

type deck struct {
	diamond int
	club    int
	heart   int
	spade   int
}

type Math52 struct {
	Deck               []int
	SpecialHandTypePay []int
	WinByKnockingPay   int
	WinByClearingPay   []int
	FollowSuitPay      float32
	ComparingPay       []int
}

func (d *deck) Sum(cards []int) int {
	s := 0
	for _, p := range cards {
		s += d.point(p)
	}
	return s
}

func (d *deck) RuleCards(cards []int, math *Math52) (rule, oder, oder2, pay int) {
	cardKind := d.kindTool(cards)
	four, three, two := d.FlushTool(cards)
	straight := d.StraightTool(cards)
	special := d.SpecialTool(cards)
	if special {
		straight = 10
	}
	//  Straight Flush
	if cardKind >= 0 && special {
		return 6, 10, cardKind, math.SpecialHandTypePay[0]
	}
	if cardKind >= 0 && straight >= 0 {
		return 6, straight, cardKind, math.SpecialHandTypePay[0]
	}
	//  Four of a Kind
	if four >= 0 {
		return 5, four, -1, math.SpecialHandTypePay[1]
	}
	//  Full House
	if three >= 0 && two >= 0 {
		return 4, three, two, math.SpecialHandTypePay[2]
	}
	//  Flush
	if cardKind >= 0 {
		return 3, cardKind, cards[4], math.SpecialHandTypePay[3]
	}
	//  Straight
	if straight >= 0 {
		return 2, straight, cardKind, math.SpecialHandTypePay[4]
	}
	//  Three of a Kind
	if three >= 0 {
		return 1, three, -1, math.SpecialHandTypePay[5]
	}
	return 0, -1, -1, 0
}

func (d *deck) ThreeOfAKind(cards []int, math *Math52) (rule, oder, oder2, pay int, isRule bool) {
	_, three, two := d.FlushTool(cards)
	if three > 0 && two < 0 {
		return 1, three, -1, math.SpecialHandTypePay[5], true
	}
	return -1, -1, -1, -1, false
}

func (d *deck) FlushTool(cards []int) (fourkind, threekind, twopair int) {
	cardnum := [13]int{0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}

	fourkindNum := -1
	threekindNum := -1
	twopairNum := -1
	for _, i := range cards {
		c := i % 13
		cardnum[c]++
	}
	for d, i := range cardnum {
		if i == 4 {
			fourkindNum = d
		}
		if i == 3 {
			threekindNum = d
		}
		if i == 2 {
			twopairNum = d
		}
	}
	return fourkindNum, threekindNum, twopairNum
}

func (d *deck) kindTool(card []int) int {
	cardKind := card[0] / 13
	for _, i := range card {
		if k := i / 13; k != cardKind {
			return -1
		}
	}
	return cardKind
}

func (d *deck) StraightTool(card []int) int {
	var pointCard []int
	for _, c := range card {
		pointCard = append(pointCard, c % 13)
	}
	sort.Ints(pointCard)
	for i, c := range pointCard {
		if (c % 13) - i != pointCard[0] % 13 {
			return -1
		}
	}
	return pointCard[0] % 13
}

func (d *deck) SpecialTool(card []int) bool {
	specialCard := [5]int{0, 9, 10, 11, 12}
	specialNum := 0
	for _, sc := range specialCard {
		for _, c := range card {
			if c % 13 == sc {
				specialNum++
				break
			}
		}
	}
	if specialNum == 5 {
		return true
	}
	return false
}

func (d *deck) point(card int) int {
	p := card % 13
	p = p + 1
	if p > 9 {
		p = 10
	}
	return p
}

func (d *deck) ConvertToLog(card []int) []string {
	var log []string
	var point []int
	for _, c := range card {
		str := ""

		switch c / 13 {
		case 0:
			str += "♦"

		case 1:
			str += "♣"

		case 2:
			str += "♥"

		case 3:
			str += "♠"
		}

		p := c % 13 + 1
		str += strconv.Itoa(p)
		log = append(log, str)
		point = append(point, p)
	}

	for i, _ := range point {
		for j, _ := range point {
			if point[i] < point[j] {
				point[i], point[j] = point[j], point[i]
				log[i], log[j] = log[j], log[i]
			}
		}
	}

	return log
}
