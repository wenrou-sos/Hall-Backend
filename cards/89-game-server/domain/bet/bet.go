package bet

import (
	bet_proto "89-game-server/domain/bet/proto"
	common89_proto "89-game-server/models/proto"
	"crypto/rand"
	"math/big"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/gogo/protobuf/proto"
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/wallet"
)

const (
	EMSGID_eBetCall             = "EMSGID_eBetCall"
	EMSGID_eBetRecall           = "EMSGID_eBetRecall"
	EMSGID_eBetTimeout          = "EMSGID_eBetTimeout"
	EMSGID_eBroadcastBetRecall  = "EMSGID_eBroadcastBetRecall"
	EMSGID_eBroadcastBetTimeout = "EMSGID_eBroadcastBetTimeout"
	EMSGID_eBetRoundStart       = "EMSGID_eBetRoundStart"
	EMSGID_eBetRoundEnd         = "EMSGID_eBetRoundEnd"
	BOT                         = "BOT"
	PLAYER                      = "PLAYER"
	BET_MIN_INDEX               = 0
	BET_MAX_INDEX               = 7
	GAME_ROOM                   = "GAME_ROOM"
	FRIEND_ROOM                 = "FRIEND_ROOM"
)

func Builder() *builder {
	return &builder{
		bankerUuid:      "",
		secWebSocketKey: "",
		gameRoomUuid:    "",
		gameRoomType:    "",
		seat:            -1,
		waitingTime:     0,
		rate:            0,
		kind:            "",
		bets:            nil,
		cent:            0,
	}
}

type builder struct {
	bankerUuid      string
	secWebSocketKey string
	gameRoomUuid    string
	gameRoomType    string
	seat            int32
	waitingTime     uint32
	rate            uint32
	kind            string
	bets            []uint32
	cent            uint64
}

type bet struct {
	bankerUuid      string
	secWebSocketKey string
	gameRoomUuid    string
	gameRoomType    string
	seat            int32
	waitingTime     uint32
	rate            uint32
	isBet           bool
	isDestroy       bool
	kind            string
	bets            []uint32
	cent            uint64
	in              chan *flux.Action
	rwMutex         *sync.RWMutex
}

func (b *builder) SetBankerUuid(bankerUuid string) *builder {
	b.bankerUuid = bankerUuid
	return b
}

func (b *builder) SetSecWebSocketKey(secWebSocketKey string) *builder {
	b.secWebSocketKey = secWebSocketKey
	return b
}

func (b *builder) SetGameRoomUuid(gameRoomUuid string) *builder {
	b.gameRoomUuid = gameRoomUuid
	return b
}

func (b *builder) SetGameRoomType(gameRoomType string) *builder {
	b.gameRoomType = gameRoomType
	return b
}

func (b *builder) SetSeat(seat int32) *builder {
	b.seat = seat
	return b
}

func (b *builder) SetWaitingTime(waitingTime uint32) *builder {
	b.waitingTime = waitingTime
	return b
}

func (b *builder) SetRate(rate uint32) *builder {
	b.rate = rate
	return b
}

func (b *builder) SetKind(kind string) *builder {
	b.kind = kind
	return b
}

func (b *builder) SetBetList(betList string) *builder {

	for _, bet := range strings.Split(betList, ",") {
		atoiBet, _ := strconv.Atoi(bet)
		b.bets = append(b.bets, uint32(atoiBet))
	}

	return b
}

func (b *builder) SetCent(cent uint64) *builder {
	b.cent = cent
	return b
}

func (b *builder) Build() *bet {
	return &bet{
		bankerUuid:      b.bankerUuid,
		secWebSocketKey: b.secWebSocketKey,
		gameRoomUuid:    b.gameRoomUuid,
		gameRoomType:    b.gameRoomType,
		seat:            b.seat,
		waitingTime:     b.waitingTime,
		rate:            b.rate,
		isBet:           false,
		isDestroy:       false,
		kind:            b.kind,
		bets:            b.bets,
		cent:            b.cent,
		in:              make(chan *flux.Action, 32),
		rwMutex:         &sync.RWMutex{},
	}
}

func (b *bet) run() {
	flux.Register(b.hashId(), b.in)

	time.Sleep(5 * time.Second) // for web client animation

	var t *time.Timer = nil

	if b.kind == BOT {
		n, err := rand.Int(rand.Reader, big.NewInt(int64(b.waitingTime)))

		if err != nil {
			panic(err)
		}

		if n.Uint64() == 0 {
			n = big.NewInt(1)
		}

		t = time.NewTimer(time.Duration(n.Uint64()) * time.Second)
	} else {
		t = time.NewTimer(time.Duration(b.waitingTime) * time.Second)
	}

	defer t.Stop()

	for {
		select {
		case action, ok := <-b.in:
			if !ok {
				return
			}

			b.handleAction(action)

		case <-t.C:
			logger.Service.Zap.Infow("Bet Timeout",
				"GameUser", b.secWebSocketKey,
				"BankerUuid", b.bankerUuid,
				"GameRoomUuid", b.gameRoomUuid,
				"GameRoomType", b.gameRoomType,
				"Seat", b.seat,
				"WaitingTime", b.waitingTime,
			)

			b.eBroadcastBetTimeout(b.eBetTimeout())
			b.destroy()
			return
		}
	}
}

func (b *bet) handleAction(action *flux.Action) {
	if action.Key().To() != b.hashId() {
		return
	}

	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:
		logger.Service.Zap.Infow("Bet Started",
			"GameUser", b.secWebSocketKey,
			"BankerUuid", b.bankerUuid,
			"GameRoomUuid", b.gameRoomUuid,
			"GameRoomType", b.gameRoomType,
			"Seat", b.seat,
			"WaitingTime", b.waitingTime,
		)
		if b.cent == 0 {
			cent, err := wallet.Service.CentCache(b.secWebSocketKey)
			if err != nil {
				errorcode.Service.Fatal(b.secWebSocketKey, Bet_CENT_NOT_ENOUGHT)
			}
			b.cent = cent
		}
	case EMSGID_eBetCall:
		b.rwMutex.RLock()

		if b.isBet {
			b.rwMutex.RUnlock()
			return
		}
		b.rwMutex.RUnlock()

		msg := action.Payload()[0].([]byte)

		if data := b.eBetCall(msg); data != nil {
			b.rwMutex.Lock()
			b.isBet = true
			b.rwMutex.Unlock()

			if betIdx := b.checkBetIdx(); int(data.BetIdx) > betIdx {
				data.BetIdx = uint32(betIdx)
			}
			cent, err := wallet.Service.CentCache(b.secWebSocketKey)
			if err != nil {
				logger.Service.Zap.Errorw("Check Players Alive",
					"GameUser", b.secWebSocketKey,
				)
				errorcode.Service.Fatal(b.secWebSocketKey, Bet_CENT_NOT_ENOUGHT)
			}

			b.eBroadcastBetRecall(b.eBetRecall(data, cent), cent)
			b.destroy()
		}
	}
}

func (b *bet) eBetCall(msg []byte) *bet_proto.BetCall {
	// TODO JOHNNY check token
	data := &bet_proto.BetCall{}

	err := proto.Unmarshal(msg, data)

	if data.RoomUuid != b.gameRoomUuid || data.Seat != b.seat || err != nil {
		logger.Service.Zap.Errorw(Bet_PROTO_BET_CALL_INVAILD,
			"GameUser", b.secWebSocketKey,
			"BankerUuid", b.bankerUuid,
			"GameRoomUuid", b.gameRoomUuid,
			"GameRoomType", b.gameRoomType,
			"Seat", b.seat,
			"Data", data,
			"Error", err,
		)
		errorcode.Service.Fatal(b.secWebSocketKey, Bet_PROTO_BET_CALL_INVAILD)
		return nil
	}

	if data.BetIdx < BET_MIN_INDEX {
		data.BetIdx = BET_MIN_INDEX
	}

	if data.BetIdx > BET_MAX_INDEX {
		data.BetIdx = BET_MAX_INDEX
	}

	logger.Service.Zap.Infow("Bet",
		"GameUser", b.secWebSocketKey,
		"BankerUuid", b.bankerUuid,
		"GameRoomUuid", b.gameRoomUuid,
		"GameRoomType", b.gameRoomType,
		"Seat", b.seat,
		"Data", data,
	)

	return data
}

func (b *bet) eBetRecall(betCall *bet_proto.BetCall, cent uint64) *bet_proto.BetRecall {

	betCent := b.bets[betCall.BetIdx] * b.rate

	if cent < uint64(betCent)*5 {
		errorcode.Service.Fatal(b.secWebSocketKey, Bet_CENT_NOT_ENOUGHT)
		return nil
	}

	data := &bet_proto.BetRecall{
		Msgid:    common89_proto.EMSGID_eBetRecall,
		RoomUuid: betCall.RoomUuid,
		Seat:     betCall.Seat,
		BetIdx:   betCall.BetIdx,
	}

	dataByte, _ := proto.Marshal(data)

	switch b.gameRoomType {
	case GAME_ROOM:
		flux.Send(EMSGID_eBetRecall, b.hashId(), b.bankerUuid, data, b.secWebSocketKey)
		flux.Send(EMSGID_eBetRecall, b.hashId(), b.secWebSocketKey, dataByte, uint64(betCent))

	case FRIEND_ROOM:
		flux.Send(EMSGID_eBetRecall, b.hashId(), b.gameRoomUuid, data, b.bankerUuid, b.secWebSocketKey)
		flux.Send(EMSGID_eBetRecall, b.hashId(), b.secWebSocketKey, dataByte, uint64(betCent))

	default:
		panic("GAME ROOM TYPE ERROR")
	}

	return data
}

func (b *bet) eBroadcastBetRecall(betRecall *bet_proto.BetRecall, cent uint64) {
	if betRecall == nil {
		return
	}
	data := &bet_proto.BroadcastBetRecall{
		Msgid:      common89_proto.EMSGID_eBroadcastBetRecall,
		BetRecall:  betRecall,
		PlayerCent: cent,
	}
	flux.Send(EMSGID_eBroadcastBetRecall, b.hashId(), b.gameRoomUuid, data)
}

func (b *bet) eBetTimeout() *bet_proto.BetTimeout {
	b.rwMutex.Lock()
	if b.isBet {
		b.rwMutex.RUnlock()
		return nil
	}

	b.isBet = true
	b.rwMutex.Unlock()

	cent, err := wallet.Service.CentCache(b.secWebSocketKey)
	if err != nil {
		logger.Service.Zap.Errorw("Check Players Alive",
			"GameUser", b.secWebSocketKey,
		)
		errorcode.Service.Fatal(b.secWebSocketKey, Bet_CENT_NOT_ENOUGHT)
	}
	betCent := b.bets[BET_MIN_INDEX] * b.rate

	if cent < uint64(betCent)*5 {
		errorcode.Service.Fatal(b.secWebSocketKey, Bet_CENT_NOT_ENOUGHT)
		return nil
	}
	data := &bet_proto.BetTimeout{
		Msgid:    common89_proto.EMSGID_eBetTimeout,
		RoomUuid: b.gameRoomUuid,
		Seat:     b.seat,
		BetIdx:   BET_MIN_INDEX,
	}

	if b.kind == BOT {
		betIdx := b.checkBetIdx()

		if betIdx > 0 {
			n, err := rand.Int(rand.Reader, big.NewInt(int64(betIdx)))

			if err != nil {
				panic(err)
			}

			data.BetIdx = uint32(n.Uint64())
		}
		botBetCent := b.bets[data.BetIdx] * b.rate
		if cent < uint64(botBetCent*5) {
			data.BetIdx = BET_MIN_INDEX
		}
	}

	dataByte, _ := proto.Marshal(data)

	switch b.gameRoomType {
	case GAME_ROOM:
		flux.Send(EMSGID_eBetTimeout, b.hashId(), b.bankerUuid, data, b.secWebSocketKey)
		flux.Send(EMSGID_eBetTimeout, b.hashId(), b.secWebSocketKey, dataByte, uint64(betCent))

	case FRIEND_ROOM:
		flux.Send(EMSGID_eBetTimeout, b.hashId(), b.gameRoomUuid, data, b.bankerUuid, b.secWebSocketKey)
		flux.Send(EMSGID_eBetTimeout, b.hashId(), b.secWebSocketKey, dataByte, uint64(betCent))

	default:
		panic("GAME ROOM TYPE ERROR")
	}

	return data
}

func (b *bet) eBroadcastBetTimeout(betTimeout *bet_proto.BetTimeout) {

	if betTimeout == nil {
		return
	}

	data := &bet_proto.BroadcastBetTimeout{
		Msgid:      common89_proto.EMSGID_eBroadcastBetTimeout,
		BetTimeout: betTimeout,
	}

	dataByte, _ := proto.Marshal(data)

	flux.Send(EMSGID_eBroadcastBetTimeout, b.hashId(), b.gameRoomUuid, dataByte, betTimeout.Seat)
}

func (b *bet) checkBetIdx() int {
	switch {
	case uint64(b.bets[0]*b.rate) > b.cent:
		logger.Service.Zap.Errorw(Bet_CENT_NOT_ENOUGHT,
			"GameUser", b.secWebSocketKey,
			"BankerUuid", b.bankerUuid,
			"GameRoomUuid", b.gameRoomUuid,
			"GameRoomType", b.gameRoomType,
			"Seat", b.seat,
			"Bet", b.bets[0],
			"Rate", b.rate,
			"Cent", b.cent,
		)
		errorcode.Service.Fatal(b.secWebSocketKey, Bet_CENT_NOT_ENOUGHT)
		//panic(Bet_CENT_NOT_ENOUGHT)
		return -1

	case uint64(b.bets[1]*b.rate) > b.cent:
		return 0

	case uint64(b.bets[2]*b.rate) > b.cent:
		return 1

	case uint64(b.bets[3]*b.rate) > b.cent:
		return 2

	case uint64(b.bets[4]*b.rate) > b.cent:
		return 3

	case uint64(b.bets[5]*b.rate) > b.cent:
		return 4

	case uint64(b.bets[6]*b.rate) > b.cent:
		return 5

	case uint64(b.bets[7]*b.rate) > b.cent:
		return 6

	default:

		return BET_MAX_INDEX
	}
}

func (b *bet) hashId() string {
	return Service.HashId(b.secWebSocketKey, b.gameRoomUuid)
}

func (b *bet) destroy() {
	if !b.isDestroy {
		b.isDestroy = true
		flux.UnRegister(b.hashId(), b.in)
	}
}
