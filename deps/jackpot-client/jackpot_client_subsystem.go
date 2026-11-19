package jackpot_client

import (
	"fmt"
	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/common"
	"gitlab.iplaystar.net/game-server/flux"
	jackpot_proto "gitlab.iplaystar.net/game-server/jackpot-client/proto"
	"gitlab.iplaystar.net/game-server/logger"
	"sync"
)

const (
	JackpotType_MYS  = "Mystery"
	JackpotType_LKD  = "LuckyDraw"
	JackpotType_LKD2 = "LuckyDraw2"

	actionJackpotHit     = "actionJackpotHit"
	actionJackpotEnd     = "actionJackpotEnd"
	EMSGID_kHitInfo      = "EMSGID_kHitInfo"
	EMSGID_kNotifyInfo   = "EMSGID_kNotifyInfo"
	EMSGID_kGroupInfoMap = "EMSGID_kGroupInfoMap"
)

func Builder() *builder {
	return &builder{
		scheme: "",
		host:   "",
		port:   "",
		path:   "",
	}
}

type builder struct {
	scheme 		string
	host 		string
	port 		string
	useSSL 		bool
	path 		string
	jackpotType string
	iJackpot 	IJackpot
}

type jackpotClientSubsystem struct {
	jackpotClient map[string]interface{}
	stopped		  bool
	rwMutex       *sync.RWMutex
	iHandler  	  IHandler
}

type IHandler interface {
	JackpotContributeHandler(accountingSn uint64, contributeRate float64, hostExtId, secWebSocketKey string)
	JackpotHitHandler(hitInfo *jackpot_proto.HitInfo, from, secWebsocketKey string)
	JackpotEndHandler(hitInfo *jackpot_proto.HitInfo)
	JackpotNotifyHandler(notifyInfo *jackpot_proto.NotifyInfo, from string)
	JackpotUpdateHandler(poolInfoMap map[int32]*jackpot_proto.PoolInfoMap, from, jackpotType, secWebsocketKey string)
}

type IJackpot interface {
	OnJackpotHit(hitInfo *jackpot_proto.HitInfo, accountingSn uint64, jackpotType string)
	OnJackpotNotify(notifyInfo *jackpot_proto.NotifyInfo, jackpotType string)
	OnJackpotUpdate(poolInfoMap map[int32]*jackpot_proto.PoolInfoMap, jackpotType, secWebsocketKey string)
	OnJackpotOffline()
}

func (b *builder) SetScheme(scheme string) *builder {
	b.scheme = scheme
	return b
}

func (b *builder) SetHost(host string) *builder {
	b.host = host
	return b
}

func (b *builder) SetPort(port string) *builder {
	b.port = port
	return b
}

func (b *builder) SetUseSSL(useSSL bool) *builder {
	b.useSSL = useSSL
	return b
}

func (b *builder) SetPath(path string) *builder {
	b.path = path
	return b
}

func (b *builder) SetJackpotType(t string) *builder {
	b.jackpotType = t
	return b
}

func (b *builder) SetIJackpot(i IJackpot) *builder {
	b.iJackpot = i
	return b
}

func (b *builder) Build() interface{} {
	switch b.jackpotType {
	case JackpotType_MYS:
		return b.newMysterJackpotClient(b.scheme, b.host, b.port, b.useSSL, b.path, b.iJackpot)
	default:
		return nil
	}
}

func (b *builder) newMysterJackpotClient(scheme, host, port string, useSSL bool, path string, jackpot IJackpot) *mysteryJackpotClient {
	m := &mysteryJackpotClient{
		accountingSnMap: 	make(map[string]uint64),
		totalBetMap: 		make(map[string]uint64),
		scheme: 			scheme,
		host: 				host,
		port: 				port,
		useSSL: 			useSSL,
		path: 				path,
		hitInfo:    		make(map[uint64]*jackpot_proto.HitInfo),
		poolInfoMaps: 		make(map[int32]*jackpot_proto.PoolInfoMap, 0),
		clientInfoMap: 		&jackpot_proto.ClientInfoMap{
			Map: make(map[string]*jackpot_proto.ClientInfo),
		},
		hasSynced:  		false,
		reconnect:  		true,
		connected:  		false,
		iJackpot:   		jackpot,
		in: 				make(chan *flux.Action, common.Service.ChanSize),
		rwMutex: 			&sync.RWMutex{},
		contributeMutex:	&sync.RWMutex{},
	}
	go m.run()

	logger.Service.Zap.Infow("Mystery Jackpot Client Create",
		"Chan", fmt.Sprintf("%p", m.in),
	)

	return m
}

func (j *jackpotClientSubsystem) OnJackpotHit(hitInfo *jackpot_proto.HitInfo, accountingSn uint64, jackpotType string) {
	j.rwMutex.Lock()
	defer j.rwMutex.Unlock()

	if _, ok := j.jackpotClient[jackpotType]; ok && j.iHandler != nil {
		hitInfo.Status = jackpot_proto.HitInfo_kCommit
		hitInfo.AccountingSn = accountingSn
		dataBuffer, _ := proto.Marshal(hitInfo)

		flux.Send(actionJackpotHit, Service.HashId(jackpotType), Service.HashId(jackpotType), dataBuffer)

		// todo jackpot win transfer

		if !hitInfo.IsDumb {
			j.iHandler.JackpotHitHandler(hitInfo, Service.HashId(jackpotType), hitInfo.ClientInfo.SessionId)
		}

		j.OnJackpotEnd(hitInfo, jackpotType)

		return
	}

	logger.Service.Zap.Warnw("On Jackpot Hit Failed",
		"GameUser", hitInfo.ClientInfo.SessionId,
		"AccountingSn", accountingSn,
		"Type", jackpotType,
	)
}

func (j *jackpotClientSubsystem) OnJackpotEnd(hitInfo *jackpot_proto.HitInfo, jackpotType string) {
	if hitInfo.Status == jackpot_proto.HitInfo_kCommit && j.iHandler != nil {
		j.iHandler.JackpotEndHandler(hitInfo)

		hitInfo.Status = jackpot_proto.HitInfo_kPaid
		dataBuffer, _ := proto.Marshal(hitInfo)

		flux.Send(actionJackpotEnd, Service.HashId(jackpotType), Service.HashId(jackpotType), dataBuffer)

		return
	}

	logger.Service.Zap.Warnw("On Jackpot End Failed",
		"GameUser", hitInfo.ClientInfo.SessionId,
		"AccountingSn", hitInfo.AccountingSn,
		"Type", jackpotType,
	)
}

func (j *jackpotClientSubsystem) OnJackpotNotify(notifyInfo *jackpot_proto.NotifyInfo, jackpotType string) {
	j.rwMutex.Lock()
	defer j.rwMutex.Unlock()

	if notifyInfo != nil && j.iHandler != nil {
		j.iHandler.JackpotNotifyHandler(notifyInfo, Service.HashId(jackpotType))

		return
	}

	logger.Service.Zap.Warnw("On Jackpot Notify Failed",
		"Type", jackpotType,
	)
}

func (j *jackpotClientSubsystem) OnJackpotUpdate(poolInfoMap map[int32]*jackpot_proto.PoolInfoMap, jackpotType, secWebsocketKey string) {
	j.rwMutex.Lock()
	defer j.rwMutex.Unlock()

	if j.iHandler != nil && poolInfoMap != nil {
		j.iHandler.JackpotUpdateHandler(poolInfoMap, Service.HashId(jackpotType), jackpotType, secWebsocketKey)

		return
	}

	logger.Service.Zap.Warnw("On Jackpot Update Failed",
		"Type", jackpotType,
	)
}

func (j *jackpotClientSubsystem) OnJackpotOffline() {}