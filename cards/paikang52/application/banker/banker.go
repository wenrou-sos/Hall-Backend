package banker

import (
	banker_proto "52-game-server/application/banker/proto"
	"52-game-server/application/gamesetting52"
	"52-game-server/application/lottery"
	"52-game-server/domain/shuffle52"
	"crypto/rand"
	"math/big"
	"sort"

	errorcode "gitlab.iplaystar.net/game-server/error-code"

	"52-game-server/domain/draw"
	draw_proto "52-game-server/domain/draw/proto"

	lobby_setting52_proto "52-game-server/application/lobbysetting52/proto"
	"52-game-server/domain/playcards"
	play_cards_proto "52-game-server/domain/playcards/proto"
	"52-game-server/domain/probability"

	PSC_ON_00007_1 "52-game-server/domain/probability/PSC-ON-00007-1"
	probability_proto "52-game-server/domain/probability/proto"
	common52_proto "52-game-server/models/proto"
	"strconv"
	"sync"
	"time"

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
	EMSGID_eShowdownCall              = "EMSGID_eShowdownCall"

	ActionBankerDeal         = "ActionBankerDeal"
	ActionBankerStart        = "ActionBankerStart"
	ActionBankerAccountingSn = "ActionBankerAccountingSn"
	ActionPlayerRoundStart   = "ActionPlayerRoundStart"
	ActionPlayerResumeGame   = "ActionPlayerResumeGame"
	ActionPlayerResult       = "ActionPlayerResult"
	BANKER_SEAT              = 5
	GAME_ROOM                = "GAME_ROOM"
	FRIEND_ROOM              = "FRIEND_ROOM"
	PLAYER_ROUND_START_DELAY = 1
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
		vip:       false,
	}
}

type builder struct {
	from      string
	uuid      string
	roomUuid  string
	roomType  string
	size      int32
	startSeat int32
	betCent   uint64
	vip       bool
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
	totalCards              []int
	results                 map[string]*probability_proto.PlayerData
	startSeat               int32
	seatIndex               int32
	seatArr                 []int
	callCard                int32
	hitSeat                 int32
	initial                 bool
	first                   bool
	firstCount              int32
	resumePlayer            map[string]string
	haveDrawn               map[string]bool
	haveCalledCards         map[string]bool
	havePlayCards           map[string]bool
	vip                     bool
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
	// include banker self
	b.size = size
	return b
}
func (b *builder) setStartSeat(startSeat int32) *builder {
	// include banker self
	if seat := shuffle52.Service.StartSeat(); seat < 0 || seat >= int(b.size) {
		b.startSeat = startSeat
	} else {
		b.startSeat = int32(seat)
	}
	return b
}
func (b *builder) setBetCent(betCent uint64) *builder {
	// include banker self
	b.betCent = betCent
	return b
}
func (b *builder) setVip(vip bool) *builder {
	b.vip = vip
	return b
}

func (b *builder) build() *banker {
	v := &banker{
		from:                    b.from,
		uuid:                    uuid.New().String(),
		roomUuid:                b.roomUuid,
		roomType:                b.roomType,
		size:                    b.size,
		betCent:                 b.betCent,
		deck:                    make(map[int][]int),
		accountingSn:            make(map[string]uint64),
		in:                      make(chan *flux.Action, 128),
		rwMutex:                 &sync.RWMutex{},
		results:                 make(map[string]*probability_proto.PlayerData),
		startSeat:               b.startSeat,
		seatIndex:               0,
		seatArr:                 make([]int, 0),
		callCard:                -1,
		hitSeat:                 -1,
		initial:                 false,
		first:                   true,
		firstCount:              0,
		resumePlayer:            make(map[string]string),
		haveDrawn:               make(map[string]bool),
		haveCalledCards:         make(map[string]bool),
		havePlayCards:           make(map[string]bool),
		vip:                     b.vip,
		originalSecWebSocketKey: map[string]string{},
	}

	v.init()

	go v.run()

	return v
}

func (b *banker) init() {
	cards := shuffle.Service.ShuffleCard52(b.uuid)
	b.cards = cards
	b.totalCards = cards
}

func (b *banker) run() {
	flux.Register(b.uuid, b.in)
	checkTimer := time.NewTimer(10 * time.Second)

	for {
		select {
		case action, ok := <-b.in:
			if !ok || b.size == -1 {
				return
			}
			b.handleAction(action)

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

				b.result("", "", -1)

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
		"StartSeat", b.startSeat,
		"SeatArray", b.seatArr,
		//"PlayerData", b.results,
		"Data", b.accountingSn,
	)
	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:

		flux.Send(ActionBankerStart, b.uuid, b.roomUuid, b.uuid)

		time.Sleep(1500 * time.Millisecond)

		b.eRoundStart()

	case ActionBankerAccountingSn:
		switch b.roomType {
		case GAME_ROOM:
			secWebSocketKey := action.Key().From()
			accountingSn := action.Payload()[0].(uint64)

			b.accountingSn[secWebSocketKey] = accountingSn

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
		seat := action.Payload()[0].(int)

		secWebSocketKey := action.Key().From()

		b.rwMutex.Lock()
		b.deck[seat] = []int{}
		for i := 0; i < 5; i++ {
			card := b.totalCards[seat*5+i]
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
			ChangeWin:   0,
			ChangeScore: 0,
			AllWin:      0,
			AllScore:    0,
			Cards: &probability_proto.Cards{
				Hands:    ToInt32Arr(hands),
				SumPoint: int32(PSC_ON_00007_1.Deck.Sum(hands)),
			},
			HitWin:        0,
			HitLose:       0,
			HitWinCards:   make([]*probability_proto.HitCards, 0),
			HitLoseCards:  make([]*probability_proto.HitCards, 0),
			ShowdownScore: 0,
		}
		cent, _ := wallet.Service.CentCache(secWebSocketKey)
		p.Cent = cent
		b.results[secWebSocketKey] = p
		b.seatArr = append(b.seatArr, seat)
		if seat == int(b.startSeat) {
			b.seatIndex = int32(len(b.seatArr) - 1)
		}
		b.rwMutex.Unlock()

		flux.Send(ActionBankerDeal, b.uuid, secWebSocketKey, p, len(b.totalCards)-int(b.size)*5)
		if len(b.seatArr) == int(b.size) {
			sort.Ints(b.seatArr)
			b.initial = true
			b.eSpecialResult()
		}
	case ActionPlayerRoundStart:
		if !b.checkLegal() {
			return
		}

		b.rwMutex.Lock()
		defer b.rwMutex.Unlock()

		seat := b.seatArr[b.seatIndex]
		logger.Service.Zap.Infow("QA LOG ---> Player's Round", "ID", b.uuid, "Seat", seat, "Deck:", PSC_ON_00007_1.Deck.ConvertToLog(b.cards))
		logger.Service.Zap.Infow("QA LOG ---> Player's Round", "ID", b.uuid, "Seat", seat, "Hand:", PSC_ON_00007_1.Deck.ConvertToLog(b.deck[seat]))
		b.eBroadcastPlayerRoundStart(b.ePlayerRoundStart(seat, probability.Service.CallCards(b.deck[seat], int(b.callCard))))
		b.seatIndex++
		if b.seatIndex == b.size {
			b.seatIndex = 0
		}
		b.firstCount++
		if b.firstCount > b.size {
			b.first = false
		}

		secWebSocketKey := action.Key().From()
		b.haveDrawn[secWebSocketKey] = false
		b.haveCalledCards[secWebSocketKey] = false
		b.havePlayCards[secWebSocketKey] = false

	case ActionPlayerResumeGame:
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
		data := action.Payload()[0].(*lobby_setting52_proto.ConfigRecall)
		seat := data.ResumeGame.GameRecovery.Snapshot.Seat
		data.ResumeGame.Pool = uint32(len(b.cards))
		data.ResumeGame.Seat = int32(b.seatArr[b.seatIndex])
		data.ResumeGame.StartSeat = b.startSeat
		data.ResumeGame.BankerUuid = b.uuid
		for k, p := range b.results {
			if p.Seat == seat {
				data.ResumeGame.PlayerData = append(data.ResumeGame.PlayerData, p)
				delete(b.results, k)
				b.results[secWebSocketKey] = p
				b.resumePlayer[k] = secWebSocketKey
				gamesetting52.Service.Clone(k, secWebSocketKey)
				flux.Send(draw.ActionDrawResume, b.uuid, draw.Service.Id, secWebSocketKey, k, b.resumePlayer)
				flux.Send(playcards.ActionPlayCardsResume, b.uuid, playcards.Service.Id, secWebSocketKey, k, b.resumePlayer)
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
					ChangeWin:   p.ChangeWin,
					ChangeScore: p.ChangeScore,
					AllWin:      p.AllWin,
					AllScore:    p.AllScore,
					Cent:        p.Cent,
				}
				data.ResumeGame.PlayerData = append(data.ResumeGame.PlayerData, p)
			}
		}
		data.ResumeGame.WaitingTime = append(data.ResumeGame.WaitingTime, gamesetting52.Service.FirstRoundStartWaitingTime(secWebSocketKey))
		data.ResumeGame.WaitingTime = append(data.ResumeGame.WaitingTime, gamesetting52.Service.DrawCardsWaitingTime(secWebSocketKey))
		data.ResumeGame.WaitingTime = append(data.ResumeGame.WaitingTime, gamesetting52.Service.PlayCardsWaitingTime(secWebSocketKey))
		data.ResumeGame.WaitingTime = append(data.ResumeGame.WaitingTime, gamesetting52.Service.RoundStartWaitingTime(secWebSocketKey))

		flux.Send(ActionPlayerResumeGame, b.uuid, b.roomUuid, data, secWebSocketKey)

	case draw.EMSGID_eDrawTimeout:
		fallthrough
	case draw.EMSGID_eDrawRecall:
		if !b.checkLegal() {
			return
		}

		b.rwMutex.Lock()
		defer b.rwMutex.Unlock()

		secWebSocketKey := action.Payload()[1].(string)

		if v, ok := b.resumePlayer[secWebSocketKey]; ok {
			secWebSocketKey = v
		}

		if v, ok := b.haveCalledCards[secWebSocketKey]; ok && v {
			return
		}
		b.haveDrawn[secWebSocketKey] = true

		index := 0
		playerData := b.results[secWebSocketKey]
		r, _ := rand.Int(rand.Reader, big.NewInt(100))
		if secWebSocketKey != wallet.Service.MemberId(secWebSocketKey) && int(r.Int64()) < gamesetting52.Service.UnluckyRate(secWebSocketKey, b.vip) {
			index = lottery.Service.DrawCardLogic(playerData, b.cards)
		}
		card := b.cards[index]
		b.cards = append(b.cards[:index], b.cards[(index+1):]...)
		b.deck[int(playerData.Seat)] = append(b.deck[int(playerData.Seat)], card)

		hands := b.deck[int(playerData.Seat)]
		playerData.Cards.Hands = ToInt32Arr(hands)
		cards := &probability_proto.Cards{
			Hands:    ToInt32Arr(hands),
			SumPoint: int32(PSC_ON_00007_1.Deck.Sum(hands)),
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
			flux.Send(draw.EMSGID_eBroadcastDrawTimeout, b.uuid, b.roomUuid,
				draw.Service.BroadcastDrawTimeout(data),
			)
			time.Sleep(500 * time.Millisecond)
			flux.Send(draw.EMSGID_eDrawTimeout, b.uuid, secWebSocketKey, dataByte, card)

		case *draw_proto.DrawRecall:
			data := action.Payload()[0].(*draw_proto.DrawRecall)

			data.PlayerData = playerData
			data.Pool = uint32(len(b.cards))
			data.Card = int32(card)
			dataByte, _ := proto.Marshal(data)

			flux.Send(draw.EMSGID_eDrawRecall, b.uuid, secWebSocketKey, dataByte, card)

			flux.Send(draw.EMSGID_eBroadcastDrawRecall, b.uuid, b.roomUuid,
				draw.Service.BroadcastDrawRecall(data),
			)

		}

		logger.Service.Zap.Infow("QA LOG ---> Player Draw", "ID", b.uuid, "Seat", playerData.Seat, "Hand:", PSC_ON_00007_1.Deck.ConvertToLog(b.deck[int(playerData.Seat)]))

	case playcards.ActionCallCardsTimeout:
		fallthrough
	case playcards.ActionCallCards:
		if !b.checkLegal() {
			return
		}

		b.rwMutex.Lock()

		secWebSocketKey := action.Payload()[0].(string)
		seat := int(action.Payload()[1].(int32))

		if v, ok := b.resumePlayer[secWebSocketKey]; ok {
			secWebSocketKey = v
		}

		if v, ok := b.haveDrawn[secWebSocketKey]; ok && v {
			b.rwMutex.Unlock()
			return
		}
		b.haveCalledCards[secWebSocketKey] = true

		p := b.results[secWebSocketKey]
		var callArray []int
		if callArray = probability.Service.CallCards(b.deck[seat], int(b.callCard)); len(callArray) == 0 {
			logger.Service.Zap.Errorw(playcards.PlayCards_CALL_CARDS_INVAILD,
				"GameUser", secWebSocketKey,
				"BankerUuid", b.uuid,
				"GameRoomUuid", b.roomUuid,
				"GameRoomType", b.roomType,
				"Seat", seat,
			)
			errorcode.Service.Fatal(secWebSocketKey, playcards.PlayCards_CALL_CARDS_INVAILD)
			b.rwMutex.Unlock()
			return
		}

		win := int(b.betCent) / 2 * len(callArray)
		hitCards := &probability_proto.HitCards{
			Cards: ToInt32Arr(callArray),
		}
		p.ChangeWin = 1
		p.ChangeScore = uint64(win)
		p.AllScore += int64(win)
		p.Cards = b.playCard(callArray[0], seat)
		p.PokerNumber = int32(len(b.deck[seat]))
		p.PlayCard = ToInt32Arr(callArray)
		p.HitWin += uint64(win)
		p.HitWinCards = append(p.HitWinCards, hitCards)

		allScore := []int64{0, 0, 0, 0, 0}

		for _, p := range b.results {
			if p.Seat == b.hitSeat {
				p.ChangeWin = 0
				p.ChangeScore = uint64(win)
				p.AllScore -= int64(win)
				p.HitLose += uint64(win)
				p.HitLoseCards = append(p.HitLoseCards, hitCards)
			}
			allScore[p.Seat] = p.AllScore
		}

		playcards.Service.BroadcastPlayCardsRecall(playcards.Service.PlayCardsRecall(b.roomUuid, secWebSocketKey, p, b.hitSeat, allScore))

		logger.Service.Zap.Infow("QA LOG ---> Player Call Card", "ID", b.uuid, "Seat", p.Seat, "Hand:", PSC_ON_00007_1.Deck.ConvertToLog(b.deck[int(p.Seat)]))

		b.rwMutex.Unlock()

		if len(p.Cards.Hands) == 0 {
			winType := lottery.CALL_CARD_WIN

			b.result(secWebSocketKey, winType, b.hitSeat)
		}

	case playcards.ActionPlayCardsTimeout:
		fallthrough
	case playcards.ActionPlayCards:
		if b.size == -1 || !b.initial {
			b.size = -1
			return
		}

		b.rwMutex.Lock()

		secWebSocketKey := action.Payload()[0].(string)
		seat := action.Payload()[1].(int32)
		playCard := action.Payload()[3].(int32)
		logic := action.Payload()[4].(bool)

		if v, ok := b.resumePlayer[secWebSocketKey]; ok {
			secWebSocketKey = v
		}
		if v, ok := b.havePlayCards[secWebSocketKey]; ok && v {
			b.rwMutex.Unlock()
			return
		}
		b.havePlayCards[secWebSocketKey] = true

		p := b.results[secWebSocketKey]
		p.ChangeWin = 0
		p.ChangeScore = 0
		b.hitSeat = seat

		var nextP *probability_proto.PlayerData
		for _, r := range b.results {
			if r.Seat == int32(b.seatArr[b.seatIndex]) {
				nextP = r
				break
			}
		}

		switch action.Payload()[2].(type) {
		case *play_cards_proto.PlayCardsTimeout:
			data := action.Payload()[2].(*play_cards_proto.PlayCardsTimeout)
			card := probability.Service.PlayCards(ToIntArr(p.Cards.Hands), ToIntArr(nextP.Cards.Hands), logic)
			if playCard == -1 {
				if len(card) == 0 {
					b.rwMutex.Unlock()
					return
				}
				p.Cards = b.playCard(card[0], int(seat))
				p.PlayCard = ToInt32Arr(card)
				b.callCard = int32(card[0])
			} else {
				p.Cards = b.playCard(int(playCard), int(seat))
				p.PlayCard = []int32{playCard}
				b.callCard = playCard
			}
			p.PokerNumber = int32(len(b.deck[int(seat)]))
			data.PlayerData = p

			allScore := []int64{0, 0, 0, 0, 0}
			for _, p := range b.results {
				allScore[p.Seat] = p.AllScore
			}
			data.AllScore = allScore

			dataByte, _ := proto.Marshal(data)
			playcards.Service.BroadcastPlayCardsTimeout(data)
			time.Sleep(500 * time.Millisecond)
			flux.Send(playcards.EMSGID_ePlayCardsTimeout, b.uuid, secWebSocketKey, dataByte)

		case *play_cards_proto.PlayCardsCall:
			data := action.Payload()[2].(*play_cards_proto.PlayCardsCall)
			card := data.Cards
			p.Cards = b.playCard(int(card[0]), int(seat))
			p.PokerNumber = int32(len(b.deck[int(seat)]))
			p.PlayCard = card
			b.callCard = card[0]

			allScore := []int64{0, 0, 0, 0, 0}
			for _, p := range b.results {
				allScore[p.Seat] = p.AllScore
			}

			playcards.Service.BroadcastPlayCardsRecall(playcards.Service.PlayCardsRecall(b.roomUuid, secWebSocketKey, p, -1, allScore))
		}

		logger.Service.Zap.Infow("QA LOG ---> Player Play Card", "ID", b.uuid, "Seat", p.Seat, "Hand:", PSC_ON_00007_1.Deck.ConvertToLog(b.deck[int(p.Seat)]))

		b.rwMutex.Unlock()

		if len(p.Cards.Hands) == 0 {
			winType := lottery.PLAY_CARD_WIN

			b.result(secWebSocketKey, winType, -1)
		} else if len(b.cards) == 0 {
			lottery.Service.EndResult(b.betCent, b.accountingSn, b.results, b.roomUuid, b.roomType, b.originalSecWebSocketKey)

			time.Sleep(15 * time.Second) // for web client animation

			b.eRoundEnd()
			b.destroy()
		}

	case ActionPlayerResult:
		b.rwMutex.Lock()

		secWebSocketKey := action.Key().From()

		if v, ok := b.haveDrawn[secWebSocketKey]; v && ok {
			b.rwMutex.Unlock()
			return
		}

		b.rwMutex.Unlock()

		b.result(secWebSocketKey, lottery.NORMAL_WIN, -1)
	}
}

func (b *banker) playCard(cards int, seat int) *probability_proto.Cards {
	var newCards []int
	kind := cards % 13
	for _, deckCard := range b.deck[seat] {
		if deckCard%13 != kind {
			newCards = append(newCards, deckCard)
		}
	}

	b.deck[seat] = newCards

	card := &probability_proto.Cards{
		Hands:    ToInt32Arr(newCards),
		SumPoint: int32(PSC_ON_00007_1.Deck.Sum(newCards)),
	}

	return card
}

func (b *banker) eSpecialResult() {
	logger.Service.Zap.Infow("eSpecialResult")
	s := lottery.Service.SpecialResult(b.betCent, b.accountingSn, b.results, b.roomUuid, b.roomType, b.originalSecWebSocketKey)
	if s != nil {
		b.destroy()
		time.Sleep(15 * time.Second) // for web client animation
		b.eRoundEnd()
	} else {
		time.Sleep(5 * time.Second)
		flux.Send(ActionPlayerRoundStart, b.uuid, b.uuid)
	}
}

func (b *banker) eRoundStart() {
	data := &banker_proto.RoundStart{
		Msgid:       common52_proto.EMSGID_eRoundStart,
		RoomUuid:    b.roomUuid,
		BankerUuid:  b.uuid,
		PlayerInfos: nil,
	}
	logger.Service.Zap.Infow("eRoundStart")
	flux.Send(EMSGID_eRoundStart, b.uuid, b.roomUuid, data)
}

func (b *banker) eRoundEnd() {
	data := &banker_proto.RoundEnd{
		Msgid:    common52_proto.EMSGID_eRoundEnd,
		RoomUuid: b.roomUuid,
	}

	dataByte, _ := proto.Marshal(data)

	flux.Send(EMSGID_eRoundEnd, b.uuid, b.roomUuid, dataByte)
}
func (b *banker) ePlayerRoundStart(seat int, cards []int) *banker_proto.PlayerRoundStart {
	logger.Service.Zap.Infow("ePlayerRoundStart")
	data := &banker_proto.PlayerRoundStart{
		Msgid:     common52_proto.EMSGID_ePlayRoundStart,
		RoomUuid:  b.roomUuid,
		Seat:      int32(seat),
		CallCards: ToInt32Arr(cards),
	}
	flux.Send(EMSGID_ePlayerRoundStart, b.uuid, b.roomUuid, data, b.first, b.results, b.vip, b.deck[seat])
	return data
}

func (b *banker) eBroadcastPlayerRoundStart(playerroundstar *banker_proto.PlayerRoundStart) {
	data := &banker_proto.BroadcastPlayerRoundStart{
		Msgid: common52_proto.EMSGID_eBroadcastPlayRoundStart,
		PlayerRoundStart: &banker_proto.PlayerRoundStart{
			Msgid:    common52_proto.EMSGID_ePlayRoundStart,
			RoomUuid: playerroundstar.RoomUuid,
			Seat:     playerroundstar.Seat,
		},
	}
	dataByte, _ := proto.Marshal(data)
	flux.Send(EMSGID_eBroadcastPlayerRoundStart, b.uuid, b.roomUuid, dataByte)
}

func (b *banker) result(secWebSocketKey, winType string, hitSeat int32) {
	lottery.Service.Result(b.first, b.betCent, b.accountingSn, secWebSocketKey, b.results, b.roomUuid, b.roomType, winType, hitSeat, b.originalSecWebSocketKey)

	if secWebSocketKey == "" {
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
