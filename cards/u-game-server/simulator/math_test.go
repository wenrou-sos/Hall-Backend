package simulator

import (
	"crypto/rand"
	"encoding/json"
	"fmt"
	"gitlab.iplaystar.net/game-server/shuffle"
	"math"
	"math/big"
	"os"
	"strconv"
	"testing"
	"u-game-server/application/banker"
	"u-game-server/application/lottery"
	"u-game-server/domain/probability"
	PSC_ON_00013 "u-game-server/domain/probability/PSC-ON-00013"
	probability_proto "u-game-server/domain/probability/proto"
)

const (
	PLAYER 				= 0
	BOT 				= 1
	INIT_HANDS_AMOUNT	= 7
	LUCKY_PERCENT		= 60
	LUCKY_MAX			= 6
)

var (
	DEBUG				= false
	TIMES 				= 100000
	PLAYER_AMOUNT		= 4
	BOT_N1 				= 10
	BOT_N2 				= 0
	PLAYER_M			= 5
	bet uint64 			= 1000
	winCount 			[]uint64
	totalWin 			[]int64
	totalLose 			[]int64
	totalSumPoint 	    []int32
	ranking				[]int32
	playerType	 		[]int
	cards               []int
	disCards            []int
	playerData          map[string]*probability_proto.PlayerData
	lastCard            = -1
	lastColor           = -1
	seatOperator int32  = 1
	seat int32 			= 0
	seatStr				= ""
	penalty             = 0
	begin               = true
)

func TestService_Result(t *testing.T) {
	config := deserialization()
	DEBUG = config.Debug
	TIMES = config.Times * 10000
	PLAYER_AMOUNT = config.PlayerAmount
	BOT_N1 = config.BotN1
	BOT_N2 = config.BotN2
	PLAYER_M = config.PlayerM

	for i := 0; i < PLAYER_AMOUNT; i++ {
		winCount = append(winCount, 0)
		totalWin = append(totalWin, 0)
		totalLose = append(totalLose, 0)
		totalSumPoint = append(totalSumPoint, 0)
		ranking = append(ranking, 0)
		playerType = append(playerType, config.PlayerType[i])
	}

	for i := 0; i < TIMES; i++ {
		Init()

		cards = shuffle.Service.ShuffleCardU("bankerUuid")
		lastCard = probability.Service.InitialCard(cards)
		_, lastColor, _ = PSC_ON_00013.Deck.CardInfo(lastCard)
		_, str := PSC_ON_00013.Deck.Convert(lastCard)
		debug("Start", str)

		for j := 0; j < PLAYER_AMOUNT; j++ {
			var tempCards []int
			luckyCount := 0
			for k := 0; k < INIT_HANDS_AMOUNT; k++ {
				card := probability.Service.LuckyCard(cards, luckyCount, LUCKY_MAX, LUCKY_PERCENT)
				tempCards = append(tempCards, card)
				var newCards []int
				for _, c := range cards {
					if c != card {
						newCards = append(newCards, c)
					}
				}
				cards = newCards
			}
			playerData[strconv.Itoa(j)] = &probability_proto.PlayerData{
				Seat: 			int32(j),
				Cards: &probability_proto.Cards{
					Hands: 		banker.ToInt32Arr(tempCards),
					SumPoint: 	int32(PSC_ON_00013.Deck.Sum(tempCards)),
				},
				AllScore: 		0,
				Rank: 			1,
			}
			debug("Seat:", j, "Hands:", PSC_ON_00013.Deck.ConvertToLog(tempCards))
		}

		n, err := rand.Int(rand.Reader, big.NewInt(int64(PLAYER_AMOUNT)))
		if err != nil {
			panic(err)
		}
		seat = int32(n.Uint64())

		for j := 0; j < 10000000; j++ {
			if begin {
				begin = false
			} else {
				seat = NextSeat()
			}
			seatStr = strconv.Itoa(int(seat))

			isWildDraw := false
			blackFirst := false
			numberFirst := false
			canPlus2 := true
			for _, p := range playerData {
				if p.Seat != seat {
					if len(p.Cards.Hands) <= 3 {
						blackFirst = true
					}
				}
			}

			if playerType[seat] == PLAYER {
				blackFirst = false
				if  j < PLAYER_M {
					canPlus2 = false
				}
			} else {
				if  j < BOT_N2 {
					numberFirst = true
				}
			}

			c, color := probability.Service.PlayCardsBot(banker.ToIntArr(playerData[seatStr].Cards.Hands), lastCard, lastColor, penalty, blackFirst, numberFirst, canPlus2)
			if len(c) == 0 {
				card := probability.Service.DrawBot(cards, lastCard, lastColor, BOT_N1)
				if playerType[seat] == PLAYER || card == -1 {
					card = cards[0]
				}

				var newCards []int
				for _, c := range cards {
					if c != card {
						newCards = append(newCards, c)
					}
				}
				cards = newCards

				playerData[seatStr].Cards.Hands = append(playerData[seatStr].Cards.Hands, int32(card))
				c, color = probability.Service.PlayCardsBot(banker.ToIntArr(playerData[seatStr].Cards.Hands), lastCard, lastColor, penalty, blackFirst, numberFirst, canPlus2)
				_, str := PSC_ON_00013.Deck.Convert(card)
				debug("Draw Card - ", "Seat:", seat, "Card:", str, "Hands:", PSC_ON_00013.Deck.ConvertToLog(banker.ToIntArr(playerData[seatStr].Cards.Hands)))

			}

			if len(c) > 0 {
				_, _, name := PSC_ON_00013.Deck.CardInfo(c[0])
				if name == "W" || name == "WD" {
					color = probability.Service.ChooseColor(playerData[seatStr], playerData)
				}

				_, str := PSC_ON_00013.Deck.Convert(c[0])
				debug("Play Card - ", "Seat:", seat, "Card:", str, "Hands:", PSC_ON_00013.Deck.ConvertToLog(banker.ToIntArr(playerData[seatStr].Cards.Hands)))


				playerData[seatStr].Cards.Hands = NewCards(int32(c[0]), playerData[seatStr].Cards.Hands)
				disCards = append(disCards, lastCard)
				lastCard = c[0]
				lastColor = color
				isWildDraw = SpecialCard(c[0])
			}

			if penalty > 0 {
				CheckPenalty(isWildDraw)
			}

			playerData[seatStr].Cards.SumPoint = int32(PSC_ON_00013.Deck.Sum(banker.ToIntArr(playerData[seatStr].Cards.Hands)))

			if len(cards) == 0 {
				s := shuffle.Service.ShuffleU("bankerUuid")
				s.Shuffle(disCards)
				cards = disCards
				disCards = []int{}
				debug("Shuffle   - ", "Cards:", cards)
			}

			if len(cards) == 0 || len(playerData[seatStr].Cards.Hands) == 0 {
				accountingSn := make(map[string]uint64)
				lottery.Service.Result(bet, accountingSn, seat, playerData, "", "", "", true)

				for _, p := range playerData {
					switch PLAYER_AMOUNT {
					case 2:
						fallthrough
					case 3:
						if p.Rank == 1 {
							totalWin[int(p.Seat)] += p.AllScore
							winCount[int(p.Seat)]++
						} else {
							totalLose[int(p.Seat)] += p.AllScore
						}
					case 4:
						if p.Rank == 1 || p.Rank == 2 {
							totalWin[int(p.Seat)] += p.AllScore
							winCount[int(p.Seat)]++
						} else {
							totalLose[int(p.Seat)] += p.AllScore
						}
					}
					totalSumPoint[int(p.Rank - 1)] += p.Cards.SumPoint
					ranking[int(p.Seat)] = p.Rank
				}

				fmt.Println("Result    - ", "Ranking:", ranking)
				debug("**************************************************")

				break
			}
		}
	}

	fmt.Println("贏錢總額", "輸錢總額", "勝率")
	for i := 0; i < PLAYER_AMOUNT; i++ {
		winRate := math.Floor(float64(winCount[i]) / float64(TIMES) * 10000) / 100
		fmt.Println(totalWin[i], totalLose[i], winRate, "%")
	}

	for i := 0; i < PLAYER_AMOUNT; i++ {
		str := "第" + strconv.Itoa(i + 1) + "名平均分數"
		avg := math.Floor(float64(totalSumPoint[i]) / float64(TIMES) * 100) / 100
		fmt.Println(str, avg)
	}

	fmt.Scanf("End")
}

func Init() {
	cards = []int{}
	disCards = []int{}
	playerData = make(map[string]*probability_proto.PlayerData)
	lastCard = -1
	lastColor = -1
	seatOperator = 1
	seat = 0
	penalty = 0
	begin = true
}

func NewCards(card int32, playerCards []int32) []int32 {
	var cardArr []int32
	for _, c := range playerCards {
		if c != card {
			cardArr = append(cardArr, c)
		}
	}

	return cardArr
}

func SpecialCard(card int) bool {
	_, _, name := PSC_ON_00013.Deck.CardInfo(card)
	switch name {
	case "RE":
		if PLAYER_AMOUNT > 2 {
			seatOperator = seatOperator * -1
		} else {
			seat = NextSeat()
		}

	case "SK":
		seat = NextSeat()

	case "D":
		penalty += 2

	case "WD":
		penalty += 4
		return true
	}

	return false
}

func NextSeat() int32 {
	s := seat
	s += seatOperator
	if s == int32(PLAYER_AMOUNT) {
		s = 0
	} else if s < 0 {
		s += int32(PLAYER_AMOUNT)
	}

	return s
}

func CheckPenalty(force bool) {
	if !force {
		for _, c := range playerData[seatStr].Cards.Hands {
			if _, _, n := PSC_ON_00013.Deck.CardInfo(int(c)); n == "D" || n == "WD" {
				return
			}
		}
	}

	seat = NextSeat()

	Penalty()
}

func Penalty() {
	var penaltyCard []string
	for i := 0; i < penalty; i++ {
		if len(cards) == 0 {
			if len(disCards) > 0 {
				s := shuffle.Service.ShuffleU("bankerUuid")
				s.Shuffle(disCards)
				cards = disCards
				disCards = []int{}
				debug("Shuffle   - ", "Cards:", cards)
			} else {
				break
			}
		}

		card := cards[0]
		cards = cards[1:]

		_, name := PSC_ON_00013.Deck.Convert(card)
		penaltyCard = append(penaltyCard, name)
		playerData[seatStr].Cards.Hands = append(playerData[seatStr].Cards.Hands, int32(card))
		if len(disCards) == 0 {
			break
		}
	}

	penalty = 0

	debug("Penalty   - ", "Seat:", seat, "Card:", penaltyCard, "Hands", PSC_ON_00013.Deck.ConvertToLog(banker.ToIntArr(playerData[seatStr].Cards.Hands)))
}

type Config struct {
	Times        int
	PlayerAmount int
	PlayerType   []int
	BotN1        int
	BotN2        int
	PlayerM      int
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