package gameuser89

import (
	"89-game-server/application/accounting89"
	"89-game-server/application/atm"
	"89-game-server/application/banker"
	banker_proto "89-game-server/application/banker/proto"
	"89-game-server/application/filter"
	"89-game-server/application/friendroom"
	friend_room_proto "89-game-server/application/friendroom/proto"
	"89-game-server/application/gamesetting89"
	game_setting89_proto "89-game-server/application/gamesetting89/proto"
	"89-game-server/application/lobbysetting89"
	lobby_setting89_proto "89-game-server/application/lobbysetting89/proto"
	"89-game-server/application/twin"
	"89-game-server/domain/avatar"
	"89-game-server/domain/bet"
	"89-game-server/domain/draw"
	"89-game-server/domain/gamerecovery89"
	"89-game-server/domain/probability"
	"89-game-server/domain/waitingroom"
	"89-game-server/domain/wallet89"
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
	gamerecovery "gitlab.iplaystar.net/game-server/game-recovery-v2"
	gamesetting "gitlab.iplaystar.net/game-server/game-setting"
	gameuser "gitlab.iplaystar.net/game-server/game-user"
	heartbeat "gitlab.iplaystar.net/game-server/heart-beat"
	"gitlab.iplaystar.net/game-server/idle"
	lobbyroom "gitlab.iplaystar.net/game-server/lobby-room"
	lobbysetting "gitlab.iplaystar.net/game-server/lobby-setting"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/mediator"
	"gitlab.iplaystar.net/game-server/postman"
	"gitlab.iplaystar.net/game-server/session"
	sessionmanager "gitlab.iplaystar.net/game-server/session-manager"
	"gitlab.iplaystar.net/game-server/wallet"
)

type GameUser89 struct {
	controllerId     string
	secWebSocketKey  string
	bankerUuid       string
	hostExtId        string
	gameRoomUuid     string
	lobbyRoomUuid    string
	gameRoomType     string
	ipAddress        string
	seat             int
	profile          *auth.MemberInfo
	gameConfigRecall *game_setting89_proto.ConfigRecall
	isGaming         bool
	isWaiting        bool
	isDestroy        bool
	accountingSn     uint64
}

func New(controllerId, secWebSocketKey, hostExtId, remoteAddr string) *GameUser89 {
	return &GameUser89{
		controllerId:     controllerId,
		secWebSocketKey:  secWebSocketKey,
		hostExtId:        hostExtId,
		ipAddress:        remoteAddr,
		seat:             -1,
		profile:          nil,
		gameConfigRecall: nil,
		isGaming:         false,
		isWaiting:        false,
		isDestroy:        false,
		accountingSn:     0,
	}
}

func (g89 *GameUser89) MsgHandler(g *gameuser.GameUser, msg []byte) {
	v, err := filter.FindActionName(msg)
	if err != nil {
		logger.Service.Zap.Errorw(gameuser.GameUser_MSGID_PROTO_INVALID,
			"GameUser89", g89.secWebSocketKey,
			"Error", err,
		)
		errorcode.Service.Fatal(g89.secWebSocketKey, gameuser.GameUser_MSGID_PROTO_INVALID)
		return
	}

	switch v {
	case auth.EMSGID_eLoginCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		flux.Send(auth.EMSGID_eLoginCall, g89.secWebSocketKey, auth.Service.Id, msg)

	case atm.EMSGID_eDepositCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g89.isGaming || g89.isWaiting || g89.gameRoomUuid != "" {
			logger.Service.Zap.Errorw(GameUser89_DEPOSIT_CALL_INVALID,
				"GameUser", g89.secWebSocketKey,
				"GameRoomUuid", g89.gameRoomUuid,
				"IsGaming", g89.isGaming,
				"IsWaiting", g89.isWaiting,
			)
			errorcode.Service.Fatal(g89.secWebSocketKey, GameUser89_DEPOSIT_CALL_INVALID)
			return
		}
		if g89.profile != nil {
			flux.Send(atm.EMSGID_eDepositCall, g89.secWebSocketKey, atm.Service.Id, msg, g89.hostExtId, g89.profile.MemberId)

		} else {
			logger.Service.Zap.Warnw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", g89.secWebSocketKey,
				"HostExtId", g89.hostExtId,
				"IsGaming", g89.isGaming,
				"IsWaiting", g89.isWaiting,
			)
		}

	case atm.EMSGID_eWithdrawCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g89.isGaming || g89.isWaiting || g89.gameRoomUuid != "" {
			logger.Service.Zap.Errorw(GameUser89_WITHDRAW_CALL_INVALID,
				"GameUser", g89.secWebSocketKey,
				"GameRoomUuid", g89.gameRoomUuid,
				"IsGaming", g89.isGaming,
				"IsWaiting", g89.isWaiting,
			)
			errorcode.Service.Fatal(g89.secWebSocketKey, GameUser89_WITHDRAW_CALL_INVALID)
			return
		}

		if g89.profile != nil {
			flux.Send(atm.EMSGID_eWithdrawCall, g89.secWebSocketKey, atm.Service.Id, msg, g89.hostExtId, g89.profile.MemberId)
		} else {
			logger.Service.Zap.Errorw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", g89.secWebSocketKey,
				"HostExtId", g89.hostExtId,
				"GameRoomUuid", g89.gameRoomUuid,
				"IsGaming", g89.isGaming,
				"IsWaiting", g89.isWaiting,
			)
			errorcode.Service.Fatal(g89.secWebSocketKey, gameuser.GameUser_PROFILE_NIL)
		}

	case atm.EMSGID_eInquireCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g89.profile != nil {
			flux.Send(atm.EMSGID_eInquireCall, g89.secWebSocketKey, atm.Service.Id, msg, g89.hostExtId, g89.profile.MemberId)
		} else {
			logger.Service.Zap.Errorw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", g89.secWebSocketKey,
				"HostExtId", g89.hostExtId,
				"GameRoomUuid", g89.gameRoomUuid,
				"IsGaming", g89.isGaming,
				"IsWaiting", g89.isWaiting,
			)
			errorcode.Service.Fatal(g89.secWebSocketKey, gameuser.GameUser_PROFILE_NIL)
		}

	case lobbysetting.EMSGID_eLobbyConfigCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g89.profile != nil {
			flux.Send(lobbysetting.EMSGID_eLobbyConfigRecall, g89.secWebSocketKey, g89.secWebSocketKey,
				lobbysetting.Service.EMSGID_eLobbyConfigCall(
					g89.secWebSocketKey,
					g89.profile.MemberId,
					g89.profile.GuestEnable,
					msg,
				),
			)
		} else {
			logger.Service.Zap.Errorw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", g89.secWebSocketKey,
				"HostExtId", g89.hostExtId,
				"GameRoomUuid", g89.gameRoomUuid,
				"IsGaming", g89.isGaming,
				"IsWaiting", g89.isWaiting,
			)
			errorcode.Service.Fatal(g89.secWebSocketKey, gameuser.GameUser_PROFILE_NIL)
		}

	case gamesetting.EMSGID_eGameConfigCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g89.isGaming || g89.isWaiting || g89.gameRoomUuid != "" {
			logger.Service.Zap.Infow(gamesetting.EMSGID_eGameConfigCall,
				"GameUser", g89.secWebSocketKey,
				"GameRoomUuid", g89.gameRoomUuid,
				"IsGaming", g89.isGaming,
				"IsWaiting", g89.isWaiting,
			)
			return
		}

		if g89.profile != nil {
			flux.Send(gamesetting.EMSGID_eGameConfigRecall, g89.secWebSocketKey, g89.secWebSocketKey,
				gamesetting.Service.EMSGID_eGameConfigCall(
					g89.secWebSocketKey,
					g89.profile.MemberId,
					g89.profile.GuestEnable,
					msg,
				),
			)
		} else {
			logger.Service.Zap.Errorw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", g89.secWebSocketKey,
				"HostExtId", g89.hostExtId,
				"GameRoomUuid", g89.gameRoomUuid,
				"IsGaming", g89.isGaming,
				"IsWaiting", g89.isWaiting,
			)
			errorcode.Service.Fatal(g89.secWebSocketKey, gameuser.GameUser_PROFILE_NIL)
		}

	case heartbeat.ActionHeartBeatCall:
		flux.Send(heartbeat.ActionHeartBeatCall, g89.secWebSocketKey, heartbeat.Service.Id, msg)

	case bet.EMSGID_eBetCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if !g89.isGaming {
			return
		}

		// TODO JOHNNY 驗證 TOKEN
		flux.Send(bet.EMSGID_eBetCall, g89.secWebSocketKey, bet.Service.HashId(g89.secWebSocketKey, g89.gameRoomUuid), msg)

	case draw.EMSGID_eDrawCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if !g89.isGaming {
			return
		}

		// TODO JOHNNY 驗證 TOKEN
		flux.Send(draw.EMSGID_eDrawCall, g89.secWebSocketKey, draw.Service.HashId(g89.secWebSocketKey, g89.gameRoomUuid), msg)

	case atm.EMSGID_eAutoTransferCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g89.isGaming || g89.lobbyRoomUuid == "" {
			logger.Service.Zap.Errorw(GameUser89_AUTO_TRANSFER_CALL_INVALID,
				"GameUser", g89.secWebSocketKey,
				"LobbyRoomUuid", g89.lobbyRoomUuid,
				"GameRoomUuid", g89.gameRoomUuid,
				"IsGaming", g89.isGaming,
				"IsWaiting", g89.isWaiting,
			)
			errorcode.Service.Fatal(g89.secWebSocketKey, GameUser89_AUTO_TRANSFER_CALL_INVALID)
			return
		}

		flux.Send(atm.EMSGID_eAutoTransferCall, g89.secWebSocketKey, atm.Service.Id, msg, g89.hostExtId, g89.profile.MemberId)

	case atm.EMSGID_eAutoTransferOutCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g89.isGaming || g89.lobbyRoomUuid == "" {
			logger.Service.Zap.Errorw(GameUser89_AUTO_TRANSFER_CALL_INVALID,
				"GameUser", g89.secWebSocketKey,
				"LobbyRoomUuid", g89.lobbyRoomUuid,
				"GameRoomUuid", g89.gameRoomUuid,
				"IsGaming", g89.isGaming,
				"IsWaiting", g89.isWaiting,
			)
			errorcode.Service.Fatal(g89.secWebSocketKey, GameUser89_AUTO_TRANSFER_CALL_INVALID)
			return
		}

		flux.Send(atm.EMSGID_eAutoTransferOutCall, g89.secWebSocketKey, atm.Service.Id, msg, g89.hostExtId, g89.profile.MemberId)

	case friendroom.EMSGID_eFriendRoomJoinCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g89.isGaming || g89.gameRoomUuid != "" || g89.profile.GuestEnable == auth.GuestOn {
			logger.Service.Zap.Infow(friendroom.EMSGID_eFriendRoomJoinCall,
				"GameUser", g89.secWebSocketKey,
				"GameRoomUuid", g89.gameRoomUuid,
				"GameRoomType", g89.gameRoomType,
				"IsGaming", g89.isGaming,
				"IsWaiting", g89.isWaiting,
				"GuestEnable", g89.profile.GuestEnable,
			)
			return
		}

		if v := friendroom.Service.Get(g89.secWebSocketKey); v != nil {
			v.EMSGID_eFriendRoomJoinCall(msg, g89.hostExtId, g89.ipAddress)
		} else {
			friendroom.Service.Create(friendroom.Builder().
				SetSecWebSocketKey(g89.secWebSocketKey).
				SetMemberId(g89.profile.MemberId).
				SetMemberName(g89.profile.MemberName).
				SetAvatar(g89.profile.Avatar).
				SetHostExtId(g89.hostExtId).
				SetKind(friendroom.PLAYER).
				SetGuest(g89.profile.GuestEnable).
				Build(),
			).EMSGID_eFriendRoomJoinCall(msg, g89.hostExtId, g89.ipAddress)
		}

	case friendroom.EMSGID_eFriendRoomLeaveCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g89.isGaming || g89.profile.GuestEnable == auth.GuestOn {
			logger.Service.Zap.Infow(friendroom.EMSGID_eFriendRoomLeaveCall,
				"GameUser", g89.secWebSocketKey,
				"GameRoomUuid", g89.gameRoomUuid,
				"GameRoomType", g89.gameRoomType,
				"IsGaming", g89.isGaming,
				"IsWaiting", g89.isWaiting,
				"GuestEnable", g89.profile.GuestEnable,
			)
			return
		}

		if v := friendroom.Service.Get(g89.secWebSocketKey); v != nil {
			if lobbysetting89.Service.AutoATM(g89.secWebSocketKey) {
				// TODO JOHNNY 以後可能會有要自動儲值幾%的...
				flux.Send(atm.ActionAtmAutoWithdraw, g89.secWebSocketKey, atm.Service.Id, uint8(100), g89.hostExtId, g89.profile.MemberId)
			}
			v.EMSGID_eFriendRoomLeaveCall(msg)
		}

	case friendroom.EMSGID_eFriendRoomGameStart:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g89.profile.GuestEnable == auth.GuestOn {
			logger.Service.Zap.Infow(friendroom.EMSGID_eFriendRoomGameStart,
				"GameUser", g89.secWebSocketKey,
				"GameRoomUuid", g89.gameRoomUuid,
				"GameRoomType", g89.gameRoomType,
				"IsGaming", g89.isGaming,
				"IsWaiting", g89.isWaiting,
				"GuestEnable", g89.profile.GuestEnable,
			)
			return
		}

		if v := friendroom.Service.Get(g89.secWebSocketKey); v != nil {
			v.EMSGID_eFriendRoomGameStart(msg)
		}
	}
}

func (g89 *GameUser89) DeferRunWriteMessageHandler(g *gameuser.GameUser) {
	g89.leaveRooms()
}

func (g89 *GameUser89) FluxActionHandler(action *flux.Action, g *gameuser.GameUser) {
	if g89.secWebSocketKey != action.Key().To() {
		return
	}
	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:
		logger.Service.Zap.Infow("GameUser89 Flux Registered",
			"GameUser89", g89.secWebSocketKey,
			"HostExtId", g89.hostExtId,
		)

	case auth.ActionLoginFailed:
		logger.Service.Zap.Errorw(auth.Auth_LOGIN_FAILED,
			"GameUser89", g89.secWebSocketKey,
		)
		errorcode.Service.Fatal(g89.secWebSocketKey, auth.Auth_LOGIN_FAILED)

	case auth.ActionLoginSuccess:
		g89.profile = action.Payload()[0].(*auth.MemberInfo)

		flux.Send(atm.ActionAtmStart, g89.secWebSocketKey, atm.Service.Id, g89.hostExtId, g89.profile.MemberId)

		logger.Service.Zap.Infow("GameUser89 Login Success",
			"GameUser89", g89.secWebSocketKey,
			"HostId", g89.profile.HostId,
			"HostExtId", g89.hostExtId,
			"MemberId", g89.profile.MemberId,
			"MemberName", g89.profile.MemberName,
			"Avatar", g89.profile.Avatar,
		)

		wallet.Service.Open(
			wallet.Builder().
				SetSecWebSocketKey(g89.secWebSocketKey).
				SetHostId(g89.profile.HostId).
				SetHostExtId(g89.hostExtId).
				SetMemberId(g89.profile.MemberId).
				SetMemberName(g89.profile.MemberName).
				SetBalance(g89.profile.Balance).
				SetCategory(g89.profile.WalletType).
				SetPurposeMajor(wallet.WalletSharedFish).
				SetPurposeMinor(wallet.WalletSharedCard89).
				SetGuest(g89.profile.GuestEnable).
				SetDB(g89.hostExtId).
				Build(),
		)

		if g89.profile.Avatar == "" && g89.profile.GuestEnable == auth.GuestOff {
			g89.profile.Avatar = avatar.Service.Create(
				g89.secWebSocketKey,
				g89.hostExtId,
				g89.profile.HostId,
				g89.profile.MemberId,
			)
		}

		twin.New(
			g89.secWebSocketKey,
			g89.bankerUuid,
			g89.profile.MemberId,
			g89.profile.HostId,
			g89.hostExtId,
			g89.gameRoomUuid,
			g89.controllerId,
			g89.seat,
			g89.profile.GuestEnable,
			g89.accountingSn,
		)

	case wallet.ActionWalletOpened:

		if g89.profile.GuestEnable == auth.GuestOff {
			fluxData := &flux_proto.FluxAction{
				Name: wallet.ActionWalletOpened,
				From: wallet89.Service.Id,
				To:   postman.SERVER_TRIGGER,
			}

			fluxData.Payload = append(fluxData.Payload, []byte(g89.secWebSocketKey))
			fluxData.Payload = append(fluxData.Payload, []byte(g89.profile.HostId))
			fluxData.Payload = append(fluxData.Payload, []byte(g89.hostExtId))
			fluxData.Payload = append(fluxData.Payload, []byte(g89.profile.MemberId))
			fluxData.Payload = append(fluxData.Payload, []byte(g89.profile.MemberName))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatUint(g89.profile.Balance, 10)))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatInt(int64(g89.profile.WalletType), 10)))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatInt(int64(wallet.WalletSharedFish), 10)))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatInt(int64(wallet.WalletSharedCard89), 10)))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatInt(int64(g89.profile.GuestEnable), 10)))

			fluxDataByte, _ := proto.Marshal(fluxData)

			postman.Service.Pub(fluxDataByte)
		}

		flux.Send(auth.EMSGID_eLoginRecall, g89.secWebSocketKey, auth.Service.Id, true)

	case auth.EMSGID_eLoginRecall:
		g.SendAction(action)

	case lobbysetting.EMSGID_eLobbyConfigRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		recovery, isGaming := g89.gameRecovery(lobbysetting89.Service.GameId(g89.secWebSocketKey))

		g89.isGaming = isGaming

		if g89.gameRoomUuid != "" && !g89.isGaming {
			if lobbysetting89.Service.AutoATM(g89.secWebSocketKey) {
				// TODO JOHNNY 以後可能會有要自動儲值幾%的...
				flux.Send(atm.ActionAtmAutoWithdraw, g89.secWebSocketKey, atm.Service.Id, uint8(100), g89.hostExtId, g89.profile.MemberId)
			}
			flux.Send(auth.EMSGID_eBroadcastPlayerOut, g89.secWebSocketKey, g89.gameRoomUuid, auth.Service.BroadcastPlayerOut(
				g89.gameRoomUuid,
				g89.secWebSocketKey,
				g89.profile.MemberName,
				g89.profile.Avatar,
				uint32(g89.seat),
				uint64(0),
			))

			switch g89.gameRoomType {
			case banker.FRIEND_ROOM:
				flux.Send(gameuser.ActionLeaveGameRoomCall, g89.secWebSocketKey, g89.gameRoomUuid, g89.secWebSocketKey)

			case banker.GAME_ROOM:
				flux.Send(gameuser.ActionLeaveGameRoomCall, g89.secWebSocketKey, g89.controllerId, g89.gameRoomUuid)

			default:
				panic("ERROR GAME ROOM TYPE " + g89.secWebSocketKey)
			}
		}

		if recovery != nil {
			g.SendByte(recovery)
		}
		cent, errCent := wallet.Service.Cent(g89.secWebSocketKey)
		if errCent != nil {
			logger.Service.Zap.Errorw(atm.Atm_GET_CENT_FAILED,
				"GameUser", g89.secWebSocketKey,
				"Error", errCent,
			)
			errorcode.Service.Fatal(g89.secWebSocketKey, atm.Atm_GET_CENT_FAILED)
		}
		balance, errBalance := wallet.Service.Balance(g89.secWebSocketKey)
		if errBalance != nil {
			logger.Service.Zap.Errorw(GameUser89_GET_CENT_FAILED,
				"GameUser", g89.secWebSocketKey,
				"BankerUuid", g89.bankerUuid,
				"GameRoomUuid", g89.gameRoomUuid,
				"IsWaiting", g89.isWaiting,
				"IsGaming", g89.isGaming,
			)
			errorcode.Service.Fatal(g89.secWebSocketKey, GameUser89_GET_CENT_FAILED)
			return
		}

		dataByte := action.Payload()[0].([]byte)

		data := &lobby_setting89_proto.ConfigRecall{}

		if err := proto.Unmarshal(dataByte, data); err != nil {
			logger.Service.Zap.Errorw(lobbysetting.LobbySetting_CONFIG_RECALL_PROTO_INVALID,
				"GameUser", g89.secWebSocketKey,
			)
			errorcode.Service.Fatal(g89.secWebSocketKey, lobbysetting.LobbySetting_CONFIG_RECALL_PROTO_INVALID)
			return
		}
		totalBlance := balance + cent
		data.Cent = cent
		data.Balance = totalBlance
		data.PlayerInfo = &auth_proto.PlayerInfo{
			Id:      g89.secWebSocketKey,
			Balance: balance,
			Name:    g89.profile.MemberName,
			Avatar:  g89.profile.Avatar,
			Visible: nil,
		}

		if g89.isGaming {
			data.StatusCode = common_proto.Status_kInvalid
			dataByte, _ := proto.Marshal(data)
			g.SendByte(dataByte)
			return
		}

		if data.StatusCode == common_proto.Status_kSuccess {
			flux.Send(gameuser.ActionJoinLobbyRoomCall, g89.secWebSocketKey, g89.controllerId, "")
			g89.isWaiting = false
			dataByte, _ := proto.Marshal(data)
			g.SendByte(dataByte)
		}

	case gameuser.ActionJoinLobbyRoomRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		g89.seat = -1
		g89.gameRoomUuid = ""
		g89.gameRoomType = ""
		g89.isWaiting = false
		g89.isGaming = false
		g89.lobbyRoomUuid = action.Payload()[0].(string)

	case gameuser.ActionLeaveLobbyRoomRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		g89.lobbyRoomUuid = ""

	case gamesetting.EMSGID_eGameConfigRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		dataByte := action.Payload()[0].([]byte)

		data := &game_setting89_proto.ConfigRecall{}

		if err := proto.Unmarshal(dataByte, data); err != nil {
			logger.Service.Zap.Errorw(gamesetting.GameSetting_CONFIG_RECALL_PROTO_INVALID,
				"GameUser", g89.secWebSocketKey,
			)
			errorcode.Service.Fatal(g89.secWebSocketKey, gamesetting.GameSetting_CONFIG_RECALL_PROTO_INVALID)

			return
		}

		if data.StatusCode != common_proto.Status_kSuccess {
			g.SendByte(dataByte)
			return
		}

		recovery, isGaming := g89.gameRecovery(gamesetting89.Service.GameId(g89.secWebSocketKey))

		g89.isGaming = isGaming

		if g89.isGaming {
			data.StatusCode = common_proto.Status_kInvalid
			dataByte, _ := proto.Marshal(data)
			g.SendByte(dataByte)
			return
		}

		if recovery != nil {
			g.SendByte(recovery)
		}

		if g89.lobbyRoomUuid != "" {
			flux.Send(lobbyroom.ActionLobbyRoomLeaveCall, g89.secWebSocketKey, g89.controllerId,
				g89.lobbyRoomUuid,
				false,
			)
		}

		if !g89.isWaiting {

			cent, err := wallet.Service.CentCache(g89.secWebSocketKey)
			balance, err := wallet.Service.BalanceCache(g89.secWebSocketKey)

			if err != nil {
				logger.Service.Zap.Errorw("BUG",
					"GameUser", g89.secWebSocketKey,
					"Error", err,
				)
				errorcode.Service.Fatal(g89.secWebSocketKey, GameUser89_GET_CENT_FAILED)
			}

			data.Cent = cent
			data.Balance = balance
			data.PlayerInfo = &auth_proto.PlayerInfo{
				Id:      g89.secWebSocketKey,
				Balance: cent,
				Name:    g89.profile.MemberName,
				Avatar:  g89.profile.Avatar,
				Visible: nil,
			}

			g89.gameConfigRecall = data
			g89.isWaiting = true
			g89.gameRoomType = banker.GAME_ROOM

			flux.Send(gameuser.ActionJoinGameRoomCall, g89.secWebSocketKey, g89.controllerId,
				g89.hostExtId,
				g89.profile.Avatar,
				g89.ipAddress,
			)

		}

	case gameuser.ActionJoinGameRoomRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		gameRoomUuid := action.Payload()[0].(string)
		seat := action.Payload()[1].(int)
		gameRoomType := action.Payload()[2].(string)

		// join game room failed
		if seat == -1 {

			gamerecovery89.Service.Update(
				g89.secWebSocketKey,
				"",
				int32(-1),
				gamesetting89.Service.Rate(g89.secWebSocketKey),
				gamerecovery89.IDLE,
			)
		} else {
			g89.lobbyRoomUuid = ""
			g89.gameRoomUuid = gameRoomUuid
			g89.seat = seat
			g89.isWaiting = true
			g89.isGaming = false
			g89.gameRoomType = gameRoomType
			gamerecovery89.Service.Update(
				g89.secWebSocketKey,
				g89.gameRoomUuid,
				int32(g89.seat),
				gamesetting89.Service.Rate(g89.secWebSocketKey),
				gamerecovery89.IDLE,
			)
		}

		if g89.gameConfigRecall != nil && gameRoomType == banker.GAME_ROOM {
			g89.gameConfigRecall.RoomUuid = g89.gameRoomUuid
			g89.gameConfigRecall.PlayerInfo.Seat = uint32(g89.seat)
			dataByte, _ := proto.Marshal(g89.gameConfigRecall)
			g.SendByte(dataByte)

			flux.Send(auth.EMSGID_eBroadcastPlayerIn, g89.secWebSocketKey, g89.gameRoomUuid, auth_proto.PLAYER_TYPE_GAME)

			return
		}

	case gameuser.ActionLeaveGameRoomRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		g89.gameRoomUuid = ""
		g89.gameRoomType = ""
		g89.seat = -1
		g89.isWaiting = false
		g89.isGaming = false

		gamerecovery89.Service.Update(
			g89.secWebSocketKey,
			g89.gameRoomUuid,
			int32(g89.seat),
			gamesetting89.Service.Rate(g89.secWebSocketKey),
			gamerecovery89.IDLE,
		)

	case errorcode.ActionErrorCode:
		if g89.profile != nil {
			dataByte := action.Payload()[0].([]byte)

			data := &errorcode_proto.Error{}

			proto.Unmarshal(dataByte, data)

			if data.Code == sessionmanager.SessionManager_DUPICATE_SESSION {
				flux.Send(sessionmanager.SessionManager_DUPICATE_SESSION, g89.secWebSocketKey, atm.Service.Id,
					g89.hostExtId,
					g89.profile.MemberId,
				)
			}
		}

		g.SendAction(action)

		flux.Send(auth.ActionUserDisconnect, g89.secWebSocketKey, gameuser.Service.Id, g89.secWebSocketKey)

	case atm.EMSGID_eDepositRecall:
		g.SendAction(action)

	case atm.EMSGID_eWithdrawRecall:
		g.SendAction(action)

	case atm.EMSGID_eInquireRecall:
		g.SendAction(action)

	case banker.EMSGID_eRoundStart:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		dataByte := action.Payload()[0].([]byte)
		gameRoomUuid := string(action.Payload()[1].([]byte))

		g89.isWaiting = false
		g89.isGaming = true

		data := &banker_proto.RoundStart{}

		if err := proto.Unmarshal(dataByte, data); err != nil {
			logger.Service.Zap.Errorw(GameUser89_ROUND_START_PROTO_INVALID,
				"GameUser", g89.secWebSocketKey,
				"GameRoomUuid", gameRoomUuid,
				"Seat", g89.seat,
				"BankerUuid", g89.bankerUuid,
				"IsGaming", g89.isGaming,
				"IsWaiting", g89.isWaiting,
			)
			errorcode.Service.Fatal(g89.secWebSocketKey, GameUser89_ROUND_START_PROTO_INVALID)
			return
		}

		for _, v := range data.PlayerInfos {
			if v.Id == g89.secWebSocketKey {
				g89.seat = int(v.Seat)
				g89.gameRoomUuid = gameRoomUuid
			}
		}

		if g89.seat < 0 || g89.gameRoomUuid == "" || g89.bankerUuid == "" {
			logger.Service.Zap.Errorw("ERROR SEAT",
				"GameUser", g89.secWebSocketKey,
				"GameRoomUuid", gameRoomUuid,
				"Seat", g89.seat,
				"BankerUuid", g89.bankerUuid,
				"IsGaming", g89.isGaming,
				"IsWaiting", g89.isWaiting,
			)
			panic("ERROR SEAT : " + g89.secWebSocketKey)
			return
		}

		flux.Send(idle.ActionIdleTimeoutReset, g89.secWebSocketKey, idle.Service.HashId(g89.secWebSocketKey),
			g89.secWebSocketKey,
			gamesetting89.Service.Idle(g89.secWebSocketKey),
		)

		gamerecovery89.Service.Update(
			g89.secWebSocketKey,
			g89.gameRoomUuid,
			int32(g89.seat),
			gamesetting89.Service.Rate(g89.secWebSocketKey),
			gamerecovery89.GAMING,
		)

		g.SendAction(action)

		logger.Service.Zap.Infow("GameUser89 Round Start",
			"GameUser", g89.secWebSocketKey,
			"GameRoomUuid", g89.gameRoomUuid,
			"Seat", g89.seat,
			"BankerUuid", g89.bankerUuid,
			"AccountingSn", g89.accountingSn,
		)

		if g89.seat != banker.BANKER_SEAT {
			cent, err := wallet.Service.CentCache(g89.secWebSocketKey)

			if err != nil {
				errorcode.Service.Fatal(g89.secWebSocketKey, GameUser89_GET_CENT_FAILED)
			}

			flux.Send(bet.ActionBetStart, g89.secWebSocketKey, bet.Service.Id,
				bet.Builder().
					SetBankerUuid(g89.bankerUuid).
					SetSecWebSocketKey(g89.secWebSocketKey).
					SetGameRoomUuid(g89.gameRoomUuid).
					SetGameRoomType(g89.gameRoomType).
					SetSeat(int32(g89.seat)).
					SetWaitingTime(gamesetting89.Service.BetWaitingTime(g89.secWebSocketKey)).
					SetKind(bet.PLAYER).
					SetRate(gamesetting89.Service.Rate(g89.secWebSocketKey)).
					SetBetList(gamesetting89.Service.BetList(g89.secWebSocketKey)).
					SetCent(cent).
					Build(),
			)
		}

	case banker.EMSGID_eRoundEnd:
		g.RwMutex.Lock()
		g89.bankerUuid = ""
		g89.isWaiting = false
		g89.isGaming = false
		g89.accountingSn = 0
		gamerecovery89.Service.Update(
			g89.secWebSocketKey,
			g89.gameRoomUuid,
			int32(g89.seat),
			gamesetting89.Service.Rate(g89.secWebSocketKey),
			gamerecovery89.IDLE,
		)
		g.RwMutex.Unlock()

		g.SendAction(action)

		g89.balanceLimit()

	case bet.EMSGID_eBetRoundStart:
		g.SendAction(action)

	case bet.EMSGID_eBetRoundEnd:
		g.SendAction(action)

	case bet.EMSGID_eBetRecall:
		betcent := action.Payload()[1].(uint64)
		g.SendAction(action)
		if lobbysetting89.Service.AutoATM(g89.secWebSocketKey) {
			flux.Send(atm.ActionAtmAutoWithdrawBlance, g89.secWebSocketKey, atm.Service.Id, betcent, g89.hostExtId, g89.profile.MemberId)
		}
	case bet.EMSGID_eBroadcastBetRecall:
		g.SendAction(action)
	case bet.EMSGID_eBetTimeout:
		betcent := action.Payload()[1].(uint64)
		g.SendAction(action)
		if lobbysetting89.Service.AutoATM(g89.secWebSocketKey) {
			flux.Send(atm.ActionAtmAutoWithdrawBlance, g89.secWebSocketKey, atm.Service.Id, betcent, g89.hostExtId, g89.profile.MemberId)
		}

	case bet.EMSGID_eBroadcastBetTimeout:
		g.SendAction(action)

	case draw.EMSGID_eDrawTimeout:
		g.SendAction(action)

	case draw.EMSGID_eBroadcastDrawTimeout:
		g.SendAction(action)

	case draw.EMSGID_eDrawRecall:
		g.SendAction(action)

	case draw.EMSGID_eBroadcastDrawRecall:
		g.SendAction(action)

	case draw.EMSGID_eDrawRoundStart:
		g.SendAction(action)

	case draw.EMSGID_eDrawRoundEnd:
		g.SendAction(action)

	case draw.EMSGID_eBroadcastDrawRoundStart:
		g.SendAction(action)

	case draw.EMSGID_eBroadcastDrawRoundEnd:
		g.SendAction(action)

	case banker.ActionBankerDeal:
		dataByte := action.Payload()[0].([]byte)
		isEnd, _ := strconv.ParseBool(string(action.Payload()[1].([]byte)))
		isDrawDelay, _ := strconv.ParseBool(string(action.Payload()[2].([]byte)))

		logger.Service.Zap.Infow("Banker Deal",
			"GameUser", g89.secWebSocketKey,
			"BankerUuid", g89.bankerUuid,
			"GameRoomUuid", g89.gameRoomUuid,
			"Seat", g89.seat,
		)

		if g89.seat < 0 {
			// TODO JOHNNY DEBUG
			panic("BUG error seat id")
		}

		data := &banker_proto.Deal{}

		// TODO JOHNNY error code
		proto.Unmarshal(dataByte, data)

		g.SendAction(action)

		if !isEnd {
			sleepTime := 0

			if isDrawDelay && g89.seat == 0 {
				sleepTime = 2
			}

			if g89.seat == 0 {
				sleepTime = 5
			}

			d := draw.Builder().
				SetBankerUuid(g89.bankerUuid).
				SetSecWebSocketKey(g89.secWebSocketKey).
				SetGameRoomUuid(g89.gameRoomUuid).
				SetGameRoomType(g89.gameRoomType).
				SetSeat(int32(g89.seat)).
				SetSumPoint(data.Cards[g89.seat].SumPoint).
				SetWaitingTime(gamesetting89.Service.DrawWaitingTime(g89.secWebSocketKey)).
				SetKind(draw.PLAYER).
				SetSleepTime(uint32(sleepTime)).
				Build()

			flux.Send(draw.ActionDrawStart, g89.secWebSocketKey, draw.Service.Id, d)
		}

	case banker.ActionBankerStart:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		g89.isWaiting = false
		g89.isGaming = true

		switch action.Payload()[0].(type) {
		case string:
			g89.bankerUuid = action.Payload()[0].(string)

		case []byte:
			g89.bankerUuid = string(action.Payload()[0].([]byte))
			flux.Send(banker.ActionBankerStart, g89.secWebSocketKey, g89.gameRoomUuid, g89.bankerUuid)
		}

		cent, err := wallet.Service.Cent(g89.secWebSocketKey)

		if err != nil {
			errorcode.Service.Fatal(g89.secWebSocketKey, GameUser89_GET_CENT_FAILED)
		}

		if a := accounting.Builder().
			SetSecWebSocketKey(g89.secWebSocketKey).
			SetHostExtId(g89.hostExtId).
			SetGuestEnable(g89.profile.GuestEnable == auth.GuestOn).
			SetHostId(g89.profile.HostId).
			SetGameId(gamesetting89.Service.GameId(g89.secWebSocketKey)).
			SetSubgameId(gamesetting89.Service.RateIndex(g89.secWebSocketKey)).
			SetMemberId(g89.profile.MemberId).
			SetInitCent(cent).
			SetDenom(uint64(gamesetting89.Service.Rate(g89.secWebSocketKey))).
			SetGameModule(gamesetting89.Service.MathModuleId(g89.secWebSocketKey)).
			SetDB(g89.hostExtId).
			SetKind(accounting.PLAYER).
			SetHandler(&accounting89.Accounting89{}).
			Build(); a != nil {

			g89.accountingSn = a.Start.Sn

			isDone := make(chan bool)
			flux.Send(twin.ActionTwinAccountingSn, g89.secWebSocketKey, g89.secWebSocketKey, g89.accountingSn, isDone)

			switch g89.gameRoomType {
			case banker.FRIEND_ROOM:
				flux.Send(banker.ActionBankerAccountingSn, g89.secWebSocketKey, g89.gameRoomUuid, g89.accountingSn)

			case banker.GAME_ROOM:
				flux.Send(banker.ActionBankerAccountingSn, g89.secWebSocketKey, g89.bankerUuid, g89.accountingSn)

			default:
				logger.Service.Zap.Errorw("ERROR TYPE GAME ROOM",
					"GameUser", g89.secWebSocketKey,
					"GameRoom", g89.gameRoomUuid,
					"BankerUuid", g89.bankerUuid,
					"AccountingSN", g89.accountingSn,
				)
				panic("ERROR TYPE GAME ROOM" + g89.secWebSocketKey)
			}

			<-isDone
		}

		if g89.profile.GuestEnable == auth.GuestOn {
			switch g89.gameRoomType {
			case banker.FRIEND_ROOM:
				flux.Send(banker.ActionBankerAccountingSn, g89.secWebSocketKey, g89.gameRoomUuid, g89.accountingSn)

			case banker.GAME_ROOM:
				flux.Send(banker.ActionBankerAccountingSn, g89.secWebSocketKey, g89.bankerUuid, uint64(0))

			default:
				panic("ERROR TYPE GAME ROOM")
			}
		}

		if g89.accountingSn == 0 && g89.profile.GuestEnable == auth.GuestOff {
			logger.Service.Zap.Errorw(GameUser89_ACCOUNTING_SN_ZERO,
				"GameUser", g89.secWebSocketKey,
				"AccountingSn", g89.accountingSn,
				"Guest", g89.profile.GuestEnable,
			)
			errorcode.Service.Fatal(g89.secWebSocketKey, GameUser89_ACCOUNTING_SN_ZERO)
			return
		}

	case probability.EMSGID_eBroadcastResult:
		g.SendAction(action)

	case heartbeat.ActionHeartBeatRecall:
		g.SendAction(action)

	case auth.ActionAuthNotify:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		g89.isWaiting = false
		g89.isGaming = false

		gamerecovery89.Service.Update(
			g89.secWebSocketKey,
			g89.gameRoomUuid,
			int32(g89.seat),
			gamesetting89.Service.Rate(g89.secWebSocketKey),
			gamerecovery89.IDLE,
		)
		cent, err := wallet.Service.CentCache(g89.secWebSocketKey)
		if err != nil {
			errorcode.Service.Fatal(g89.secWebSocketKey, GameUser89_GET_CENT_FAILED)
		}
		if lobbysetting89.Service.AutoATM(g89.secWebSocketKey) && cent > 0 {
			// TODO JOHNNY 以後可能會有要自動儲值幾%的...
			flux.Send(atm.ActionAtmAutoWithdraw, g89.secWebSocketKey, atm.Service.Id, uint8(100), g89.hostExtId, g89.profile.MemberId)
		}
		g.SendAction(action)

	case waitingroom.EMSGID_eWaitingCountdown:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		g89.isWaiting = true
		g89.isGaming = false

		if g89.gameRoomUuid != "" {
			g.SendAction(action)
		}

	case auth.EMSGID_eBroadcastPlayerIn:
		fallthrough
	case auth.EMSGID_eBroadcastPlayerOut:
		switch action.Payload()[0].(type) {
		case [][]byte:
			g89.postman(action, g)

		default:
			g.SendAction(action)
		}

	case friendroom.EMSGID_eFriendRoomJoinRecall:
		dataByte := action.Payload()[0].([]byte)

		data := &friend_room_proto.FriendRoomJoinRecall{}

		proto.Unmarshal(dataByte, data)

		if data.StatusCode == common_proto.Status_kSuccess {
			g89.gameRoomUuid = action.Key().From()
			g89.gameRoomType = banker.FRIEND_ROOM
		} else {
			if lobbysetting89.Service.AutoATM(g89.secWebSocketKey) {
				flux.Send(atm.ActionAtmAutoWithdraw, g89.secWebSocketKey, atm.Service.Id, uint8(100), g89.hostExtId, g89.profile.MemberId)
				time.Sleep(2 * time.Second)
			}
		}
		cent, err := wallet.Service.CentCache(g89.secWebSocketKey)
		if err != nil {
			errorcode.Service.Fatal(g89.secWebSocketKey, GameUser89_GET_CENT_FAILED)
		}
		balance, errBalance := wallet.Service.BalanceCache(g89.secWebSocketKey)
		if errBalance != nil {
			errorcode.Service.Fatal(g89.secWebSocketKey, GameUser89_GET_CENT_FAILED)
		}
		data.GameConfigRecall.Cent = cent
		data.GameConfigRecall.Balance = balance
		newDataByte, _ := proto.Marshal(data)
		g.SendByte(newDataByte)
	case friendroom.EMSGID_eFriendRoomLeaveRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		flux.Send(gameuser.ActionLeaveGameRoomCall, g89.secWebSocketKey, g89.gameRoomUuid, g89.secWebSocketKey)

		gamerecovery89.Service.Update(
			g89.secWebSocketKey,
			g89.gameRoomUuid,
			int32(g89.seat),
			gamesetting89.Service.Rate(g89.secWebSocketKey),
			gamerecovery89.IDLE,
		)

		g89.gameRoomUuid = ""
		g89.gameRoomType = ""
		g89.seat = -1
		g89.isWaiting = false
		g89.isGaming = false
		g.SendAction(action)

	case friendroom.EMSGID_eFriendRoomHostChanged:
		g.SendAction(action)

	case friendroom.EMSGID_eFriendRoomDestroy:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()
		if lobbysetting89.Service.AutoATM(g89.secWebSocketKey) {
			// TODO JOHNNY 以後可能會有要自動儲值幾%的...
			flux.Send(atm.ActionAtmAutoWithdraw, g89.secWebSocketKey, atm.Service.Id, uint8(100), g89.hostExtId, g89.profile.MemberId)
		}
		flux.Send(gameuser.ActionLeaveGameRoomCall, g89.secWebSocketKey, g89.gameRoomUuid, g89.secWebSocketKey)

		friendroom.Service.Delete(g89.secWebSocketKey)

		gamerecovery89.Service.Update(
			g89.secWebSocketKey,
			g89.gameRoomUuid,
			int32(g89.seat),
			gamesetting89.Service.Rate(g89.secWebSocketKey),
			gamerecovery89.IDLE,
		)

		g89.gameRoomUuid = ""
		g89.gameRoomType = ""
		g89.seat = -1
		g89.isWaiting = false
		g89.isGaming = false

		g.SendAction(action)

	case atm.EMSGID_eAutoTransferRecall:
		g.SendAction(action)
	case atm.EMSGID_eAutoTransferOutRecall:
		g.SendAction(action)
	case draw.ActionDrawNext:
		gameRoomUuid := string(action.Payload()[0].([]byte))

		seat, _ := strconv.Atoi(string(action.Payload()[1].([]byte)))

		if seat < g89.seat {
			flux.Send(draw.ActionDrawNext, g89.secWebSocketKey, draw.Service.Id, gameRoomUuid, int32(seat))
		}

	case waitingroom.EMSGID_eWaitingRoundEnd:
		g.SendAction(action)
	}
}

func (g89 *GameUser89) postman(action *flux.Action, g *gameuser.GameUser) {
	dataByte := action.Payload()[0].([][]byte)
	g.SendByte(dataByte[0])
}

func (g89 *GameUser89) balanceLimit() (cent uint64) {
	if g89.gameRoomUuid == "" {
		return
	}

	blance, blanceErr := wallet.Service.Balance(g89.secWebSocketKey)
	if blanceErr != nil {
		logger.Service.Zap.Errorw(GameUser89_GET_CENT_FAILED,
			"GameUser", g89.secWebSocketKey,
			"BankerUuid", g89.bankerUuid,
			"GameRoomUuid", g89.gameRoomUuid,
			"IsWaiting", g89.isWaiting,
			"IsGaming", g89.isGaming,
		)
		errorcode.Service.Fatal(g89.secWebSocketKey, GameUser89_GET_CENT_FAILED)
		return
	}
	cent, centErr := wallet.Service.Cent(g89.secWebSocketKey)

	if centErr != nil {
		logger.Service.Zap.Errorw(GameUser89_GET_CENT_FAILED,
			"GameUser", g89.secWebSocketKey,
			"BankerUuid", g89.bankerUuid,
			"GameRoomUuid", g89.gameRoomUuid,
			"IsWaiting", g89.isWaiting,
			"IsGaming", g89.isGaming,
		)
		errorcode.Service.Fatal(g89.secWebSocketKey, GameUser89_GET_CENT_FAILED)
		return 0
	}

	l := gamesetting89.Service.BalanceLimit(g89.secWebSocketKey)

	if cent+blance < uint64(l) {
		logger.Service.Zap.Infow("No Money",
			"GameUser", g89.secWebSocketKey,
			"BankerUuid", g89.bankerUuid,
			"Cent", cent,
			"BalanceLimit", l,
			"GameRoomUuid", g89.gameRoomUuid,
			"IsWaiting", g89.isWaiting,
			"IsGaming", g89.isGaming,
		)
		if lobbysetting89.Service.AutoATM(g89.secWebSocketKey) {
			// TODO JOHNNY 以後可能會有要自動儲值幾%的...
			flux.Send(atm.ActionAtmAutoWithdraw, g89.secWebSocketKey, atm.Service.Id, uint8(100), g89.hostExtId, g89.profile.MemberId)
		}
		flux.Send(auth.EMSGID_eBroadcastPlayerOut, g89.secWebSocketKey, g89.gameRoomUuid, auth.Service.BroadcastPlayerOut(
			g89.gameRoomUuid,
			g89.secWebSocketKey,
			g89.profile.MemberName,
			g89.profile.Avatar,
			uint32(g89.seat),
			cent,
		))

		time.Sleep(1 * time.Second)

		switch g89.gameRoomType {
		case banker.FRIEND_ROOM:
			flux.Send(gameuser.ActionLeaveGameRoomCall, g89.secWebSocketKey, g89.gameRoomUuid, g89.secWebSocketKey)

			isDone := make(chan bool)
			flux.Send(friendroom.ActionNoEnoughCredit, g89.secWebSocketKey, g89.gameRoomUuid, isDone)

			<-isDone

			friendroom.Service.Delete(g89.secWebSocketKey)

		case banker.GAME_ROOM:
			flux.Send(gameuser.ActionLeaveGameRoomCall, g89.secWebSocketKey, g89.controllerId, g89.gameRoomUuid)

		default:
			panic("ERROR  GAME ROOM TYPE")
		}
	} else {

		if blance > 0 {
			if lobbysetting89.Service.AutoATM(g89.secWebSocketKey) {
				// TODO JOHNNY 以後可能會有要自動儲值幾%的...
				flux.Send(atm.ActionAtmAutoDeposit, g89.secWebSocketKey, atm.Service.Id, uint8(100), g89.hostExtId, g89.profile.MemberId)

			}
		}
	}
	return cent + blance
}

func (g89 *GameUser89) gameRecovery(gameId string) ([]byte, bool) {
	if data := gamerecovery89.Service.Check(
		gamerecovery.Builder().
			SetSecWebSocketKey(g89.secWebSocketKey).
			SetHostId(g89.profile.HostId).
			SetHostExtId(g89.hostExtId).
			SetServerId(gamerecovery89.Service.ServerId).
			SetGameId(gameId).
			SetMemberId(g89.profile.MemberId).
			SetGuest(g89.profile.GuestEnable == auth.GuestOn).
			SetDB(g89.hostExtId).
			Build(),
	); data != nil {
		logger.Service.Zap.Infow("Check Game Recovery",
			"GameUser", g89.secWebSocketKey,
			"GameRoomUuid", g89.gameRoomUuid,
			"BankerUuid", g89.bankerUuid,
			"Status", data.Snapshot.Status == gamerecovery89.GAMING,
			"IsGaming", g89.isGaming,
			"IsWaiting", g89.isWaiting,
		)

		dataByte, _ := proto.Marshal(data)

		return dataByte, data.Snapshot.Status == gamerecovery89.GAMING
	}
	return nil, false
}

func (g89 *GameUser89) CleanDataHandler(g *gameuser.GameUser) {
	if g89.profile != nil {
		session.Service.End(
			g89.secWebSocketKey,
			g89.profile.HostId,
			g89.hostExtId,
			g89.profile.MemberId,
			0, // TODO JOHNNY need implement
		)
	} else {
		logger.Service.Zap.Warnw(gameuser.GameUser_PROFILE_NIL,
			"GameUser", g89.secWebSocketKey,
			"HostExtId", g89.hostExtId,
			"IsGaming", g89.isGaming,
			"IsWaiting", g89.isWaiting,
		)
	}

	if !g89.isGaming {
		flux.Send(twin.ActionTwinDestroy, g89.secWebSocketKey, g89.secWebSocketKey, g89.gameRoomUuid, g89.gameRoomType)
	}
	sessionmanager.Service.End(g89.secWebSocketKey, g89.hostExtId)

	flux.Send(idle.ActionIdleTimeoutStop, g89.secWebSocketKey, idle.Service.Id, g89.secWebSocketKey)
	lobbysetting.Service.Delete(g89.secWebSocketKey)
	mediator.Service.Delete(g89.secWebSocketKey)

}

func (g89 *GameUser89) leaveRooms() {
	logger.Service.Zap.Infow("leaveRooms",
		"GameUser", g89.secWebSocketKey,
		"GameRoomUuid", g89.gameRoomUuid,
		"LobbyRoomUuid", g89.lobbyRoomUuid,
	)
	g89.isDestroy = true
	if g89.isGaming {
		flux.Send(twin.ActionTwinActive, g89.secWebSocketKey, g89.secWebSocketKey, true)
	}

	if g89.gameRoomUuid != "" {
		if g89.isWaiting {
			flux.Send(auth.EMSGID_eBroadcastPlayerOut, g89.secWebSocketKey, g89.gameRoomUuid, auth.Service.BroadcastPlayerOut(
				g89.gameRoomUuid,
				g89.secWebSocketKey,
				g89.profile.MemberName,
				g89.profile.Avatar,
				uint32(g89.seat),
				uint64(0),
			))
			flux.Send(gameuser.ActionLeaveGameRoomCall, g89.secWebSocketKey, g89.controllerId, g89.gameRoomUuid)
		}
	} else {
		flux.Send(gameuser.ActionGameUserDelete, g89.secWebSocketKey, gameuser.Service.Id, g89.secWebSocketKey)
	}

	if g89.lobbyRoomUuid != "" {
		flux.Send(gameuser.ActionLeaveLobbyRoomCall, g89.secWebSocketKey, g89.controllerId, g89.lobbyRoomUuid, true)
	} else {
		flux.Send(gameuser.ActionGameUserDelete, g89.secWebSocketKey, gameuser.Service.Id, g89.secWebSocketKey)
	}
}
