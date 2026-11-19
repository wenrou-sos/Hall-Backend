package twin

import (
	"colorgame-game-server/application/gamesettingFS"
	"colorgame-game-server/application/lottery"
	lottery_proto "colorgame-game-server/application/lottery/proto"
	"colorgame-game-server/application/playerstate"
	bet_proto "colorgame-game-server/domain/bet/proto"
	"colorgame-game-server/domain/vip"
	"runtime/debug"
	"sync"
	"time"

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
	secWebSocketKey string
	gameRoomUuid    string
	controllerId    string
	hostExtId       string
	memberId        string
	memberName      string
	hostId          string
	billCurrency    string
	guestEnable     bool
	avatar          string
	seat            int
	accountingSn    uint64
	in              chan *flux.Action
	rwMutex         *sync.RWMutex
	isActive        bool
}

func New(secWebSocketKey, gameRoomUuid, controllerId, hostExtId, memberId, memberName, hostId, billCurrency string, guestEnable bool, avatar string) {
	t := &twin{
		secWebSocketKey: secWebSocketKey,
		gameRoomUuid:    gameRoomUuid,
		controllerId:    controllerId,
		hostExtId:       hostExtId,
		memberId:        memberId,
		memberName:      memberName,
		hostId:          hostId,
		billCurrency:    billCurrency,
		guestEnable:     guestEnable,
		avatar:          avatar,
		accountingSn:    0,
		isActive:        false,
		in:              make(chan *flux.Action, 1024),
		rwMutex:         &sync.RWMutex{},
	}
	go t.run()
}

func (t *twin) handleAction(action *flux.Action) {
	defer func() {
		if err := recover(); err != nil {
			logger.Service.Zap.Fatalw("999",
				"err", err,
				"stacktrace", string(debug.Stack()),
			)
		}
	}()

	if action.Key().To() != t.secWebSocketKey {
		return
	}

	logger.Service.Zap.Infow(action.Key().Name(),
		"GameUser", t.secWebSocketKey,
		"GameRoomUuid", t.gameRoomUuid,
		"Seat", t.seat,
		"MemberId", t.memberId,
		"HostId", t.hostId,
	)

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

	case lottery.EMSGID_eLotteryResult:
		if t.isActive && t.accountingSn != 0 {
			playerResult := action.Payload()[1].(map[string]uint64)
			vip.Service.CheckVip(
				true,
				t.secWebSocketKey,
				t.hostExtId,
				t.hostId,
				t.memberId,
				gamesettingFS.Service.GameId(t.secWebSocketKey),
				t.billCurrency,
				playerResult["total_Bet"],
				playerResult["total_Win"],
				t.accountingSn,
			)
		} else {
			logger.Service.Zap.Warnw("Twin Update VIP Failed",
				"GameUser", t.secWebSocketKey,
			)
		}

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

			if len(data2[t.secWebSocketKey]) > 0 {
				data3 := action.Payload()[2].([3]int32) //dice
				memberName := wallet.Service.MemberName(t.secWebSocketKey)
				balance, _ := wallet.Service.BalanceCache(t.secWebSocketKey)
				flux.Send(accounting.ActionAccountingEnd, t.secWebSocketKey, accounting.Service.HashId(t.secWebSocketKey, t.accountingSn), data1, data2, data3, memberName, balance, t.gameRoomUuid)
			} else {
				logger.Service.Zap.Warnw("EMSGID_eBroadcastLotteryResult BetCall nil",
					"GameUser", t.secWebSocketKey,
				)
			}

			wallet.Service.Close(t.secWebSocketKey)
			flux.Send(playerstate.ActionClearBetState, t.secWebSocketKey, playerstate.Service.Id,
				t.secWebSocketKey,
				t.hostId)

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
	time.Sleep(1 * time.Second)
	logger.Service.Zap.Infow("Unregister Twin GameUser",
		"GameUser", t.secWebSocketKey,
		"GameRoomUuid", t.gameRoomUuid,
		"Seat", t.seat,
		"MemberId", t.memberId,
		"AccountingSn", t.accountingSn,
		"HostId", t.hostId,
	)
	gamesetting.Service.Delete(t.secWebSocketKey)
	flux.UnRegister(t.secWebSocketKey, t.in)

	//有下注, 先不清除錢包
	if !t.isActive {
		wallet.Service.Close(t.secWebSocketKey)
		flux.Send(playerstate.ActionClearBetState, t.secWebSocketKey, playerstate.Service.Id,
			t.secWebSocketKey,
			t.hostId)
	}
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
