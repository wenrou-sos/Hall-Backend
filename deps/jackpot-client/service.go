package jackpot_client

import (
	"fmt"
	"gitlab.iplaystar.net/game-server/common"
	"gitlab.iplaystar.net/game-server/flux"
	jackpot_proto "gitlab.iplaystar.net/game-server/jackpot-client/proto"
	"gitlab.iplaystar.net/game-server/logger"
	"os"
	"strconv"
	"sync"
)

const (
	ActionJackpotClientCreate = "ActionJackpotClientCreate"
	ActionJackpotUpdate       = "ActionJackpotUpdate"
	ActionJackpotContribute   = "ActionJackpotContribute"
	ActionJackpotDeleteUser	  = "ActionJackpotDeleteUser"
)

var Service = &service{
	Id:       "JackpotClientService",
	poolSize: os.Getenv("POOL_SIZE"),
	in:       make(chan *flux.Action, common.Service.ChanSize),
	mutex:    sync.Mutex{},
}

type service struct {
	Id       	string
	poolSize 	string
	subsystem 	*jackpotClientSubsystem
	in       	chan *flux.Action
	mutex    	sync.Mutex
}

func init() {
	logger.Service.Zap.Infow("Service created.",
		"Service", Service.Id,
		"Chan", fmt.Sprintf("%p", Service.in),
	)

	Service.run()
}

func (s *service) run() {
	flux.Register(s.Id, s.in)

	s.subsystem = &jackpotClientSubsystem{
		jackpotClient: 	make(map[string]interface{}),
		stopped: 		false,
		rwMutex: 		&sync.RWMutex{},
		iHandler: 		nil,
	}

	poolSize := 10

	if s.poolSize != "" {
		if poolSize, _ = strconv.Atoi(s.poolSize); poolSize == 0 {
			poolSize = 10
		}
	}

	for i := 0; i < poolSize * 10; i++ {
		go func() {
			for action := range s.in {
				s.handleAction(action)
			}
		}()
	}
}

func (s *service) handleAction(action *flux.Action) {
	s.mutex.Lock()
	defer s.mutex.Unlock()

	switch action.Key().Name() {
	case ActionJackpotUpdate:
		secWebsocketKey := action.Payload()[0].(string)

		for _, v := range s.subsystem.jackpotClient {
			if client, ok := v.(*mysteryJackpotClient); ok {
				client.jackpotUpdate(secWebsocketKey)
			} else {
				logger.Service.Zap.Warnw("Jackpot Update Failed.",
					"GameUser", secWebsocketKey,
				)
			}
		}

	case ActionJackpotClientCreate:
		// maybe other jackpot type in future
		iHandler := action.Payload()[0].(IHandler)
		s.subsystem.iHandler = iHandler

		m := Builder().
			SetScheme("ws").
			SetHost(Config.Client.MYS.Server).
			SetPort(strconv.Itoa(Config.Client.MYS.Port)).
			SetUseSSL(Config.Client.MYS.UseSSL).
			SetPath("/MYS").
			SetJackpotType(JackpotType_MYS).
			SetIJackpot(s.subsystem).
			Build()
		s.subsystem.jackpotClient[JackpotType_MYS] = m

	case ActionJackpotContribute:
		clientInfo := action.Payload()[0].(*jackpot_proto.ClientInfo)
		accountingSn := action.Payload()[1].(uint64)
		offline := action.Payload()[2].(bool)

		for _, v := range s.subsystem.jackpotClient {
			if client, ok := v.(*mysteryJackpotClient); ok {
				contributeValue := client.contribute(clientInfo, accountingSn)

				if !offline && contributeValue != 0 {
					s.subsystem.iHandler.JackpotContributeHandler(
						accountingSn,
						contributeValue,
						clientInfo.HostName,
						clientInfo.SessionId,
					)
				}
			} else {
				logger.Service.Zap.Warnw("Jackpot Contribute Failed.",
					"GameUser", clientInfo.SessionId,
				)
			}
		}

	case ActionJackpotDeleteUser:
		secWebsocketKey := action.Payload()[0].(string)

		for _, v := range s.subsystem.jackpotClient {
			if client, ok := v.(*mysteryJackpotClient); ok {
				client.deleteUser(secWebsocketKey)
			} else {
				logger.Service.Zap.Warnw("Jackpot Delete User Failed.",
					"GameUser", secWebsocketKey,
				)
			}
		}

	default:
		break
	}
}

func (s *service) HashId(jackpotType string) string {
	return jackpotType + Service.Id
}

func (s *service) Destroy() {
	flux.UnRegister(s.Id, s.in)
}