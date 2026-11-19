package playcards

import (
	play_cards_proto "52-game-server/domain/playcards/proto"
	common52_proto "52-game-server/models/proto"
	"crypto/rand"
	"math/big"
	"sync"
	"time"

	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
)

const (
	EMSGID_ePlayCardsCall             = "EMSGID_ePlayCardsCall"
	EMSGID_ePlayCardsRecall           = "EMSGID_ePlayCardsRecall"
	EMSGID_eBroadcastPlayCardsRecall  = "EMSGID_eBroadcastPlayCardsRecall"
	EMSGID_ePlayCardsTimeout          = "EMSGID_ePlayCardsTimeout"
	EMSGID_eBroadcastPlayCardsTimeout = "EMSGID_eBroadcastPlayCardsTimeout"
	ActionPlayCardsCreate			  = "ActionPlayCardsCreate"
	ActionPlayCardsReset			  = "ActionPlayCardsReset"
	ActionPlayCardsResume			  = "ActionPlayCardsResume"
	ActionPlayCardsDelete			  = "ActionPlayCardsDelete"
	ActionPlayCards                   = "ActionPlayCards"
	ActionPlayCardsTimeout            = "ActionPlayCardsTimeout"
	ActionCallCards                   = "ActionCallCards"
	ActionCallCardsTimeout            = "ActionCallCardsTimeout"
	BOT                               = "BOT"
	PLAYER                            = "PLAYER"
	GAME_ROOM                         = "GAME_ROOM"
	FRIEND_ROOM                       = "FRIEND_ROOM"
	TYPE_PLAYCARD                     = 0
	TYPE_CALLCARD                     = 1
)

func Builder() *builder {
	return &builder{
		bankerUuid:      "",
		secWebSocketKey: "",
		gameRoomUuid:    "",
		gameRoomType:    "",
		seat:            -1,
		waitingTime:     0,
		kind:            "",
		sleepTime:       0,
		playType:        -1,
	}
}

type builder struct {
	bankerUuid      string
	secWebSocketKey string
	gameRoomUuid    string
	gameRoomType    string
	seat            int32
	waitingTime     uint32
	kind            string
	sleepTime       uint32
	playType        int32
}

type playCards struct {
	bankerUuid      string
	secWebSocketKey string
	gameRoomUuid    string
	gameRoomType    string
	seat            int32
	waitingTime     uint32
	sleepTime       uint32
	isPlayCards     bool
	isDestroy       bool
	kind            string
	playType        int32
	playCard 		int32
	logic           bool
	in              chan *flux.Action
	rwMutex         *sync.RWMutex
	timer           *time.Timer
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

func (b *builder) SetKind(kind string) *builder {
	b.kind = kind
	return b
}

func (b *builder) SetSleepTime(sleepTime uint32) *builder {
	b.sleepTime = sleepTime
	return b
}

func (b *builder) SetPlayType(playType int32) *builder {
	b.playType = playType
	return b
}

func (b *builder) Build() *playCards {
	p := &playCards{
		bankerUuid:      b.bankerUuid,
		secWebSocketKey: b.secWebSocketKey,
		gameRoomUuid:    b.gameRoomUuid,
		gameRoomType:    b.gameRoomType,
		seat:            b.seat,
		waitingTime:     b.waitingTime,
		sleepTime:       b.sleepTime,
		isPlayCards:     false,
		isDestroy:       false,
		kind:            b.kind,
		playType: 		 b.playType,
		playCard:        -1,
		logic:           false,
		in:              make(chan *flux.Action, 32),
		rwMutex:         &sync.RWMutex{},
	}

	return p
}

func (p *playCards) run() {
	p.rwMutex.Lock()

	p.timer = time.NewTimer(100 * time.Second)
	p.timer.Stop()

	p.rwMutex.Unlock()

	defer p.destroy()

	for {
		select {
		case <-p.timer.C:
			if !p.isPlayCards && !p.isDestroy && p.waitingTime != 0 {
				logger.Service.Zap.Infow("PlayCards Timeout",
					"GameUser", p.secWebSocketKey,
					"BankerUuid", p.bankerUuid,
					"GameRoomUuid", p.gameRoomUuid,
					"GameRoomType", p.gameRoomType,
					"Seat", p.seat,
					"WaitingTime", p.waitingTime,
				)
				p.ePlayCardsTimeout()
				time.Sleep(1 * time.Second)
			}
		}
	}
}

func (p *playCards) ePlayCardsCall() {
	p.rwMutex.Lock()
	defer p.rwMutex.Unlock()

	if p.isPlayCards || p.isDestroy {
		return
	}

	p.timer.Stop()
}

func (p *playCards) ePlayCardsTimeout() {
	p.rwMutex.Lock()
	defer p.rwMutex.Unlock()

	p.isPlayCards = true

	data := &play_cards_proto.PlayCardsTimeout{
		Msgid:      common52_proto.EMSGID_ePlayCardsTimeout,
		RoomUuid:   p.gameRoomUuid,
		PlayerData: nil,
		HitSeat:    -1,
	}

	switch p.playType {
	case TYPE_CALLCARD:
		flux.Send(ActionCallCardsTimeout, p.hashId(), p.bankerUuid, p.secWebSocketKey, p.seat, data)

	case TYPE_PLAYCARD:
		flux.Send(ActionPlayCardsTimeout, p.hashId(), p.bankerUuid, p.secWebSocketKey, p.seat, data, p.playCard, p.logic)
	}
}

func (p *playCards) reset() {
	p.rwMutex.Lock()
	defer p.rwMutex.Unlock()

	n, err := rand.Int(rand.Reader, big.NewInt(int64(p.waitingTime)))

	if err != nil {
		panic(err)
	}

	if n.Uint64() == 0 {
		n = big.NewInt(1)
	}

	p.isPlayCards = false

	if p.kind == BOT {
		p.timer.Reset(time.Duration(n.Uint64()) * time.Second)
	} else {
		p.timer.Reset(time.Duration(p.waitingTime) * time.Second)
	}
}

func (p *playCards) hashId() string {
	return Service.HashId(p.secWebSocketKey, p.gameRoomUuid)
}

func (p *playCards) destroy() {
	p.rwMutex.Lock()
	defer p.rwMutex.Unlock()

	if !p.isDestroy {
		if p.timer != nil {
			p.timer.Stop()
		}
		p.isDestroy = true
	}
}
