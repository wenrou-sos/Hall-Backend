package round

import (
	"crypto/rand"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
	"math"
	"math/big"
	"sync"
	"time"
)

const (
	ActionRoundCreate			    = "ActionRoundCreate"
	ActionRoundResume			  	= "ActionRoundResume"
	ActionRoundDelete			  	= "ActionRoundDelete"
	ActionRoundTimeout			  	= "ActionRoundTimeout"
	ActionRoundStateChange			= "ActionRoundStateChange"
	STATE_START						= "STATE_START"
	STATE_DRAW						= "STATE_DRAW"
	STATE_PLAYCARD					= "STATE_PLAYCARD"
	STATE_END						= "STATE_END"
	BOT                             = "BOT"
	PLAYER                          = "PLAYER"
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
}

type round struct {
	bankerUuid      string
	secWebSocketKey string
	gameRoomUuid    string
	gameRoomType    string
	seat            int32
	waitingTime     uint32
	isDestroy       bool
	kind            string
	state           string
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

func (b *builder) Build() *round {
	r := &round{
		bankerUuid:      b.bankerUuid,
		secWebSocketKey: b.secWebSocketKey,
		gameRoomUuid:    b.gameRoomUuid,
		gameRoomType:    b.gameRoomType,
		seat:            b.seat,
		waitingTime:     b.waitingTime,
		isDestroy:       false,
		kind:            b.kind,
		state:           STATE_START,
		in:              make(chan *flux.Action, 32),
		rwMutex:         &sync.RWMutex{},
	}

	return r
}

func (r *round) run() {
	r.rwMutex.Lock()

	r.timer = time.NewTimer(100 * time.Second)
	r.timer.Stop()

	r.rwMutex.Unlock()

	defer r.destroy()

	for {
		select {
		case <-r.timer.C:
			if !r.isDestroy && r.waitingTime != 0 {
				logger.Service.Zap.Infow("Round Timeout",
					"GameUser", r.secWebSocketKey,
					"BankerUuid", r.bankerUuid,
					"GameRoomUuid", r.gameRoomUuid,
					"GameRoomType", r.gameRoomType,
					"Seat", r.seat,
					"WaitingTime", r.waitingTime,
				)

				r.eRoundTimeout()
			}
		}
	}
}

func (r *round) eRoundTimeout() {
	r.rwMutex.Lock()
	defer r.rwMutex.Unlock()

	if r.isDestroy {
		return
	}

	switch r.state {
	case STATE_START:
		fallthrough
	case STATE_DRAW:
		flux.Send(ActionRoundTimeout, r.hashId(), r.bankerUuid, r.secWebSocketKey, r.kind, r.state)

	case STATE_PLAYCARD:
		r.state = STATE_END

	default:
		break
	}
}

func (r *round) reset() {
	n, err := rand.Int(rand.Reader, big.NewInt(int64(r.waitingTime)))

	if err != nil {
		panic(err)
	}

	if n.Uint64() == 0 {
		n = big.NewInt(1)
	}

	if r.kind == BOT {
		t := int(math.Ceil(float64(n.Uint64()) * 0.7))
		r.timer.Reset(time.Duration(t) * time.Second)
	} else {
		r.timer.Reset(time.Duration(r.waitingTime) * time.Second)
	}
}

func (r *round) stateChange(state string) {
	r.rwMutex.Lock()
	defer r.rwMutex.Unlock()

	r.state = state

	switch r.state {
	case STATE_START:
		r.reset()

	case STATE_DRAW:

	case STATE_PLAYCARD:
		fallthrough
	case STATE_END:
		if r.timer != nil {
			r.timer.Stop()
		}
	}
}

func (r *round) hashId() string {
	return Service.HashId(r.secWebSocketKey, r.gameRoomUuid)
}

func (r *round) destroy() {
	r.rwMutex.Lock()
	defer r.rwMutex.Unlock()

	if !r.isDestroy {
		if r.timer != nil {
			r.timer.Stop()
		}
		r.isDestroy = true
	}
}
