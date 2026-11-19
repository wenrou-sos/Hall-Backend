package draw

import (
    draw_proto "89-game-server/domain/draw/proto"
    common89_proto "89-game-server/models/proto"
    "github.com/gogo/protobuf/proto"
    errorcode "gitlab.iplaystar.net/game-server/error-code"
    "gitlab.iplaystar.net/game-server/flux"
    "gitlab.iplaystar.net/game-server/logger"
    "sync"
    "time"
)

const (
    EMSGID_eDrawCall                = "EMSGID_eDrawCall"
    EMSGID_eDrawRecall              = "EMSGID_eDrawRecall"
    EMSGID_eBroadcastDrawRecall     = "EMSGID_eBroadcastDrawRecall"
    EMSGID_eDrawTimeout             = "EMSGID_eDrawTimeout"
    EMSGID_eBroadcastDrawTimeout    = "EMSGID_eBroadcastDrawTimeout"
    EMSGID_eDrawRoundStart          = "EMSGID_eDrawRoundStart"
    EMSGID_eDrawRoundEnd            = "EMSGID_eDrawRoundEnd"
    EMSGID_eBroadcastDrawRoundStart = "EMSGID_eBroadcastDrawRoundStart"
    EMSGID_eBroadcastDrawRoundEnd   = "EMSGID_eBroadcastDrawRoundEnd"
    BOT                             = "BOT"
    PLAYER                          = "PLAYER"
    GAME_ROOM                       = "GAME_ROOM"
    FRIEND_ROOM                     = "FRIEND_ROOM"
)

func Builder() *builder {
    return &builder{
        bankerUuid:      "",
        secWebSocketKey: "",
        gameRoomUuid:    "",
        gameRoomType:    "",
        seat:            -1,
        sumPoint:        -1,
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
    sumPoint        int32
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
    sumPoint        int32
    waitingTime     uint32
    sleepTime       uint32
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

func (b *builder) SetSumPoint(sumPoint int32) *builder {
    b.sumPoint = sumPoint
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
    return &draw{
        bankerUuid:      b.bankerUuid,
        secWebSocketKey: b.secWebSocketKey,
        gameRoomUuid:    b.gameRoomUuid,
        gameRoomType:    b.gameRoomType,
        seat:            b.seat,
        sumPoint:        b.sumPoint,
        waitingTime:     b.waitingTime,
        sleepTime:       b.sleepTime,
        isDraw:          false,
        isDestroy:       false,
        kind:            b.kind,
        in:              make(chan *flux.Action, 32),
        rwMutex:         &sync.RWMutex{},
    }
}

func (d *draw) isRule() bool {
    if d.sumPoint == 8 || d.sumPoint == 9 {
        logger.Service.Zap.Infow("Draw Timeout With Special Rule",
            "GameUser", d.secWebSocketKey,
            "BankerUuid", d.bankerUuid,
            "GameRoomUuid", d.gameRoomUuid,
            "GameRoomType", d.gameRoomType,
            "Seat", d.seat,
            "Kind", d.kind,
            "SumPoint", d.sumPoint,
            "NeedDraw", false,
        )

        d.eDrawTimeout(false)
        return true
    }

    if d.sumPoint >= 0 && d.sumPoint <= 3 {
        time.Sleep(2 * time.Second) // for web client animation

        logger.Service.Zap.Infow("Draw Timeout With Special Rule",
            "GameUser", d.secWebSocketKey,
            "BankerUuid", d.bankerUuid,
            "GameRoomUuid", d.gameRoomUuid,
            "GameRoomType", d.gameRoomType,
            "Seat", d.seat,
            "Kind", d.kind,
            "SumPoint", d.sumPoint,
            "NeedDraw", true,
        )

        d.eDrawTimeout(true)
        return true
    }

    if (d.sumPoint == 4 || d.sumPoint == 5) && d.kind == BOT {
        time.Sleep(2 * time.Second) // for web client animation

        logger.Service.Zap.Infow("Draw Timeout With Special Rule",
            "GameUser", d.secWebSocketKey,
            "BankerUuid", d.bankerUuid,
            "GameRoomUuid", d.gameRoomUuid,
            "GameRoomType", d.gameRoomType,
            "Seat", d.seat,
            "Kind", d.kind,
            "SumPoint", d.sumPoint,
            "NeedDraw", true,
        )

        d.eDrawTimeout(true)
        return true
    }

    if (d.sumPoint == 6 || d.sumPoint == 7) && d.kind == BOT {
        time.Sleep(2 * time.Second) // for web client animation

        logger.Service.Zap.Infow("Draw Timeout With Special Rule",
            "GameUser", d.secWebSocketKey,
            "BankerUuid", d.bankerUuid,
            "GameRoomUuid", d.gameRoomUuid,
            "GameRoomType", d.gameRoomType,
            "Seat", d.seat,
            "Kind", d.kind,
            "SumPoint", d.sumPoint,
            "NeedDraw", false,
        )

        d.eDrawTimeout(false)
        return true
    }

    return false
}

func (d *draw) run() {
    if d.sleepTime > 0 {
        time.Sleep(time.Duration(d.sleepTime) * time.Second)
    }

    flux.Register(d.hashId(), d.in)

    t := time.NewTimer(time.Duration(d.waitingTime) * time.Second)

    defer t.Stop()

    for {
        select {
        case action, ok := <-d.in:
            if !ok {
                return
            }

            d.handleAction(action)

        case <-t.C:

            if d.isDraw {
                return
            }

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
            d.destroy()
            time.Sleep(1 * time.Second)
            d.eBroadcastDrawRoundEnd(d.eDrawRoundEnd())

            switch d.gameRoomType {
            case GAME_ROOM:
                flux.Send(ActionDrawNext, d.hashId(), Service.Id, d.gameRoomUuid, d.seat)

            case FRIEND_ROOM:
                flux.Send(ActionDrawNext, d.hashId(), d.gameRoomUuid, d.seat, d.secWebSocketKey)

            default:
                panic("ERROR ROOM TYPE")
            }
            return
        }
    }
}

func (d *draw) handleAction(action *flux.Action) {
    if action.Key().To() != d.hashId() {
        return
    }

    switch action.Key().Name() {
    case flux.ActionFluxRegisterDone:
        logger.Service.Zap.Infow("Draw Started",
            "GameUser", d.secWebSocketKey,
            "BankerUuid", d.bankerUuid,
            "GameRoomUuid", d.gameRoomUuid,
            "GameRoomType", d.gameRoomType,
            "Seat", d.seat,
            "WaitingTime", d.waitingTime,
            "IsDraw", d.isDraw,
        )

        d.eBroadcastDrawRoundStart(d.eDrawRoundStart())

        if d.isRule() {
            d.destroy()
            d.eBroadcastDrawRoundEnd(d.eDrawRoundEnd())
            time.Sleep(500 * time.Millisecond) // for web client animation

            switch d.gameRoomType {
            case GAME_ROOM:
                flux.Send(ActionDrawNext, d.hashId(), Service.Id, d.gameRoomUuid, d.seat)

            case FRIEND_ROOM:
                flux.Send(ActionDrawNext, d.hashId(), d.gameRoomUuid, d.seat, d.secWebSocketKey)

            default:
                panic("ERROR ROOM TYPE")
            }
        }

    case EMSGID_eDrawCall:
        msg := action.Payload()[0].([]byte)

        if data := d.eDrawCall(msg); data != nil {
            d.eDrawRecall(data)
            d.destroy()
            time.Sleep(1 * time.Second)
            d.eBroadcastDrawRoundEnd(d.eDrawRoundEnd())

            switch d.gameRoomType {
            case GAME_ROOM:
                flux.Send(ActionDrawNext, d.hashId(), Service.Id, data.RoomUuid, data.Seat)

            case FRIEND_ROOM:
                flux.Send(ActionDrawNext, d.hashId(), data.RoomUuid, data.Seat, d.secWebSocketKey)

            default:
                panic("ERROR GAME ROOM TYPE")
            }

        }
    }
}

func (d *draw) eDrawTimeout(needDraw bool) {
    d.rwMutex.Lock()
    defer d.rwMutex.Unlock()

    if d.isDraw {
        return
    }

    d.isDraw = true

    data := &draw_proto.DrawTimeout{
        Msgid:    common89_proto.EMSGID_eDrawTimeout,
        RoomUuid: d.gameRoomUuid,
        Seat:     d.seat,
        Card:     -1,
        SumPoint: -1,
    }

    switch d.gameRoomType {

    case GAME_ROOM:
        flux.Send(EMSGID_eDrawTimeout, d.hashId(), d.bankerUuid,
            d.secWebSocketKey,
            data,
            needDraw,
        )

    case FRIEND_ROOM:
        dataByte, _ := proto.Marshal(data)

        flux.Send(EMSGID_eDrawTimeout, d.hashId(), d.gameRoomUuid,
            dataByte,
            d.bankerUuid,
            needDraw,
            d.secWebSocketKey,
            d.seat,
        )

    default:
        panic("ERROR GAME ROOM TYPE")
    }
}

func (d *draw) eDrawCall(msg []byte) *draw_proto.DrawCall {
    d.rwMutex.Lock()
    defer d.rwMutex.Unlock()

    if d.isDraw {
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

    return data
}

func (d *draw) eDrawRecall(drawCall *draw_proto.DrawCall) {
    data := &draw_proto.DrawRecall{
        Msgid:    common89_proto.EMSGID_eDrawRecall,
        RoomUuid: drawCall.RoomUuid,
        Seat:     drawCall.Seat,
        Card:     -1,
        SumPoint: -1,
    }

    switch d.gameRoomType {
    case GAME_ROOM:
        flux.Send(EMSGID_eDrawRecall, d.hashId(), d.bankerUuid,
            d.secWebSocketKey,
            data,
            drawCall.Status,
        )
    case FRIEND_ROOM:
        dataByte, _ := proto.Marshal(data)

        flux.Send(EMSGID_eDrawRecall, d.hashId(), drawCall.RoomUuid,
            dataByte,
            d.bankerUuid,
            drawCall.Status,
            d.secWebSocketKey,
            d.seat,
        )
    }
}

func (d *draw) eDrawRoundEnd() *draw_proto.DrawRoundEnd {
    data := &draw_proto.DrawRoundEnd{
        Msgid:    common89_proto.EMSGID_eDrawRoundEnd,
        RoomUuid: d.gameRoomUuid,
        Seat:     d.seat,
    }

    dataByte, _ := proto.Marshal(data)

    // TODO JOHNNY REDIS 廣播
    flux.Send(EMSGID_eDrawRoundEnd, d.hashId(), d.secWebSocketKey, dataByte)
    return data
}

func (d *draw) eBroadcastDrawRoundEnd(drawRoundEnd *draw_proto.DrawRoundEnd) {
    data := &draw_proto.BroadcastDrawRoundEnd{
        Msgid:        common89_proto.EMSGID_eBroadcastDrawRoundEnd,
        DrawRoundEnd: drawRoundEnd,
    }

    dataByte, _ := proto.Marshal(data)

    flux.Send(EMSGID_eBroadcastDrawRoundEnd, d.hashId(), d.gameRoomUuid, dataByte, drawRoundEnd.Seat)
}

func (d *draw) eDrawRoundStart() *draw_proto.DrawRoundStart {
    data := &draw_proto.DrawRoundStart{
        Msgid:    common89_proto.EMSGID_eDrawRoundStart,
        RoomUuid: d.gameRoomUuid,
        Seat:     d.seat,
    }

    dataByte, _ := proto.Marshal(data)

    flux.Send(EMSGID_eDrawRoundStart, d.hashId(), d.secWebSocketKey, dataByte)

    return data
}

func (d *draw) eBroadcastDrawRoundStart(drawRoundStart *draw_proto.DrawRoundStart) {
    data := &draw_proto.BroadcastDrawRoundStart{
        Msgid:          common89_proto.EMSGID_eBroadcastDrawRoundStart,
        DrawRoundStart: drawRoundStart,
    }

    dataByte, _ := proto.Marshal(data)

    flux.Send(EMSGID_eBroadcastDrawRoundStart, d.hashId(), d.gameRoomUuid, dataByte, drawRoundStart.Seat)
}

func (d *draw) hashId() string {
    return Service.HashId(d.secWebSocketKey, d.gameRoomUuid)
}

func (d *draw) destroy() {
    d.rwMutex.Lock()
    defer d.rwMutex.Unlock()

    if !d.isDestroy {
        d.isDestroy = true
        flux.UnRegister(d.hashId(), d.in)
    }
}
