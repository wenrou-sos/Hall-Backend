package draw

import (
    draw_proto "89-game-server/domain/draw/proto"
    common89_proto "89-game-server/models/proto"
    "github.com/gogo/protobuf/proto"
    "gitlab.iplaystar.net/game-server/common"
    "gitlab.iplaystar.net/game-server/flux"
    "sync"
)

const (
    ActionDrawStart  = "ActionDrawStart"
    ActionDrawNext   = "ActionDrawNext"
    ActionDrawDelete = "ActionDrawDelete"
)

var Service = &service{
    Id:      "DrawService",
    in:      make(chan *flux.Action, common.Service.ChanSize),
    rwMutex: &sync.RWMutex{},
}

type service struct {
    Id      string
    in      chan *flux.Action
    rwMutex *sync.RWMutex
}

func init() {
    go Service.run()
}

func (s *service) run() {
    flux.Register(s.Id, s.in)

    draws := make(map[string]*draw)

    for action := range s.in {
        s.handleAction(action, draws)
    }
}

func (s *service) handleAction(action *flux.Action, draws map[string]*draw) {
    s.rwMutex.Lock()
    defer s.rwMutex.Unlock()

    if action.Key().To() != s.Id {
        return
    }

    switch action.Key().Name() {
    case ActionDrawStart:
        draw := action.Payload()[0].(*draw)

        if draw.seat == 0 {
            go draw.run()
            return
        }

        if v, ok := draws[draw.hashId()]; ok {
            delete(draws, v.hashId())
        }

        draws[draw.hashId()] = draw

    case ActionDrawNext:
        gameRoomUuid := action.Payload()[0].(string)
        seat := action.Payload()[1].(int32)

        temp := make(map[int32]*draw)

        for k, v := range draws {
            if v.gameRoomUuid == gameRoomUuid {

                if v.seat == seat && v.isDestroy {
                    delete(draws, k)
                } else {
                    temp[v.seat] = v
                }
            }
        }

        for i := 0; i < 6; i++ {
            if v, ok := temp[int32(i)]; ok {
                delete(draws, v.hashId())
                go v.run()
                break
            }
        }

    case ActionDrawDelete:
        gameRoomUuid := action.Payload()[0].(string)

        for k, v := range draws {
            if v.gameRoomUuid == gameRoomUuid {
                delete(draws, k)
            }
        }
    }
}

func (s *service) BroadcastDrawRecall(drawRecall *draw_proto.DrawRecall) []byte {
    data := &draw_proto.BroadcastDrawRecall{
        Msgid:      common89_proto.EMSGID_eBroadcastDrawRecall,
        DrawRecall: drawRecall,
    }

    dataByte, _ := proto.Marshal(data)

    return dataByte
}

func (s *service) BroadcastDrawTimeout(drawTimeout *draw_proto.DrawTimeout) []byte {
    data := &draw_proto.BroadcastDrawTimeout{
        Msgid:       common89_proto.EMSGID_eBroadcastDrawTimeout,
        DrawTimeout: drawTimeout,
    }

    dataByte, _ := proto.Marshal(data)

    return dataByte
}

func (s *service) HashId(secWebSocketKey, gameRoomUuid string) string {
    return secWebSocketKey + s.Id + gameRoomUuid
}

func (s *service) destroy() {
    flux.UnRegister(s.Id, s.in)
}
