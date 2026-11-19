package banker

import (
	banker_proto "89-game-server/application/banker/proto"
	"89-game-server/application/gamesetting89"
	"89-game-server/application/lottery"
	"89-game-server/domain/bet"
	bet_proto "89-game-server/domain/bet/proto"
	"89-game-server/domain/draw"
	draw_proto "89-game-server/domain/draw/proto"
	"89-game-server/domain/probability"
	probability_proto "89-game-server/domain/probability/proto"
	common89_proto "89-game-server/models/proto"
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
	EMSGID_eRoundStart       = "EMSGID_eRoundStart"
	EMSGID_eRoundEnd         = "EMSGID_eRoundEnd"
	ActionBankerDeal         = "ActionBankerDeal"
	ActionBankerStart        = "ActionBankerStart"
	ActionBankerAccountingSn = "ActionBankerAccountingSn"
	BANKER_SEAT              = 5
	GAME_ROOM                = "GAME_ROOM"
	FRIEND_ROOM              = "FRIEND_ROOM"
)

func Builder() *builder {
	return &builder{
		from:            "",
		uuid:            "",
		secWebSocketKey: "",
		roomUuid:        "",
		roomType:        "",
		seat:            -1,
		size:            0,
	}
}

type builder struct {
	from            string
	uuid            string
	secWebSocketKey string
	roomUuid        string
	roomType        string
	seat            int32
	size            int32
}

type banker struct {
	from            string // not used now
	uuid            string
	secWebSocketKey string // this is used bot's uuid or player's secWebSocketKey
	roomUuid        string
	roomType        string
	seat            int32
	size            int32 // how many players
	betCount        map[string]uint32
	drawCount       map[string]bool
	deck            map[int][3]int
	deal            *banker_proto.Deal
	results         map[string]*probability_proto.Card
	betCent         map[string]uint64
	accountingSn    map[string]uint64
	in              chan *flux.Action
	rwMutex         *sync.RWMutex
}

func (b *builder) setFrom(from string) *builder {
	b.from = from
	return b
}

func (b *builder) setSecWebSocketKey(secWebSocketKey string) *builder {
	b.secWebSocketKey = secWebSocketKey
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

func (b *builder) setSeat(seat int32) *builder {
	b.seat = seat
	return b
}

func (b *builder) setSize(size int32) *builder {
	// include banker self
	b.size = size
	return b
}

func (b *builder) build() *banker {
	v := &banker{
		from:            b.from,
		uuid:            uuid.New().String(),
		secWebSocketKey: b.secWebSocketKey, // this is used bot's uuid now
		roomUuid:        b.roomUuid,
		roomType:        b.roomType,
		seat:            b.seat,
		size:            b.size,
		betCount:        make(map[string]uint32),
		drawCount:       make(map[string]bool),
		deck:            make(map[int][3]int),
		deal: &banker_proto.Deal{
			Msgid:    common89_proto.EMSGID_eDeal,
			RoomUuid: b.roomUuid,
			Cards:    make([]*banker_proto.Card, 6),
		},
		results:      make(map[string]*probability_proto.Card),
		betCent:      make(map[string]uint64),
		accountingSn: make(map[string]uint64),
		in:           make(chan *flux.Action, 128),
		rwMutex:      &sync.RWMutex{},
	}

	v.init()

	go v.run()

	return v
}

func (b *banker) init() {
	cards := shuffle.Service.Shuffle52(b.uuid)

	b.deck[0] = [3]int{cards[0], cards[1], cards[2]}
	b.deck[1] = [3]int{cards[3], cards[4], cards[5]}
	b.deck[2] = [3]int{cards[6], cards[7], cards[8]}
	b.deck[3] = [3]int{cards[9], cards[10], cards[11]}
	b.deck[4] = [3]int{cards[12], cards[13], cards[14]}
	b.deck[BANKER_SEAT] = [3]int{cards[15], cards[16], cards[17]}

	// b.deck[0] = [3]int{1, 2, 3}
	// b.deck[1] = [3]int{17, 18, 19}
	// b.deck[2] = [3]int{33, 34, 35}
	// b.deck[3] = [3]int{49, 50, 51}
	// b.deck[4] = [3]int{1, 2, 3}
	// b.deck[BANKER_SEAT] = [3]int{49, 50, 51}
}

func (b *banker) run() {
	flux.Register(b.uuid, b.in)

	for action := range b.in {
		b.handleAction(action)
	}
}

func (b *banker) handleAction(action *flux.Action) {
	if b.uuid != action.Key().To() {
		return
	}

	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:

		flux.Send(ActionBankerStart, b.uuid, b.roomUuid, b.uuid)

		time.Sleep(3000 * time.Millisecond)

		b.eRoundStart()

		time.Sleep(3500 * time.Millisecond) // for web client animation

		bet.Service.BetRoundStart(b.roomUuid)

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

	case bet.EMSGID_eBetTimeout:
		fallthrough
	case bet.EMSGID_eBetRecall:

		var secWebSocketKey = ""
		var data interface{}
		var betCent uint64 = 0

		roomUuid := ""
		var seat int32 = -1
		var betIdx uint32 = 0

		switch b.roomType {
		case GAME_ROOM:
			data = action.Payload()[0]
			secWebSocketKey = action.Payload()[1].(string)

			switch data.(type) {
			case *bet_proto.BetRecall:
				roomUuid = data.(*bet_proto.BetRecall).RoomUuid
				seat = data.(*bet_proto.BetRecall).Seat
				betIdx = data.(*bet_proto.BetRecall).BetIdx

			case *bet_proto.BetTimeout:
				roomUuid = data.(*bet_proto.BetTimeout).RoomUuid
				seat = data.(*bet_proto.BetTimeout).Seat
				betIdx = data.(*bet_proto.BetTimeout).BetIdx
			}

			betCent = uint64(gamesetting89.Service.Bet(secWebSocketKey, betIdx) * gamesetting89.Service.Rate(secWebSocketKey))

		case FRIEND_ROOM:
			dataByte := action.Payload()[0].([]byte)
			secWebSocketKey = string(action.Payload()[1].([]byte))
			betCent, _ = strconv.ParseUint(string(action.Payload()[2].([]byte)), 10, 64)

			if action.Key().Name() == bet.EMSGID_eBetTimeout {
				data1 := &bet_proto.BetTimeout{}

				proto.Unmarshal(dataByte, data1)

				data = data1
			} else {
				data2 := &bet_proto.BetRecall{}

				proto.Unmarshal(dataByte, data2)

				data = data2
			}

			switch data.(type) {
			case *bet_proto.BetRecall:
				roomUuid = data.(*bet_proto.BetRecall).RoomUuid
				seat = data.(*bet_proto.BetRecall).Seat
				betIdx = data.(*bet_proto.BetRecall).BetIdx

			case *bet_proto.BetTimeout:
				roomUuid = data.(*bet_proto.BetTimeout).RoomUuid
				seat = data.(*bet_proto.BetTimeout).Seat
				betIdx = data.(*bet_proto.BetTimeout).BetIdx
			}

		default:
			panic("ERROR ROOM TYPE")
		}

		if roomUuid == b.roomUuid && seat != b.seat {

			if _, ok := b.betCount[secWebSocketKey]; ok {
				return
			}

			b.betCount[secWebSocketKey] = betIdx

			b.betCent[secWebSocketKey] = betCent

			b.bet(secWebSocketKey, seat, betCent)
		}

		// exclude banker's bet
		if int32(len(b.betCount)) == b.size-1 {
			bet.Service.BetRoundEnd(b.roomUuid)

			v := b.bet(b.secWebSocketKey, b.seat, 0) // banker self

			logger.Service.Zap.Infow("Banker Deal",
				"SecWebSocketKey", b.secWebSocketKey,
				"BankerUuid", b.uuid,
				"GameRoomUuid", b.roomUuid,
				"Size", b.size,
				"BetCount", b.betCount,
				"Seat", b.seat,
				"DealCards0", b.deal.Cards[0],
				"DealCards1", b.deal.Cards[1],
				"DealCards2", b.deal.Cards[2],
				"DealCards3", b.deal.Cards[3],
				"DealCards4", b.deal.Cards[4],
				"DealCards5", b.deal.Cards[5],
			)

			// banker got pok8 pok9
			isDirectEnd := v.Rule > 0 && v.Rule < 5

			isDrawDelay := false

			for _, v := range b.results {
				if v.Rule > 0 && v.Rule < 5 {
					isDrawDelay = true
				}
			}

			time.Sleep(2 * time.Second) // for web client animation

			for k, v := range b.deal.Cards {
				if v == nil {
					b.deal.Cards[k] = &banker_proto.Card{
						Seat:     -1,
						Hand:     []int32{-1, -1},
						SumPoint: -1,
						Pay:      0,
						Rule:     -1,
					}
				}
			}

			dataByte, _ := proto.Marshal(b.deal)

			flux.Send(ActionBankerDeal, b.uuid, b.roomUuid,
				dataByte,
				[]byte(strconv.FormatBool(isDirectEnd)),
				[]byte(strconv.FormatBool(isDrawDelay)),
			)

			if isDirectEnd {
				lottery.Service.Result(b.results, b.betCent, b.accountingSn, b.secWebSocketKey, b.roomUuid, b.roomType)
				b.destroy()
				time.Sleep(15 * time.Second) // for web client animation
				b.eRoundEnd()
			}
		}

	case draw.EMSGID_eDrawTimeout:
		fallthrough
	case draw.EMSGID_eDrawRecall:

		var secWebSocketKey = ""
		var data interface{}
		var isDraw = false

		switch b.roomType {
		case GAME_ROOM:
			secWebSocketKey = action.Payload()[0].(string)
			data = action.Payload()[1]
			isDraw = action.Payload()[2].(bool)

		case FRIEND_ROOM:
			secWebSocketKey = string(action.Payload()[0].([]byte))
			dataByte := action.Payload()[1].([]byte)
			v, _ := strconv.ParseBool(string(action.Payload()[2].([]byte)))
			isDraw = v

			if action.Key().Name() == draw.EMSGID_eDrawTimeout {
				data1 := &draw_proto.DrawTimeout{}

				proto.Unmarshal(dataByte, data1)

				data = data1
			} else {
				data2 := &draw_proto.DrawRecall{}

				proto.Unmarshal(dataByte, data2)

				data = data2
			}

		default:
			panic("ERROR ROOM TYPE")
		}

		if _, ok := b.drawCount[secWebSocketKey]; ok {
			return
		}

		b.drawCount[secWebSocketKey] = isDraw

		switch data.(type) {
		case *draw_proto.DrawTimeout:
			data := data.(*draw_proto.DrawTimeout)

			if isDraw {
				// three cards result
				data.Card, data.SumPoint = b.draw(secWebSocketKey, data.Seat)
			}

			dataByte, _ := proto.Marshal(data)

			switch b.roomType {
			case GAME_ROOM:
				flux.Send(draw.EMSGID_eDrawTimeout, b.uuid, secWebSocketKey, dataByte)

			case FRIEND_ROOM:
				flux.Send(draw.EMSGID_eDrawTimeout, b.uuid, b.roomUuid, dataByte, secWebSocketKey, data.Seat)

			default:
				panic("ERROR ROOM TYPE")
			}

			flux.Send(draw.EMSGID_eBroadcastDrawTimeout, b.uuid, b.roomUuid,
				draw.Service.BroadcastDrawTimeout(data),
			)

		case *draw_proto.DrawRecall:
			data := data.(*draw_proto.DrawRecall)

			if isDraw {
				// three cards result
				data.Card, data.SumPoint = b.draw(secWebSocketKey, data.Seat)
			}

			dataByte, _ := proto.Marshal(data)

			switch b.roomType {
			case GAME_ROOM:
				flux.Send(draw.EMSGID_eDrawRecall, b.uuid, secWebSocketKey, dataByte)

			case FRIEND_ROOM:
				flux.Send(draw.EMSGID_eDrawRecall, b.uuid, b.roomUuid, dataByte, secWebSocketKey, data.Seat)

			default:
				panic("ERROR ROOM TYPE")
			}

			flux.Send(draw.EMSGID_eBroadcastDrawRecall, b.uuid, b.roomUuid,
				draw.Service.BroadcastDrawRecall(data),
			)
		}

		if int32(len(b.drawCount)) == b.size {
			lottery.Service.Result(b.results, b.betCent, b.accountingSn, b.secWebSocketKey, b.roomUuid, b.roomType)
			b.destroy()
			time.Sleep(15 * time.Second) // for web client animation
			b.eRoundEnd()
		}
	}
}

func (b *banker) bet(secWebSocketKey string, seat int32, betCent uint64) *probability_proto.Card {
	card1 := b.deck[int(seat)][0]
	card2 := b.deck[int(seat)][1]

	result := probability.Service.Calc2Cards(card1, card2)

	cent, err := wallet.Service.Cent(secWebSocketKey)

	if err != nil {
		logger.Service.Zap.Errorw("BUG error cent",
			"GameUser", secWebSocketKey,
			"BankerUuid", b.uuid,
			"GameRoomUuid", b.roomUuid,
			"Error", err,
		)
		panic("BUG error cent")
	}

	v := &probability_proto.Card{
		Seat: seat,
		Hand: []int32{
			int32(probability.Service.CardToIndex(card1)),
			int32(probability.Service.CardToIndex(card2)),
		},
		SumPoint:   int32(result.Point),
		Pay:        uint64(result.Pay),
		Rule:       int32(result.Rule),
		Cent:       betCent,
		Status:     probability_proto.Card_NONE,
		PlayerCent: cent,
	}

	b.results[secWebSocketKey] = v

	b.deal.Cards[seat] = &banker_proto.Card{
		Seat: seat,
		Hand: []int32{
			int32(probability.Service.CardToIndex(card1)),
			int32(probability.Service.CardToIndex(card2)),
		},
		SumPoint: int32(result.Point),
		Pay:      uint32(result.Pay),
		Rule:     int32(result.Rule),
	}

	return v
}

func (b *banker) draw(secWebSocketKey string, seat int32) (cardIndex, sumPoint int32) {
	card1 := b.deck[int(seat)][0]
	card2 := b.deck[int(seat)][1]
	card3 := b.deck[int(seat)][2]

	result := probability.Service.Calc3Cards(card1, card2, card3)

	cent, err := wallet.Service.Cent(secWebSocketKey)

	if err != nil {
		panic("error cent")
	}

	b.results[secWebSocketKey] = &probability_proto.Card{
		Seat: seat,
		Hand: []int32{
			int32(probability.Service.CardToIndex(card1)),
			int32(probability.Service.CardToIndex(card2)),
			int32(probability.Service.CardToIndex(card3)),
		},
		SumPoint:   int32(result.Point),
		Pay:        uint64(result.Pay),
		Rule:       int32(result.Rule),
		Cent:       b.betCent[secWebSocketKey],
		Status:     probability_proto.Card_NONE,
		PlayerCent: cent,
		Suit:       int32(result.Suit),
	}

	return int32(probability.Service.CardToIndex(card3)), int32(result.Point)
}

func (b *banker) eRoundStart() {
	data := &banker_proto.RoundStart{
		Msgid:       common89_proto.EMSGID_eRoundStart,
		RoomUuid:    b.roomUuid,
		PlayerInfos: nil,
	}

	flux.Send(EMSGID_eRoundStart, b.uuid, b.roomUuid, data)
}

func (b *banker) eRoundEnd() {
	data := &banker_proto.RoundEnd{
		Msgid:    common89_proto.EMSGID_eRoundEnd,
		RoomUuid: b.roomUuid,
	}

	dataByte, _ := proto.Marshal(data)

	flux.Send(EMSGID_eRoundEnd, b.uuid, b.roomUuid, dataByte)
}

func (b *banker) destroy() {
	logger.Service.Zap.Infow("Unregister Banker",
		"GameUser", b.secWebSocketKey,
		"BankerUuid", b.uuid,
		"GameRoomUuid", b.roomUuid,
	)

	flux.Send(ActionBankerDelete, b.uuid, Service.Id, b.roomUuid)
	flux.Send(bet.ActionBetDelete, b.uuid, bet.Service.Id, b.roomUuid)
	flux.Send(draw.ActionDrawDelete, b.uuid, draw.Service.Id, b.roomUuid)
	shuffle.Service.Delete(b.uuid)
	flux.UnRegister(b.uuid, b.in)
	mediator.Service.Delete(b.uuid)
}
