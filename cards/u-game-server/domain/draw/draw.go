package draw

import (
	"sync"
	draw_proto "u-game-server/domain/draw/proto"
	commonU_proto "u-game-server/models/proto"

	"github.com/gogo/protobuf/proto"
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
)

const (
	EMSGID_eDrawCall                = "EMSGID_eDrawCall"
	EMSGID_eDrawRecall              = "EMSGID_eDrawRecall"
	EMSGID_eBroadcastDrawRecall     = "EMSGID_eBroadcastDrawRecall"
	EMSGID_eDrawTimeout             = "EMSGID_eDrawTimeout"
	EMSGID_eBroadcastDrawTimeout    = "EMSGID_eBroadcastDrawTimeout"
	ActionDrawCreate			    = "ActionDrawCreate"
	ActionDrawResume			  	= "ActionDrawResume"
	ActionDrawDelete			  	= "ActionDrawDelete"
	ActionDrawReset			    	= "ActionDrawReset"
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
		kind:            "",
	}
}

type builder struct {
	bankerUuid      string
	secWebSocketKey string
	gameRoomUuid    string
	gameRoomType    string
	seat            int32
	kind            string
}

type draw struct {
	bankerUuid      string
	secWebSocketKey string
	gameRoomUuid    string
	gameRoomType    string
	seat            int32
	isDraw          bool
	isDestroy       bool
	kind            string
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

func (b *builder) SetKind(kind string) *builder {
	b.kind = kind
	return b
}

func (b *builder) Build() *draw {
	d := &draw{
		bankerUuid:      b.bankerUuid,
		secWebSocketKey: b.secWebSocketKey,
		gameRoomUuid:    b.gameRoomUuid,
		gameRoomType:    b.gameRoomType,
		seat:            b.seat,
		isDraw:          false,
		isDestroy:       false,
		kind:            b.kind,
		in:              make(chan *flux.Action, 32),
		rwMutex:         &sync.RWMutex{},
	}

	return d
}

func (d *draw) eDrawTimeout() {
	d.rwMutex.Lock()
	defer d.rwMutex.Unlock()

	if d.isDraw || d.isDestroy {
		return
	}

	d.isDraw = true

	data := &draw_proto.DrawTimeout{
		Msgid:    commonU_proto.EMSGID_eDrawTimeout,
		RoomUuid: d.gameRoomUuid,
	}

	flux.Send(EMSGID_eDrawTimeout, d.hashId(), d.bankerUuid, data, d.secWebSocketKey, d.kind)
}

func (d *draw) eDrawCall(msg []byte) *draw_proto.DrawCall {
	d.rwMutex.Lock()
	defer d.rwMutex.Unlock()

	if d.isDraw || d.isDestroy {
		return nil
	}

	d.isDraw = true

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

	return data
}

func (d *draw) eDrawRecall() {
	data := &draw_proto.DrawRecall{
		Msgid:    commonU_proto.EMSGID_eDrawRecall,
		RoomUuid: d.gameRoomUuid,
	}

	flux.Send(EMSGID_eDrawRecall, d.hashId(), d.bankerUuid, data, d.secWebSocketKey, d.kind)
}

func (d *draw) BroadcastDrawRecall(drawRecall *draw_proto.DrawRecall) []byte {
	data := &draw_proto.BroadcastDrawRecall{
		Msgid: commonU_proto.EMSGID_eBroadcastDrawRecall,
	}

	dataByte, _ := proto.Marshal(data)

	return dataByte
}

func (d *draw) BroadcastDrawTimeout(drawTimeout *draw_proto.DrawTimeout) []byte {
	data := &draw_proto.BroadcastDrawTimeout{
		Msgid: commonU_proto.EMSGID_eBroadcastDrawTimeout,
	}

	dataByte, _ := proto.Marshal(data)

	return dataByte
}

func (d *draw) reset() {
	d.rwMutex.Lock()
	defer d.rwMutex.Unlock()

	d.isDraw = false
}

func (d *draw) hashId() string {
	return Service.HashId(d.secWebSocketKey, d.gameRoomUuid)
}

func (d *draw) destroy() {
	d.rwMutex.Lock()
	defer d.rwMutex.Unlock()

	if !d.isDestroy {
		d.isDestroy = true
	}
}
