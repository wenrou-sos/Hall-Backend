package heartbeat

import (
	"fmt"
	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/common"
	common_proto "gitlab.iplaystar.net/game-server/common/proto"
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	"gitlab.iplaystar.net/game-server/flux"
	heartbeat_proto "gitlab.iplaystar.net/game-server/heart-beat/proto"
	"gitlab.iplaystar.net/game-server/logger"
	"os"
	"strconv"
	"time"
)

const (
	ActionHeartBeatCall    = "ActionHeartBeatCall"
	ActionHeartBeatRecall  = "ActionHeartBeatRecall"
	ActionHeartBeatQuality = "ActionHeartBeatQuality"
)

var Service = &service{
	Id:       "HeartBeatService",
	poolSize: os.Getenv("POOL_SIZE"),
	in:       make(chan *flux.Action, common.Service.ChanSize),
}

type service struct {
	Id       string
	poolSize string
	in       chan *flux.Action
}

func init() {
	go Service.run()
	logger.Service.Zap.Infow("Service Created",
		"Service", Service.Id,
		"Chan", fmt.Sprintf("%p", Service.in),
	)
}

func (s *service) run() {
	flux.Register(s.Id, s.in)

	poolSize := 10

	if s.poolSize != "" {
		if poolSize, _ = strconv.Atoi(s.poolSize); poolSize == 0 {
			poolSize = 10
		}
	}

	for i := 0; i < poolSize; i++ {
		go func() {
			for action := range s.in {
				s.handleAction(action)
			}
		}()
	}
}

func (s *service) handleAction(action *flux.Action) {
	switch action.Key().Name() {
	case ActionHeartBeatCall:
		data := &heartbeat_proto.HeartbeatCall{}

		if err := proto.Unmarshal(action.Payload()[0].([]byte), data); err != nil {
			errorcode.Service.Fatal(action.Key().From(), HeartBeat_HEARTBEAT_CALL_PROTO_INVALID)
			return
		}

		dataByte, _ := proto.Marshal(
			&heartbeat_proto.HeartbeatRecall{
				Msgid:           common_proto.EMSGID_eHeartbeatRecall,
				ClientTimestamp: data.ClientTimestamp,
				ServerTimestamp: time.Now().Unix(),
			},
		)

		flux.Send(ActionHeartBeatRecall, s.Id, action.Key().From(), dataByte)

	case ActionHeartBeatQuality:
		s.calc(action)
	}
}

func (s *service) calc(action *flux.Action) {
	pingTime := action.Payload()[0].(string)

	if t, err := strconv.ParseInt(pingTime, 10, 64); err == nil {
		latency := (time.Now().UnixNano() - t) / 1e6

		if latency > 300 {
			logger.Service.Zap.Infow("Ping",
				"GameUser", action.Key().From(),
				"ms", latency,
			)
		}
	}
}

func (s *service) Destroy() {
	flux.UnRegister(s.Id, s.in)
}
