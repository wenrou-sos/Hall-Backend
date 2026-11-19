package draw

import (
	draw_proto "52-game-server/domain/draw/proto"
	common52_proto "52-game-server/models/proto"
	"crypto/rand"
	"math/big"
	"sync"
	"time"

	"github.com/gogo/protobuf/proto"
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
)

const (
	EMSGID_eDrawCall             = "EMSGID_eDrawCall"
	EMSGID_eDrawRecall           = "EMSGID_eDrawRecall"
	EMSGID_eBroadcastDrawRecall  = "EMSGID_eBroadcastDrawRecall"
	EMSGID_eDrawTimeout          = "EMSGID_eDrawTimeout"
	EMSGID_eBroadcastDrawTimeout = "EMSGID_eBroadcastDrawTimeout"
	ActionDrawCreate             = "ActionDrawCreate"
	ActionDrawReset              = "ActionDrawReset"
	ActionDrawResume             = "ActionDrawResume"
	ActionDrawStop               = "ActionDrawStop"
	ActionDrawDelete             = "ActionDrawDelete"
	BOT                          = "BOT"
	PLAYER                       = "PLAYER"
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
}

type draw struct {
	bankerUuid      string
	secWebSocketKey string
	gameRoomUuid    string
	gameRoomType    string
	seat            int32
	waitingTime     uint32
	sleepTime       uint32
	isDraw          bool
	isDestroy       bool
	kind            string
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

func (b *builder) Build() *draw {
	d := &draw{
		bankerUuid:      b.bankerUuid,
		secWebSocketKey: b.secWebSocketKey,
		gameRoomUuid:    b.gameRoomUuid,
		gameRoomType:    b.gameRoomType,
		seat:            b.seat,
		waitingTime:     b.waitingTime,
		sleepTime:       b.sleepTime,
		isDraw:          false,
		isDestroy:       false,
		kind:            b.kind,
		in:              make(chan *flux.Action, 32),
		rwMutex:         &sync.RWMutex{},
	}

	return d
}

func (d *draw) run() {
	d.rwMutex.Lock()

	d.timer = time.NewTimer(100 * time.Second)
	d.timer.Stop()

	d.rwMutex.Unlock()

	defer d.destroy()

	for {
		select {
		case <-d.timer.C:
			if !d.isDraw && !d.isDestroy && d.waitingTime != 0 {
				logger.Service.Zap.Infow("Draw Timeout",
					"GameUser", d.secWebSocketKey,
					"BankerUuid", d.bankerUuid,
					"GameRoomUuid", d.gameRoomUuid,
					"GameRoomType", d.gameRoomType,
					"Seat", d.seat,
					"NeedDraw", false,
					"WaitingTime", d.waitingTime,
				)

				d.eDrawTimeout(false)
			}
		}
	}
}

func (d *draw) eDrawTimeout(needDraw bool) {
	d.rwMutex.Lock()
	defer d.rwMutex.Unlock()

	if d.isDraw || d.isDestroy {
		return
	}

	d.isDraw = true

	data := &draw_proto.DrawTimeout{
		Msgid:    common52_proto.EMSGID_eDrawTimeout,
		RoomUuid: d.gameRoomUuid,
	}

	flux.Send(EMSGID_eDrawTimeout, d.hashId(), d.bankerUuid,
		data,
		d.secWebSocketKey,
		needDraw,
	)
}

func (d *draw) eDrawCall(msg []byte) *draw_proto.DrawCall {
	d.rwMutex.Lock()
	defer d.rwMutex.Unlock()

	if d.isDraw || d.isDestroy {
		return nil
	}

	d.isDraw = true

	// TODO JOHNNY 要去驗證 token

	data := &draw_proto.DrawCall{}

	err := proto.Unmarshal(msg, data)

	if data.RoomUuid != d.gameRoomUuid || data.Seat != d.seat || err != nil {
		logger.Service.Zap.Errorw(Draw_PROTO_DRAW_CALL_INVAILD,
			"GameUser", d.secWebSocketKey,
			"BankerUuid", d.bankerUuid,
			"GameRoomUuid", d.gameRoomUuid,
			"GameRoomType", d.gameRoomType,
			"Seat", d.seat,
			"Data", data,
			"Error", err,
		)
		errorcode.Service.Fatal(d.secWebSocketKey, Draw_PROTO_DRAW_CALL_INVAILD)
		return nil
	}

	logger.Service.Zap.Infow("Draw",
		"GameUser", d.secWebSocketKey,
		"BankerUuid", d.bankerUuid,
		"GameRoomUuid", d.gameRoomUuid,
		"GameRoomType", d.gameRoomType,
		"Seat", d.seat,
		"Data", data,
	)

	d.timer.Stop()

	return data
}

func (d *draw) eDrawRecall() {
	data := &draw_proto.DrawRecall{
		Msgid:    common52_proto.EMSGID_eDrawRecall,
		RoomUuid: d.gameRoomUuid,
	}

	flux.Send(EMSGID_eDrawRecall, d.hashId(), d.bankerUuid,
		data,
		d.secWebSocketKey,
	)
}

func (d *draw) BroadcastDrawRecall(drawRecall *draw_proto.DrawRecall) []byte {
	data := &draw_proto.BroadcastDrawRecall{
		Msgid: common52_proto.EMSGID_eBroadcastDrawRecall,
	}

	dataByte, _ := proto.Marshal(data)

	return dataByte
}

func (d *draw) BroadcastDrawTimeout(drawTimeout *draw_proto.DrawTimeout) []byte {
	data := &draw_proto.BroadcastDrawTimeout{
		Msgid: common52_proto.EMSGID_eBroadcastDrawTimeout,
	}

	dataByte, _ := proto.Marshal(data)

	return dataByte
}

func (d *draw) reset() {
	d.rwMutex.Lock()
	defer d.rwMutex.Unlock()

	n, err := rand.Int(rand.Reader, big.NewInt(int64(d.waitingTime)))

	if err != nil {
		panic(err)
	}

	if n.Uint64() == 0 {
		n = big.NewInt(1)
	}

	d.isDraw = false

	if d.kind == BOT {
		d.timer.Reset(time.Duration(n.Uint64()) * time.Second)
	} else {
		d.timer.Reset(time.Duration(d.waitingTime) * time.Second)
	}
}

func (d *draw) hashId() string {
	return Service.HashId(d.secWebSocketKey, d.gameRoomUuid)
}

func (d *draw) destroy() {
	d.rwMutex.Lock()
	defer d.rwMutex.Unlock()

	if !d.isDestroy {
		if d.timer != nil {
			d.timer.Stop()
		}
		d.isDestroy = true
	}
}
