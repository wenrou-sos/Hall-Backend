package jackpot

import (
	"fmt"
	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/broadcaster"
	"gitlab.iplaystar.net/game-server/common"
	common_proto "gitlab.iplaystar.net/game-server/common/proto"
	"gitlab.iplaystar.net/game-server/flux"
	jackpot_client "gitlab.iplaystar.net/game-server/jackpot-client"
	jackpot_proto "gitlab.iplaystar.net/game-server/jackpot-client/proto"
	"gitlab.iplaystar.net/game-server/logger"
	"os"
	"strconv"
	"sync"
	"time"
)

const (
	ActionJackpotUpdate      = "ActionJackpotUpdate"
	ActionJackpotContribute  = "ActionJackpotContribute"
	ActionJackpotDeleteUser  = "ActionJackpotDeleteUser"
	ActionBroadcasterJackpot = "ActionBroadcasterJackpot"
	EMSGID_eCentInAsk        = "EMSGID_eCentInAsk"
	EMSGID_eCentInReask      = "EMSGID_eCentInReask"
	EMSGID_eJackpotInfo      = "EMSGID_eJackpotInfo"
	EMSGID_eJackpotNotify    = "EMSGID_eJackpotNotify"
)

var Service = &service{
	Id:       "JackpotService",
	poolSize: os.Getenv("POOL_SIZE"),
	in:       make(chan *flux.Action, common.Service.ChanSize),
	mutex:    sync.Mutex{},
}

type service struct {
	Id       string
	poolSize string
	groupId  int32
	in       chan *flux.Action
	mutex    sync.Mutex
}

func init() {
	logger.Service.Zap.Infow("Service created.",
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
	s.mutex.Lock()
	defer s.mutex.Unlock()

	switch action.Key().Name() {
	case ActionJackpotUpdate:
		secWebsocketKey := action.Payload()[0].(string)
		jackpotGroup := action.Payload()[1].(int32)

		s.groupId = jackpotGroup
		flux.Send(jackpot_client.ActionJackpotUpdate, Service.Id, jackpot_client.Service.Id, secWebsocketKey)

	case ActionJackpotContribute:
		cent := action.Payload()[0].(uint64)
		hostId := action.Payload()[1].(string)
		hostExtId := action.Payload()[2].(string)
		memberId := action.Payload()[3].(string)
		secWebSocketKey := action.Payload()[4].(string)
		accountingSn := action.Payload()[5].(uint64)
		offline := action.Payload()[6].(bool)
		gameId := action.Payload()[7].(string)
		subgameId := action.Payload()[8].(int)
		jackpotGroup := action.Payload()[9].(int32)

		s.groupId = jackpotGroup

		clientInfo := &jackpot_proto.ClientInfo{
			SessionId:    secWebSocketKey,
			HostId:       hostId,
			HostName:     hostExtId,
			MemberId:     memberId,
			TotalBet:     uint32(cent),
			TotalBetLong: cent,
			GameId:       gameId,
			SubgameId:    uint32(subgameId),
			ExchangeRate: 1,
			GroupId: 	  jackpotGroup,
		}

		if offline {
			clientInfo.LeaveTs = uint64(time.Now().Unix())
		}

		if offline || cent > 0 {
			flux.Send(jackpot_client.ActionJackpotContribute, Service.Id, jackpot_client.Service.Id,
				clientInfo,
				accountingSn,
				offline,
			)
		}

	case ActionJackpotDeleteUser:
		secWebsocketKey := action.Payload()[0].(string)
		flux.Send(jackpot_client.ActionJackpotDeleteUser, Service.Id, jackpot_client.Service.Id, secWebsocketKey)

	default:
		break
	}
}

func (s *service) Start() {
	Service.run()
	flux.Send(jackpot_client.ActionJackpotClientCreate, Service.Id, jackpot_client.Service.Id, s)
}

func (s *service) JackpotContributeHandler(accountingSn uint64, contributeRate float64, hostExtId, secWebSocketKey string) {
	s.InsertVp1(accountingSn, contributeRate, hostExtId, secWebSocketKey)
}

func (s *service) JackpotHitHandler(hitInfo *jackpot_proto.HitInfo, from, secWebsocketKey string) {
	data := &jackpot_proto.CentInAsk{
		Msgid:  common_proto.EMSGID_eCentInAsk,
		Type:   jackpot_proto.ECENTINTYPE(hitInfo.ShowType),
		Tid:    hitInfo.JackpotSn,
		PoolId: hitInfo.Level,
		Cent:   hitInfo.WinningCent,
	}
	dataBuffer, _ := proto.Marshal(data)

	flux.Send(EMSGID_eCentInAsk, from, secWebsocketKey, dataBuffer, hitInfo.WinningCent)
}

func (s *service) JackpotEndHandler(hitInfo *jackpot_proto.HitInfo) {
	jackpot := Builder().
		SetAccountingSn(hitInfo.AccountingSn).
		SetJackpotSn(hitInfo.JackpotSn).
		SetHostId(hitInfo.ClientInfo.HostId).
		SetJackpotType(hitInfo.JackpotType).
		SetJackpotGroup(hitInfo.ClientInfo.GroupId).
		SetJackpotPool(hitInfo.PoolId).
		SetJackpotName(hitInfo.PoolName).
		SetJackpotWin(hitInfo.WinningCent).
		SetJackpotData(hitInfo.JackpotData).
		Build()

	s.InsertJackpot(jackpot, hitInfo.ClientInfo.HostName, hitInfo.ClientInfo.SessionId)
	s.Award(hitInfo)
	s.UpdateJackpot(jackpot, hitInfo.ClientInfo.HostName, hitInfo.ClientInfo.SessionId)
}

func (s *service) JackpotNotifyHandler(notifyInfo *jackpot_proto.NotifyInfo, from string) {
	data := &jackpot_proto.JackpotNotify{
		Msgid:  common_proto.EMSGID_eJackpotNotify,
		PoolId: notifyInfo.PoolInfo.Level,
		Type:   int32(notifyInfo.Type),
	}
	dataBuffer, _ := proto.Marshal(data)

	flux.Send(ActionBroadcasterJackpot, from, broadcaster.Service.Id,
		EMSGID_eJackpotNotify,
		dataBuffer,
		s.groupId,
	)
}

func (s *service) JackpotUpdateHandler(poolInfoMap map[int32]*jackpot_proto.PoolInfoMap, from string, jackpotType, secWebsocketKey string) {
	data := &jackpot_proto.JackpotInfo{
		Msgid:      common_proto.EMSGID_eJackpotInfo,
		StatusCode: common_proto.Status_kSuccess,
		Type:       jackpot_proto.ECENTINTYPE_eJackpot,
	}

	var poolList []*jackpot_proto.Pool

	switch jackpotType {
	case jackpot_client.JackpotType_MYS:
		if _, ok := poolInfoMap[s.groupId]; ok {
			for _, v := range poolInfoMap[s.groupId].Map {
				pool := &jackpot_proto.Pool{
					Id:          v.Level,
					Name:        v.PoolName,
					CurrentCent: v.CurrentCent,
					MaxCent:     v.MaxCent,
					Enable:      v.Enable,
				}
				poolList = append(poolList, pool)
			}
			data.PoolList = poolList
		}

	default:
		break
	}

	if len(data.PoolList) > 0 {
		dataBuffer, _ := proto.Marshal(data)

		if secWebsocketKey == "" {
			flux.Send(ActionBroadcasterJackpot, from, broadcaster.Service.Id,
				EMSGID_eJackpotInfo,
				dataBuffer,
				s.groupId,
			)
		} else {
			flux.Send(EMSGID_eJackpotInfo, from, secWebsocketKey, dataBuffer)
		}
	}
}

func (s *service) HashId(key string) string {
	return key + Service.Id
}

func (s *service) Destroy() {
	flux.UnRegister(s.Id, s.in)
}
