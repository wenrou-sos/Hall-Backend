package lottery

import (
	PSC_ON_00007_1 "52-game-server/domain/probability/PSC-ON-00007-1"
	PSCM_00007_1 "52-game-server/domain/probability/PSCM-00007-1"
	"crypto/rand"
	"encoding/json"
	"fmt"
	"math"
	"math/big"
	"os"
	"testing"

	"gitlab.iplaystar.net/game-server/shuffle"
)

const (
	PLAYER 				= 0
	BOT 				= 1
	INIT_HANDS_AMOUNT	= 5
	TOTAL_CARDS_AMOUNT  = 52
	TYPE_NORMAL_WIN 	= "TYPE_NORMAL_WIN"
	TYPE_PLAY_CARD_WIN 	= "TYPE_PLAY_CARD_WIN"
	TYPE_CALL_CARD_WIN 	= "TYPE_CALL_CARD_WIN"
)

var (
	DEBUG				= false
	TIMES 				= 100000
	PLAYER_AMOUNT		= 3
	PLAYER_N1			= 5
	PLAYER_N2			= 3
	PLAYCARD_PERCENT 	= 50
	SHOWDOWN_PERCENT 	= 50
	BOT_X				= 25
	BOT_Y				= 25
	BOT_W				= 25
	BOT_Z				= 25
	bet uint64 			= 1000
	startSeat			= 0
	winCount 			[]uint64
	totalWin 			[]uint64
	totalLose 			[]uint64
	callCardNum 		[]uint64
	byCallCardNum 		[]uint64
	playerType	 		[]int
)

type SpecialProbability struct {
	Pay   	int
	Rule  	int
	Order  	int
	Order2 	int
}

func TestService_Result(t *testing.T) {
	config := deserialization()
	DEBUG = config.Debug
	TIMES = config.Times * 10000
	PLAYER_AMOUNT = config.PlayerAmount
	PLAYCARD_PERCENT = config.BotN1
	SHOWDOWN_PERCENT = config.BotN2
	BOT_X = config.BotX
	BOT_Y = config.BotY
	BOT_W = config.BotW
	BOT_Z = config.BotZ
	PLAYER_N1 = config.PlayerN1
	PLAYER_N2 = config.PlayerN2

	for i := 0; i < PLAYER_AMOUNT; i++ {
		winCount = append(winCount, 0)
		totalWin = append(totalWin, 0)
		totalLose = append(totalLose, 0)
		callCardNum = append(callCardNum, 0)
		byCallCardNum = append(byCallCardNum, 0)
		playerType = append(playerType, config.PlayerType[i])
	}


	for i := 0; i < TIMES; i++ {
		cards := shuffle.Service.ShuffleCard52("bankerUuid")

		var playerCard [][]int
		var sumPoint []int

		for j := 0; j < PLAYER_AMOUNT; j++ {
			var tempCards []int
			for k := 0; k < INIT_HANDS_AMOUNT; k++ {
				tempCards = append(tempCards, cards[j * INIT_HANDS_AMOUNT + k])
			}
			playerCard = append(playerCard, tempCards)
			sumPoint = append(sumPoint, PSC_ON_00007_1.Deck.Sum(tempCards))
		}

		debug("All cards", playerCard)

		pool := INIT_HANDS_AMOUNT * PLAYER_AMOUNT
		callCard := -1
		hitSeat := -1
		first := true

		if seat, pay := SpecialResult(playerCard); seat > -1 {
			for i := 0; i < PLAYER_AMOUNT; i++ {
				otherSeat := (seat + i) % PLAYER_AMOUNT
				if otherSeat == seat {
					continue
				}
				PlayerScoreWin(seat, otherSeat, pay)
			}
			winCount[seat]++
		} else {
			originPool := TOTAL_CARDS_AMOUNT - pool
			for i := 0; i < originPool; i++ {
				winType := TYPE_NORMAL_WIN
				seat = (i + startSeat) % PLAYER_AMOUNT
				if i == 1 {
					first = false
				}
				if ShowDownLogic(first, seat, playerCard, playerType[seat]) {
					Result(first, seat, sumPoint, winType, -1)
					break
				} else {
					c := callCards(playerCard[seat], callCard)

					if len(c) > 0 {
						totalWin[seat] += bet / 2 * uint64(len(c))
						callCardNum[seat] += 1
						totalLose[hitSeat] += bet / 2 * uint64(len(c))
						byCallCardNum[hitSeat] += 1
						debug("Cards", seat, playerCard[seat], "/ Call cards", c)
						playerCard[seat] = NewCards(playerCard[seat], c[0])
						sumPoint[seat] = PSC_ON_00007_1.Deck.Sum(playerCard[seat])
						if sumPoint[seat] == 0 || i == originPool - 1 {
							if sumPoint[seat] == 0 {
								winType = TYPE_CALL_CARD_WIN
							}
							Result(first, seat, sumPoint, winType, hitSeat)
							break
						}
					} else {
						playerCard[seat] = append(playerCard[seat], cards[pool])
						pool++
						nextSeat := (seat + 1) % PLAYER_AMOUNT
						logic := PlayCardLogic(playerCard[seat], playerCard[nextSeat], playerType[seat])
						pc := playCards(playerCard[seat], playerCard[nextSeat], logic, seat)
						callCard = pc[0]
						hitSeat = seat
						playerCard[seat] = NewCards(playerCard[seat], pc[0])
						sumPoint[seat] = PSC_ON_00007_1.Deck.Sum(playerCard[seat])
						if sumPoint[seat] == 0 || i == originPool - 1 {
							if sumPoint[seat] == 0 {
								winType = TYPE_PLAY_CARD_WIN
							}
							Result(first, seat, sumPoint, winType, -1)
							break
						}
					}
				}
			}
		}
	}
	fmt.Println("贏錢總額", "輸錢總額", "跟牌總次數", "被跟牌總次數", "勝率")
	for i := 0; i < PLAYER_AMOUNT; i++ {
		fmt.Println(totalWin[i], totalLose[i], callCardNum[i], byCallCardNum[i],
			math.Floor(float64(winCount[i]) / float64(TIMES) * 10000) / 100, "%")
	}

	fmt.Scanf("End")
}

func CalcSpecialCards(card []int) *SpecialProbability {
	rule, Order, Order2, pay := PSC_ON_00007_1.Deck.RuleCards(card, PSCM_00007_1.Math52.PSC_ON_00007_1)

	return &SpecialProbability{
		Pay:   	pay,
		Rule:  	rule,
		Order:  Order,
		Order2: Order2,
	}
}

func CalcCards(seat int, sumPoint []int) bool {
	for i := 0; i < PLAYER_AMOUNT; i++ {
		otherSeat := (seat + i) % PLAYER_AMOUNT
		if otherSeat == seat {
			continue
		}
		if sumPoint[seat] >= sumPoint[otherSeat] {
			return false
		}
	}
	return true
}

func callCards(cards []int, card int) []int {
	var callCardArray []int

	kind := card % 13

	for _, c := range cards {
		if c % 13 == kind {
			callCardArray = append(callCardArray, c)
		}
	}
	return callCardArray
}

func playCards(cards, otherCards []int, logic bool, seat int) []int {
	var playCardArray []int
	cardSum := [13]int{0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}

	max := 0
	maxPoint := cardSum[0]

	for _, c := range cards {
		k := c % 13
		cardSum[k] = cardSum[k] + (k + 1)
	}

	for i, s := range cardSum {
		if logic {
			otherNo := true
			for _, c := range otherCards {
				if s != 0 && c % 13 == i {
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
	}

	for _, c := range cards {
		if c % 13 == max {
			playCardArray = append(playCardArray, c)
		}
	}

	debug("Cards", seat, cards, "/ Play cards", playCardArray)

	return playCardArray
}

func NewCards(cards []int, playCard int) []int {
	var playCardArray []int
	for _, c := range cards {
		if c % 13 != playCard % 13 {
			playCardArray = append(playCardArray, c)
		}
	}
	return playCardArray
}

func Result(firstRound bool, seat int, sumPoint []int, winType string, hitSeat int) {
	win := CalcCards(seat, sumPoint)
	if win {
		for i := 0; i < PLAYER_AMOUNT; i++ {
			otherSeat := (seat + i) % PLAYER_AMOUNT
			if seat == otherSeat {
				continue
			}

			pay := PSCM_00007_1.Math52.PSC_ON_00007_1.ComparingPay[2]
			switch winType {
			case TYPE_NORMAL_WIN:
				if firstRound {
					pay = PSCM_00007_1.Math52.PSC_ON_00007_1.ComparingPay[1]
				}

			case TYPE_PLAY_CARD_WIN:
				pay = PSCM_00007_1.Math52.PSC_ON_00007_1.ComparingPay[0]

			case TYPE_CALL_CARD_WIN:
				if hitSeat == otherSeat {
					pay = PSCM_00007_1.Math52.PSC_ON_00007_1.ComparingPay[0]
				}

			default:
				panic("ERROR WIN TYPE")
			}

			PlayerScoreWin(seat, otherSeat, pay)
		}
		winCount[seat]++
		startSeat = seat
		fmt.Println("*** Show Down         *** || Sum Points", sumPoint, "Winner", seat)
	} else {
		var winner []int
		for i := 0; i < PLAYER_AMOUNT; i++ {
			otherSeat := (seat + i) % PLAYER_AMOUNT
			if seat == otherSeat {
				continue
			}
			winner = append(winner, otherSeat)

			pay1 := PSCM_00007_1.Math52.PSC_ON_00007_1.ComparingPay[0]
			pay2 := PSCM_00007_1.Math52.PSC_ON_00007_1.ComparingPay[1]
			if !firstRound {
				pay1 = PSCM_00007_1.Math52.PSC_ON_00007_1.ComparingPay[1]
				pay2 = PSCM_00007_1.Math52.PSC_ON_00007_1.ComparingPay[2]
			}
			winCount[otherSeat]++
			PlayerScoreLose(seat, otherSeat, pay1, pay2, sumPoint)
			if n, err := rand.Int(rand.Reader, big.NewInt(2)); err == nil {
				if n.Uint64() == 0 {
					startSeat = otherSeat
				}
			} else {
				panic(err)
			}
		}
		fmt.Println("*** Show Down         *** || Sum Points", sumPoint, "Winner", winner)
	}
}

func SpecialResult(playerCard [][]int) (seat, pay int) {
	specialCalc := make(map[int][]int)
	for i, p := range playerCard {
		sp := CalcSpecialCards(p)
		if sp.Rule > 0 {
			specialCalc[i] = p
		}
	}
	if len(specialCalc) == 0 {
		return -1, 0
	} else if len(specialCalc) >= 1 {
		rule := 0
		for i, p := range specialCalc {
			sp := CalcSpecialCards(p)
			if sp.Rule > rule {
				seat = i
				rule = sp.Rule
				pay = sp.Pay
			} else if sp.Rule == rule {
				scle := specialCalc[seat]
				ssp := CalcSpecialCards(scle)
				if sp.Order > ssp.Order {
					seat = i
					rule = sp.Rule
					pay = sp.Pay
				} else if sp.Order == ssp.Order {
					if sp.Order2 < ssp.Order2 {
						seat = i
						rule = sp.Rule
						pay = sp.Pay
					}
				}
			}
		}
	}

	fmt.Println("*** Special Show Down *** || Player Cards", playerCard, "Winner", seat)

	return seat, pay
}

func PlayerScoreWin(seat, otherSeat, pay int) {
	totalWin[seat] += bet * uint64(pay)
	totalLose[otherSeat] += bet * uint64(pay)
}

func PlayerScoreLose(seat, otherSeat, pay1, pay2 int, sumPoint []int) {
	if sumPoint[seat] > sumPoint[otherSeat] {
		totalLose[seat] += bet * uint64(pay1)
		totalWin[otherSeat] += bet * uint64(pay1)
	} else {
		totalLose[seat] += bet * uint64(pay2)
		totalWin[otherSeat] += bet * uint64(pay2)
	}
}

func ShowDownLogic(firstRound bool, seat int, playerCards [][]int, playerType int) bool {
	sum := PSC_ON_00007_1.Deck.Sum(playerCards[seat])
	switch playerType {
	case PLAYER:
		length := INIT_HANDS_AMOUNT
		for i := 0; i < PLAYER_AMOUNT; i++ {
			if i == seat {
				continue
			}
			if len(playerCards[i]) < length {
				length = len(playerCards[i])
			}
		}
		if length == 4 || length == 5 {
			if sum < length * PLAYER_N1 {
				return true
			}
		} else {
			if sum < length * PLAYER_N2 {
				return true
			}
		}
		return false
	case BOT:
		isSmallest := true
		for i := 0; i < PLAYER_AMOUNT; i++ {
			if i == seat {
				continue
			}
			otherSum := PSC_ON_00007_1.Deck.Sum(playerCards[i])
			if sum >= otherSum {
				isSmallest = false
			}
		}
		if n, err := rand.Int(rand.Reader, big.NewInt(100)); err == nil {
			if n.Uint64() < uint64(SHOWDOWN_PERCENT) {
				if !isSmallest {
					return false
				}
				if firstRound {
					if sum <= BOT_X {
						return true
					}
				} else {
					if sum <= BOT_Y {
						return true
					}
				}
				return false
			} else {
				if firstRound {
					if sum <= BOT_W {
						return true
					}
				} else {
					if sum <= BOT_Z {
						return true
					}
				}
				return false
			}
		} else {
			panic(err)
		}
	}
	return false
}

func PlayCardLogic(cards, otherCards []int, playerType int) bool {
	switch playerType {
	case PLAYER:
		return false

	case BOT:
		var isSameCards = func() bool {
			var same []bool
			sameCount := 0
			for _, c := range cards {
				for _, oc := range otherCards {
					if c % 13 == oc % 13 {
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
			if n.Uint64() < uint64(PLAYCARD_PERCENT) {
				return true
			} else {
				return false
			}
		} else {
			panic(err)
		}
	}
	return false
}

type Config struct {
	Times        int
	PlayerAmount int
	PlayerType   []int
	BotN1        int
	BotN2        int
	BotX         int
	BotY         int
	BotW         int
	BotZ         int
	PlayerN1     int
	PlayerN2     int
	Debug 		 bool
}

func deserialization() *Config {
	config := &Config{}
	if err := json.NewDecoder(open()).Decode(&config); err != nil {
		panic(err)
	}
	return config
}

func open() *os.File {
	var file *os.File
	var err error

	defer file.Close()

	if file, err = os.Open("config.json"); err != nil {
		panic(err)
	}

	return file
}

func debug(a ...interface{}) {
	if DEBUG {
		fmt.Println(a...)
	}
}