package twin

import (
	"strconv"
	"sync"
	"time"
	"u-game-server/application/accountingU"
	"u-game-server/application/atm"
	"u-game-server/application/banker"
	banker_proto "u-game-server/application/banker/proto"
	"u-game-server/application/friendroom"
	friend_room_proto "u-game-server/application/friendroom/proto"
	"u-game-server/application/gamesettingU"
	"u-game-server/application/playerinfo"
	"u-game-server/domain/draw"
	"u-game-server/domain/gamerecoveryU"
	game_recoveryU_proto "u-game-server/domain/gamerecoveryU/proto"
	"u-game-server/domain/playcards"
	"u-game-server/domain/probability"
	"u-game-server/domain/round"
	"u-game-server/domain/walletU"

	"gitlab.iplaystar.net/game-server/blacklist"

	probability_proto "u-game-server/domain/probability/proto"

	"gitlab.iplaystar.net/game-server/avatar"

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
	ActionTwinResume       = "ActionTwinResume"
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
	avatar          string
	subGameId       int32
	seat            int
	guestEnable     int
	accountingSn    uint64
	isActive        bool
	isDestroy       bool
	blacklistValue  uint32
	in              chan *flux.Action
	rwMutex         *sync.RWMutex
}

func New(secWebSocketKey, bankerUuid, memberId, hostId, hostExtId, gameRoomUuid, controllerId, avatar string, subGameId int32, seat, guestEnable int, accountingSn uint64) {
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
		avatar:          avatar,
		subGameId:       subGameId,
		seat:            seat,
		guestEnable:     guestEnable,
		accountingSn:    accountingSn,
		isActive:        false,
		isDestroy:       false,
		blacklistValue:  0,
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
	logger.Service.Zap.Infow(action.Key().Name(),
		"GameUser", t.secWebSocketKey,
		"GameRoomUuid", t.gameRoomUuid,
		"GameRoomType", t.gameRoomType,
		"Seat", t.seat,
		"GuestEnable", t.guestEnable,
	)
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
		blacklistValue := action.Payload()[2].(uint32)

		t.accountingSn = accountingSn
		t.blacklistValue = blacklistValue

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
			cent, _ := wallet.Service.Cent(t.secWebSocketKey)
			if wallet.Service.WalletCategory(t.secWebSocketKey) == wallet.CategoryHost && t.accountingSn != 0 && cent > 0 {
				wallet.Service.Refund(t.secWebSocketKey, t.accountingSn, true)
				flux.Send(accounting.ActionAccountingDelete, t.secWebSocketKey, accounting.Service.HashId(t.secWebSocketKey, t.accountingSn))
			} else if wallet.Service.WalletCategory(t.secWebSocketKey) != wallet.CategoryHost && t.guestEnable == auth.GuestOff {
				flux.Send(atm.ActionAtmAutoWithdraw, t.secWebSocketKey, atm.Service.Id, uint8(100), t.hostExtId, t.memberId, t.accountingSn)
			}

			t.destroy()
		}

	case ActionTwinResume:
		t.secWebSocketKey = action.Key().From()
		t.bankerUuid = action.Payload()[0].(string)
		t.memberId = action.Payload()[1].(string)
		t.hostId = action.Payload()[2].(string)
		t.hostExtId = action.Payload()[3].(string)
		t.gameRoomUuid = action.Payload()[4].(string)
		t.gameRoomType = action.Payload()[5].(string)
		t.controllerId = action.Payload()[6].(string)
		t.avatar = action.Payload()[7].(string)
		t.subGameId = action.Payload()[8].(int32)
		t.seat = action.Payload()[9].(int)
		t.guestEnable = action.Payload()[10].(int)
		t.accountingSn = action.Payload()[11].(uint64)
		t.blacklistValue = action.Payload()[12].(uint32)

	case friendroom.EMSGID_eFriendRoomLeaveRecall:
		gamerecoveryU.Service.Update(
			t.secWebSocketKey,
			t.gameRoomUuid,
			t.gameRoomType,
			t.bankerUuid,
			t.subGameId,
			int32(t.seat),
			gamerecoveryU.IDLE,
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
		t.subGameId = gamesettingU.Service.SubGameId(t.secWebSocketKey)

		if !t.isActive {
			return
		}

		gamerecoveryU.Service.Update(
			t.secWebSocketKey,
			t.gameRoomUuid,
			t.gameRoomType,
			t.bankerUuid,
			t.subGameId,
			int32(t.seat),
			gamerecoveryU.IDLE,
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

		gamerecoveryU.Service.Update(
			t.secWebSocketKey,
			t.gameRoomUuid,
			t.gameRoomType,
			t.bankerUuid,
			t.subGameId,
			int32(t.seat),
			gamerecoveryU.GAMING,
		)

	case banker.EMSGID_eRoundStart:
		t.rwMutex.Lock()
		defer t.rwMutex.Unlock()

		dataByte := action.Payload()[0].([]byte)
		gameRoomUuid := string(action.Payload()[1].([]byte))

		data := &banker_proto.RoundStart{}

		if err := proto.Unmarshal(dataByte, data); err != nil {
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
		}
		if !t.isActive {
			return
		}
		gamerecoveryU.Service.Update(
			t.secWebSocketKey,
			t.gameRoomUuid,
			t.gameRoomType,
			t.bankerUuid,
			t.subGameId,
			int32(t.seat),
			gamerecoveryU.GAMING,
		)

		if t.accountingSn == 0 && wallet.Service.WalletCategory(t.secWebSocketKey) != wallet.CategoryHost {
			cent, err := wallet.Service.Cent(t.secWebSocketKey)

			if err != nil {
				panic("BUG ERROR WALLET CENT : " + t.secWebSocketKey)
			}

			if a := accounting.Builder().
				SetSecWebSocketKey(t.secWebSocketKey).
				SetHostExtId(t.hostExtId).
				SetGuestEnable(t.guestEnable == auth.GuestOn).
				SetHostId(t.hostId).
				SetGameId(gamesettingU.Service.GameId(t.secWebSocketKey)).
				SetSubgameId(uint32(gamesettingU.Service.SubGameId(t.secWebSocketKey))).
				SetMemberId(t.memberId).
				SetInitCent(cent).
				SetDB(t.hostExtId).
				SetKind(accounting.PLAYER).
				SetHandler(&accountingU.AccountingU{}).
				Build(); a != nil {

				t.accountingSn = a.Start.Sn
			}
		}

		switch t.gameRoomType {
		case banker.FRIEND_ROOM:
			flux.Send(banker.ActionBankerAccountingSn, t.secWebSocketKey, t.gameRoomUuid, t.accountingSn, t.seat)

		case banker.GAME_ROOM:
			flux.Send(banker.ActionBankerAccountingSn, t.secWebSocketKey, t.bankerUuid, t.accountingSn, t.seat)

		default:
			panic("ERROR GAME ROOM TYPE")
		}

		if t.guestEnable == auth.GuestOn {
			switch t.gameRoomType {
			case banker.FRIEND_ROOM:
				flux.Send(banker.ActionBankerAccountingSn, t.secWebSocketKey, t.gameRoomUuid, t.accountingSn, t.seat)

			case banker.GAME_ROOM:
				flux.Send(banker.ActionBankerAccountingSn, t.secWebSocketKey, t.bankerUuid, uint64(0), t.seat)

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

		/*if t.accountingSn == 0 && t.guestEnable == auth.GuestOff {
			panic("BUG TWIN SN ROUND START : " + t.secWebSocketKey)
		}*/

		flux.Send(banker.ActionBankerDeal, t.secWebSocketKey, t.bankerUuid, t.seat, t.avatar, t.blacklistValue)

		d := draw.Builder().
			SetBankerUuid(t.bankerUuid).
			SetSecWebSocketKey(t.secWebSocketKey).
			SetGameRoomUuid(t.gameRoomUuid).
			SetGameRoomType(t.gameRoomType).
			SetSeat(int32(t.seat)).
			SetKind(draw.PLAYER).
			Build()

		flux.Send(draw.ActionDrawCreate, t.secWebSocketKey, draw.Service.Id, d)

		p := playcards.Builder().
			SetBankerUuid(t.bankerUuid).
			SetSecWebSocketKey(t.secWebSocketKey).
			SetGameRoomUuid(t.gameRoomUuid).
			SetGameRoomType(t.gameRoomType).
			SetSeat(int32(t.seat)).
			SetKind(playcards.PLAYER).
			Build()

		flux.Send(playcards.ActionPlayCardsCreate, t.secWebSocketKey, playcards.Service.Id, p)

		r := round.Builder().
			SetBankerUuid(t.bankerUuid).
			SetSecWebSocketKey(t.secWebSocketKey).
			SetGameRoomUuid(t.gameRoomUuid).
			SetGameRoomType(t.gameRoomType).
			SetSeat(int32(t.seat)).
			SetWaitingTime(gamesettingU.Service.PlayerRoundWaitingTime(t.secWebSocketKey)).
			SetKind(round.PLAYER).
			Build()

		flux.Send(round.ActionRoundCreate, t.secWebSocketKey, round.Service.Id, r)

	case banker.EMSGID_eRoundEnd:
		if !t.isActive {
			return
		}

		defer t.destroy()

	case banker.EMSGID_ePlayerRoundStart:
		flux.Send(draw.ActionDrawReset, t.secWebSocketKey, draw.Service.Id)
		flux.Send(playcards.ActionPlayCardsReset, t.secWebSocketKey, playcards.Service.Id)
		flux.Send(round.ActionRoundStateChange, t.secWebSocketKey, round.Service.Id, t.secWebSocketKey, round.STATE_START)

	case draw.EMSGID_eDrawTimeout:

		canPlay := action.Payload()[1].(bool)

		if canPlay {
			flux.Send(round.ActionRoundStateChange, t.secWebSocketKey, round.Service.Id, t.secWebSocketKey, round.STATE_DRAW)

			time.Sleep(banker.NORMAL_DELAY * time.Second)

			flux.Send(playcards.EMSGID_ePlayCardsTimeout, t.secWebSocketKey, playcards.Service.Id, t.secWebSocketKey)
		} else {
			flux.Send(round.ActionRoundStateChange, t.secWebSocketKey, round.Service.Id, t.secWebSocketKey, round.STATE_END)

			flux.Send(banker.ActionPlayerRoundStart, t.secWebSocketKey, t.bankerUuid)
		}

	case draw.EMSGID_eDrawRecall:

		canPlay := action.Payload()[1].(bool)

		if !canPlay {
			flux.Send(round.ActionRoundStateChange, t.secWebSocketKey, round.Service.Id, t.secWebSocketKey, round.STATE_END)

			flux.Send(banker.ActionPlayerRoundStart, t.secWebSocketKey, t.bankerUuid)
		}

	case playcards.EMSGID_ePlayCardsTimeout:
		fallthrough
	case playcards.EMSGID_ePlayCardsRecall:

		flux.Send(round.ActionRoundStateChange, t.secWebSocketKey, round.Service.Id, t.secWebSocketKey, round.STATE_END)

		flux.Send(banker.ActionPlayerRoundStart, t.secWebSocketKey, t.bankerUuid)

	case banker.EMSGID_eKeepTimeout:
		fallthrough
	case banker.EMSGID_eKeepRecall:

		flux.Send(round.ActionRoundStateChange, t.secWebSocketKey, round.Service.Id, t.secWebSocketKey, round.STATE_END)

		flux.Send(banker.ActionPlayerRoundStart, t.secWebSocketKey, t.bankerUuid)

	case probability.EMSGID_eBroadcastResult:
		if BlacklistCondition := gamesettingU.Service.BlacklistCondition(t.secWebSocketKey); BlacklistCondition > 0 {
			databyte := action.Payload()[0].([]byte)
			data := &probability_proto.BroadcastResult{}
			proto.Unmarshal(databyte, data)
			for _, playerdata := range data.Result.PlayerData {
				if t.seat == int(playerdata.Seat) {
					if playerdata.AllWin == 1 && playerdata.AllScore/int64(gamesettingU.Service.Bet(t.secWebSocketKey)) >= int64(BlacklistCondition) {
						value := gamesettingU.Service.AutoBlacklistValue(t.secWebSocketKey)
						blacklist.Service.UpdateMemberBlacklist(t.hostExtId, t.hostId, t.memberId, gamesettingU.Service.GameId(t.secWebSocketKey), value, t.accountingSn)
					}
					break
				}
			}
		}

		t.rwMutex.Lock()
		t.bankerUuid = ""
		t.accountingSn = 0
		t.rwMutex.Unlock()

		gamerecoveryU.Service.Update(
			t.secWebSocketKey,
			t.gameRoomUuid,
			t.gameRoomType,
			t.bankerUuid,
			t.subGameId,
			int32(t.seat),
			gamerecoveryU.IDLE,
		)

		if !t.isActive {
			return
		}
		cent, _ := wallet.Service.Cent(t.secWebSocketKey)
		if cent > 0 {
			if wallet.Service.WalletCategory(t.secWebSocketKey) != wallet.CategoryHost {
				wallet.Service.Withdraw(t.secWebSocketKey, t.accountingSn, cent, 0, 0)
			} else if t.accountingSn != 0 {
				wallet.Service.Refund(t.secWebSocketKey, t.accountingSn, true)
				flux.Send(accounting.ActionAccountingDelete, t.secWebSocketKey, accounting.Service.HashId(t.secWebSocketKey, t.accountingSn))
			}
		}
		flux.Send(draw.ActionDrawDelete, t.secWebSocketKey, draw.Service.Id)
		flux.Send(playcards.ActionPlayCardsDelete, t.secWebSocketKey, playcards.Service.Id)
		flux.Send(round.ActionRoundDelete, t.secWebSocketKey, round.Service.Id)

		data := &game_recoveryU_proto.GameRecovery{
			Msgid: common_proto.EMSGID_eGameRecovery,
			Snapshot: &game_recoveryU_proto.Snapshot{
				ServerId:  "",
				RoomUuid:  "",
				Seat:      -1,
				SubgameId: -1,
				Rate:      0,
				BetIdx:    0,
				Status:    gamerecoveryU.IDLE,
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
	case avatar.EMSGID_eAvatarRecall:
		avatar := action.Payload()[1].(int32)
		t.avatar = strconv.Itoa(int(avatar))
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

	time.Sleep(2 * time.Second)

	flux.Send(atm.ActionAtmDelete, t.secWebSocketKey, atm.Service.Id, t.memberId, t.hostExtId)

	gamerecoveryU.Service.Delete(t.secWebSocketKey)
	gamerecovery.Service.Close(t.secWebSocketKey)
	gamesetting.Service.Delete(t.secWebSocketKey)
	friendroom.Service.Delete(t.secWebSocketKey)
	wallet.Service.Close(t.secWebSocketKey)
	playerinfo.Service.Delete(t.hostId, t.memberId)

	fluxData := &flux_proto.FluxAction{
		Name: walletU.ActionWalletClosed,
		From: walletU.Service.Id,
		To:   postman.SERVER_TRIGGER,
	}

	fluxData.Payload = append(fluxData.Payload, []byte(t.secWebSocketKey))
	fluxDataByte, _ := proto.Marshal(fluxData)

	postman.Service.Pub(fluxDataByte)
}
