package broadcaster

import (
	"fmt"
	"github.com/gogo/protobuf/proto"
	broadcaster_proto "gitlab.iplaystar.net/game-server/broadcaster/proto"
	common_proto "gitlab.iplaystar.net/game-server/common/proto"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
)

const (
	BigWinPay                   uint64 = 200
	ActionBroadcasterConfig            = "ActionBroadcasterConfig"
	ActionBroadcasterRegister          = "ActionBroadcasterRegister"
	ActionBroadcasterUnRegister        = "ActionBroadcasterUnRegister"
	ActionBroadcasterBigWin            = "ActionBroadcasterBigWin"
	ActionBroadcasterShutdown          = "ActionBroadcasterShutdown"
	ActionBroadcasterJackpot           = "ActionBroadcasterJackpot"
	EMSGID_eBroadcaster                = "EMSGID_eBroadcaster"
)

var Service = &service{
	Id: "BroadcasterService",
	in: make(chan *flux.Action, 1024),
}

type service struct {
	Id string
	in chan *flux.Action
}

type IHandler interface {
	BigWinHandler(action *flux.Action, allGames map[string]*RegisterBroadcaster, allGamesConfig map[string]*ConfigBroadcaster)
	JackpotHandler(action *flux.Action, allGames map[string]*RegisterBroadcaster)
}

func (s *service) Start(h IHandler) {
	go s.run(h)
	logger.Service.Zap.Infow("Service created.",
		"Service", s.Id,
		"Chan", fmt.Sprintf("%p", s.in),
	)
}

func (s *service) run(h IHandler) {
	flux.Register(s.Id, s.in)

	allGames := make(map[string]*RegisterBroadcaster)

	allGamesConfig := make(map[string]*ConfigBroadcaster)

	for {
		select {
		case action, ok := <-s.in:
			if !ok {
				return
			}

			switch action.Key().Name() {
			case ActionBroadcasterConfig:
				c := action.Payload()[0].(*ConfigBroadcaster)
				allGamesConfig[c.Id()] = c

			case ActionBroadcasterRegister:
				r := action.Payload()[0].(*RegisterBroadcaster)
				allGames[r.RoomUuid] = r

			case ActionBroadcasterUnRegister:
				u := action.Payload()[0].(*UnRegisterBroadcaster)
				delete(allGames, u.roomUuid)

			case ActionBroadcasterBigWin:
				h.BigWinHandler(action, allGames, allGamesConfig)

			case ActionBroadcasterShutdown:
				message := action.Payload()[0].(string)

				data := &broadcaster_proto.Broadcaster{
					Msgid:     common_proto.EMSGID_eBroadcaster,
					BcType:    broadcaster_proto.BROADCASTER_TYPE_SHUTDOWN,
					GameId:    "",
					SubgameId: 0,
					MemberId:  "PS",
					Message:   message,
					Time:      60,
				}

				dataByte, _ := proto.Marshal(data)

				for k, v := range allGames {
					// Lobby Room Rate is 0
					if v.Rate == 0 {
						data.DvType = broadcaster_proto.DELIVER_TYPE_LOBBY
					} else {
						data.DvType = broadcaster_proto.DELIVER_TYPE_GAME
					}

					flux.Send(EMSGID_eBroadcaster, s.Id, k, dataByte)
				}

			case ActionBroadcasterJackpot:
				h.JackpotHandler(action, allGames)

			}
		}
	}
}

func (s *service) parseMemberId(memberId string) string {
	// john ****
	// leo* ****
	// dd** ****
	switch len(memberId) {
	case 0:
		return "********"

	case 1:
		return memberId + "*******"

	case 2:
		return memberId + "******"

	case 3:
		return memberId + "******"

	default:
		return memberId[0:4] + "****"
	}
}

func (s *service) Destroy() {
	flux.UnRegister(s.Id, s.in)
}
