package twin

import (
	"89-game-server/application/accounting89"
	"89-game-server/application/atm"
	"89-game-server/application/banker"
	banker_proto "89-game-server/application/banker/proto"
	"89-game-server/application/friendroom"
	friend_room_proto "89-game-server/application/friendroom/proto"
	"89-game-server/application/gamesetting89"
	"89-game-server/application/lobbysetting89"
	"89-game-server/domain/bet"
	"89-game-server/domain/draw"
	"89-game-server/domain/gamerecovery89"
	game_recovery89_proto "89-game-server/domain/gamerecovery89/proto"
	"89-game-server/domain/wallet89"
	"strconv"
	"sync"
	"time"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/accounting"
	"gitlab.iplaystar.net/game-server/auth"
	auth_proto "gitlab.iplaystar.net/game-server/auth/proto"
	common_proto "gitlab.iplaystar.net/game-server/common/proto"
	"gitlab.iplaystar.net/game-server/flux"
	flux_proto "gitlab.iplaystar.net/game-server/flux/proto"
	gamerecovery "gitlab.iplaystar.net/game-server/game-recovery-v2"
	gamesetting "gitlab.iplaystar.net/game-server/game-setting"
	gameuser "gitlab.iplaystar.net/game-server/game-user"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/postman"
	"gitlab.iplaystar.net/game-server/wallet"
)

const (
	ActionTwinAccountingSn = "ActionTwinAccountingSn"
	ActionTwinActive       = "ActionTwinActive"
	ActionTwinDestroy      = "ActionTwinDestroy"
	ActionTwinCheck        = "ActionTwinCheck"
)

type twin struct {
	secWebSocketKey string
	bankerUuid      string
	memberId        string
	hostId          string
	hostExtId       string
	gameRoomUuid    string
	gameRoomType    string
	controllerId    string
	seat            int
	guestEnable     int
	accountingSn    uint64
	isActive        bool
	isDestroy       bool
	in              chan *flux.Action
	rwMutex         *sync.RWMutex
}

func New(secWebSocketKey, bankerUuid, memberId, hostId, hostExtId, gameRoomUuid, controllerId string, seat, guestEnable int, accountingSn uint64) {
	logger.Service.Zap.Infow("Twin GameUser Create",
		"GameUser", secWebSocketKey,
		"GameRoomUuid", gameRoomUuid,
		"Seat", seat,
		"GuestEnable", guestEnable,
		"MemberId", memberId,
		"BankerUuid", bankerUuid,
		"AccountingSn", accountingSn,
		"HostId", hostId,
		"HostExtId", hostExtId,
	)

	t := &twin{
		secWebSocketKey: secWebSocketKey,
		bankerUuid:      bankerUuid,
		memberId:        memberId,
		hostId:          hostId,
		hostExtId:       hostExtId,
		gameRoomUuid:    gameRoomUuid,
		controllerId:    controllerId,
		seat:            seat,
		guestEnable:     guestEnable,
		accountingSn:    accountingSn,
		isActive:        false,
		isDestroy:       false,
		in:              make(chan *flux.Action, 1024),
		rwMutex:         &sync.RWMutex{},
	}

	go t.run()
}

func (t *twin) run() {
	flux.Register(t.secWebSocketKey, t.in)

	for action := range t.in {
		t.handleAction(action)
	}
}

func (t *twin) handleAction(action *flux.Action) {

	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:
		logger.Service.Zap.Infow("Twin GameUser Started",
			"GameUser", t.secWebSocketKey,
			"GameRoomUuid", t.gameRoomUuid,
			"GameRoomType", t.gameRoomType,
			"Seat", t.seat,
			"GuestEnable", t.guestEnable,
			"MemberId", t.memberId,
			"BankerUuid", t.bankerUuid,
			"AccountingSn", t.accountingSn,
			"HostId", t.hostId,
			"HostExtId", t.hostExtId,
		)

	case friendroom.EMSGID_eFriendRoomJoinRecall:
		dataByte := action.Payload()[0].([]byte)

		data := &friend_room_proto.FriendRoomJoinRecall{}

		proto.Unmarshal(dataByte, data)

		if data.StatusCode == common_proto.Status_kSuccess {
			t.gameRoomUuid = action.Key().From()
			t.gameRoomType = banker.FRIEND_ROOM
		}

	case ActionTwinActive:
		t.rwMutex.Lock()
		defer t.rwMutex.Unlock()

		//isDisconnect := action.Payload()[0].(bool)
		logger.Service.Zap.Infow("Twin GameUser Take Over",
			"GameUser", t.secWebSocketKey,
			"GameRoomUuid", t.gameRoomUuid,
			"GameRoomType", t.gameRoomType,
			"Seat", t.seat,
			"GuestEnable", t.guestEnable,
			"MemberId", t.memberId,
			"BankerUuid", t.bankerUuid,
			"HostExtId", t.hostExtId,
		)

		t.isActive = true

	case ActionTwinAccountingSn:
		t.rwMutex.Lock()
		defer t.rwMutex.Unlock()

		accountingSn := action.Payload()[0].(uint64)
		isDone := action.Payload()[1].(chan bool)

		t.accountingSn = accountingSn

		if !t.isActive {
			isDone <- true
			close(isDone)
			return
		}

		switch t.gameRoomType {
		case banker.FRIEND_ROOM:
			flux.Send(banker.ActionBankerAccountingSn, t.secWebSocketKey, t.gameRoomUuid, t.accountingSn)

		case banker.GAME_ROOM:
			flux.Send(banker.ActionBankerAccountingSn, t.secWebSocketKey, t.bankerUuid, t.accountingSn)

		default:
			panic("ERROR GAME ROOM TYPE")
		}

		isDone <- true
		close(isDone)

	case ActionTwinDestroy:

		t.isActive = false
		if t.gameRoomUuid == "" {
			t.gameRoomUuid = action.Payload()[0].(string)
			t.gameRoomType = action.Payload()[1].(string)
		}
		//go t.leaveRoom()
		if t.bankerUuid == "" {
			if lobbysetting89.Service.AutoATM(t.secWebSocketKey) && t.guestEnable == auth.GuestOff {
				// TODO JOHNNY 以後可能會有要自動儲值幾%的...
				flux.Send(atm.ActionAtmAutoWithdraw, t.secWebSocketKey, atm.Service.Id, uint8(100), t.hostExtId, t.memberId)

			}

			t.destroy()
		}

	case friendroom.EMSGID_eFriendRoomLeaveRecall:
		gamerecovery89.Service.Update(
			t.secWebSocketKey,
			t.gameRoomUuid,
			int32(t.seat),
			gamesetting89.Service.Rate(t.secWebSocketKey),
			gamerecovery89.IDLE,
		)

		t.seat = -1
		t.gameRoomUuid = ""
		t.gameRoomType = ""

	case gameuser.ActionJoinLobbyRoomRecall:
		fallthrough
	case gameuser.ActionLeaveGameRoomRecall:
		t.rwMutex.Lock()
		defer t.rwMutex.Unlock()

		t.seat = -1
		t.gameRoomUuid = ""
		t.gameRoomType = ""

	case gameuser.ActionJoinGameRoomRecall:
		t.rwMutex.Lock()
		defer t.rwMutex.Unlock()

		t.gameRoomUuid = action.Payload()[0].(string)
		t.seat = action.Payload()[1].(int)
		t.gameRoomType = action.Payload()[2].(string)

		if !t.isActive {
			return
		}

		gamerecovery89.Service.Update(
			t.secWebSocketKey,
			t.gameRoomUuid,
			int32(t.seat),
			gamesetting89.Service.Rate(t.secWebSocketKey),
			gamerecovery89.IDLE,
		)

		flux.Send(auth.EMSGID_eBroadcastPlayerIn, t.secWebSocketKey, t.gameRoomUuid, auth_proto.PLAYER_TYPE_GAME)

	case banker.ActionBankerStart:
		t.rwMutex.Lock()
		defer t.rwMutex.Unlock()

		switch action.Payload()[0].(type) {
		case string:
			t.bankerUuid = action.Payload()[0].(string)

		case []byte:
			t.bankerUuid = string(action.Payload()[0].([]byte))
			flux.Send(banker.ActionBankerStart, t.secWebSocketKey, t.gameRoomUuid, t.bankerUuid)
		}

		logger.Service.Zap.Infow("Twin GameUser Banker Start",
			"GameUser", t.secWebSocketKey,
			"GameRoomUuid", t.gameRoomUuid,
			"GameRoomType", t.gameRoomType,
			"Seat", t.seat,
			"GuestEnable", t.guestEnable,
			"MemberId", t.memberId,
			"BankerUuid", t.bankerUuid,
			"AccountingSn", t.accountingSn,
			"HostId", t.hostId,
			"HostExtId", t.hostExtId,
		)

		if !t.isActive {
			return
		}

		gamerecovery89.Service.Update(
			t.secWebSocketKey,
			t.gameRoomUuid,
			int32(t.seat),
			gamesetting89.Service.Rate(t.secWebSocketKey),
			gamerecovery89.GAMING,
		)

	case banker.EMSGID_eRoundStart:
		t.rwMutex.Lock()
		defer t.rwMutex.Unlock()

		dataByte := action.Payload()[0].([]byte)
		gameRoomUuid := string(action.Payload()[1].([]byte))

		data := &banker_proto.RoundStart{}

		if err := proto.Unmarshal(dataByte, data); err != nil {
			// TODO JOHNNY error code

			return
		}

		for _, v := range data.PlayerInfos {
			if v.Id == t.secWebSocketKey {
				t.seat = int(v.Seat)
				t.gameRoomUuid = gameRoomUuid
			}
		}

		if t.seat < 0 || t.gameRoomUuid == "" || t.bankerUuid == "" {
			logger.Service.Zap.Errorw("ERROR SEAT",
				"GameUser", t.secWebSocketKey,
				"GameRoomUuid", gameRoomUuid,
				"Seat", t.seat,
				"BankerUuid", t.bankerUuid,
			)

			panic("ERROR SEAT : " + t.secWebSocketKey)
			return
		}
		if !t.isActive {
			return
		}
		gamerecovery89.Service.Update(
			t.secWebSocketKey,
			t.gameRoomUuid,
			int32(t.seat),
			gamesetting89.Service.Rate(t.secWebSocketKey),
			gamerecovery89.GAMING,
		)

		if t.accountingSn == 0 {
			cent, err := wallet.Service.Cent(t.secWebSocketKey)

			if err != nil {
				panic("BUG ERROR WALLET CENT : " + t.secWebSocketKey)
			}

			if a := accounting.Builder().
				SetSecWebSocketKey(t.secWebSocketKey).
				SetHostExtId(t.hostExtId).
				SetGuestEnable(t.guestEnable == auth.GuestOn).
				SetHostId(t.hostId).
				SetGameId(gamesetting89.Service.GameId(t.secWebSocketKey)).
				SetSubgameId(gamesetting89.Service.RateIndex(t.secWebSocketKey)).
				SetMemberId(t.memberId).
				SetInitCent(cent).
				SetDenom(uint64(gamesetting89.Service.Rate(t.secWebSocketKey))).
				SetGameModule(gamesetting89.Service.MathModuleId(t.secWebSocketKey)).
				SetDB(t.hostExtId).
				SetKind(accounting.PLAYER).
				SetHandler(&accounting89.Accounting89{}).
				Build(); a != nil {

				t.accountingSn = a.Start.Sn

				switch t.gameRoomType {
				case banker.FRIEND_ROOM:
					flux.Send(banker.ActionBankerAccountingSn, t.secWebSocketKey, t.gameRoomUuid, t.accountingSn)

				case banker.GAME_ROOM:
					flux.Send(banker.ActionBankerAccountingSn, t.secWebSocketKey, t.bankerUuid, t.accountingSn)

				default:
					panic("ERROR GAME ROOM TYPE")

				}
			}
		}

		if t.guestEnable == auth.GuestOn {
			switch t.gameRoomType {
			case banker.FRIEND_ROOM:
				flux.Send(banker.ActionBankerAccountingSn, t.secWebSocketKey, t.gameRoomUuid, t.accountingSn)

			case banker.GAME_ROOM:
				flux.Send(banker.ActionBankerAccountingSn, t.secWebSocketKey, t.bankerUuid, uint64(0))

			default:
				panic("ERROR TYPE GAME ROOM")
			}
		}

		logger.Service.Zap.Infow("Twin GameUser Round Start",
			"GameUser", t.secWebSocketKey,
			"GameRoomUuid", t.gameRoomUuid,
			"Seat", t.seat,
			"GuestEnable", t.guestEnable,
			"MemberId", t.memberId,
			"BankerUuid", t.bankerUuid,
			"AccountingSn", t.accountingSn,
			"HostId", t.hostId,
			"HostExtId", t.hostExtId,
		)

		if t.accountingSn == 0 && t.guestEnable == auth.GuestOff {
			panic("BUG TWIN SN ROUND START : " + t.secWebSocketKey)
		}

		if t.seat != banker.BANKER_SEAT {
			cent, err := wallet.Service.CentCache(t.secWebSocketKey)

			if err != nil {
				panic("BOT CENT ERROR" + t.secWebSocketKey)
			}

			flux.Send(bet.ActionBetStart, t.secWebSocketKey, bet.Service.Id,
				bet.Builder().
					SetBankerUuid(t.bankerUuid).
					SetSecWebSocketKey(t.secWebSocketKey).
					SetGameRoomUuid(t.gameRoomUuid).
					SetGameRoomType(t.gameRoomType).
					SetSeat(int32(t.seat)).
					SetWaitingTime(gamesetting89.Service.BetWaitingTime(t.secWebSocketKey)).
					SetKind(bet.PLAYER).
					SetRate(gamesetting89.Service.Rate(t.secWebSocketKey)).
					SetBetList(gamesetting89.Service.BetList(t.secWebSocketKey)).
					SetCent(cent).
					Build(),
			)
		}
	case bet.EMSGID_eBetRecall:
		if !t.isActive {
			return
		}
		betcent := action.Payload()[1].(uint64)
		flux.Send(atm.ActionAtmAutoWithdrawBlance, t.secWebSocketKey, atm.Service.Id, betcent, t.hostExtId, t.memberId)

	case bet.EMSGID_eBetTimeout:
		if !t.isActive {
			return
		}
		betcent := action.Payload()[1].(uint64)
		flux.Send(atm.ActionAtmAutoWithdrawBlance, t.secWebSocketKey, atm.Service.Id, betcent, t.hostExtId, t.memberId)

	case banker.ActionBankerDeal:
		t.rwMutex.RLock()
		defer t.rwMutex.RUnlock()

		if !t.isActive {
			return
		}

		dataByte := action.Payload()[0].([]byte)
		isEnd, _ := strconv.ParseBool(string(action.Payload()[1].([]byte)))
		isDrawDelay, _ := strconv.ParseBool(string(action.Payload()[2].([]byte)))

		data := &banker_proto.Deal{}

		// TODO JOHNNY error code
		proto.Unmarshal(dataByte, data)

		if !isEnd {
			sleepTime := 0

			if isDrawDelay && t.seat == 0 {
				sleepTime = 2
			}

			if t.seat == 0 {
				sleepTime = 5
			}

			d := draw.Builder().
				SetBankerUuid(t.bankerUuid).
				SetSecWebSocketKey(t.secWebSocketKey).
				SetGameRoomUuid(t.gameRoomUuid).
				SetGameRoomType(t.gameRoomType).
				SetSeat(int32(t.seat)).
				SetSumPoint(data.Cards[t.seat].SumPoint).
				SetWaitingTime(gamesetting89.Service.DrawWaitingTime(t.secWebSocketKey)).
				SetKind(draw.PLAYER).
				SetSleepTime(uint32(sleepTime)).
				Build()

			flux.Send(draw.ActionDrawStart, t.secWebSocketKey, draw.Service.Id, d)
		}

	case banker.EMSGID_eRoundEnd:
		t.rwMutex.Lock()
		t.bankerUuid = ""
		t.accountingSn = 0
		t.rwMutex.Unlock()

		if !t.isActive {
			return
		}
		if lobbysetting89.Service.AutoATM(t.secWebSocketKey) {
			flux.Send(atm.ActionAtmAutoWithdraw, t.secWebSocketKey, atm.Service.Id, uint8(100), t.hostExtId, t.memberId)
		}
		gamerecovery89.Service.Update(
			t.secWebSocketKey,
			t.gameRoomUuid,
			int32(t.seat),
			gamesetting89.Service.Rate(t.secWebSocketKey),
			gamerecovery89.IDLE,
		)
		data := &game_recovery89_proto.GameRecovery{
			Msgid: common_proto.EMSGID_eGameRecovery,
			Snapshot: &game_recovery89_proto.Snapshot{
				ServerId:  "",
				RoomUuid:  "",
				Seat:      -1,
				SubgameId: -1,
				Rate:      0,
				BetIdx:    0,
				Status:    gamerecovery89.IDLE,
			},
		}

		dataByte, _ := proto.Marshal(data)

		switch t.gameRoomType {
		case banker.FRIEND_ROOM:
			flux.Send(auth.ActionAuthNotify, t.secWebSocketKey, t.gameRoomUuid,
				t.memberId,
				t.hostId,
				dataByte,
			)

		case banker.GAME_ROOM:
			flux.Send(auth.ActionAuthNotify, t.secWebSocketKey, auth.Service.Id,
				t.memberId,
				t.hostId,
				dataByte,
			)

		default:
			panic("ERROR GAME ROOM TYPE " + t.secWebSocketKey)
		}

		//go t.leaveRoom()

		defer t.destroy()

	case draw.ActionDrawNext:
		if !t.isActive {
			return
		}

		gameRoomUuid := string(action.Payload()[0].([]byte))

		seat, _ := strconv.Atoi(string(action.Payload()[1].([]byte)))

		if seat < t.seat {
			logger.Service.Zap.Infow("Twin GameUser Draw Next",
				"GameUser", t.secWebSocketKey,
				"GameRoomUuid", t.gameRoomUuid,
				"Seat", seat,
				"GuestEnable", t.guestEnable,
				"MemberId", t.memberId,
				"BankerUuid", t.bankerUuid,
				"AccountingSn", t.accountingSn,
				"HostId", t.hostId,
				"HostExtId", t.hostExtId,
			)

			flux.Send(draw.ActionDrawNext, t.secWebSocketKey, draw.Service.Id, gameRoomUuid, int32(seat))
		}
	case auth.ActionAuthNotify:
		if !t.isActive || t.secWebSocketKey == action.Key().From() {
			return
		}

		if lobbysetting89.Service.AutoATM(t.secWebSocketKey) {
			// TODO JOHNNY 以後可能會有要自動儲值幾%的...
			flux.Send(atm.ActionAtmAutoWithdraw, t.secWebSocketKey, atm.Service.Id, uint8(100), t.hostExtId, t.memberId)
		}
		defer t.destroy()
	}
}
func (t *twin) leaveRoom() {
	if t.gameRoomUuid != "" {

		switch t.gameRoomType {
		case banker.FRIEND_ROOM:
			flux.Send(gameuser.ActionLeaveGameRoomCall, t.secWebSocketKey, t.gameRoomUuid, t.secWebSocketKey)

		case banker.GAME_ROOM:
			flux.Send(gameuser.ActionLeaveGameRoomCall, t.secWebSocketKey, t.controllerId, t.gameRoomUuid)
		default:
			panic("TWIN ERROR GAME ROOM TYPE " + t.secWebSocketKey)
		}
		flux.Send(auth.EMSGID_eBroadcastPlayerOut, t.secWebSocketKey, t.gameRoomUuid, auth.Service.BroadcastPlayerOut(
			t.gameRoomUuid,
			t.secWebSocketKey,
			t.memberId,
			"0",
			uint32(t.seat),
			uint64(0),
		))
	}
}
func (t *twin) destroy() {
	t.rwMutex.Lock()
	defer t.rwMutex.Unlock()

	logger.Service.Zap.Infow("Unregister Twin GameUser",
		"GameUser", t.secWebSocketKey,
		"GameRoomUuid", t.gameRoomUuid,
		"Seat", t.seat,
		"GuestEnable", t.guestEnable,
		"MemberId", t.memberId,
		"AccountingSn", t.accountingSn,
		"HostId", t.hostId,
		"HostExtId", t.hostExtId,
		"IsDestroy", t.isDestroy,
	)

	if t.isDestroy {
		return
	}
	t.isActive = false
	t.isDestroy = true
	flux.UnRegister(t.secWebSocketKey, t.in)
	flux.Send(auth.ActionUserDisconnect, t.secWebSocketKey, auth.Service.Id, t.secWebSocketKey)
	t.leaveRoom()

	gamerecovery89.Service.Delete(t.secWebSocketKey)
	gamerecovery.Service.Close(t.secWebSocketKey)

	time.Sleep(2 * time.Second)

	flux.Send(atm.ActionAtmDelete, t.secWebSocketKey, atm.Service.Id, t.memberId, t.hostExtId)

	gamesetting.Service.Delete(t.secWebSocketKey)
	friendroom.Service.Delete(t.secWebSocketKey)
	wallet.Service.Close(t.secWebSocketKey)

	fluxData := &flux_proto.FluxAction{
		Name: wallet89.ActionWalletClosed,
		From: wallet89.Service.Id,
		To:   postman.SERVER_TRIGGER,
	}

	fluxData.Payload = append(fluxData.Payload, []byte(t.secWebSocketKey))
	fluxDataByte, _ := proto.Marshal(fluxData)

	postman.Service.Pub(fluxDataByte)
}
