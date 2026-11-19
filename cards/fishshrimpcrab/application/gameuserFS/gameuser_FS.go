package gameuserFS

import (
	"crypto/rand"
	"fish-shrimp-crab-game-server/application/accountingFS"
	"fish-shrimp-crab-game-server/application/filter"
	"fish-shrimp-crab-game-server/application/gameroom"
	gameroom_proto "fish-shrimp-crab-game-server/application/gameroom/proto"
	"fish-shrimp-crab-game-server/application/gamesettingFS"
	game_settingFS_proto "fish-shrimp-crab-game-server/application/gamesettingFS/proto"
	"fish-shrimp-crab-game-server/application/lobbysettingFS"
	lobby_settingFS_proto "fish-shrimp-crab-game-server/application/lobbysettingFS/proto"
	"fish-shrimp-crab-game-server/application/lottery"
	lottery_proto "fish-shrimp-crab-game-server/application/lottery/proto"
	"fish-shrimp-crab-game-server/application/playerdata"
	playdata_proto "fish-shrimp-crab-game-server/application/playerdata/proto"
	"fish-shrimp-crab-game-server/application/playerstate"
	"fish-shrimp-crab-game-server/application/twin"
	"fish-shrimp-crab-game-server/domain/avatar"
	avatar_proto "fish-shrimp-crab-game-server/domain/avatar/proto"
	"fish-shrimp-crab-game-server/domain/bet"
	bet_proto "fish-shrimp-crab-game-server/domain/bet/proto"
	"fish-shrimp-crab-game-server/domain/probability"
	"fish-shrimp-crab-game-server/domain/vip"
	"fish-shrimp-crab-game-server/domain/walletFS"
	walletFS_proto "fish-shrimp-crab-game-server/domain/walletFS/proto"
	commonFS_proto "fish-shrimp-crab-game-server/models/proto"
	"math/big"
	"strconv"
	"time"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/accounting"
	"gitlab.iplaystar.net/game-server/auth"
	auth_proto "gitlab.iplaystar.net/game-server/auth/proto"
	common_proto "gitlab.iplaystar.net/game-server/common/proto"
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	errorcode_proto "gitlab.iplaystar.net/game-server/error-code/proto"
	"gitlab.iplaystar.net/game-server/flux"
	flux_proto "gitlab.iplaystar.net/game-server/flux/proto"
	gamesetting "gitlab.iplaystar.net/game-server/game-setting"
	gameuser "gitlab.iplaystar.net/game-server/game-user"
	heartbeat "gitlab.iplaystar.net/game-server/heart-beat"
	"gitlab.iplaystar.net/game-server/idle"
	lobbysetting "gitlab.iplaystar.net/game-server/lobby-setting"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/maintain"
	"gitlab.iplaystar.net/game-server/postman"
	"gitlab.iplaystar.net/game-server/session"
	"gitlab.iplaystar.net/game-server/wallet"
)

const (
	CHANGE_ROOM_COUNTDOWN_TIME = 600 //換房倒數的時間(秒)
)

type GameUserFS struct {
	controllerId     string
	secWebSocketKey  string
	hostExtId        string
	gameRoomUuid     string
	lobbyRoomUuid    string
	gameRoomType     string
	ipAddress        string
	seat             int
	profile          *auth.MemberInfo
	gameConfigRecall *game_settingFS_proto.ConfigRecall
	isDestroy        bool
	accountingSn     uint64
	leavingRoom      string
	leavingSeat      int
	startBalance     uint64 //for accounting
	changeRoomTimer  *changeRoomTimer
	lastGameRoomUuid string
	histories        [10][3]int32
    isVipChangeRoom  bool
	roomKind         string
}

type changeRoomTimer struct {
	timer         *time.Timer
	stopTimerChan chan bool
}

func New(controllerId, secWebSocketKey, hostExtId, remoteAddr string) *GameUserFS {
	return &GameUserFS{
		controllerId:     controllerId,
		secWebSocketKey:  secWebSocketKey,
		hostExtId:        hostExtId,
		ipAddress:        remoteAddr,
		seat:             -1,
		profile:          nil,
		gameConfigRecall: nil,
		isDestroy:        false,
		accountingSn:     0,
		leavingRoom:      "",
		leavingSeat:      -1,
		startBalance:     0,
		changeRoomTimer:  nil,
		isVipChangeRoom:  false,
		roomKind:         "",
	}
}

func (gFS *GameUserFS) MsgHandler(g *gameuser.GameUser, msg []byte) {
	v, err := filter.FindActionName(msg)
	if err != nil {
		logger.Service.Zap.Errorw(gameuser.GameUser_MSGID_PROTO_INVALID,
			"GameUserFS", gFS.secWebSocketKey,
			"Error", err,
		)
		errorcode.Service.Fatal(gFS.secWebSocketKey, gameuser.GameUser_MSGID_PROTO_INVALID)
		return
	}
	logger.Service.Zap.Infow(v,
		"GameUserFS", gFS.secWebSocketKey,
		"HostExtId", gFS.hostExtId,
		"Seat", gFS.seat,
		"LobbyRoomUuid", gFS.lobbyRoomUuid,
		"GameRoomUuid", gFS.gameRoomUuid,
	)
	switch v {
	case auth.EMSGID_eLoginCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		flux.Send(auth.EMSGID_eLoginCall, gFS.secWebSocketKey, auth.Service.Id, msg)

	case lobbysetting.EMSGID_eLobbyConfigCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if gFS.profile != nil {
			flux.Send(lobbysetting.EMSGID_eLobbyConfigRecall, gFS.secWebSocketKey, gFS.secWebSocketKey,
				lobbysetting.Service.EMSGID_eLobbyConfigCall(
					gFS.secWebSocketKey,
					gFS.profile.MemberId,
					gFS.profile.GuestEnable,
					msg,
				),
			)
		} else {
			logger.Service.Zap.Errorw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", gFS.secWebSocketKey,
				"HostExtId", gFS.hostExtId,
				"GameRoomUuid", gFS.gameRoomUuid,
			)
			errorcode.Service.Fatal(gFS.secWebSocketKey, gameuser.GameUser_PROFILE_NIL)
		}

	case gamesetting.EMSGID_eGameConfigCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		state := playerstate.Service.GetState(gFS.profile.HostId, gFS.profile.MemberId)

		if state != nil {
			warn := &bet_proto.PlayerStillBetWarn{
				Msgid:        commonFS_proto.EMSGID_ePlayerStillBetWarn,
				BetRoundUuid: state.BetRoundUuid,
			}
			bytes, _ := proto.Marshal(warn)

			if state.BetRoundUuid != "" { //進這段通常是押注後離房，但在押住階段又進來
				//紀錄該名玩家有重連
				flux.Send(gameroom.PlayerIsReconnected, gFS.secWebSocketKey, gameroom.Service.Id, state.BetRoundUuid, gFS.profile.MemberId)

				//通知前端等待
				flux.Send(bet.EMSGID_ePlayerStillBetWarn, gFS.secWebSocketKey, gFS.secWebSocketKey, bytes)
				return
			} else {
				//進這裡通常是押注後離房，但在結算階段進房
				//所以會沒有betroundid但有gameRoomId，一樣需給前端發betWarn等待
				if gFS.gameRoomUuid != "" {
					flux.Send(bet.EMSGID_ePlayerStillBetWarn, gFS.secWebSocketKey, gFS.secWebSocketKey, bytes)
					return
				}
			}
		}

		if gFS.gameRoomUuid != "" { //預期是一些網路延遲錯誤才會進這裡
			logger.Service.Zap.Infow(gamesetting.EMSGID_eGameConfigCall,
				"GameUser", gFS.secWebSocketKey,
				"GameRoomUuid", gFS.gameRoomUuid,
			)
			return
		}

		if gFS.profile != nil {
			flux.Send(gamesetting.EMSGID_eGameConfigRecall, gFS.secWebSocketKey, gFS.secWebSocketKey,
				gamesetting.Service.EMSGID_eGameConfigCall(
					gFS.secWebSocketKey,
					gFS.profile.MemberId,
					gFS.profile.GuestEnable,
					msg,
				),
			)
		} else {
			logger.Service.Zap.Errorw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", gFS.secWebSocketKey,
				"HostExtId", gFS.hostExtId,
				"GameRoomUuid", gFS.gameRoomUuid,
			)
			errorcode.Service.Fatal(gFS.secWebSocketKey, gameuser.GameUser_PROFILE_NIL)
		}

	case heartbeat.ActionHeartBeatCall:
		flux.Send(heartbeat.ActionHeartBeatCall, gFS.secWebSocketKey, heartbeat.Service.Id, msg)

	case bet.EMSGID_eBetCall:
		betCall := &bet_proto.BetCall{}
		_ = proto.Unmarshal(msg, betCall)

		if betCall.BetIndex < 0 || betCall.BetIndex > 3 ||
			betCall.BetType < 0 || betCall.BetType > 23 ||
			betCall.Seat != int32(gFS.seat) {
			errorcode.Service.Error("bet call invalid", bet.Bet_PROTO_BET_CALL_INVAILD)
			logger.Service.Zap.Infow("bet call invalid",
				"player secWebSocketKey", gFS.secWebSocketKey,
				"betCall index", betCall.BetIndex,
				"betCall Type", betCall.BetType,
				"betCall seat", betCall.Seat,
			)
			return
		}

		flux.Send(bet.EMSGID_eBetCall, gFS.secWebSocketKey, betCall.BetRoundUuid, msg)

	case bet.EMSGID_eMultiBetCall:
		multiBetCall := &bet_proto.MultiBetCall{}
		_ = proto.Unmarshal(msg, multiBetCall)

		if len(multiBetCall.BetCalls) > 0 {
			flux.Send(bet.EMSGID_eMultiBetCall, gFS.secWebSocketKey, multiBetCall.BetCalls[0].BetRoundUuid, msg)
		}

	case bet.EMSGID_eClearBetsCall:
		c := &bet_proto.ClearBetsCall{}
		_ = proto.Unmarshal(msg, c)

		flux.Send(bet.EMSGID_eClearBetsCall, gFS.secWebSocketKey, c.BetRoundUuid, msg)

	case gameroom.EMSGID_eGameroomHistoryCall:
		call := &gameroom_proto.GameroomHistoryCall{}
		_ = proto.Unmarshal(msg, call)

		flux.Send(gameroom.EMSGID_eGameroomHistoryCall, gFS.secWebSocketKey, call.RoomUuid, msg)

	case playerdata.EMSGID_eUserDataCall:
		call := &playdata_proto.PlayerDataCall{}
		_ = proto.Unmarshal(msg, call)

		flux.Send(playerdata.EMSGID_eUserDataCall, gFS.secWebSocketKey, playerdata.Service.Id, msg)

	case avatar.EMSGID_eAvatarChangeCall:
		call := &avatar_proto.AvatarChangeCall{}
		err := proto.Unmarshal(msg, call)
		if err != nil {
			return
		}
		if call.AvatarId == "" {
			a := &avatar_proto.AvatarChangeRecall{
				Msgid:    commonFS_proto.EMSGID_eAvatarChangeRecall,
				Status:   0,
				AvatarId: gFS.profile.Avatar,
			}

			bytes, _ := proto.Marshal(a)

			g.SendByte(bytes)

			logger.Service.Zap.Errorw(avatar.Avatar_UPDATE_MEMBER_FAILED)
			return
		}
		flux.Send(avatar.EMSGID_eAvatarChangeRecall, gFS.secWebSocketKey, gFS.secWebSocketKey, call.AvatarId)

	case walletFS.EMSGID_eWalletBalanceCall:
		call := &walletFS_proto.WalletBalanceCall{}
		err := proto.Unmarshal(msg, call)
		if err != nil {
			return
		}

		//錢包金額
		flux.Send(walletFS.EMSGID_eWalletBalanceRecall, gFS.secWebSocketKey, gFS.secWebSocketKey)

		//是否有下注
		playerState := playerstate.Service.GetState(gFS.profile.HostId, gFS.profile.MemberId)
		if playerState != nil {
			if playerState.BetRoundUuid != "" {
				warn := &bet_proto.PlayerStillBetWarn{
					Msgid:        commonFS_proto.EMSGID_ePlayerStillBetWarn,
					BetRoundUuid: playerState.BetRoundUuid,
				}
				bytes, _ := proto.Marshal(warn)
				flux.Send(bet.EMSGID_ePlayerStillBetWarn, gFS.secWebSocketKey, gFS.secWebSocketKey, bytes)
			}
		}

	}
}

func (gFS *GameUserFS) DeferRunWriteMessageHandler(g *gameuser.GameUser) {
	gFS.disconnectedFromRoom()
}

func (gFS *GameUserFS) FluxActionHandler(action *flux.Action, g *gameuser.GameUser) {
	if gFS.secWebSocketKey != action.Key().To() {
		return
	}

	logger.Service.Zap.Infow(action.Key().Name(),
		"GameUser89", gFS.secWebSocketKey,
		"HostExtId", gFS.hostExtId,
		"Seat", gFS.seat,
		"LobbyRoomUuid", gFS.lobbyRoomUuid,
		"GameRoomUuid", gFS.gameRoomUuid,
	)

	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:
		logger.Service.Zap.Infow("GameUserFS Flux Registered",
			"GameUserFS", gFS.secWebSocketKey,
			"HostExtId", gFS.hostExtId,
		)

	case auth.ActionLoginFailed:
		logger.Service.Zap.Errorw(auth.Auth_LOGIN_FAILED,
			"GameUserFS", gFS.secWebSocketKey,
		)
		errorcode.Service.Fatal(gFS.secWebSocketKey, auth.Auth_LOGIN_FAILED)

	case auth.ActionLoginSuccess:
		gFS.profile = action.Payload()[0].(*auth.MemberInfo)

		logger.Service.Zap.Infow("GameUserFS Login Success",
			"GameUserFS", gFS.secWebSocketKey,
			"HostId", gFS.profile.HostId,
			"HostExtId", gFS.hostExtId,
			"MemberId", gFS.profile.MemberId,
			"MemberName", gFS.profile.MemberName,
			"Avatar", gFS.profile.Avatar,
		)

		wallet.Service.Open(
			wallet.Builder().
				SetSecWebSocketKey(gFS.secWebSocketKey).
				SetHostId(gFS.profile.HostId).
				SetHostExtId(gFS.hostExtId).
				SetMemberId(gFS.profile.MemberId).
				SetMemberName(gFS.profile.MemberName).
				SetBalance(gFS.profile.Balance).
				SetCategory(gFS.profile.WalletType).
				SetPurposeMajor(wallet.WalletSharedFish).
				SetPurposeMinor(wallet.WalletSharedCard89).
				SetGuest(gFS.profile.GuestEnable).
				SetDB(gFS.hostExtId).
				Build(),
		)

		if playerstate.Service.GetState(gFS.profile.HostId, gFS.profile.MemberId) == nil {
			flux.Send(playerstate.ActionCreateState, gFS.secWebSocketKey, playerstate.Service.Id,
				gFS.profile.MemberId,
				gFS.profile.HostId,
			)
		} else {
			flux.Send(playerstate.ActionUpdateConnectionState, gFS.secWebSocketKey, playerstate.Service.Id,
				gFS.profile.MemberId,
				gFS.profile.HostId,
			)
		}

		if gFS.profile.Avatar == "" && gFS.profile.GuestEnable == auth.GuestOff {
			gFS.profile.Avatar = avatar.Service.Create(
				gFS.secWebSocketKey,
				gFS.hostExtId,
				gFS.profile.HostId,
				gFS.profile.MemberId,
				avatarName(),
			)
		}

		twin.New(gFS.secWebSocketKey,
			gFS.profile.MemberId,
			gFS.profile.HostId,
			gFS.gameRoomUuid,
			gFS.profile.Avatar,
			gFS.controllerId)

	case wallet.ActionWalletOpened:

		if gFS.profile.GuestEnable == auth.GuestOff {
			fluxData := &flux_proto.FluxAction{
				Name: wallet.ActionWalletOpened,
				From: walletFS.Service.Id,
				To:   postman.SERVER_TRIGGER,
			}

			fluxData.Payload = append(fluxData.Payload, []byte(gFS.secWebSocketKey))
			fluxData.Payload = append(fluxData.Payload, []byte(gFS.profile.HostId))
			fluxData.Payload = append(fluxData.Payload, []byte(gFS.hostExtId))
			fluxData.Payload = append(fluxData.Payload, []byte(gFS.profile.MemberId))
			fluxData.Payload = append(fluxData.Payload, []byte(gFS.profile.MemberName))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatUint(gFS.profile.Balance, 10)))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatInt(int64(gFS.profile.WalletType), 10)))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatInt(int64(wallet.WalletSharedFish), 10)))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatInt(int64(wallet.WalletSharedCard89), 10)))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatInt(int64(gFS.profile.GuestEnable), 10)))

			fluxDataByte, _ := proto.Marshal(fluxData)

			postman.Service.Pub(fluxDataByte)
		}

		flux.Send(auth.EMSGID_eLoginRecall, gFS.secWebSocketKey, auth.Service.Id, true)

	case auth.EMSGID_eLoginRecall:
		g.SendAction(action)

	case lobbysetting.EMSGID_eLobbyConfigRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		gameid := lobbysettingFS.Service.GameId(gFS.secWebSocketKey)
		if maintain.Service.CheckMaintain(gFS.secWebSocketKey, gameid, gFS.hostExtId, maintain.Card) {
			return
		}

		if gFS.gameRoomUuid != "" {
			state := playerstate.Service.GetState(gFS.profile.HostId, gFS.profile.MemberId)
			if state != nil {
				if state.BetRoundUuid == "" {
					gFS.leaveRoom(gFS.seat)
				} else {
					logger.Service.Zap.Infow("delay leaving",
						"secWebSocketKey", gFS.secWebSocketKey)
					gFS.leavingRoom = gFS.gameRoomUuid
					gFS.leavingSeat = gFS.seat
				}
			}
		}

		balance, errBalance := wallet.Service.Balance(gFS.secWebSocketKey)
		if errBalance != nil {
			logger.Service.Zap.Errorw(GameUserFS_GET_BALANCE_FAILED,
				"GameUser", gFS.secWebSocketKey,
				"GameRoomUuid", gFS.gameRoomUuid,
			)
			errorcode.Service.Fatal(gFS.secWebSocketKey, GameUserFS_GET_BALANCE_FAILED)
			return
		}

		dataByte := action.Payload()[0].([]byte)

		data := &lobby_settingFS_proto.ConfigRecall{}

		if err := proto.Unmarshal(dataByte, data); err != nil {
			logger.Service.Zap.Errorw(lobbysetting.LobbySetting_CONFIG_RECALL_PROTO_INVALID,
				"GameUser", gFS.secWebSocketKey,
			)
			errorcode.Service.Fatal(gFS.secWebSocketKey, lobbysetting.LobbySetting_CONFIG_RECALL_PROTO_INVALID)
			return
		}
		data.PlayerInfo = &auth_proto.PlayerInfo{
			Id:      gFS.secWebSocketKey,
			Balance: balance,
			Name:    gFS.profile.MemberName,
			Avatar:  gFS.profile.Avatar,
			Visible: nil,
		}

		if data.StatusCode == common_proto.Status_kSuccess {
			flux.Send(gameuser.ActionJoinLobbyRoomCall, gFS.secWebSocketKey, gFS.controllerId, "")
			dataByte, _ := proto.Marshal(data)
			g.SendByte(dataByte)
		}

	case gameuser.ActionJoinLobbyRoomRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		gFS.seat = -1
		//gFS.gameRoomUuid = ""
		//gFS.gameRoomType = ""
		gFS.lobbyRoomUuid = action.Payload()[0].(string)

	case gameuser.ActionLeaveLobbyRoomRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		gFS.lobbyRoomUuid = ""

	case gamesetting.EMSGID_eGameConfigRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		dataByte := action.Payload()[0].([]byte)

		data := &game_settingFS_proto.ConfigRecall{}

		if err := proto.Unmarshal(dataByte, data); err != nil {
			logger.Service.Zap.Errorw(gamesetting.GameSetting_CONFIG_RECALL_PROTO_INVALID,
				"GameUser", gFS.secWebSocketKey,
			)
			errorcode.Service.Fatal(gFS.secWebSocketKey, gamesetting.GameSetting_CONFIG_RECALL_PROTO_INVALID)

			return
		}

		if data.StatusCode != common_proto.Status_kSuccess {
			g.SendByte(dataByte)
			return
		}

		gameid := lobbysettingFS.Service.GameId(gFS.secWebSocketKey)
		if maintain.Service.CheckMaintain(gFS.secWebSocketKey, gameid, gFS.hostExtId, maintain.Card) {
			return
		}

		balance, err := wallet.Service.BalanceCache(gFS.secWebSocketKey)

		if err != nil {
			logger.Service.Zap.Errorw("BUG",
				"GameUser", gFS.secWebSocketKey,
				"Error", err,
			)
			errorcode.Service.Fatal(gFS.secWebSocketKey, GameUserFS_GET_BALANCE_FAILED)
		}

		data.Balance = balance
		data.PlayerInfo = &auth_proto.PlayerInfo{
			Id:      gFS.secWebSocketKey,
			Balance: balance,
			Name:    gFS.profile.MemberName,
			Avatar:  gFS.profile.Avatar,
			Visible: nil,
		}

		gFS.gameConfigRecall = data

		flux.Send(gameuser.ActionJoinGameRoomCall, gFS.secWebSocketKey, gFS.controllerId,
			gFS.hostExtId,
			gFS.profile.Avatar,
			gFS.ipAddress,
			gFS.lastGameRoomUuid,
			gFS.histories,
            gFS.profile.HostId,
            gFS.profile.MemberId,
            gameid,
            gFS.profile.BillCurrency,
            gFS.isVipChangeRoom,
		)
		gFS.isVipChangeRoom = false

	case gameuser.ActionJoinGameRoomRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()
		gFS.lobbyRoomUuid = ""
		gFS.gameRoomUuid = action.Payload()[0].(string)
		gFS.seat = action.Payload()[1].(int)
		gFS.lastGameRoomUuid = action.Payload()[2].(string)
		gFS.roomKind = action.Payload()[3].(string)

		flux.Send(auth.EMSGID_eBroadcastPlayerIn, gFS.secWebSocketKey, gFS.gameRoomUuid, auth_proto.PLAYER_TYPE_GAME)
		return

	case gameroom.EMSGID_ePlayerLevaeRoom:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		gFS.histories = action.Payload()[1].([10][3]int32)

		// 若玩家有下注離房，則保留房間資訊
		gFS.gameRoomUuid = ""
		gFS.seat = -1
		gFS.leavingRoom = ""
		gFS.leavingSeat = -1
		gFS.roomKind = ""

		g.SendAction(action)

	case errorcode.ActionErrorCode:
		if gFS.profile != nil {
			dataByte := action.Payload()[0].([]byte)

			data := &errorcode_proto.Error{}

			proto.Unmarshal(dataByte, data)
		}

		g.SendAction(action)

		flux.Send(auth.ActionUserDisconnect, gFS.secWebSocketKey, gameuser.Service.Id, gFS.secWebSocketKey)

	case gameroom.EMSGID_eRoundEnd:
		if gFS.leavingRoom != "" {
			gFS.leaveRoom(gFS.leavingSeat)
		}
		g.SendAction(action)

	case gameroom.EMSGID_eRoundStart:
		g.SendAction(action)
		gameid := lobbysettingFS.Service.GameId(gFS.secWebSocketKey)
		if maintain.Service.CheckMaintain(gFS.secWebSocketKey, gameid, gFS.hostExtId, maintain.Card) {
			return
		}

	case bet.EMSGID_eBetRoundStart:
		/*flux.Send(idle.ActionIdleTimeoutReset,
			gFS.secWebSocketKey,
			idle.Service.HashId(gFS.secWebSocketKey),
			gFS.secWebSocketKey,
			gamesettingFS.Service.Idle(gFS.secWebSocketKey),
		)*/

		balance, balanceerr := wallet.Service.Balance(gFS.secWebSocketKey)

		if balanceerr != nil {
			errorcode.Service.Fatal(gFS.secWebSocketKey, GameUserFS_GET_BALANCE_FAILED)
		}

		gFS.startBalance = balance

		g.SendAction(action)

	case bet.EMSGID_eBetRoundCountdown:
		g.SendAction(action)

	case bet.EMSGID_eBetRoundEnd:
		g.SendAction(action)

	case bet.EMSGID_eBetRecall:
		betRoundUuid := action.Key().From()
		status := action.Payload()[1].(common_proto.Status_Code)
		if status == common_proto.Status_kSuccess {
			flux.Send(playerstate.ActionSaveBetState, gFS.secWebSocketKey, playerstate.Service.Id,
				gFS.profile.MemberId,
				gFS.profile.HostId,
				betRoundUuid)
		}
		g.SendAction(action)

	case bet.EMSGID_eMultiBetRecall:
		betRoundUuid := action.Key().From()
		status := action.Payload()[1].(common_proto.Status_Code)
		if status == common_proto.Status_kSuccess {
			flux.Send(playerstate.ActionSaveBetState, gFS.secWebSocketKey, playerstate.Service.Id,
				gFS.profile.MemberId,
				gFS.profile.HostId,
				betRoundUuid)
		}
		g.SendAction(action)

	case bet.EMSGID_eBroadcastBetRecall:
		g.SendAction(action)

	case bet.EMSGID_eBroadcastMultiBetRecall:
		g.SendAction(action)

	case bet.EMSGID_eClearBetsRecall:
		flux.Send(playerstate.ActionClearBetState, gFS.secWebSocketKey, playerstate.Service.Id,
			gFS.profile.MemberId,
			gFS.profile.HostId)
		g.SendAction(action)

	case bet.EMSGID_eBroadcastClearBetsRecall:
		g.SendAction(action)

	case probability.EMSGID_eBroadcastDeal:
		g.SendAction(action)

	case probability.EMSGID_eBroadcastResult:
		g.SendAction(action)

	case lottery.EMSGID_eLotteryResult:
		playerResult := action.Payload()[1].(map[string]uint64)

		if gFS.accountingSn != 0 {
			//共用錢包
		} else if a := accounting.Builder().
			SetSecWebSocketKey(gFS.secWebSocketKey).
			SetHostExtId(gFS.hostExtId).
			SetGuestEnable(gFS.profile.GuestEnable == auth.GuestOn).
			SetHostId(gFS.profile.HostId).
			SetGameId(gamesettingFS.Service.GameId(gFS.secWebSocketKey)).
			SetSubgameId(gamesettingFS.Service.RateIndex(gFS.secWebSocketKey)).
			SetMemberId(gFS.profile.MemberId).
			SetInitCent(gFS.startBalance).
			SetDenom(0).
			SetDB(gFS.hostExtId).
			SetKind(accounting.PLAYER).
			SetHandler(&accountingFS.AccountingFS{}).
			Build(); a != nil {
				gFS.accountingSn = a.Start.Sn
				if newLevel := vip.Service.CheckVip(
					true,
					gFS.secWebSocketKey,
					gFS.hostExtId,
					gFS.profile.HostId,
					gFS.profile.MemberId,
					gamesettingFS.Service.GameId(gFS.secWebSocketKey),
					gFS.profile.BillCurrency,
					playerResult["total_Bet"],
					playerResult["total_Win"],
					gFS.accountingSn,
				); newLevel != 0 && gFS.roomKind == "GAME_ROOM" {
					//離房通知
					flux.Send(auth.EMSGID_eBroadcastPlayerOut, gFS.secWebSocketKey, gFS.secWebSocketKey, auth.Service.BroadcastPlayerOut(
						gFS.gameRoomUuid,
						gFS.secWebSocketKey,
						gFS.profile.MemberName,
						gFS.profile.Avatar,
						uint32(gFS.seat),
						uint64(0),
					))
					gFS.isVipChangeRoom = true
				} else if gFS.roomKind == "VIP_ROOM" {
					flux.Send(gameroom.ActionVipSetting, gFS.secWebSocketKey, gFS.gameRoomUuid, newLevel)
				}
		}
		g.SendAction(action)

	case lottery.EMSGID_eBroadcastLotteryResult:
		dataByte := action.Payload()[0].([]byte)
		data1 := &lottery_proto.BroadcastResult{} //braodcastResult
		if err := proto.Unmarshal(dataByte, data1); err != nil {
			logger.Service.Zap.Errorw(gamesetting.GameSetting_CONFIG_RECALL_PROTO_INVALID,
				"GameUser", gFS.secWebSocketKey,
			)
			errorcode.Service.Fatal(gFS.secWebSocketKey, gamesetting.GameSetting_CONFIG_RECALL_PROTO_INVALID)
		}

		data2 := action.Payload()[1].(map[string][]bet_proto.BetCall) //betCall
		if len(data2[gFS.secWebSocketKey]) > 0 {
			if gFS.accountingSn != 0 { //獨立錢包 & 共用錢包
				accountingSn := gFS.accountingSn
				gFS.accountingSn = 0
				data3 := action.Payload()[2].([3]int32) //dice
				memberName := wallet.Service.MemberName(gFS.secWebSocketKey)
				balance, _ := wallet.Service.BalanceCache(gFS.secWebSocketKey)
				flux.Send(accounting.ActionAccountingEnd, gFS.secWebSocketKey, accounting.Service.HashId(gFS.secWebSocketKey, accountingSn), data1, data2, data3, memberName, balance)
			} else if a := accounting.Builder(). //正常不該進這裡
				SetSecWebSocketKey(gFS.secWebSocketKey).
				SetHostExtId(gFS.hostExtId).
				SetGuestEnable(gFS.profile.GuestEnable == auth.GuestOn).
				SetHostId(gFS.profile.HostId).
				SetGameId(gamesettingFS.Service.GameId(gFS.secWebSocketKey)).
				SetSubgameId(gamesettingFS.Service.RateIndex(gFS.secWebSocketKey)).
				SetMemberId(gFS.profile.MemberId).
				SetInitCent(gFS.startBalance).
				SetDenom(0).
				SetDB(gFS.hostExtId).
				SetKind(accounting.PLAYER).
				SetHandler(&accountingFS.AccountingFS{}).
				Build(); a != nil {
				gFS.accountingSn = 0
				data3 := action.Payload()[2].([3]int32) //dice
				memberName := wallet.Service.MemberName(gFS.secWebSocketKey)
				balance, _ := wallet.Service.BalanceCache(gFS.secWebSocketKey)
				flux.Send(accounting.ActionAccountingEnd, gFS.secWebSocketKey, accounting.Service.HashId(gFS.secWebSocketKey, a.Start.Sn), data1, data2, data3, memberName, balance)
			}
		}
		g.SendAction(action)

	case heartbeat.ActionHeartBeatRecall:
		g.SendAction(action)

	case auth.ActionAuthNotify:
		g.SendAction(action)

	case auth.EMSGID_eBroadcastPlayerIn:
		fallthrough
	case auth.EMSGID_eBroadcastPlayerOut:
		switch action.Payload()[0].(type) {
		case [][]byte:
			gFS.postman(action, g)

		default:
			g.SendAction(action)
		}

	case gameroom.EMSGID_eHistory:
		g.SendAction(action)

	case bet.EMSGID_ePlayerStillBetWarn:
		g.SendAction(action)

	case bet.ActionClearBetStatus:
		flux.Send(playerstate.ActionClearBetState, gFS.secWebSocketKey, playerstate.Service.Id,
			gFS.profile.MemberId,
			gFS.profile.HostId,
		)

	case gameroom.EMSGID_eKickOutWarn:
		g.SendAction(action)

	case bet.EMSGID_eJoinedBetRoundInfo:
		g.SendAction(action)

	case gameroom.EMSGID_eJoinedRoomInfo:
		joinedRoomInfo := action.Payload()[0].(*game_settingFS_proto.JoinedRoomInfo)

		configRecall := gFS.gameConfigRecall
		configRecall.JoinedRoomInfo = joinedRoomInfo

		//處理下注區域
		betsMap := bet.Service.GetAllAreaBets(gFS.gameRoomUuid)
		seatHoldeBets := make([]*game_settingFS_proto.SeatsHoldBets, 0)
		for seatId, betTypeMap := range betsMap {
			seatHoldeBet := &game_settingFS_proto.SeatsHoldBets{
				Seat: seatId,
			}

			betAreaBets := make([]*game_settingFS_proto.BetAreaBets, 0)
			for betType, betIndexMap := range betTypeMap {
				betAreaBet := &game_settingFS_proto.BetAreaBets{
					BetType: betType,
				}

				//取得下注的籌碼索引與數量
				betIndexAndNums := make([]*game_settingFS_proto.BetsIndexAndNum, 0)
				for betIndex, num := range betIndexMap {
					betIndexAndNum := &game_settingFS_proto.BetsIndexAndNum{
						BetIndex: betIndex,
						BetNum:   num,
					}

					betIndexAndNums = append(betIndexAndNums, betIndexAndNum)
				}
				betAreaBet.BetsIndexAndNum = betIndexAndNums

				betAreaBets = append(betAreaBets, betAreaBet)
			}
			seatHoldeBet.BetAreaBets = betAreaBets

			seatHoldeBets = append(seatHoldeBets, seatHoldeBet)

		}

		configRecall.SeatHoldBets = seatHoldeBets

		//序列化
		bytes, _ := proto.Marshal(configRecall)

		g.SendByte(bytes)

	case gameroom.EMSGID_eGameroomHistoryRecall:
		g.SendAction(action)

	case playerdata.EMSGID_eUserDataRecall:
		g.SendAction(action)

	case avatar.EMSGID_eAvatarChangeRecall:
		avatarId := action.Payload()[0].(string)

		gFS.profile.Avatar = avatarId

		if gFS.profile.GuestEnable == auth.GuestOff {
			gFS.profile.Avatar = avatar.Service.Create(
				gFS.secWebSocketKey,
				gFS.hostExtId,
				gFS.profile.HostId,
				gFS.profile.MemberId,
				avatarId,
			)
		}

		aRecall := &avatar_proto.AvatarChangeRecall{
			Msgid:    commonFS_proto.EMSGID_eAvatarChangeRecall,
			Status:   1,
			AvatarId: gFS.profile.Avatar,
		}
		bytes, err := proto.Marshal(aRecall)
		if err != nil {
			return
		}
		g.SendByte(bytes)

	case walletFS.EMSGID_eWalletBalanceRecall:
		balance, _ := wallet.Service.Balance(gFS.secWebSocketKey)
		recall := &walletFS_proto.WalletBalanceRecall{
			Msgid:         commonFS_proto.EMSGID_eWalletBalanceRecall,
			PlayerBalance: balance,
		}
		bytes, _ := proto.Marshal(recall)
		g.SendByte(bytes)

	case "startChangeRoomCountdown": //開始換房的倒數計時
		gFS.startChangeRoomTimer()
	}
}

//開始換房倒數計時
func (gFS *GameUserFS) startChangeRoomTimer() {
	if gFS.changeRoomTimer == nil { //初始化
		gFS.changeRoomTimer = &changeRoomTimer{
			timer:         time.NewTimer(CHANGE_ROOM_COUNTDOWN_TIME * time.Second),
			stopTimerChan: make(chan bool),
		}
	} else { //目前理論上流程不該進這
		logger.Service.Zap.Infow("異常的倒數踢人計時器流程發生，有計時器沒被銷毀乾淨而又啟用!!", "secWebSocketKey", gFS.secWebSocketKey, "gameRoomUuid", gFS.gameRoomUuid)
		gFS.stopChangeRoomTimer()
		//建新的Timer
		gFS.changeRoomTimer = &changeRoomTimer{
			timer:         time.NewTimer(CHANGE_ROOM_COUNTDOWN_TIME * time.Second),
			stopTimerChan: make(chan bool),
		}
	}

	go func() {
		for {
			select {
			case <-gFS.changeRoomTimer.timer.C: //時間到了踢人
				//此Playerout僅發給本人做通知準備離開用，不廣播給其它玩家
				flux.Send(auth.EMSGID_eBroadcastPlayerOut, gFS.secWebSocketKey, gFS.secWebSocketKey, auth.Service.BroadcastPlayerOut(
					gFS.gameRoomUuid,
					gFS.secWebSocketKey,
					gFS.profile.MemberName,
					gFS.profile.Avatar,
					uint32(gFS.seat),
					uint64(0),
				))

				//清空原本的timer
				gFS.changeRoomTimer = nil

				return

			case <-gFS.changeRoomTimer.stopTimerChan: //時間沒到被終止，釋放這條goroutine
				return
			}
		}

	}()
}

//停止換房倒數
func (gFS *GameUserFS) stopChangeRoomTimer() {
	if gFS.changeRoomTimer != nil { //進這裡，代表計時器尚未到時而重製須中止
		changeRoomTimer := gFS.changeRoomTimer
		changeRoomTimer.timer.Stop()
		changeRoomTimer.stopTimerChan <- true

		//清空原本的timer
		gFS.changeRoomTimer = nil
	} else { //目前理論上流程不該進這
		logger.Service.Zap.Infow("異常的倒數踢人計時器流程發生，有計時器連續被中止!!", "secWebSocketKey", gFS.secWebSocketKey, "gameRoomUuid", gFS.gameRoomUuid)
	}
}

func avatarName() string {
	randNum, _ := rand.Int(rand.Reader, big.NewInt(int64(11)))
	return strconv.Itoa(int(randNum.Int64()))
}

func (gFS *GameUserFS) postman(action *flux.Action, g *gameuser.GameUser) {
	dataByte := action.Payload()[0].([][]byte)
	g.SendByte(dataByte[0])
}

func (gFS *GameUserFS) balanceLimit() (balance uint64) {
	if gFS.gameRoomUuid == "" {
		return
	}

	blance, blanceErr := wallet.Service.Balance(gFS.secWebSocketKey)
	if blanceErr != nil {
		logger.Service.Zap.Errorw(GameUserFS_GET_BALANCE_FAILED,
			"GameUser", gFS.secWebSocketKey,
			"GameRoomUuid", gFS.gameRoomUuid,
		)
		errorcode.Service.Fatal(gFS.secWebSocketKey, GameUserFS_GET_BALANCE_FAILED)
		return
	}
	balance, balanceErr := wallet.Service.Balance(gFS.secWebSocketKey)

	if balanceErr != nil {
		logger.Service.Zap.Errorw(GameUserFS_GET_BALANCE_FAILED,
			"GameUser", gFS.secWebSocketKey,
			"GameRoomUuid", gFS.gameRoomUuid,
		)
		errorcode.Service.Fatal(gFS.secWebSocketKey, GameUserFS_GET_BALANCE_FAILED)
		return 0
	}

	return balance + blance
}

func (gFS *GameUserFS) CleanDataHandler(g *gameuser.GameUser) {
	if gFS.profile != nil {
		session.Service.End(
			gFS.secWebSocketKey,
			gFS.profile.HostId,
			gFS.hostExtId,
			gFS.profile.MemberId,
			0, // TODO JOHNNY need implement
		)
		state := playerstate.Service.GetState(gFS.profile.HostId, gFS.profile.MemberId)

		if state != nil {
			if state.BetRoundUuid == "" {
				flux.Send(twin.ActionTwinDestroy, gFS.secWebSocketKey, gFS.secWebSocketKey)
			}
		}

	} else {
		logger.Service.Zap.Warnw(gameuser.GameUser_PROFILE_NIL,
			"GameUser", gFS.secWebSocketKey,
			"HostExtId", gFS.hostExtId,
		)
	}

	flux.Send(idle.ActionIdleTimeoutStop, gFS.secWebSocketKey, idle.Service.Id, gFS.secWebSocketKey)
	lobbysetting.Service.Delete(gFS.secWebSocketKey)

}

//離開遊戲房
func (gFS *GameUserFS) leaveRoom(leaveSeat int) {
	logger.Service.Zap.Infow("leaveRoom",
		"GameUser", gFS.secWebSocketKey,
		"LeavingGameRoomUuid", gFS.gameRoomUuid,
		"LobbyRoomUuid", gFS.lobbyRoomUuid,
		"Seat", leaveSeat,
	)

	//停止換房計時器
	gFS.stopChangeRoomTimer()

	//廣播玩家離開
	flux.Send(auth.EMSGID_eBroadcastPlayerOut, gFS.secWebSocketKey, gFS.gameRoomUuid, auth.Service.BroadcastPlayerOut(
		gFS.gameRoomUuid,
		gFS.secWebSocketKey,
		gFS.profile.MemberName,
		gFS.profile.Avatar,
		uint32(leaveSeat),
		uint64(0),
	))
	flux.Send(gameuser.ActionLeaveGameRoomCall, gFS.secWebSocketKey, gFS.controllerId, gFS.gameRoomUuid)
}

func (gFS *GameUserFS) disconnectedFromRoom() {
	logger.Service.Zap.Infow("disconnected from room",
		"GameUser", gFS.secWebSocketKey,
		"GameRoomUuid", gFS.gameRoomUuid,
		"LobbyRoomUuid", gFS.lobbyRoomUuid,
	)

	if gFS.gameRoomUuid != "" {
		if state := playerstate.Service.GetState(gFS.profile.HostId, gFS.profile.MemberId); state == nil || state.BetRoundUuid == "" {
			// 離房
			flux.Send(auth.EMSGID_eBroadcastPlayerOut, gFS.secWebSocketKey, gFS.gameRoomUuid, auth.Service.BroadcastPlayerOut(
				gFS.gameRoomUuid,
				gFS.secWebSocketKey,
				gFS.profile.MemberName,
				gFS.profile.Avatar,
				uint32(gFS.seat),
				uint64(0),
			))
			flux.Send(gameuser.ActionLeaveGameRoomCall, gFS.secWebSocketKey, gFS.controllerId, gFS.gameRoomUuid)
		} else {
			if a := accounting.Builder().
				SetSecWebSocketKey(gFS.secWebSocketKey).
				SetHostExtId(gFS.hostExtId).
				SetGuestEnable(gFS.profile.GuestEnable == auth.GuestOn).
				SetHostId(gFS.profile.HostId).
				SetGameId(gamesettingFS.Service.GameId(gFS.secWebSocketKey)).
				SetSubgameId(gamesettingFS.Service.RateIndex(gFS.secWebSocketKey)).
				SetMemberId(gFS.profile.MemberId).
				SetInitCent(gFS.startBalance).
				SetDenom(0).
				SetDB(gFS.hostExtId).
				SetKind(accounting.PLAYER).
				SetHandler(&accountingFS.AccountingFS{}).
				Build(); a != nil {
				flux.Send(twin.ActionTwinActive, gFS.secWebSocketKey, gFS.secWebSocketKey, a.Start.Sn)
			}
		}
	} else {
		flux.Send(gameuser.ActionGameUserDelete, gFS.secWebSocketKey, gameuser.Service.Id, gFS.secWebSocketKey)
	}

	if gFS.lobbyRoomUuid != "" {
		flux.Send(gameuser.ActionLeaveLobbyRoomCall, gFS.secWebSocketKey, gFS.controllerId, gFS.lobbyRoomUuid, true)
	} else {
		flux.Send(gameuser.ActionGameUserDelete, gFS.secWebSocketKey, gameuser.Service.Id, gFS.secWebSocketKey)
	}

	if gFS.profile != nil {
		flux.Send(playerstate.ActionDisconnectState, gFS.secWebSocketKey, playerstate.Service.Id,
			gFS.profile.MemberId,
			gFS.profile.HostId,
		)
	}
}
