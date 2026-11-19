package PSC_ON_00001_1

var Deck = &deck{
	club:    0,
	diamond: 16,
	heart:   32,
	spade:   48,
}

type deck struct {
	club    int
	diamond int
	heart   int
	spade   int
}

type Math89 struct {
	Deck  []int
	Kinds []struct {
		Rule  int
		Hand  int
		Cards []int
		Point []int
		Suit  bool
		Pay   int
	}
}

func (d *deck) Sum(card1, card2 int) int {
	return (d.point89(card1) + d.point89(card2)) % 10
}

func (d *deck) Rule2Cards(card1, card2 int, math *Math89) (pay, rule, point int) {
	// 博9（加倍）: 手牌2張  且  花色相同  且  點數合  為  9  點
	if d.suit(card1) == d.suit(card2) && d.Sum(card1, card2) == math.Kinds[0].Point[0] {
		return math.Kinds[0].Pay, math.Kinds[0].Rule, math.Kinds[0].Point[0]
	}

	// 博9 : 手牌2張  且  點數合  為  9  點
	if d.suit(card1) != d.suit(card2) && d.Sum(card1, card2) == math.Kinds[1].Point[0] {
		return math.Kinds[1].Pay, math.Kinds[1].Rule, math.Kinds[1].Point[0]
	}

	// 博8（加倍）: 手牌2張  且  （點數相同  或  花色相同）  且  點數合  為  8  點
	if (d.suit(card1) == d.suit(card2) || d.point89(card1) == d.point89(card2)) && d.Sum(card1, card2) == math.Kinds[2].Point[0] {
		return math.Kinds[2].Pay, math.Kinds[2].Rule, math.Kinds[2].Point[0]
	}

	// 博8 : 手牌2張  且  點數合  為  8  點
	if d.suit(card1) != d.suit(card2) && d.Sum(card1, card2) == math.Kinds[3].Point[0] {
		return math.Kinds[3].Pay, math.Kinds[3].Rule, math.Kinds[3].Point[0]
	}

	// 一般（2同花）: 手牌2張  且  2張  花色相同
	if d.suit(card1) == d.suit(card2) {
		return math.Kinds[48].Pay, math.Kinds[48].Rule, d.Sum(card1, card2)
	}

	// 一般（對子）: 手牌2張  且  2張  點數相同
	if d.point(card1) == d.point(card2) {
		return math.Kinds[49].Pay, math.Kinds[49].Rule, d.Sum(card1, card2)
	}

	// 一般 : 手牌2張  且  點數合  為  0~7  點
	for _, v := range math.Kinds[51].Point {
		if d.Sum(card1, card2) == v {
			return math.Kinds[51].Pay, math.Kinds[51].Rule, v
		}
	}

	return 0, -2, -2
}

func (d *deck) Rule3Cards(card1, card2, card3 int, math *Math89) (pay, rule, point, deck int) {
	// 三條
	if (card1%d.diamond == card2%d.diamond) && (card2%d.diamond == card3%d.diamond) {
		switch card1 % d.diamond {
		case 1:
			return math.Kinds[4].Pay, math.Kinds[4].Rule, math.Kinds[4].Point[0], d.suit(card1)

		case 13:
			return math.Kinds[5].Pay, math.Kinds[5].Rule, math.Kinds[5].Point[0], d.suit(card1)

		case 12:
			return math.Kinds[6].Pay, math.Kinds[6].Rule, math.Kinds[6].Point[0], d.suit(card1)

		case 11:
			return math.Kinds[7].Pay, math.Kinds[7].Rule, math.Kinds[7].Point[0], d.suit(card1)

		case 10:
			return math.Kinds[8].Pay, math.Kinds[8].Rule, math.Kinds[8].Point[0], d.suit(card1)

		case 9:
			return math.Kinds[9].Pay, math.Kinds[9].Rule, math.Kinds[9].Point[0], d.suit(card1)

		case 8:
			return math.Kinds[10].Pay, math.Kinds[10].Rule, math.Kinds[10].Point[0], d.suit(card1)

		case 7:
			return math.Kinds[11].Pay, math.Kinds[11].Rule, math.Kinds[11].Point[0], d.suit(card1)

		case 6:
			return math.Kinds[12].Pay, math.Kinds[12].Rule, math.Kinds[12].Point[0], d.suit(card1)

		case 5:
			return math.Kinds[13].Pay, math.Kinds[13].Rule, math.Kinds[13].Point[0], d.suit(card1)

		case 4:
			return math.Kinds[14].Pay, math.Kinds[14].Rule, math.Kinds[14].Point[0], d.suit(card1)

		case 3:
			return math.Kinds[15].Pay, math.Kinds[15].Rule, math.Kinds[15].Point[0], d.suit(card1)

		case 2:
			return math.Kinds[16].Pay, math.Kinds[16].Rule, math.Kinds[16].Point[0], d.suit(card1)
		}
	}

	// 同花順子 / 順子 AQK
	isSuit, isRule, suit := d.rule(card1, card2, card3, map[int]int{1: 1, 2: 12, 3: 13}, 1)
	if isSuit && isRule {
		return math.Kinds[17].Pay, math.Kinds[17].Rule, math.Kinds[17].Point[0], suit
	}

	if isRule {
		return math.Kinds[29].Pay, math.Kinds[29].Rule, math.Kinds[29].Point[0], suit
	}

	// 同花順子 / 順子 JQK
	isSuit, isRule, suit = d.rule(card1, card2, card3, map[int]int{1: 11, 2: 12, 3: 13}, 13)
	if isSuit && isRule {
		return math.Kinds[18].Pay, math.Kinds[18].Rule, math.Kinds[18].Point[0], suit
	}

	if isRule {
		return math.Kinds[30].Pay, math.Kinds[30].Rule, math.Kinds[30].Point[0], suit
	}

	// 同花順子 / 順子 10JQ
	isSuit, isRule, suit = d.rule(card1, card2, card3, map[int]int{1: 10, 2: 11, 3: 12}, 12)
	if isSuit && isRule {
		return math.Kinds[19].Pay, math.Kinds[19].Rule, math.Kinds[19].Point[0], suit
	}

	if isRule {
		return math.Kinds[31].Pay, math.Kinds[31].Rule, math.Kinds[31].Point[0], suit
	}

	// 同花順子 / 順子 910J
	isSuit, isRule, suit = d.rule(card1, card2, card3, map[int]int{1: 9, 2: 10, 3: 11}, 11)
	if isSuit && isRule {
		return math.Kinds[20].Pay, math.Kinds[20].Rule, math.Kinds[20].Point[0], suit
	}

	if isRule {
		return math.Kinds[32].Pay, math.Kinds[32].Rule, math.Kinds[32].Point[0], suit
	}

	// 同花順子 / 順子 8910
	isSuit, isRule, suit = d.rule(card1, card2, card3, map[int]int{1: 8, 2: 9, 3: 10}, 10)
	if isSuit && isRule {
		return math.Kinds[21].Pay, math.Kinds[21].Rule, math.Kinds[21].Point[0], suit
	}

	if isRule {
		return math.Kinds[33].Pay, math.Kinds[33].Rule, math.Kinds[33].Point[0], suit
	}

	// 同花順子 / 順子 789
	isSuit, isRule, suit = d.rule(card1, card2, card3, map[int]int{1: 7, 2: 8, 3: 9}, 9)
	if isSuit && isRule {
		return math.Kinds[22].Pay, math.Kinds[22].Rule, math.Kinds[22].Point[0], suit
	}

	if isRule {
		return math.Kinds[34].Pay, math.Kinds[34].Rule, math.Kinds[34].Point[0], suit
	}

	// 同花順子 / 順子 678
	isSuit, isRule, suit = d.rule(card1, card2, card3, map[int]int{1: 6, 2: 7, 3: 8}, 8)
	if isSuit && isRule {
		return math.Kinds[23].Pay, math.Kinds[23].Rule, math.Kinds[23].Point[0], suit
	}

	if isRule {
		return math.Kinds[35].Pay, math.Kinds[35].Rule, math.Kinds[35].Point[0], suit
	}

	// 同花順子 / 順子 567
	isSuit, isRule, suit = d.rule(card1, card2, card3, map[int]int{1: 5, 2: 6, 3: 7}, 7)
	if isSuit && isRule {
		return math.Kinds[24].Pay, math.Kinds[24].Rule, math.Kinds[24].Point[0], suit
	}

	if isRule {
		return math.Kinds[36].Pay, math.Kinds[36].Rule, math.Kinds[36].Point[0], suit
	}

	// 同花順子 / 順子 456
	isSuit, isRule, suit = d.rule(card1, card2, card3, map[int]int{1: 4, 2: 5, 3: 6}, 6)
	if isSuit && isRule {
		return math.Kinds[25].Pay, math.Kinds[25].Rule, math.Kinds[25].Point[0], suit
	}

	if isRule {
		return math.Kinds[37].Pay, math.Kinds[37].Rule, math.Kinds[37].Point[0], suit
	}

	// 同花順子 / 順子 345
	isSuit, isRule, suit = d.rule(card1, card2, card3, map[int]int{1: 3, 2: 4, 3: 5}, 5)
	if isSuit && isRule {
		return math.Kinds[26].Pay, math.Kinds[26].Rule, math.Kinds[26].Point[0], suit
	}

	if isRule {
		return math.Kinds[38].Pay, math.Kinds[38].Rule, math.Kinds[38].Point[0], suit
	}

	// 同花順子 / 順子 234
	isSuit, isRule, suit = d.rule(card1, card2, card3, map[int]int{1: 2, 2: 3, 3: 4}, 4)
	if isSuit && isRule {
		return math.Kinds[27].Pay, math.Kinds[27].Rule, math.Kinds[27].Point[0], suit
	}

	if isRule {
		return math.Kinds[39].Pay, math.Kinds[39].Rule, math.Kinds[39].Point[0], suit
	}

	// 同花順子 / 順子 A23
	// isSuit, isRule = d.rule(card1, card2, card3, map[int]int{1: 1, 2: 2, 3: 3})
	// if isSuit && isRule {
	//     return math.Kinds[28].Pay, math.Kinds[28].Rule, math.Kinds[28].Point[0]
	// }

	// if isRule {
	// 	return math.Kinds[40].Pay, math.Kinds[40].Rule, math.Kinds[40].Point[0]
	// }

	// 三公 KKQ
	if _, isRule, suit = d.rule(card1, card2, card3, map[int]int{1: 13, 2: 13, 3: 12}, 13); isRule {
		return math.Kinds[41].Pay, math.Kinds[41].Rule, math.Kinds[41].Point[0], suit
	}

	// 三公 KKJ
	if _, isRule, suit = d.rule(card1, card2, card3, map[int]int{1: 13, 2: 13, 3: 11}, 13); isRule {
		return math.Kinds[42].Pay, math.Kinds[42].Rule, math.Kinds[42].Point[0], suit
	}

	// 三公 QQK
	if _, isRule, suit = d.rule(card1, card2, card3, map[int]int{1: 12, 2: 12, 3: 13}, 12); isRule {
		return math.Kinds[43].Pay, math.Kinds[43].Rule, math.Kinds[43].Point[0], suit
	}

	// 三公 QQJ
	if _, isRule, suit = d.rule(card1, card2, card3, map[int]int{1: 12, 2: 12, 3: 11}, 12); isRule {
		return math.Kinds[44].Pay, math.Kinds[44].Rule, math.Kinds[44].Point[0], suit
	}

	// 三公 JJK
	if _, isRule, suit = d.rule(card1, card2, card3, map[int]int{1: 11, 2: 11, 3: 13}, 11); isRule {
		return math.Kinds[45].Pay, math.Kinds[45].Rule, math.Kinds[45].Point[0], suit
	}

	// 三公 JJQ
	if _, isRule, suit = d.rule(card1, card2, card3, map[int]int{1: 11, 2: 11, 3: 12}, 11); isRule {
		return math.Kinds[46].Pay, math.Kinds[46].Rule, math.Kinds[46].Point[0], suit
	}

	// 一般（3同花） : 手牌3張  且  花色相同  且    點數合  0~9  點
	if d.suit(card1) == d.suit(card2) && d.suit(card2) == d.suit(card3) {
		for _, v := range math.Kinds[47].Point {
			if (d.point89(card1)+d.point89(card2)+d.point89(card3))%10 == v {
				return math.Kinds[47].Pay, math.Kinds[47].Rule, v, 0
			}
		}
	}

	// 一般 : 手牌3張  且  點數合  為  0~9  點
	for _, v := range math.Kinds[50].Point {
		if (d.point89(card1)+d.point89(card2)+d.point89(card3))%10 == v {
			return math.Kinds[50].Pay, math.Kinds[50].Rule, v, 0
		}
	}

	return 0, -2, -2, -1
}

func (d *deck) rule(card1, card2, card3 int, temp map[int]int, deck int) (isSuit, isRule bool, sule int) {
	for k, v := range temp {
		if card1%d.diamond == v {
			delete(temp, k)
			break
		}
	}

	for k, v := range temp {
		if card2%d.diamond == v {
			delete(temp, k)
			break
		}
	}

	for k, v := range temp {
		if card3%d.diamond == v {
			delete(temp, k)
			break
		}
	}
	kind := 0
	if card1%d.diamond == deck {
		if d.suit(card1) > kind {
			kind = d.suit(card1)
		}
	}
	if card2%d.diamond == deck {
		if d.suit(card2) > kind {
			kind = d.suit(card2)
		}
	}
	if card3%d.diamond == deck {
		if d.suit(card3) > kind {
			kind = d.suit(card3)
		}
	}
	return (d.suit(card1) == d.suit(card2)) && (d.suit(card2) == d.suit(card3)), len(temp) == 0, kind
}

func (d *deck) suit(card int) int {
	switch {
	case card > 0 && card < 16:
		return d.club

	case card > 16 && card < 32:
		return d.diamond

	case card > 32 && card < 48:
		return d.heart

	case card > 48 && card < 62:
		return d.spade

	default:
		panic("ERROR SUIT")
	}
}

func (d *deck) point89(card int) int {
	switch card {
	case 1, 17, 33, 49:
		return 1

	case 2, 18, 34, 50:
		return 2

	case 3, 19, 35, 51:
		return 3

	case 4, 20, 36, 52:
		return 4

	case 5, 21, 37, 53:
		return 5

	case 6, 22, 38, 54:
		return 6

	case 7, 23, 39, 55:
		return 7

	case 8, 24, 40, 56:
		return 8

	case 9, 25, 41, 57:
		return 9

	case 10, 26, 42, 58:
		return 0

	case 11, 27, 43, 59:
		return 0

	case 12, 28, 44, 60:
		return 0

	case 13, 29, 45, 61:
		return 0

	default:
		panic("ERROR CARD POINT89")
	}
}

func (d *deck) point(card int) int {
	switch card {
	case 1, 17, 33, 49:
		return 1

	case 2, 18, 34, 50:
		return 2

	case 3, 19, 35, 51:
		return 3

	case 4, 20, 36, 52:
		return 4

	case 5, 21, 37, 53:
		return 5

	case 6, 22, 38, 54:
		return 6

	case 7, 23, 39, 55:
		return 7

	case 8, 24, 40, 56:
		return 8

	case 9, 25, 41, 57:
		return 9

	case 10, 26, 42, 58:
		return 10

	case 11, 27, 43, 59:
		return 11

	case 12, 28, 44, 60:
		return 12

	case 13, 29, 45, 61:
		return 13

	default:
		panic("ERROR CARD POINT")
	}
}
