package banker

import (
	"crypto/rand"
	"math/big"
	"sort"
	banker_proto "u-game-server/application/banker/proto"
	"u-game-server/application/gamesettingU"
	"u-game-server/application/lottery"
	"u-game-server/domain/round"
	"u-game-server/domain/shuffleU"

	errorcode "gitlab.iplaystar.net/game-server/error-code"

	"u-game-server/domain/draw"
	draw_proto "u-game-server/domain/draw/proto"

	lobby_settingU_proto "u-game-server/application/lobbysettingU/proto"
	"u-game-server/domain/playcards"
	play_cards_proto "u-game-server/domain/playcards/proto"
	"u-game-server/domain/probability"

	"strconv"
	"sync"
	"time"
	PSC_ON_00013 "u-game-server/domain/probability/PSC-ON-00013"
	probability_proto "u-game-server/domain/probability/proto"
	commonU_proto "u-game-server/models/proto"

	"github.com/gogo/protobuf/proto"
	"github.com/google/uuid"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/mediator"
	"gitlab.iplaystar.net/game-server/shuffle"
	"gitlab.iplaystar.net/game-server/wallet"
)

const (
	EMSGID_eRoundStart                = "EMSGID_eRoundStart"
	EMSGID_eRoundEnd                  = "EMSGID_eRoundEnd"
	EMSGID_ePlayerRoundStart          = "EMSGID_ePlayerRoundStart"
	EMSGID_eBroadcastPlayerRoundStart = "EMSGID_eBroadcastPlayerRoundStart"
	EMSGID_ePenalty                   = "EMSGID_ePenalty"
	EMSGID_eBroadcastPenalty          = "EMSGID_eBroadcastPenalty"
	EMSGID_eKeepCall                  = "EMSGID_eKeepCall"
	EMSGID_eKeepRecall                = "EMSGID_eKeepRecall"
	EMSGID_eKeepTimeout               = "EMSGID_eKeepTimeout"
	EMSGID_eBroadcastKeepRecall       = "EMSGID_eBroadcastKeepRecall"
	EMSGID_eBroadcastKeepTimeout      = "EMSGID_eBroadcastKeepTimeout"
	EMSGID_eBroadcastShuffle          = "EMSGID_eBroadcastShuffle"
	ActionBankerDeal                  = "ActionBankerDeal"
	ActionBankerStart                 = "ActionBankerStart"
	ActionBankerAccountingSn          = "ActionBankerAccountingSn"
	ActionPlayerRoundStart            = "ActionPlayerRoundStart"
	ActionPlayerResumeGame            = "ActionPlayerResumeGame"
	BANKER_SEAT                       = 5
	GAME_ROOM                         = "GAME_ROOM"
	FRIEND_ROOM                       = "FRIEND_ROOM"
	INIT_PLAYER_CARDS_AMOUNT          = 7
	RANKING_UNO                       = 0
	RANKING_PREDICT                   = 1
	SHUFFLE_DELAY                     = 2
	WILDDRAW_DELAY                    = 3
	FUNCTIONAL_DELAY                  = 2
	NORMAL_DELAY                      = 1
)

func Builder() *builder {
	return &builder{
		from:      "",
		uuid:      "",
		roomUuid:  "",
		roomType:  "",
		size:      0,
		startSeat: 0,
		betCent:   0,
		roundTime: 0,
	}
}

type builder struct {
	from        string
	uuid        string
	roomUuid    string
	roomType    string
	size        int32
	startSeat   int32
	betCent     uint64
	roundTime   uint32
	predictTime uint32
}

type seatInfo struct {
	startSeat    int32
	seatIndex    int32
	seatOperator int32
	seatArr      []int
}

type banker struct {
	from                    string // not used now
	uuid                    string
	roomUuid                string
	roomType                string
	size                    int32 // how many players
	deck                    map[int][]int
	betCent                 uint64
	accountingSn            map[string]uint64
	in                      chan *flux.Action
	rwMutex                 *sync.RWMutex
	cards                   []int
	disCards                []int
	totalCards              []int
	results                 map[string]*probability_proto.PlayerData
	seatInfo                *seatInfo
	resumePlayer            map[string]string
	lastColor               int
	lastCard                int
	lastDraw                int
	penalty                 int
	luckyCard               int
	nextDelay               int
	begin                   bool
	shuffle                 bool
	vip                     bool
	initial                 bool
	roundTime               uint32
	predictTime             uint32
	endTime                 time.Time
	accountingSnBySeat      map[int]uint64
	originalSecWebSocketKey map[string]string
}

func (b *builder) setFrom(from string) *builder {
	b.from = from
	return b
}

func (b *builder) setRoomUuid(roomUuid string) *builder {
	b.roomUuid = roomUuid
	return b
}

func (b *builder) setRoomType(roomType string) *builder {
	b.roomType = roomType
	return b
}

func (b *builder) setSize(size int32) *builder {
	b.size = size
	return b
}

func (b *builder) setStartSeat(startSeat int32) *builder {
	if seat := shuffleU.Service.StartSeat(); seat < 0 || seat >= int(b.size) {
		b.startSeat = startSeat
	} else {
		b.startSeat = int32(seat)
	}
	return b
}

func (b *builder) setBetCent(betCent uint64) *builder {
	b.betCent = betCent
	return b
}

func (b *builder) setRoundTime(time uint32) *builder {
	b.roundTime = time
	return b
}

func (b *builder) setPredictTime(time uint32) *builder {
	b.predictTime = time
	return b
}

func (b *builder) build() *banker {
	v := &banker{
		from:         b.from,
		uuid:         uuid.New().String(),
		roomUuid:     b.roomUuid,
		roomType:     b.roomType,
		size:         b.size,
		betCent:      b.betCent,
		deck:         make(map[int][]int),
		accountingSn: make(map[string]uint64),
		in:           make(chan *flux.Action, 128),
		rwMutex:      &sync.RWMutex{},
		results:      make(map[string]*probability_proto.PlayerData),
		seatInfo: &seatInfo{
			startSeat:    -1,
			seatIndex:    b.startSeat,
			seatOperator: 1,
			seatArr:      make([]int, 0),
		},
		resumePlayer:            make(map[string]string),
		lastColor:               -1,
		lastCard:                -1,
		lastDraw:                -1,
		penalty:                 0,
		luckyCard:               0,
		nextDelay:               0,
		begin:                   true,
		shuffle:                 false,
		vip:                     false,
		initial:                 false,
		roundTime:               b.roundTime,
		predictTime:             b.predictTime,
		accountingSnBySeat:      map[int]uint64{},
		originalSecWebSocketKey: map[string]string{},
	}

	v.init()

	go v.run()

	return v
}

func (b *banker) init() {
	cards := shuffle.Service.ShuffleCardU(b.uuid)
	startCard := shuffleU.Service.StartCard()
	if startCard < 0 || startCard >= len(cards) {
		b.lastCard = probability.Service.InitialCard(cards)
	} else {
		b.lastCard = startCard
	}
	_, b.lastColor, _ = PSC_ON_00013.Deck.CardInfo(b.lastCard)
	var newCards []int
	for _, card := range cards {
		if card != b.lastCard {
			newCards = append(newCards, card)
		}
	}
	b.luckyCard = shuffleU.Service.LuckyCard()
	b.cards = newCards
	b.totalCards = newCards
	b.disCards = []int{}
}

func (b *banker) run() {
	flux.Register(b.uuid, b.in)
	timer := time.NewTimer(time.Duration(b.roundTime) * time.Second)
	predictTimer := time.NewTimer(time.Duration(b.roundTime-b.predictTime) * time.Second)
	checkTimer := time.NewTimer(10 * time.Second)
	b.endTime = time.Now().Add(time.Duration(b.roundTime))

	for {
		select {
		case action, ok := <-b.in:
			if !ok || b.size == -1 {
				return
			}
			b.handleAction(action)

		case <-timer.C:
			if b.size > 0 {
				b.roundTimeUp()
			}

		case <-predictTimer.C:
			if b.size > 0 {
				switch b.size {
				case 2:
					lottery.Service.Ranking2(int32(b.seatInfo.seatArr[b.seatInfo.seatIndex]), b.results)
				case 3:
					lottery.Service.Ranking3(int32(b.seatInfo.seatArr[b.seatInfo.seatIndex]), b.results)
				case 4:
					lottery.Service.Ranking4(int32(b.seatInfo.seatArr[b.seatInfo.seatIndex]), b.results)
				}
				lottery.Service.BroadcastRanking(b.roomUuid, b.results, RANKING_PREDICT)
			}

		case <-checkTimer.C:
			if !b.initial {
				// something wrong, result directly
				logger.Service.Zap.Errorw(Banker_INITIAL_ERROR,
					"BankerUuid", b.uuid,
					"GameRoomUuid", b.roomUuid,
					"GameRoomType", b.roomType,
					"Size", b.size,
					"PlayerData", b.results,
				)

				b.result(-1)

				for k := range b.results {
					errorcode.Service.Fatal(k, Banker_INITIAL_ERROR)
				}
			}
		}
	}
}

func (b *banker) handleAction(action *flux.Action) {
	if b.uuid != action.Key().To() {
		return
	}
	logger.Service.Zap.Infow(action.Key().Name(),
		"BankerUuid", b.uuid,
		"GameRoomUuid", b.roomUuid,
		"GameRoomType", b.roomType,
		"Size", b.size,
		"Data", b.accountingSn,
	)
	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:

		flux.Send(ActionBankerStart, b.uuid, b.roomUuid, b.uuid)

		time.Sleep(1000 * time.Millisecond)

		b.eRoundStart()

	case ActionBankerAccountingSn:
		switch b.roomType {
		case GAME_ROOM:
			secWebSocketKey := action.Key().From()
			accountingSn := action.Payload()[0].(uint64)
			seat := action.Payload()[1].(int)

			b.accountingSn[secWebSocketKey] = accountingSn
			b.accountingSnBySeat[seat] = accountingSn

		case FRIEND_ROOM:
			secWebSocketKey := string(action.Payload()[0].([]byte))
			accountingSn, _ := strconv.ParseUint(string(action.Payload()[1].([]byte)), 10, 64)

			b.accountingSn[secWebSocketKey] = accountingSn

		default:
			panic("ERROR ROOM TYPE")
		}

		logger.Service.Zap.Infow("Banker Got Accounting SN",
			"BankerUuid", b.uuid,
			"GameRoomUuid", b.roomUuid,
			"GameRoomType", b.roomType,
			"Size", b.size,
			"Data", b.accountingSn,
		)
	case ActionBankerDeal:
		b.rwMutex.Lock()

		seat := action.Payload()[0].(int)
		avatar := action.Payload()[1].(string)
		blacklistValue := action.Payload()[2].(uint32)

		secWebSocketKey := action.Key().From()

		b.deck[seat] = []int{}
		luckyCount := 0
		luckyPercent := gamesettingU.Service.LuckyPercent(secWebSocketKey)
		luckyMax := gamesettingU.Service.LuckyMax(secWebSocketKey)
		if blacklistValue > 0 {
			r, _ := rand.Int(rand.Reader, big.NewInt(100))
			if r.Int64() < int64(blacklistValue) {
				luckyPercent = gamesettingU.Service.LuckyPercentVIP(secWebSocketKey)
				luckyMax = gamesettingU.Service.LuckyMaxVIP(secWebSocketKey)
				b.vip = true
			}
		}
		for i := 0; i < INIT_PLAYER_CARDS_AMOUNT; i++ {
			card := b.totalCards[seat*INIT_PLAYER_CARDS_AMOUNT+i]
			if b.luckyCard != 0 {
				card = probability.Service.LuckyCard(b.cards, luckyCount, luckyMax, luckyPercent)
			}
			if _, _, name := PSC_ON_00013.Deck.CardInfo(card); name != "" {
				luckyCount++
			}
			b.deck[seat] = append(b.deck[seat], card)
			var newCards []int
			for _, c := range b.cards {
				if c != card {
					newCards = append(newCards, c)
				}
			}
			b.cards = newCards
		}

		hands := b.deck[seat]
		p := &probability_proto.PlayerData{
			Seat:        int32(seat),
			PokerNumber: int32(len(hands)),
			AllWin:      0,
			AllScore:    0,
			Cards: &probability_proto.Cards{
				Hands:    ToInt32Arr(hands),
				SumPoint: int32(PSC_ON_00013.Deck.Sum(hands)),
			},
			Avatar: avatar,
		}
		cent, _ := wallet.Service.CentCache(secWebSocketKey)
		p.Cent = cent
		b.results[secWebSocketKey] = p
		b.seatInfo.seatArr = append(b.seatInfo.seatArr, seat)
		flux.Send(ActionBankerDeal, b.uuid, secWebSocketKey, p, len(b.totalCards)-int(b.size)*INIT_PLAYER_CARDS_AMOUNT)

		b.rwMutex.Unlock()

		if len(b.seatInfo.seatArr) == int(b.size) {
			sort.Ints(b.seatInfo.seatArr)
			b.seatInfo.startSeat = int32(b.seatInfo.seatArr[b.seatInfo.seatIndex])
			b.initial = true

			time.Sleep(10 * time.Second)

			flux.Send(ActionPlayerRoundStart, b.uuid, b.uuid)
		}

	case ActionPlayerRoundStart:
		if !b.checkLegal() {
			return
		}

		b.rwMutex.Lock()
		defer b.rwMutex.Unlock()

		time.Sleep(time.Duration(b.nextDelay) * time.Second)
		b.nextDelay = NORMAL_DELAY

		if b.shuffle {
			b.eBroadcastShuffle()
			b.shuffle = false
			time.Sleep(SHUFFLE_DELAY * time.Second)
		}

		if b.begin {
			b.begin = false
		} else {
			b.seatInfo.seatIndex = b.nextSeat()
		}
		seat := b.seatInfo.seatArr[b.seatInfo.seatIndex]
		logger.Service.Zap.Infow("QA LOG ---> Player's Round", "ID", b.uuid, "Seat", seat, "Deck:", PSC_ON_00013.Deck.ConvertToLog(b.cards))
		logger.Service.Zap.Infow("QA LOG ---> Player's Round", "ID", b.uuid, "Seat", seat, "Hand:", PSC_ON_00013.Deck.ConvertToLog(b.deck[seat]))
		b.eBroadcastPlayerRoundStart(b.ePlayerRoundStart(seat))
		b.lastDraw = -1

	case ActionPlayerResumeGame:
		go func() {
			if !b.initial {
				for {
					if b.initial {
						break
					}
				}
			}

			b.rwMutex.Lock()
			defer b.rwMutex.Unlock()

			secWebSocketKey := action.Key().From()
			data := action.Payload()[0].(*lobby_settingU_proto.ConfigRecall)
			seat := data.ResumeGame.GameRecovery.Snapshot.Seat
			data.ResumeGame.Pool = uint32(len(b.cards))
			data.ResumeGame.Seat = int32(b.seatInfo.seatArr[b.seatInfo.seatIndex])
			data.ResumeGame.StartSeat = b.seatInfo.startSeat
			data.ResumeGame.BankerUuid = b.uuid
			data.ResumeGame.LastCard = int32(b.lastCard)
			data.ResumeGame.RoundTime = int32(b.roundTime) - int32(time.Now().Sub(b.endTime).Seconds())
			if b.seatInfo.seatOperator == 1 {
				data.ResumeGame.Direction = 0
			} else {
				data.ResumeGame.Direction = 1
			}
			data.ResumeGame.LastColor = int32(b.lastColor)
			data.ResumeGame.Penalty = int32(b.penalty)
			for k, p := range b.results {
				if p.Seat == seat {
					data.ResumeGame.PlayerData = append(data.ResumeGame.PlayerData, p)
					delete(b.results, k)
					b.results[secWebSocketKey] = p
					b.resumePlayer[k] = secWebSocketKey
					gamesettingU.Service.Clone(k, secWebSocketKey)
					flux.Send(draw.ActionDrawResume, b.uuid, draw.Service.Id, secWebSocketKey, k, b.resumePlayer)
					flux.Send(playcards.ActionPlayCardsResume, b.uuid, playcards.Service.Id, secWebSocketKey, k, b.resumePlayer)
					flux.Send(round.ActionRoundResume, b.uuid, round.Service.Id, secWebSocketKey, k, b.resumePlayer)
					key := k
					if kk, ok := b.originalSecWebSocketKey[key]; ok {
						key = kk
					}
					b.originalSecWebSocketKey[secWebSocketKey] = key
				} else {
					p := &probability_proto.PlayerData{
						Seat:        p.Seat,
						PokerNumber: int32(len(p.Cards.Hands)),
						PlayCard:    p.PlayCard,
						AllWin:      p.AllWin,
						AllScore:    p.AllScore,
						Cent:        p.Cent,
					}
					data.ResumeGame.PlayerData = append(data.ResumeGame.PlayerData, p)
				}
			}
			data.ResumeGame.WaitingTime = append(data.ResumeGame.WaitingTime, gamesettingU.Service.FirstRoundStartWaitingTime(secWebSocketKey))
			data.ResumeGame.WaitingTime = append(data.ResumeGame.WaitingTime, gamesettingU.Service.PlayerRoundWaitingTime(secWebSocketKey))
			data.ResumeGame.WaitingTime = append(data.ResumeGame.WaitingTime, gamesettingU.Service.RoundStartWaitingTime(secWebSocketKey))
			for i, s := range b.accountingSnBySeat {
				if i == int(seat) {
					data.ResumeGame.AccountingSn = s
				}
			}

			flux.Send(ActionPlayerResumeGame, b.uuid, b.roomUuid, data, secWebSocketKey)
		}()

	case draw.EMSGID_eDrawTimeout:
		fallthrough
	case draw.EMSGID_eDrawRecall:
		if !b.checkLegal() {
			return
		}

		b.rwMutex.Lock()

		secWebSocketKey := action.Payload()[1].(string)
		kind := action.Payload()[2].(string)

		if v, ok := b.resumePlayer[secWebSocketKey]; ok {
			secWebSocketKey = v
		}

		playerData := b.results[secWebSocketKey]
		drawPercent := gamesettingU.Service.DrawPercent(secWebSocketKey)
		if b.vip {
			drawPercent = gamesettingU.Service.DrawPercentVIP(secWebSocketKey)
		}
		card := probability.Service.DrawBot(b.cards, b.lastCard, b.lastColor, drawPercent)
		isPenalty := false

		if b.penalty > 0 {
			b.eBroadcastPenalty(b.ePenalty(secWebSocketKey, playerData))
			isPenalty = true
		} else {
			r, _ := rand.Int(rand.Reader, big.NewInt(100))
			if kind != draw.BOT && int(r.Int64()) < gamesettingU.Service.UnluckyRate(secWebSocketKey, b.vip) {
				index := probability.Service.UnluckyDrawCard(b.cards, b.lastCard, b.lastColor)
				card = b.cards[index]
				b.cards = append(b.cards[:index], b.cards[(index+1):]...)
			} else if kind == draw.BOT && card != -1 {
				var newCards []int
				for _, c := range b.cards {
					if c != card {
						newCards = append(newCards, c)
					}
				}
				b.cards = newCards
			} else {
				card = b.cards[0]
				b.cards = b.cards[1:]
			}
			b.lastDraw = card
			b.deck[int(playerData.Seat)] = append(b.deck[int(playerData.Seat)], card)
		}

		hands := b.deck[int(playerData.Seat)]
		playerData.Cards.Hands = ToInt32Arr(hands)
		cards := &probability_proto.Cards{
			Hands:    ToInt32Arr(hands),
			SumPoint: int32(PSC_ON_00013.Deck.Sum(hands)),
		}
		playerData.Cards = cards
		playerData.PokerNumber = int32(len(hands))
		switch action.Payload()[0].(type) {
		case *draw_proto.DrawTimeout:
			data := action.Payload()[0].(*draw_proto.DrawTimeout)
			data.PlayerData = playerData
			data.Pool = uint32(len(b.cards))
			data.Card = int32(card)
			dataByte, _ := proto.Marshal(data)

			canPlay := probability.Service.CheckCardNormal(card, b.lastCard, -1, b.lastColor, -1)

			if isPenalty {
				canPlay = false
			}

			flux.Send(draw.EMSGID_eDrawTimeout, b.uuid, secWebSocketKey, dataByte, canPlay, isPenalty, card)

			if !isPenalty {
				flux.Send(draw.EMSGID_eBroadcastDrawTimeout, b.uuid, b.roomUuid, draw.Service.BroadcastDrawTimeout(data))
			}

		case *draw_proto.DrawRecall:
			data := action.Payload()[0].(*draw_proto.DrawRecall)

			data.PlayerData = playerData
			data.Pool = uint32(len(b.cards))
			data.Card = int32(card)
			dataByte, _ := proto.Marshal(data)

			canPlay := probability.Service.CheckCardNormal(card, b.lastCard, -1, b.lastColor, -1)

			if isPenalty {
				canPlay = false
			}

			flux.Send(draw.EMSGID_eDrawRecall, b.uuid, secWebSocketKey, dataByte, canPlay, isPenalty, card)

			if !isPenalty {
				flux.Send(draw.EMSGID_eBroadcastDrawRecall, b.uuid, b.roomUuid, draw.Service.BroadcastDrawRecall(data))
			}
		}

		logger.Service.Zap.Infow("QA LOG ---> Player Draw", "ID", b.uuid, "Seat", playerData.Seat, "Hand:", PSC_ON_00013.Deck.ConvertToLog(b.deck[int(playerData.Seat)]))

		if len(b.cards) == 0 {
			s := shuffle.Service.ShuffleU(b.uuid)
			s.Shuffle(b.disCards)
			b.cards = b.disCards
			b.disCards = []int{}
			b.shuffle = true
		}

		b.rwMutex.Unlock()

		if len(b.cards) == 0 {
			b.size = -1

			b.result(playerData.Seat)
		}

	case playcards.EMSGID_ePlayCardsTimeout:
		fallthrough
	case playcards.EMSGID_ePlayCardsRecall:
		if !b.checkLegal() {
			return
		}

		b.rwMutex.Lock()

		secWebSocketKey := action.Payload()[1].(string)
		seat := action.Payload()[2].(int32)
		kind := action.Payload()[3].(string)

		if v, ok := b.resumePlayer[secWebSocketKey]; ok {
			secWebSocketKey = v
		}

		p := b.results[secWebSocketKey]
		blackFirst := false
		var nextP *probability_proto.PlayerData
		var nextSecWebSocketKey string
		for k, r := range b.results {
			if r.Seat == b.nextSeat() {
				nextP = r
				nextSecWebSocketKey = k
			}
			if k != secWebSocketKey {
				if len(r.Cards.Hands) <= 3 {
					blackFirst = true
				}
			}
		}
		force := false

		switch action.Payload()[0].(type) {
		case *play_cards_proto.PlayCardsTimeout:
			data := action.Payload()[0].(*play_cards_proto.PlayCardsTimeout)
			var card []int
			var color int
			if kind == playcards.PLAYER {
				card, color = probability.Service.PlayCardsPlayer(ToIntArr(p.Cards.Hands), b.lastCard, b.lastColor, b.penalty)
			} else {
				numberFirst := true
				roundTime := b.roundTime - uint32(time.Now().Sub(b.endTime).Seconds())
				if roundTime <= gamesettingU.Service.BotLogicTime(secWebSocketKey) {
					numberFirst = false
				}
				card, color = probability.Service.PlayCardsBot(ToIntArr(p.Cards.Hands), b.lastCard, b.lastColor, b.penalty, blackFirst, numberFirst, true)
			}
			if _, _, name := PSC_ON_00013.Deck.CardInfo(card[0]); name == "W" || name == "WD" {
				color = probability.Service.ChooseColor(p, b.results)
			}
			p.Cards = b.playCard(card[0], int(seat))
			p.PokerNumber = int32(len(b.deck[int(seat)]))
			p.PlayCard = ToInt32Arr(card)
			b.disCards = append(b.disCards, b.lastCard)
			b.lastCard = card[0]
			b.lastColor = color
			force = b.specialCard(card[0])

			data.PlayerData = p
			data.Color = int32(color)
			dataByte, _ := proto.Marshal(data)

			if _, _, name := PSC_ON_00013.Deck.CardInfo(card[0]); name == "WD" {
				b.nextDelay = WILDDRAW_DELAY
			} else if name != "" {
				b.nextDelay = FUNCTIONAL_DELAY
			}

			playcards.Service.BroadcastPlayCardsTimeout(data)
			flux.Send(playcards.EMSGID_ePlayCardsTimeout, b.uuid, secWebSocketKey, dataByte)

		case *play_cards_proto.PlayCardsRecall:
			data := action.Payload()[0].(*play_cards_proto.PlayCardsRecall)
			call := action.Payload()[4].(*play_cards_proto.PlayCardsCall)
			card := ToIntArr(call.Cards)
			color := int(call.Color)

			p.Cards = b.playCard(card[0], int(seat))
			p.PokerNumber = int32(len(b.deck[int(seat)]))
			p.PlayCard = ToInt32Arr(card)
			b.disCards = append(b.disCards, b.lastCard)
			b.lastCard = card[0]
			b.lastColor = color
			force = b.specialCard(card[0])

			data.PlayerData = p
			data.Color = int32(color)
			dataByte, _ := proto.Marshal(data)

			if _, _, name := PSC_ON_00013.Deck.CardInfo(card[0]); name == "WD" {
				b.nextDelay = WILDDRAW_DELAY
			} else if name != "" {
				b.nextDelay = FUNCTIONAL_DELAY
			}

			playcards.Service.BroadcastPlayCardsRecall(data)
			flux.Send(playcards.EMSGID_ePlayCardsRecall, b.uuid, secWebSocketKey, dataByte)
		}

		logger.Service.Zap.Infow("QA LOG ---> Player Play Card", "ID", b.uuid, "Seat", p.Seat, "Hand:", PSC_ON_00013.Deck.ConvertToLog(b.deck[int(p.Seat)]))

		waitPenalty := false
		if b.penalty > 0 {
			if len(p.Cards.Hands) == 0 {
				force = true
			}
			waitPenalty = b.checkPenalty(nextSecWebSocketKey, nextP, force)
		}

		if len(p.Cards.Hands) == 1 {
			time.Sleep(500 * time.Millisecond)

			switch b.size {
			case 2:
				lottery.Service.Ranking2(seat, b.results)
			case 3:
				lottery.Service.Ranking3(seat, b.results)
			case 4:
				lottery.Service.Ranking4(seat, b.results)
			}
			lottery.Service.BroadcastRanking(b.roomUuid, b.results, RANKING_UNO)
		}

		if len(b.cards) == 0 {
			s := shuffle.Service.ShuffleU(b.uuid)
			s.Shuffle(b.disCards)
			b.cards = b.disCards
			b.disCards = []int{}
			b.shuffle = true
		}

		b.rwMutex.Unlock()

		if len(p.Cards.Hands) == 0 || len(b.cards) == 0 {
			b.size = -1

			if waitPenalty {
				time.Sleep(WILDDRAW_DELAY * time.Second)
			}

			b.result(seat)
		}

	case round.ActionRoundTimeout:
		if !b.checkLegal() {
			return
		}

		secWebSocketKey := action.Payload()[0].(string)
		kind := action.Payload()[1].(string)
		state := action.Payload()[2].(string)

		playerData := b.results[secWebSocketKey]
		var cards []int
		if kind == round.PLAYER {
			cards, _ = probability.Service.PlayCardsPlayer(ToIntArr(playerData.Cards.Hands), b.lastCard, b.lastColor, b.penalty)
		} else {
			cards, _ = probability.Service.PlayCardsBot(ToIntArr(playerData.Cards.Hands), b.lastCard, b.lastColor, b.penalty, false, false, true)
		}

		switch state {
		case round.STATE_START:
			if len(cards) == 0 {
				if b.penalty > 0 {
					flux.Send(EMSGID_eKeepTimeout, b.uuid, b.uuid, secWebSocketKey)
				} else {
					flux.Send(draw.EMSGID_eDrawTimeout, b.uuid, draw.Service.Id, secWebSocketKey)
				}
			} else {
				flux.Send(playcards.EMSGID_ePlayCardsTimeout, b.uuid, playcards.Service.Id, secWebSocketKey)
			}

		case round.STATE_DRAW:
			if len(cards) == 0 {
				flux.Send(EMSGID_eKeepTimeout, b.uuid, b.uuid, secWebSocketKey)
			} else {
				flux.Send(playcards.EMSGID_ePlayCardsTimeout, b.uuid, playcards.Service.Id, secWebSocketKey)
			}

		default:
			break
		}

	case EMSGID_eKeepCall:
		flux.Send(EMSGID_eKeepRecall, b.uuid, b.uuid, action.Key().From())

	case EMSGID_eKeepTimeout:
		if !b.checkLegal() {
			return
		}

		b.rwMutex.Lock()

		secWebSocketKey := action.Payload()[0].(string)

		playerData := b.results[secWebSocketKey]

		b.eBroadcastKeepTimeout(b.eKeepTimeout(secWebSocketKey), playerData.Seat)

		b.rwMutex.Unlock()

		if b.penalty > 0 {
			time.Sleep(500 * time.Millisecond)

			b.eBroadcastPenalty(b.ePenalty(secWebSocketKey, b.results[secWebSocketKey]))

			if len(b.cards) == 0 {
				b.size = -1

				time.Sleep(3 * time.Second)

				seat := int32(b.seatInfo.seatArr[b.seatInfo.seatIndex])
				b.result(seat)
			}
		}

	case EMSGID_eKeepRecall:
		if !b.checkLegal() {
			return
		}

		b.rwMutex.Lock()

		secWebSocketKey := action.Payload()[0].(string)

		playerData := b.results[secWebSocketKey]

		b.eBroadcastKeepRecall(b.eKeepRecall(secWebSocketKey), playerData.Seat)

		b.rwMutex.Unlock()

		if b.penalty > 0 {
			time.Sleep(500 * time.Millisecond)

			b.eBroadcastPenalty(b.ePenalty(secWebSocketKey, b.results[secWebSocketKey]))

			if len(b.cards) == 0 {
				b.size = -1

				time.Sleep(3 * time.Second)

				seat := int32(b.seatInfo.seatArr[b.seatInfo.seatIndex])
				b.result(seat)
			}
		}
	}
}

func (b *banker) playCard(card int, seat int) *probability_proto.Cards {
	var newCards []int
	for _, deckCard := range b.deck[seat] {
		if deckCard != card {
			newCards = append(newCards, deckCard)
		}
	}

	b.deck[seat] = newCards

	c := &probability_proto.Cards{
		Hands:    ToInt32Arr(newCards),
		SumPoint: int32(PSC_ON_00013.Deck.Sum(newCards)),
	}

	return c
}

func (b *banker) specialCard(card int) bool {
	_, _, name := PSC_ON_00013.Deck.CardInfo(card)
	switch name {
	case "RE":
		if b.size > 2 {
			b.seatInfo.seatOperator *= -1
		} else {
			b.seatInfo.seatIndex = b.nextSeat()
		}

	case "SK":
		b.seatInfo.seatIndex = b.nextSeat()

	case "D":
		b.penalty += 2

	case "WD":
		b.penalty += 4
		return true
	}

	return false
}

func (b *banker) nextSeat() int32 {
	seat := b.seatInfo.seatIndex
	seat += b.seatInfo.seatOperator
	if seat == b.size {
		seat = 0
	} else if seat < 0 {
		seat += b.size
	}
	return seat
}

func (b *banker) checkPenalty(secWebSocketKey string, playerData *probability_proto.PlayerData, force bool) bool {
	if !force {
		for _, c := range playerData.Cards.Hands {
			if _, _, n := PSC_ON_00013.Deck.CardInfo(int(c)); n == "D" || n == "WD" {
				return false
			}
		}
	}
	b.seatInfo.seatIndex = b.nextSeat()

	time.Sleep(500 * time.Millisecond)

	b.eBroadcastPenalty(b.ePenalty(secWebSocketKey, playerData))

	return true
}

func (b *banker) eRoundStart() {
	data := &banker_proto.RoundStart{
		Msgid:       commonU_proto.EMSGID_eRoundStart,
		RoomUuid:    b.roomUuid,
		BankerUuid:  b.uuid,
		PlayerInfos: nil,
		Card:        int32(b.lastCard),
		RoundTime:   b.roundTime,
	}
	logger.Service.Zap.Infow("eRoundStart")
	flux.Send(EMSGID_eRoundStart, b.uuid, b.roomUuid, data)
}

func (b *banker) eRoundEnd() {
	data := &banker_proto.RoundEnd{
		Msgid:    commonU_proto.EMSGID_eRoundEnd,
		RoomUuid: b.roomUuid,
	}

	dataByte, _ := proto.Marshal(data)

	flux.Send(EMSGID_eRoundEnd, b.uuid, b.roomUuid, dataByte)
}

func (b *banker) ePlayerRoundStart(seat int) *banker_proto.PlayerRoundStart {
	data := &banker_proto.PlayerRoundStart{
		Msgid:    commonU_proto.EMSGID_ePlayRoundStart,
		RoomUuid: b.roomUuid,
		Seat:     int32(seat),
		Penalty:  int32(b.penalty),
	}

	flux.Send(EMSGID_ePlayerRoundStart, b.uuid, b.roomUuid, data, b.deck[seat], b.lastCard, b.lastColor, b.penalty)
	return data
}

func (b *banker) eBroadcastPlayerRoundStart(playerroundstar *banker_proto.PlayerRoundStart) {
	data := &banker_proto.BroadcastPlayerRoundStart{
		Msgid: commonU_proto.EMSGID_eBroadcastPlayRoundStart,
		PlayerRoundStart: &banker_proto.PlayerRoundStart{
			Msgid:    commonU_proto.EMSGID_ePlayRoundStart,
			RoomUuid: playerroundstar.RoomUuid,
			Seat:     playerroundstar.Seat,
		},
	}
	dataByte, _ := proto.Marshal(data)
	flux.Send(EMSGID_eBroadcastPlayerRoundStart, b.uuid, b.roomUuid, dataByte)
}

func (b *banker) ePenalty(secWebSocketKey string, playerData *probability_proto.PlayerData) *banker_proto.Penalty {
	var penaltyCards []int
	for i := 0; i < b.penalty; i++ {
		if len(b.cards) == 0 {
			if len(b.disCards) > 0 {
				s := shuffle.Service.ShuffleU(b.uuid)
				s.Shuffle(b.disCards)
				b.cards = b.disCards
				b.disCards = []int{}
				b.shuffle = true
			} else {
				break
			}
		}

		card := b.cards[0]
		b.cards = b.cards[1:]

		b.deck[int(playerData.Seat)] = append(b.deck[int(playerData.Seat)], card)
		penaltyCards = append(penaltyCards, card)
		if len(b.disCards) == 0 {
			break
		}
	}

	hands := b.deck[int(playerData.Seat)]
	playerData.Cards.Hands = ToInt32Arr(hands)
	cards := &probability_proto.Cards{
		Hands:    ToInt32Arr(hands),
		SumPoint: int32(PSC_ON_00013.Deck.Sum(hands)),
	}
	playerData.Cards = cards
	playerData.PokerNumber = int32(len(hands))

	data := &banker_proto.Penalty{
		Msgid:      commonU_proto.EMSGID_ePenalty,
		Cards:      ToInt32Arr(penaltyCards),
		CardNum:    int32(len(penaltyCards)),
		PlayerData: playerData,
		Pool:       uint32(len(b.cards)),
	}
	dataByte, _ := proto.Marshal(data)

	b.penalty = 0

	logger.Service.Zap.Infow("QA LOG ---> Player Penalty", "ID", b.uuid, "Seat", playerData.Seat, "Hand:", PSC_ON_00013.Deck.ConvertToLog(b.deck[int(playerData.Seat)]))

	flux.Send(EMSGID_ePenalty, b.uuid, secWebSocketKey, dataByte)
	return data
}

func (b *banker) eBroadcastPenalty(penalty *banker_proto.Penalty) {
	data := &banker_proto.BroadcastPenalty{
		Msgid: commonU_proto.EMSGID_eBroadcastPenalty,
		Penalty: &banker_proto.Penalty{
			Msgid:   commonU_proto.EMSGID_ePenalty,
			CardNum: penalty.CardNum,
			Pool:    penalty.Pool,
		},
		Seat: penalty.PlayerData.Seat,
	}
	dataByte, _ := proto.Marshal(data)
	flux.Send(EMSGID_eBroadcastPenalty, b.uuid, b.roomUuid, dataByte)
}

func (b *banker) eKeepRecall(secWebSocketKey string) *banker_proto.KeepRecall {
	data := &banker_proto.KeepRecall{
		Msgid: commonU_proto.EMSGID_eKeepRecall,
	}
	dataByte, _ := proto.Marshal(data)
	flux.Send(EMSGID_eKeepRecall, b.uuid, secWebSocketKey, dataByte)
	return data
}

func (b *banker) eBroadcastKeepRecall(keepRecall *banker_proto.KeepRecall, seat int32) {
	data := &banker_proto.BroadcastKeepRecall{
		Msgid: commonU_proto.EMSGID_eBroadcastKeepRecall,
		Seat:  seat,
	}
	dataByte, _ := proto.Marshal(data)
	flux.Send(EMSGID_eBroadcastKeepRecall, b.uuid, b.roomUuid, dataByte)
}

func (b *banker) eKeepTimeout(secWebSocketKey string) *banker_proto.KeepTimeout {
	data := &banker_proto.KeepTimeout{
		Msgid: commonU_proto.EMSGID_eKeepTimeout,
	}
	dataByte, _ := proto.Marshal(data)
	flux.Send(EMSGID_eKeepTimeout, b.uuid, secWebSocketKey, dataByte)
	return data
}

func (b *banker) eBroadcastKeepTimeout(keepTimeout *banker_proto.KeepTimeout, seat int32) {
	data := &banker_proto.BroadcastKeepTimeout{
		Msgid: commonU_proto.EMSGID_eBroadcastKeepTimeout,
		Seat:  seat,
	}
	dataByte, _ := proto.Marshal(data)
	flux.Send(EMSGID_eBroadcastKeepTimeout, b.uuid, b.roomUuid, dataByte)
}

func (b *banker) eBroadcastShuffle() {
	data := &banker_proto.BroadcastShuffle{
		Msgid: commonU_proto.EMSGID_eBroadcastShuffle,
	}
	dataByte, _ := proto.Marshal(data)
	flux.Send(EMSGID_eBroadcastShuffle, b.uuid, b.roomUuid, dataByte)
}

func (b *banker) roundTimeUp() {
	b.rwMutex.Lock()
	defer b.rwMutex.Unlock()

	waitPenalty := false
	if b.penalty > 0 {
		var p *probability_proto.PlayerData
		var nextP *probability_proto.PlayerData
		var secWebSocketKey string
		var nextSecWebSocketKey string
		for k, r := range b.results {
			if r.Seat == int32(b.seatInfo.seatArr[b.seatInfo.seatIndex]) {
				p = r
				secWebSocketKey = k
			} else if r.Seat == b.nextSeat() {
				nextP = r
				nextSecWebSocketKey = k
			}
		}
		if state := round.Service.State(secWebSocketKey); state == round.STATE_PLAYCARD || state == round.STATE_END {
			p = nextP
			secWebSocketKey = nextSecWebSocketKey
		}
		b.eBroadcastPenalty(b.ePenalty(secWebSocketKey, p))
		waitPenalty = true
	}

	b.size = -1

	if waitPenalty {
		time.Sleep(WILDDRAW_DELAY * time.Second)
	}

	seat := int32(b.seatInfo.seatArr[b.seatInfo.seatIndex])
	b.result(seat)
}

func (b *banker) result(seat int32) {
	lottery.Service.Result(b.betCent, b.accountingSn, seat, b.results, b.roomUuid, b.roomType, b.uuid, false, b.originalSecWebSocketKey)
	if seat == -1 {
		time.Sleep(1 * time.Second)
	} else {
		time.Sleep(15 * time.Second) // for web client animation
	}

	b.eRoundEnd()
	b.destroy()
}

func (b *banker) checkLegal() bool {
	if len(b.cards) == 0 || b.size == -1 || !b.initial {
		b.size = -1
		return false
	}
	return true
}

func ToInt32Arr(array []int) []int32 {
	var arr []int32
	for _, c := range array {
		arr = append(arr, int32(c))
	}
	return arr
}
func ToIntArr(array []int32) []int {
	var arr []int
	for _, c := range array {
		arr = append(arr, int(c))
	}
	return arr
}
func (b *banker) destroy() {
	b.rwMutex.Lock()
	defer b.rwMutex.Unlock()

	b.size = -1

	logger.Service.Zap.Infow("Unregister Banker",
		"BankerUuid", b.uuid,
		"GameRoomUuid", b.roomUuid,
	)

	flux.Send(ActionBankerDelete, b.uuid, Service.Id, b.roomUuid)

	shuffle.Service.Delete(b.uuid)
	flux.UnRegister(b.uuid, b.in)
	mediator.Service.Delete(b.uuid)
}
