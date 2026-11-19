package twin

import (
	"fish-shrimp-crab-game-server/application/lottery"
	lottery_proto "fish-shrimp-crab-game-server/application/lottery/proto"
	"fish-shrimp-crab-game-server/application/playerstate"
	bet_proto "fish-shrimp-crab-game-server/domain/bet/proto"
	"sync"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/accounting"
	"gitlab.iplaystar.net/game-server/auth"
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	"gitlab.iplaystar.net/game-server/flux"
	gamesetting "gitlab.iplaystar.net/game-server/game-setting"
	gameuser "gitlab.iplaystar.net/game-server/game-user"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/wallet"
)

const (
	ActionTwinActive  = "ActionTwinActive"
	ActionTwinDestroy = "ActionTwinDestroy"
)

type twin struct {
	uuid            string
	secWebSocketKey string
	memberId        string
	hostId          string
	gameRoomUuid    string
	memberName      string
	avatar          string
	seat            int
	accountingSn    uint64
	controllerId    string
	in              chan *flux.Action
	rwMutex         *sync.RWMutex
	isActive        bool
}

func New(secWebSocketKey string, memberId string, hostId string, gameRoomUuid string, avatar string, controllerId string) {
	t := &twin{
		secWebSocketKey: secWebSocketKey,
		memberId:        memberId,
		hostId:          hostId,
		gameRoomUuid:    gameRoomUuid,
		avatar:          avatar,
		controllerId:    controllerId,
		accountingSn:    0,
		isActive:        false,
		in:              make(chan *flux.Action, 1024),
		rwMutex:         &sync.RWMutex{},
	}
	go t.run()
}

func (t *twin) handleAction(action *flux.Action) {
	switch action.Key().Name() {

	case flux.ActionFluxRegisterDone:
		logger.Service.Zap.Infow("Twin GameUser Registered",
			"GameUser", t.secWebSocketKey,
			"GameRoomUuid", t.gameRoomUuid,
			"Seat", t.seat,
			"MemberId", t.memberId,
			"HostId", t.hostId,
		)

	case ActionTwinDestroy:
		t.destory()

	case gameuser.ActionJoinGameRoomRecall:
		t.rwMutex.Lock()
		defer t.rwMutex.Unlock()
		logger.Service.Zap.Infow("twin join room")
		t.gameRoomUuid = action.Payload()[0].(string)
		t.seat = action.Payload()[1].(int)

	case ActionTwinActive:
		t.rwMutex.Lock()
		defer t.rwMutex.Unlock()

		accountingSn := action.Payload()[0].(uint64)
		t.accountingSn = accountingSn
		t.isActive = true
		logger.Service.Zap.Infow("Twin GameUser Take Over",
			"GameUser", t.secWebSocketKey,
			"GameRoomUuid", t.gameRoomUuid,
			"Seat", t.seat,
			"MemberId", t.memberId,
			"AccountingSn", t.accountingSn,
		)

	case lottery.EMSGID_eBroadcastLotteryResult:
		if t.isActive {
			logger.Service.Zap.Infow("twin leave room", "twin uuid", t.secWebSocketKey)

			dataByte := action.Payload()[0].([]byte)
			data1 := &lottery_proto.BroadcastResult{} //braodcastResult
			if err := proto.Unmarshal(dataByte, data1); err != nil {
				logger.Service.Zap.Errorw(gamesetting.GameSetting_CONFIG_RECALL_PROTO_INVALID,
					"GameUser", t.secWebSocketKey,
				)
				errorcode.Service.Fatal(t.secWebSocketKey, gamesetting.GameSetting_CONFIG_RECALL_PROTO_INVALID)
			}

			data2 := action.Payload()[1].(map[string][]bet_proto.BetCall) //betCall
			data3 := action.Payload()[2].([3]int32)                       //dice
			memberName := wallet.Service.MemberName(t.secWebSocketKey)
			balance, _ := wallet.Service.BalanceCache(t.secWebSocketKey)
			flux.Send(accounting.ActionAccountingEnd, t.secWebSocketKey, accounting.Service.HashId(t.secWebSocketKey, t.accountingSn), data1, data2, data3, memberName, balance)

			t.leaveRoom()

			flux.Send(auth.ActionAuthNotify, t.secWebSocketKey, auth.Service.Id,
				t.memberId,
				t.hostId,
				dataByte,
			)

			t.destory()
		}
	}
}

func (t *twin) run() {
	flux.Register(t.secWebSocketKey, t.in)

	for action := range t.in {
		t.handleAction(action)
	}
}

func (t *twin) destory() {
	t.rwMutex.Lock()
	defer t.rwMutex.Unlock()
	logger.Service.Zap.Infow("Unregister Twin GameUser",
		"GameUser", t.secWebSocketKey,
		"GameRoomUuid", t.gameRoomUuid,
		"Seat", t.seat,
		"MemberId", t.memberId,
		"AccountingSn", t.accountingSn,
		"HostId", t.hostId,
	)
	gamesetting.Service.Delete(t.secWebSocketKey)
	wallet.Service.Close(t.secWebSocketKey)
	flux.Send(playerstate.ActionClearBetState, t.secWebSocketKey, playerstate.Service.Id,
		t.memberId,
		t.hostId)
	flux.UnRegister(t.secWebSocketKey, t.in)
}

func (t *twin) leaveRoom() {
	flux.Send(auth.EMSGID_eBroadcastPlayerOut, t.secWebSocketKey, t.gameRoomUuid, auth.Service.BroadcastPlayerOut(
		t.gameRoomUuid,
		t.secWebSocketKey,
		t.memberName,
		t.avatar,
		uint32(t.seat),
		uint64(0),
	))

	flux.Send(gameuser.ActionLeaveGameRoomCall, t.secWebSocketKey, t.controllerId, t.gameRoomUuid)
}
