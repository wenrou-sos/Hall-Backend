package playcards

import (
	"github.com/gogo/protobuf/proto"
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	"sync"
	play_cards_proto "u-game-server/domain/playcards/proto"
	commonU_proto "u-game-server/models/proto"

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
	ActionPlayCardsResume			  = "ActionPlayCardsResume"
	ActionPlayCardsDelete			  = "ActionPlayCardsDelete"
	ActionPlayCardsReset			  = "ActionPlayCardsReset"
	BOT                               = "BOT"
	PLAYER                            = "PLAYER"
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

type playCards struct {
	bankerUuid      string
	secWebSocketKey string
	gameRoomUuid    string
	gameRoomType    string
	seat            int32
	isPlayCards     bool
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

func (b *builder) Build() *playCards {
	p := &playCards{
		bankerUuid:      b.bankerUuid,
		secWebSocketKey: b.secWebSocketKey,
		gameRoomUuid:    b.gameRoomUuid,
		gameRoomType:    b.gameRoomType,
		seat:            b.seat,
		isPlayCards:     false,
		isDestroy:       false,
		kind:            b.kind,
		in:              make(chan *flux.Action, 32),
		rwMutex:         &sync.RWMutex{},
	}

	return p
}

func (p *playCards) ePlayCardsCall(msg []byte) *play_cards_proto.PlayCardsCall {
	p.rwMutex.Lock()
	defer p.rwMutex.Unlock()

	if p.isPlayCards || p.isDestroy {
		return nil
	}

	p.isPlayCards = true

	data := &play_cards_proto.PlayCardsCall{}

	err := proto.Unmarshal(msg, data)

	if data.RoomUuid != p.gameRoomUuid || data.Seat != p.seat || err != nil {
		logger.Service.Zap.Errorw(PlayCards_PROTO_PLAY_CARDS_CALL_INVAILD,
			"GameUser", p.secWebSocketKey,
			"BankerUuid", p.bankerUuid,
			"GameRoomUuid", p.gameRoomUuid,
			"GameRoomType", p.gameRoomType,
			"Seat", p.seat,
			"Data", data,
			"Error", err,
		)
		errorcode.Service.Fatal(p.secWebSocketKey, PlayCards_PROTO_PLAY_CARDS_CALL_INVAILD)
		return nil
	}

	logger.Service.Zap.Infow("Play cards",
		"GameUser", p.secWebSocketKey,
		"BankerUuid", p.bankerUuid,
		"GameRoomUuid", p.gameRoomUuid,
		"GameRoomType", p.gameRoomType,
		"Seat", p.seat,
		"Data", data,
	)

	return data
}

func (p *playCards) ePlayCardsRecall(playCardsCall *play_cards_proto.PlayCardsCall) {
	data := &play_cards_proto.PlayCardsRecall{
		Msgid:    commonU_proto.EMSGID_ePlayCardsRecall,
		RoomUuid: p.gameRoomUuid,
	}

	flux.Send(EMSGID_ePlayCardsRecall, p.hashId(), p.bankerUuid, data, p.secWebSocketKey, p.seat, p.kind, playCardsCall)
}

func (p *playCards) ePlayCardsTimeout() {
	p.rwMutex.Lock()
	defer p.rwMutex.Unlock()

	if p.isPlayCards || p.isDestroy {
		return
	}

	p.isPlayCards = true

	data := &play_cards_proto.PlayCardsTimeout{
		Msgid:      commonU_proto.EMSGID_ePlayCardsTimeout,
		RoomUuid:   p.gameRoomUuid,
		PlayerData: nil,
		Color:      -1,
	}

	flux.Send(EMSGID_ePlayCardsTimeout, p.hashId(), p.bankerUuid, data, p.secWebSocketKey, p.seat, p.kind)
}

func (p *playCards) reset() {
	p.rwMutex.Lock()
	defer p.rwMutex.Unlock()

	p.isPlayCards = false
}

func (p *playCards) hashId() string {
	return Service.HashId(p.secWebSocketKey, p.gameRoomUuid)
}

func (p *playCards) destroy() {
	p.rwMutex.Lock()
	defer p.rwMutex.Unlock()

	if !p.isDestroy {
		p.isDestroy = true
	}
}
