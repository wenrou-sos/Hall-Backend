package gameuserU

import (
	"crypto/rand"
	"math/big"
	"strconv"
	"u-game-server/application/accountingU"
	"u-game-server/application/atm"
	atm_proto "u-game-server/application/atm/proto"
	"u-game-server/application/banker"
	banker_proto "u-game-server/application/banker/proto"
	"u-game-server/application/filter"
	"u-game-server/application/friendroom"
	friend_room_proto "u-game-server/application/friendroom/proto"
	"u-game-server/application/gameroom"
	"u-game-server/application/gamesettingU"
	game_settinU_proto "u-game-server/application/gamesettingU/proto"
	"u-game-server/application/lobbysettingU"
	lobby_settingU_proto "u-game-server/application/lobbysettingU/proto"
	lobby_setting_u_proto "u-game-server/application/lobbysettingU/proto"
	"u-game-server/application/playerinfo"
	"u-game-server/application/twin"
	"u-game-server/domain/draw"
	"u-game-server/domain/gamerecoveryU"
	gamerecoveryU_proto "u-game-server/domain/gamerecoveryU/proto"
	"u-game-server/domain/playcards"
	play_cards_proto "u-game-server/domain/playcards/proto"
	"u-game-server/domain/probability"
	"u-game-server/domain/round"
	"u-game-server/domain/waitingroom"
	"u-game-server/domain/walletU"

	"gitlab.iplaystar.net/game-server/blacklist"
	game_setting_proto "gitlab.iplaystar.net/game-server/game-setting/proto"

	probability_proto "u-game-server/domain/probability/proto"
	commonU_proto "u-game-server/models/proto"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/accounting"
	"gitlab.iplaystar.net/game-server/auth"
	auth_proto "gitlab.iplaystar.net/game-server/auth/proto"
	"gitlab.iplaystar.net/game-server/avatar"
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
	"gitlab.iplaystar.net/game-server/maintain"
	"gitlab.iplaystar.net/game-server/mediator"
	"gitlab.iplaystar.net/game-server/postman"
	"gitlab.iplaystar.net/game-server/session"
	sessionmanager "gitlab.iplaystar.net/game-server/session-manager"
	"gitlab.iplaystar.net/game-server/wallet"
)

type GameUserU struct {
	controllerId        string
	secWebSocketKey     string
	bankerUuid          string
	hostExtId           string
	gameRoomUuid        string
	lobbyRoomUuid       string
	gameRoomType        string
	ipAddress           string
	gameID              string
	subGameId           int32
	seat                int
	profile             *auth.MemberInfo
	gameConfigRecall    *game_settinU_proto.ConfigRecall
	isGaming            bool
	isWaiting           bool
	isDestroy           bool
	accountingSn        uint64
	hands               []int
	card                int
	blacklistValue      uint32
	canDeleteAccounting bool

	//banker info
	lastCard  int
	lastColor int
	lastDraw  int
	penalty   int
}

func New(controllerId, secWebSocketKey, hostExtId, remoteAddr string) *GameUserU {
	return &GameUserU{
		controllerId:        controllerId,
		secWebSocketKey:     secWebSocketKey,
		hostExtId:           hostExtId,
		ipAddress:           remoteAddr,
		gameID:              "",
		subGameId:           -1,
		seat:                -1,
		profile:             nil,
		gameConfigRecall:    nil,
		isGaming:            false,
		isWaiting:           false,
		isDestroy:           false,
		accountingSn:        0,
		card:                0,
		blacklistValue:      0,
		canDeleteAccounting: false,
	}
}

func (gU *GameUserU) MsgHandler(g *gameuser.GameUser, msg []byte) {
	v, err := filter.FindActionName(msg)
	if err != nil {
		logger.Service.Zap.Errorw(gameuser.GameUser_MSGID_PROTO_INVALID,
			"GameUserU", gU.secWebSocketKey,
			"Error", err,
		)
		errorcode.Service.Fatal(gU.secWebSocketKey, gameuser.GameUser_MSGID_PROTO_INVALID)
		return
	}

	logger.Service.Zap.Infow(v,
		"GameUser", gU.secWebSocketKey,
		"BankerUuid", gU.bankerUuid,
		"LobbyRoomUuid", gU.lobbyRoomUuid,
		"GameRoomUuid", gU.gameRoomUuid,
		"Seat", gU.seat,
		"ip", gU.ipAddress,
	)
	switch v {
	case auth.EMSGID_eLoginCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		flux.Send(auth.EMSGID_eLoginCall, gU.secWebSocketKey, auth.Service.Id, msg)

	case atm.EMSGID_eDepositCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if gU.profile != nil {
			if gU.profile.WalletType == wallet.CategoryHost {
				data := &atm_proto.DepositCall{}

				if err := proto.Unmarshal(msg, data); err != nil {
					logger.Service.Zap.Errorw("3000_5",
						"GameUser", gU.secWebSocketKey,
					)
					errorcode.Service.Fatal(gU.secWebSocketKey, "3000_5")
					return
				}

				if gU.profile.MemberType == 1 {
					data.SubgameId += 6
					msg, _ = proto.Marshal(data)
				}
				wallet.Service.SetGameIdAndSubGameId(gU.secWebSocketKey, data.GameId, int(data.SubgameId))

				balance, balanceerr := wallet.Service.Balance(gU.secWebSocketKey)

				if balanceerr != nil {
					errorcode.Service.Fatal(gU.secWebSocketKey, GameUserU_GET_CENT_FAILED)
					return
				}

				if a := accounting.Builder().
					SetSecWebSocketKey(gU.secWebSocketKey).
					SetHostExtId(gU.hostExtId).
					SetGuestEnable(gU.profile.GuestEnable == auth.GuestOn).
					SetHostId(gU.profile.HostId).
					SetGameId(data.GameId).
					SetSubgameId(data.SubgameId).
					SetMemberId(gU.profile.MemberId).
					SetInitCent(balance).
					SetDB(gU.hostExtId).
					SetKind(accounting.PLAYER).
					SetHandler(&accountingU.AccountingU{}).
					Build(); a != nil {

					gU.accountingSn = a.Start.Sn
				}

				if gU.accountingSn == 0 {
					logger.Service.Zap.Errorw(GameUserU_ACCOUNTING_SN_ZERO,
						"GameUser", gU.secWebSocketKey,
						"AccountingSn", gU.accountingSn,
						"Guest", gU.profile.GuestEnable,
					)
					errorcode.Service.Fatal(gU.secWebSocketKey, GameUserU_ACCOUNTING_SN_ZERO)
					return
				}

				isDone := make(chan bool)
				flux.Send(twin.ActionTwinAccountingSn, gU.secWebSocketKey, gU.secWebSocketKey, gU.accountingSn, isDone, gU.blacklistValue)
				<-isDone
			}

			flux.Send(atm.EMSGID_eDepositCall, gU.secWebSocketKey, atm.Service.Id, msg, gU.hostExtId, gU.profile.MemberId, gU.accountingSn)

		} else {
			logger.Service.Zap.Warnw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", gU.secWebSocketKey,
				"HostExtId", gU.hostExtId,
				"IsGaming", gU.isGaming,
				"IsWaiting", gU.isWaiting,
			)
		}

	case atm.EMSGID_eWithdrawCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if gU.isGaming || gU.isWaiting || gU.gameRoomUuid != "" {
			logger.Service.Zap.Errorw(GameUserU_WITHDRAW_CALL_INVALID,
				"GameUser", gU.secWebSocketKey,
				"GameRoomUuid", gU.gameRoomUuid,
				"IsGaming", gU.isGaming,
				"IsWaiting", gU.isWaiting,
			)
			errorcode.Service.Fatal(gU.secWebSocketKey, GameUserU_WITHDRAW_CALL_INVALID)
			return
		}

		if gU.profile != nil {
			flux.Send(atm.EMSGID_eWithdrawCall, gU.secWebSocketKey, atm.Service.Id, msg, gU.hostExtId, gU.profile.MemberId)
		} else {
			logger.Service.Zap.Errorw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", gU.secWebSocketKey,
				"HostExtId", gU.hostExtId,
				"GameRoomUuid", gU.gameRoomUuid,
				"IsGaming", gU.isGaming,
				"IsWaiting", gU.isWaiting,
			)
			errorcode.Service.Fatal(gU.secWebSocketKey, gameuser.GameUser_PROFILE_NIL)
		}

	case atm.EMSGID_eInquireCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if gU.profile != nil {
			flux.Send(atm.EMSGID_eInquireCall, gU.secWebSocketKey, atm.Service.Id, msg, gU.hostExtId, gU.profile.MemberId)
		} else {
			logger.Service.Zap.Errorw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", gU.secWebSocketKey,
				"HostExtId", gU.hostExtId,
				"GameRoomUuid", gU.gameRoomUuid,
				"IsGaming", gU.isGaming,
				"IsWaiting", gU.isWaiting,
			)
			errorcode.Service.Fatal(gU.secWebSocketKey, gameuser.GameUser_PROFILE_NIL)
		}

	case lobbysetting.EMSGID_eLobbyConfigCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if gU.profile != nil {
			flux.Send(lobbysetting.EMSGID_eLobbyConfigRecall, gU.secWebSocketKey, gU.secWebSocketKey,
				lobbysetting.Service.EMSGID_eLobbyConfigCall(
					gU.secWebSocketKey,
					gU.profile.MemberId,
					gU.profile.GuestEnable,
					msg,
				),
			)
		} else {
			logger.Service.Zap.Errorw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", gU.secWebSocketKey,
				"HostExtId", gU.hostExtId,
				"GameRoomUuid", gU.gameRoomUuid,
				"IsGaming", gU.isGaming,
				"IsWaiting", gU.isWaiting,
			)
			errorcode.Service.Fatal(gU.secWebSocketKey, gameuser.GameUser_PROFILE_NIL)
		}

	case gamesetting.EMSGID_eGameConfigCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if gU.isGaming || gU.isWaiting || gU.gameRoomUuid != "" {
			logger.Service.Zap.Infow(gamesetting.EMSGID_eGameConfigCall,
				"GameUser", gU.secWebSocketKey,
				"GameRoomUuid", gU.gameRoomUuid,
				"IsGaming", gU.isGaming,
				"IsWaiting", gU.isWaiting,
			)
			return
		}

		if gU.profile != nil {
			if gU.profile.MemberType == 1 {
				data := &game_setting_proto.ConfigCall{}

				if err := proto.Unmarshal(msg, data); err != nil {
					logger.Service.Zap.Errorw("601_0",
						"GameUser", gU.secWebSocketKey,
						"MemberId", gU.profile.MemberId,
					)
					errorcode.Service.Fatal(gU.secWebSocketKey, "601_0")
					return
				}

				data.SubgameId += 6
				msg, _ = proto.Marshal(data)
			}

			flux.Send(gamesetting.EMSGID_eGameConfigRecall, gU.secWebSocketKey, gU.secWebSocketKey,
				gamesetting.Service.EMSGID_eGameConfigCall(
					gU.secWebSocketKey,
					gU.profile.MemberId,
					gU.profile.GuestEnable,
					msg,
				),
			)
		} else {
			logger.Service.Zap.Errorw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", gU.secWebSocketKey,
				"HostExtId", gU.hostExtId,
				"GameRoomUuid", gU.gameRoomUuid,
				"IsGaming", gU.isGaming,
				"IsWaiting", gU.isWaiting,
			)
			errorcode.Service.Fatal(gU.secWebSocketKey, gameuser.GameUser_PROFILE_NIL)
		}

	case heartbeat.ActionHeartBeatCall:
		flux.Send(heartbeat.ActionHeartBeatCall, gU.secWebSocketKey, heartbeat.Service.Id, msg)

	case draw.EMSGID_eDrawCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if !gU.isGaming || !round.Service.IsValid(gU.secWebSocketKey, draw.EMSGID_eDrawCall) {
			return
		}

		flux.Send(round.ActionRoundStateChange, gU.secWebSocketKey, round.Service.Id, gU.secWebSocketKey, round.STATE_DRAW)

		flux.Send(draw.EMSGID_eDrawCall, gU.secWebSocketKey, draw.Service.Id, msg)

		flux.Send(idle.ActionIdleTimeoutReset, gU.secWebSocketKey, idle.Service.HashId(gU.secWebSocketKey),
			gU.secWebSocketKey,
			gamesettingU.Service.Idle(gU.secWebSocketKey),
		)

	case playcards.EMSGID_ePlayCardsCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		data := &play_cards_proto.PlayCardsCall{}
		err := proto.Unmarshal(msg, data)
		if !gU.isGaming || !round.Service.IsValid(gU.secWebSocketKey, playcards.EMSGID_ePlayCardsCall) || err != nil || len(data.Cards) == 0 {
			return
		}

		if ok := probability.Service.CheckCardNormal(int(data.Cards[0]), gU.lastCard, gU.lastDraw, gU.lastColor, gU.penalty); ok {
			for _, c := range gU.hands {
				if data.Cards[0] == int32(c) {
					flux.Send(round.ActionRoundStateChange, gU.secWebSocketKey, round.Service.Id, gU.secWebSocketKey, round.STATE_PLAYCARD)

					flux.Send(playcards.EMSGID_ePlayCardsCall, gU.secWebSocketKey, playcards.Service.Id, msg)

					flux.Send(idle.ActionIdleTimeoutReset, gU.secWebSocketKey, idle.Service.HashId(gU.secWebSocketKey),
						gU.secWebSocketKey,
						gamesettingU.Service.Idle(gU.secWebSocketKey),
					)
					return
				}
			}
		}
		logger.Service.Zap.Errorw(playcards.PlayCards_CHECK_CARD_FAILED,
			"PlayCard", data.Cards[0],
			"LastCard", gU.lastCard,
			"LastDraw", gU.lastDraw,
			"LastColor", gU.lastColor,
			"Penalty", gU.penalty,
			"Hands", gU.hands,
		)
		errorcode.Service.Fatal(gU.secWebSocketKey, playcards.PlayCards_CHECK_CARD_FAILED)

	case atm.EMSGID_eAutoTransferCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if gU.isGaming || gU.lobbyRoomUuid == "" {
			logger.Service.Zap.Errorw(GameUserU_AUTO_TRANSFER_CALL_INVALID,
				"GameUser", gU.secWebSocketKey,
				"LobbyRoomUuid", gU.lobbyRoomUuid,
				"GameRoomUuid", gU.gameRoomUuid,
				"IsGaming", gU.isGaming,
				"IsWaiting", gU.isWaiting,
			)
			errorcode.Service.Fatal(gU.secWebSocketKey, GameUserU_AUTO_TRANSFER_CALL_INVALID)
			return
		}

		if gU.profile.MemberType == 1 {
			data := &atm_proto.AutoTransferCall{}

			if err := proto.Unmarshal(msg, data); err != nil {
				logger.Service.Zap.Errorw("3000_5",
					"GameUser", gU.secWebSocketKey,
					"MemberId", gU.profile.MemberId,
				)
				errorcode.Service.Fatal(gU.secWebSocketKey, "3000_5")
				return
			}

			data.SubgameId += 6
			msg, _ = proto.Marshal(data)
		}

		flux.Send(atm.EMSGID_eAutoTransferCall, gU.secWebSocketKey, atm.Service.Id, msg, gU.hostExtId, gU.profile.MemberId)

	case atm.EMSGID_eAutoTransferOutCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if gU.isGaming || gU.lobbyRoomUuid == "" {
			logger.Service.Zap.Errorw(GameUserU_AUTO_TRANSFER_CALL_INVALID,
				"GameUser", gU.secWebSocketKey,
				"LobbyRoomUuid", gU.lobbyRoomUuid,
				"GameRoomUuid", gU.gameRoomUuid,
				"IsGaming", gU.isGaming,
				"IsWaiting", gU.isWaiting,
			)
			errorcode.Service.Fatal(gU.secWebSocketKey, GameUserU_AUTO_TRANSFER_CALL_INVALID)
			return
		}

		flux.Send(atm.EMSGID_eAutoTransferOutCall, gU.secWebSocketKey, atm.Service.Id, msg, gU.hostExtId, gU.profile.MemberId)

	case friendroom.EMSGID_eFriendRoomJoinCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if gU.isGaming || gU.gameRoomUuid != "" || gU.profile.GuestEnable == auth.GuestOn {
			logger.Service.Zap.Infow(friendroom.EMSGID_eFriendRoomJoinCall,
				"GameUser", gU.secWebSocketKey,
				"GameRoomUuid", gU.gameRoomUuid,
				"GameRoomType", gU.gameRoomType,
				"IsGaming", gU.isGaming,
				"IsWaiting", gU.isWaiting,
				"GuestEnable", gU.profile.GuestEnable,
			)
			return
		}

		if v := friendroom.Service.Get(gU.secWebSocketKey); v != nil {
			v.EMSGID_eFriendRoomJoinCall(msg, gU.hostExtId, gU.ipAddress)
		} else {
			friendroom.Service.Create(friendroom.Builder().
				SetSecWebSocketKey(gU.secWebSocketKey).
				SetMemberId(gU.profile.MemberId).
				SetMemberName(gU.profile.MemberName).
				SetAvatar(gU.profile.Avatar).
				SetHostExtId(gU.hostExtId).
				SetKind(friendroom.PLAYER).
				SetGuest(gU.profile.GuestEnable).
				Build(),
			).EMSGID_eFriendRoomJoinCall(msg, gU.hostExtId, gU.ipAddress)
		}

	case friendroom.EMSGID_eFriendRoomLeaveCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if gU.isGaming || gU.profile.GuestEnable == auth.GuestOn {
			logger.Service.Zap.Infow(friendroom.EMSGID_eFriendRoomLeaveCall,
				"GameUser", gU.secWebSocketKey,
				"GameRoomUuid", gU.gameRoomUuid,
				"GameRoomType", gU.gameRoomType,
				"IsGaming", gU.isGaming,
				"IsWaiting", gU.isWaiting,
				"GuestEnable", gU.profile.GuestEnable,
			)
			return
		}

		if v := friendroom.Service.Get(gU.secWebSocketKey); v != nil {
			v.EMSGID_eFriendRoomLeaveCall(msg)
		}

	case friendroom.EMSGID_eFriendRoomGameStart:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if gU.profile.GuestEnable == auth.GuestOn {
			logger.Service.Zap.Infow(friendroom.EMSGID_eFriendRoomGameStart,
				"GameUser", gU.secWebSocketKey,
				"GameRoomUuid", gU.gameRoomUuid,
				"GameRoomType", gU.gameRoomType,
				"IsGaming", gU.isGaming,
				"IsWaiting", gU.isWaiting,
				"GuestEnable", gU.profile.GuestEnable,
			)
			return
		}

		if v := friendroom.Service.Get(gU.secWebSocketKey); v != nil {
			v.EMSGID_eFriendRoomGameStart(msg)
		}

	case avatar.EMSGID_eAvatarCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		avatar.Service.EMSGID_eAvatarCall(msg, gU.secWebSocketKey, 18)

	case banker.EMSGID_eKeepCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if !gU.isGaming || !round.Service.IsValid(gU.secWebSocketKey, banker.EMSGID_eKeepCall) {
			return
		}

		flux.Send(banker.EMSGID_eKeepCall, gU.secWebSocketKey, gU.bankerUuid, msg)

		flux.Send(idle.ActionIdleTimeoutReset, gU.secWebSocketKey, idle.Service.HashId(gU.secWebSocketKey),
			gU.secWebSocketKey,
			gamesettingU.Service.Idle(gU.secWebSocketKey),
		)
	}
}

func (gU *GameUserU) DeferRunReadMessageHandler(g *gameuser.GameUser) {
	if gU.isGaming {
		flux.Send(twin.ActionTwinActive, gU.secWebSocketKey, gU.secWebSocketKey, true)
	}
}

func (gU *GameUserU) DeferRunWriteMessageHandler(g *gameuser.GameUser) {
	gU.leaveRooms()
}

func (gU *GameUserU) FluxActionHandler(action *flux.Action, g *gameuser.GameUser) {

	logger.Service.Zap.Infow(action.Key().Name(),
		"GameUser", gU.secWebSocketKey,
		"BankerUuid", gU.bankerUuid,
		"LobbyRoomUuid", gU.lobbyRoomUuid,
		"GameRoomUuid", gU.gameRoomUuid,
		"Seat", gU.seat,
	)
	if gU.secWebSocketKey != action.Key().To() {
		return
	}
	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:
		logger.Service.Zap.Infow("GameUserU Flux Registered",
			"GameUserU", gU.secWebSocketKey,
			"HostExtId", gU.hostExtId,
		)

	case auth.ActionLoginFailed:
		logger.Service.Zap.Errorw(auth.Auth_LOGIN_FAILED,
			"GameUserU", gU.secWebSocketKey,
		)
		errorcode.Service.Fatal(gU.secWebSocketKey, auth.Auth_LOGIN_FAILED)

	case auth.ActionLoginSuccess:
		gU.profile = action.Payload()[0].(*auth.MemberInfo)

		flux.Send(atm.ActionAtmStart, gU.secWebSocketKey, atm.Service.Id, gU.hostExtId, gU.profile.MemberId)

		logger.Service.Zap.Infow("GameUserU Login Success",
			"GameUserU", gU.secWebSocketKey,
			"HostId", gU.profile.HostId,
			"HostExtId", gU.hostExtId,
			"MemberId", gU.profile.MemberId,
			"MemberName", gU.profile.MemberName,
			"Avatar", gU.profile.Avatar,
		)

		wallet.Service.Open(
			wallet.Builder().
				SetSecWebSocketKey(gU.secWebSocketKey).
				SetHostId(gU.profile.HostId).
				SetHostExtId(gU.hostExtId).
				SetMemberId(gU.profile.MemberId).
				SetMemberName(gU.profile.MemberName).
				SetBalance(gU.profile.Balance).
				SetCategory(gU.profile.WalletType).
				SetPurposeMajor(wallet.WalletSharedFish).
				SetPurposeMinor(5).
				SetGuest(gU.profile.GuestEnable).
				SetHandler(gU).
				SetDB(gU.hostExtId).
				SetToken(gU.profile.Token).
				Build(),
		)

		if gU.profile.Avatar == "" && gU.profile.GuestEnable == auth.GuestOff {
			gU.profile.Avatar = avatar.Service.Create(
				gU.secWebSocketKey,
				gU.hostExtId,
				gU.profile.HostId,
				gU.profile.MemberId,
			)
		}

		twin.New(
			gU.secWebSocketKey,
			gU.bankerUuid,
			gU.profile.MemberId,
			gU.profile.HostId,
			gU.hostExtId,
			gU.gameRoomUuid,
			gU.controllerId,
			gU.profile.Avatar,
			gU.subGameId,
			gU.seat,
			gU.profile.GuestEnable,
			gU.accountingSn,
		)

		if p := playerinfo.Service.GetOrCreate(gU.profile.HostId, gU.profile.MemberId, gU.secWebSocketKey); p != nil {
			wallet.Service.SetToken(p.SecWebSocketKey, gU.profile.Token)
		}

	case wallet.ActionWalletOpened:

		if gU.profile.GuestEnable == auth.GuestOff {
			fluxData := &flux_proto.FluxAction{
				Name: wallet.ActionWalletOpened,
				From: walletU.Service.Id,
				To:   postman.SERVER_TRIGGER,
			}

			fluxData.Payload = append(fluxData.Payload, []byte(gU.secWebSocketKey))
			fluxData.Payload = append(fluxData.Payload, []byte(gU.profile.HostId))
			fluxData.Payload = append(fluxData.Payload, []byte(gU.hostExtId))
			fluxData.Payload = append(fluxData.Payload, []byte(gU.profile.MemberId))
			fluxData.Payload = append(fluxData.Payload, []byte(gU.profile.MemberName))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatUint(gU.profile.Balance, 10)))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatInt(int64(gU.profile.WalletType), 10)))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatInt(int64(wallet.WalletSharedFish), 10)))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatInt(5, 10)))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatInt(int64(gU.profile.GuestEnable), 10)))

			fluxDataByte, _ := proto.Marshal(fluxData)

			postman.Service.Pub(fluxDataByte)
		}

		flux.Send(auth.EMSGID_eLoginRecall, gU.secWebSocketKey, auth.Service.Id, true)

	case auth.EMSGID_eLoginRecall:
		g.SendAction(action)

	case lobbysetting.EMSGID_eLobbyConfigRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()
		gameid := lobbysettingU.Service.GameId(gU.secWebSocketKey)
		gU.gameID = gameid
		if maintain.Service.CheckMaintain(gU.secWebSocketKey, gameid, gU.hostExtId, maintain.Card) ||
			blacklist.Service.CheckBan(gU.secWebSocketKey, gU.hostExtId, gU.profile.HostId, gU.profile.MemberId) {
			return
		}
		recovery, isGaming := gU.gameRecovery(gameid)

		gU.isGaming = isGaming

		if gU.gameRoomUuid != "" && !gU.isGaming {
			if lobbysettingU.Service.AutoATM(gU.secWebSocketKey) {
				if gU.profile.WalletType != wallet.CategoryHost {
					flux.Send(atm.ActionAtmAutoWithdraw, gU.secWebSocketKey, atm.Service.Id, uint8(100), gU.hostExtId, gU.profile.MemberId, uint64(0))
				} else if gU.accountingSn != 0 {
					wallet.Service.Refund(gU.secWebSocketKey, gU.accountingSn, true)

					flux.Send(accounting.ActionAccountingDelete, gU.secWebSocketKey, accounting.Service.HashId(gU.secWebSocketKey, gU.accountingSn))
				}
			}
			flux.Send(auth.EMSGID_eBroadcastPlayerOut, gU.secWebSocketKey, gU.gameRoomUuid, auth.Service.BroadcastPlayerOut(
				gU.gameRoomUuid,
				gU.secWebSocketKey,
				gU.profile.MemberName,
				gU.profile.Avatar,
				uint32(gU.seat),
				uint64(0),
			))

			switch gU.gameRoomType {
			case banker.FRIEND_ROOM:
				flux.Send(gameuser.ActionLeaveGameRoomCall, gU.secWebSocketKey, gU.gameRoomUuid, gU.secWebSocketKey)

			case banker.GAME_ROOM:
				flux.Send(gameuser.ActionLeaveGameRoomCall, gU.secWebSocketKey, gU.controllerId, gU.gameRoomUuid)

			default:
				panic("ERROR GAME ROOM TYPE " + gU.secWebSocketKey)
			}
		}

		cent, errCent := wallet.Service.Cent(gU.secWebSocketKey)
		if errCent != nil {
			logger.Service.Zap.Errorw(atm.Atm_GET_CENT_FAILED,
				"GameUser", gU.secWebSocketKey,
				"Error", errCent,
			)
			errorcode.Service.Fatal(gU.secWebSocketKey, atm.Atm_GET_CENT_FAILED)
		}
		balance, errBalance := wallet.Service.Balance(gU.secWebSocketKey)
		if errBalance != nil {
			logger.Service.Zap.Errorw(GameUserU_GET_CENT_FAILED,
				"GameUser", gU.secWebSocketKey,
				"BankerUuid", gU.bankerUuid,
				"GameRoomUuid", gU.gameRoomUuid,
				"IsWaiting", gU.isWaiting,
				"IsGaming", gU.isGaming,
			)
			errorcode.Service.Fatal(gU.secWebSocketKey, GameUserU_GET_CENT_FAILED)
			return
		}

		dataByte := action.Payload()[0].([]byte)

		data := &lobby_settingU_proto.ConfigRecall{}

		if err := proto.Unmarshal(dataByte, data); err != nil {
			logger.Service.Zap.Errorw(lobbysetting.LobbySetting_CONFIG_RECALL_PROTO_INVALID,
				"GameUser", gU.secWebSocketKey,
			)
			errorcode.Service.Fatal(gU.secWebSocketKey, lobbysetting.LobbySetting_CONFIG_RECALL_PROTO_INVALID)
			return
		}
		totalBalance := balance + cent
		data.Cent = cent
		data.Balance = totalBalance
		data.PlayerInfo = &auth_proto.PlayerInfo{
			Id:       gU.secWebSocketKey,
			Balance:  balance,
			Name:     gU.profile.MemberName,
			Avatar:   gU.profile.Avatar,
			Visible:  nil,
			WinCount: 0,
		}
		data.WalletType = int32(gU.profile.WalletType)

		switch gU.profile.MemberType {
		case 0:
			var roomInfo []*lobby_setting_u_proto.ConfigRecall_RoomInfo
			for i := 0; i < 6; i++ {
				if data.RoomInfo[i].BalanceLimit != 0 {
					roomInfo = append(roomInfo, data.RoomInfo[i])
				}
			}
			data.RoomInfo = roomInfo
		case 1:
			var roomInfo []*lobby_setting_u_proto.ConfigRecall_RoomInfo
			for i := 6; i < 12; i++ {
				if data.RoomInfo[i].BalanceLimit != 0 {
					roomInfo = append(roomInfo, data.RoomInfo[i])
				}
			}
			data.RoomInfo = roomInfo
		}

		if gU.isGaming {
			wallet.Service.SetGameIdAndSubGameId(gU.secWebSocketKey, gU.gameID, int(recovery.Snapshot.SubgameId))
			data.StatusCode = common_proto.Status_kInvalid
			data.ResumeGame = &lobby_settingU_proto.ConfigRecall_ResumeGame{
				PlayerData:  make([]*probability_proto.PlayerData, 0),
				PlayerInfo:  make([]*auth_proto.PlayerInfo, 0),
				WaitingTime: make([]uint32, 0),
			}
			data.ResumeGame.GameRecovery = recovery
			gU.bankerUuid = recovery.Snapshot.BankerUuid
			gU.gameRoomUuid = recovery.Snapshot.RoomUuid
			gU.gameRoomType = recovery.Snapshot.RoomType
			gU.subGameId = recovery.Snapshot.SubgameId
			gU.seat = int(recovery.Snapshot.Seat)
			gU.isGaming = true
			flux.Send(twin.ActionTwinResume, gU.secWebSocketKey, gU.secWebSocketKey,
				gU.bankerUuid,
				gU.profile.MemberId,
				gU.profile.HostId,
				gU.hostExtId,
				gU.gameRoomUuid,
				gU.gameRoomType,
				gU.controllerId,
				gU.profile.Avatar,
				gU.subGameId,
				gU.seat,
				gU.profile.GuestEnable,
				gU.accountingSn,
				gU.blacklistValue,
			)
			flux.Send(banker.ActionPlayerResumeGame, gU.secWebSocketKey, recovery.Snapshot.BankerUuid, data)
			return
		}

		if data.StatusCode == common_proto.Status_kSuccess {
			flux.Send(gameuser.ActionJoinLobbyRoomCall, gU.secWebSocketKey, gU.controllerId, "")
			gU.isWaiting = false
			dataByte, _ := proto.Marshal(data)
			g.SendByte(dataByte)
		}

	case gameuser.ActionJoinLobbyRoomRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		gU.seat = -1
		gU.gameRoomUuid = ""
		gU.gameRoomType = ""
		gU.isWaiting = false
		gU.isGaming = false
		gU.lobbyRoomUuid = action.Payload()[0].(string)

	case gameuser.ActionLeaveLobbyRoomRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		gU.lobbyRoomUuid = ""

	case gamesetting.EMSGID_eGameConfigRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		dataByte := action.Payload()[0].([]byte)

		data := &game_settinU_proto.ConfigRecall{}

		if err := proto.Unmarshal(dataByte, data); err != nil {
			logger.Service.Zap.Errorw(gamesetting.GameSetting_CONFIG_RECALL_PROTO_INVALID,
				"GameUser", gU.secWebSocketKey,
			)
			errorcode.Service.Fatal(gU.secWebSocketKey, gamesetting.GameSetting_CONFIG_RECALL_PROTO_INVALID)
			return
		}

		if data.StatusCode != common_proto.Status_kSuccess {
			g.SendByte(dataByte)
			return
		}
		gameid := lobbysettingU.Service.GameId(gU.secWebSocketKey)
		gU.gameID = gameid
		if maintain.Service.CheckMaintain(gU.secWebSocketKey, gameid, gU.hostExtId, maintain.Card) ||
			blacklist.Service.CheckBan(gU.secWebSocketKey, gU.hostExtId, gU.profile.HostId, gU.profile.MemberId) {
			if lobbysettingU.Service.AutoATM(gU.secWebSocketKey) {
				if gU.profile.WalletType != wallet.CategoryHost {
					flux.Send(atm.ActionAtmAutoWithdraw, gU.secWebSocketKey, atm.Service.Id, uint8(100), gU.hostExtId, gU.profile.MemberId, uint64(0))
				} else if gU.accountingSn != 0 {
					wallet.Service.Refund(gU.secWebSocketKey, gU.accountingSn, true)

					flux.Send(accounting.ActionAccountingDelete, gU.secWebSocketKey, accounting.Service.HashId(gU.secWebSocketKey, gU.accountingSn))
				}
			}
			return
		}
		recovery, isGaming := gU.gameRecovery(gameid)

		gU.isGaming = isGaming

		if recovery != nil {
			recoveryByte, _ := proto.Marshal(data)
			g.SendByte(recoveryByte)
		}

		if gU.lobbyRoomUuid != "" {
			flux.Send(lobbyroom.ActionLobbyRoomLeaveCall, gU.secWebSocketKey, gU.controllerId,
				gU.lobbyRoomUuid,
				false,
			)
		}

		if !gU.isWaiting {

			cent, err := wallet.Service.CentCache(gU.secWebSocketKey)
			balance, err := wallet.Service.BalanceCache(gU.secWebSocketKey)

			if err != nil {
				logger.Service.Zap.Errorw("BUG",
					"GameUser", gU.secWebSocketKey,
					"Error", err,
				)
				panic(gU.secWebSocketKey + err.Error())
			}

			data.Cent = cent
			data.Balance = balance
			data.PlayerInfo = &auth_proto.PlayerInfo{
				Id:       gU.secWebSocketKey,
				Balance:  cent,
				Name:     gU.profile.MemberName,
				Avatar:   gU.profile.Avatar,
				Visible:  nil,
				WinCount: 0,
			}

			gU.gameConfigRecall = data
			gU.isWaiting = true
			gU.canDeleteAccounting = true
			gU.gameRoomType = banker.GAME_ROOM
			gU.blacklistValue = uint32(blacklist.Service.Check(gU.hostExtId, gU.profile.HostId, gU.profile.MemberId, "CARD", gU.gameID))
			r, _ := rand.Int(rand.Reader, big.NewInt(100))
			isIsolated := r.Int64() < int64(gamesettingU.Service.IsolateRate(gU.secWebSocketKey))

			flux.Send(gameuser.ActionJoinGameRoomCall, gU.secWebSocketKey, gU.controllerId,
				gU.hostExtId,
				gU.profile.Avatar,
				gU.ipAddress,
				uint64(data.Bet),
				gU.blacklistValue,
				gU.profile.HostId,
				gU.profile.MemberType,
				isIsolated,
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

			gamerecoveryU.Service.Update(
				gU.secWebSocketKey,
				"",
				"",
				"",
				-1,
				int32(-1),
				gamerecoveryU.IDLE,
			)
		} else {
			gU.lobbyRoomUuid = ""
			gU.gameRoomUuid = gameRoomUuid
			gU.seat = seat
			gU.isWaiting = true
			gU.isGaming = false
			gU.gameRoomType = gameRoomType
			gU.subGameId = gamesettingU.Service.SubGameId(gU.secWebSocketKey)

			gamerecoveryU.Service.Update(
				gU.secWebSocketKey,
				gU.gameRoomUuid,
				gU.gameRoomType,
				gU.bankerUuid,
				gU.subGameId,
				int32(gU.seat),
				gamerecoveryU.IDLE,
			)
		}

		if gU.gameConfigRecall != nil && gameRoomType == banker.GAME_ROOM {
			gU.gameConfigRecall.RoomUuid = gU.gameRoomUuid
			gU.gameConfigRecall.PlayerInfo.Seat = uint32(gU.seat)
			dataByte, _ := proto.Marshal(gU.gameConfigRecall)
			g.SendByte(dataByte)

			flux.Send(auth.EMSGID_eBroadcastPlayerIn, gU.secWebSocketKey, gU.gameRoomUuid, auth_proto.PLAYER_TYPE_GAME)

			return
		}

	case gameuser.ActionLeaveGameRoomRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		gU.gameRoomUuid = ""
		gU.gameRoomType = ""
		gU.seat = -1
		gU.isWaiting = false
		gU.isGaming = false
		gU.subGameId = -1

		gamerecoveryU.Service.Update(
			gU.secWebSocketKey,
			gU.gameRoomUuid,
			gU.gameRoomType,
			gU.bankerUuid,
			gU.subGameId,
			int32(gU.seat),
			gamerecoveryU.IDLE,
		)

	case errorcode.ActionErrorCode:
		if gU.profile != nil {
			dataByte := action.Payload()[0].([]byte)

			data := &errorcode_proto.Error{}

			proto.Unmarshal(dataByte, data)

			if data.Code == sessionmanager.SessionManager_DUPICATE_SESSION {
				flux.Send(sessionmanager.SessionManager_DUPICATE_SESSION, gU.secWebSocketKey, atm.Service.Id,
					gU.hostExtId,
					gU.profile.MemberId,
				)
			}
		}

		g.SendAction(action)

		flux.Send(auth.ActionUserDisconnect, gU.secWebSocketKey, gameuser.Service.Id, gU.secWebSocketKey)

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

		data := &banker_proto.RoundStart{}

		if err := proto.Unmarshal(dataByte, data); err != nil {
			logger.Service.Zap.Errorw(GameUserU_ROUND_START_PROTO_INVALID,
				"GameUser", gU.secWebSocketKey,
				"GameRoomUuid", gameRoomUuid,
				"Seat", gU.seat,
				"BankerUuid", gU.bankerUuid,
				"IsGaming", gU.isGaming,
				"IsWaiting", gU.isWaiting,
			)
			errorcode.Service.Fatal(gU.secWebSocketKey, GameUserU_ROUND_START_PROTO_INVALID)
			return
		}

		for _, v := range data.PlayerInfos {
			if v.Id == gU.secWebSocketKey {
				gU.seat = int(v.Seat)
				gU.gameRoomUuid = gameRoomUuid
			}
		}

		if gU.seat < 0 || gU.gameRoomUuid == "" || gU.bankerUuid == "" {
			logger.Service.Zap.Errorw("ERROR SEAT",
				"GameUser", gU.secWebSocketKey,
				"GameRoomUuid", gameRoomUuid,
				"Seat", gU.seat,
				"BankerUuid", gU.bankerUuid,
				"IsGaming", gU.isGaming,
				"IsWaiting", gU.isWaiting,
			)
			panic("ERROR SEAT : " + gU.secWebSocketKey)
		}
		flux.Send(idle.ActionIdleTimeoutReset, gU.secWebSocketKey, idle.Service.HashId(gU.secWebSocketKey),
			gU.secWebSocketKey,
			gamesettingU.Service.Idle(gU.secWebSocketKey),
		)

		data.AccountingSn = gU.accountingSn

		dataByte, _ = proto.Marshal(data)
		g.SendByte(dataByte)

		logger.Service.Zap.Infow("GameUserU Round Start",
			"GameUser", gU.secWebSocketKey,
			"GameRoomUuid", gU.gameRoomUuid,
			"Seat", gU.seat,
			"BankerUuid", gU.bankerUuid,
			"AccountingSn", gU.accountingSn,
		)
		flux.Send(banker.ActionBankerDeal, gU.secWebSocketKey, gU.bankerUuid, gU.seat, gU.profile.Avatar, gU.blacklistValue)

		d := draw.Builder().
			SetBankerUuid(gU.bankerUuid).
			SetSecWebSocketKey(gU.secWebSocketKey).
			SetGameRoomUuid(gU.gameRoomUuid).
			SetGameRoomType(gU.gameRoomType).
			SetSeat(int32(gU.seat)).
			SetKind(draw.PLAYER).
			Build()

		flux.Send(draw.ActionDrawCreate, gU.secWebSocketKey, draw.Service.Id, d)

		p := playcards.Builder().
			SetBankerUuid(gU.bankerUuid).
			SetSecWebSocketKey(gU.secWebSocketKey).
			SetGameRoomUuid(gU.gameRoomUuid).
			SetGameRoomType(gU.gameRoomType).
			SetSeat(int32(gU.seat)).
			SetKind(playcards.PLAYER).
			Build()

		flux.Send(playcards.ActionPlayCardsCreate, gU.secWebSocketKey, playcards.Service.Id, p)

		r := round.Builder().
			SetBankerUuid(gU.bankerUuid).
			SetSecWebSocketKey(gU.secWebSocketKey).
			SetGameRoomUuid(gU.gameRoomUuid).
			SetGameRoomType(gU.gameRoomType).
			SetSeat(int32(gU.seat)).
			SetWaitingTime(gamesettingU.Service.PlayerRoundWaitingTime(gU.secWebSocketKey)).
			SetKind(round.PLAYER).
			Build()

		flux.Send(round.ActionRoundCreate, gU.secWebSocketKey, round.Service.Id, r)

	case banker.EMSGID_eRoundEnd:
		g.SendAction(action)

		if gU.profile != nil {
			if maintain.Service.CheckMaintain(gU.secWebSocketKey, gU.gameID, gU.hostExtId, maintain.Card) ||
				blacklist.Service.CheckBan(gU.secWebSocketKey, gU.hostExtId, gU.profile.HostId, gU.profile.MemberId) {
				return
			}
		} else {
			logger.Service.Zap.Errorw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", gU.secWebSocketKey,
				"HostExtId", gU.hostExtId,
				"GameRoomUuid", gU.gameRoomUuid,
				"IsGaming", gU.isGaming,
				"IsWaiting", gU.isWaiting,
			)
			errorcode.Service.Fatal(gU.secWebSocketKey, gameuser.GameUser_PROFILE_NIL)
		}

		gU.balanceLimit()

	case banker.EMSGID_ePlayerRoundStart:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		hands := action.Payload()[1].([]int)
		lastCard := action.Payload()[2].(int)
		lastColor := action.Payload()[3].(int)
		penalty := action.Payload()[4].(int)
		gU.hands = hands
		gU.lastCard = lastCard
		gU.lastColor = lastColor
		gU.penalty = penalty
		gU.lastDraw = -1

		flux.Send(idle.ActionIdleTimeoutReset, gU.secWebSocketKey, idle.Service.HashId(gU.secWebSocketKey),
			gU.secWebSocketKey,
			gamesettingU.Service.Idle(gU.secWebSocketKey),
		)
		g.SendAction(action)

	case banker.EMSGID_eBroadcastPlayerRoundStart:
		g.SendAction(action)

	case draw.EMSGID_eDrawTimeout:
		fallthrough
	case draw.EMSGID_eDrawRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		isPenalty := action.Payload()[2].(bool)
		card := action.Payload()[3].(int)
		gU.lastDraw = card
		gU.hands = append(gU.hands, card)

		if !isPenalty {
			g.SendAction(action)
		}

	case draw.EMSGID_eBroadcastDrawTimeout:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()
		g.SendAction(action)

	case draw.EMSGID_eBroadcastDrawRecall:
		g.SendAction(action)

	case playcards.EMSGID_ePlayCardsTimeout:
		fallthrough
	case playcards.EMSGID_ePlayCardsRecall:
		g.SendAction(action)

	case playcards.EMSGID_eBroadcastPlayCardsTimeout:
		g.SendAction(action)
	case playcards.EMSGID_eBroadcastPlayCardsRecall:
		g.SendAction(action)

	case banker.EMSGID_eKeepTimeout:
		fallthrough
	case banker.EMSGID_eKeepRecall:
		g.SendAction(action)

	case banker.EMSGID_eBroadcastKeepRecall:
		g.SendAction(action)

	case banker.EMSGID_eBroadcastKeepTimeout:
		g.SendAction(action)

	case banker.EMSGID_ePenalty:
		g.SendAction(action)

	case banker.EMSGID_eBroadcastPenalty:
		g.SendAction(action)

	case banker.EMSGID_eBroadcastShuffle:
		g.SendAction(action)

	case probability.EMSGID_eBroadcastRanking:
		g.SendAction(action)

	case banker.ActionBankerDeal:
		cards := action.Payload()[0].(*probability_proto.PlayerData)
		pool := action.Payload()[1].(int)
		gU.hands = banker.ToIntArr(cards.Cards.Hands)
		logger.Service.Zap.Infow("Banker Deal",
			"GameUser", gU.secWebSocketKey,
			"BankerUuid", gU.bankerUuid,
			"GameRoomUuid", gU.gameRoomUuid,
			"Seat", gU.seat,
			"pool", pool,
		)

		if gU.seat < 0 {
			// TODO JOHNNY DEBUG
			panic("BUG error seat id")
		}

		data := &banker_proto.Deal{
			Msgid:    commonU_proto.EMSGID_eDeal,
			Cards:    cards.Cards,
			RoomUuid: gU.gameRoomUuid,
			Pool:     int32(pool),
			Seat:     int32(gU.seat),
		}
		dataByte, _ := proto.Marshal(data)
		g.SendByte(dataByte)

	case banker.ActionBankerStart:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		gU.isWaiting = false
		gU.isGaming = true

		switch action.Payload()[0].(type) {
		case string:
			gU.bankerUuid = action.Payload()[0].(string)

		case []byte:
			gU.bankerUuid = string(action.Payload()[0].([]byte))
			flux.Send(banker.ActionBankerStart, gU.secWebSocketKey, gU.gameRoomUuid, gU.bankerUuid)
		}

		cent, err := wallet.Service.Cent(gU.secWebSocketKey)

		if err != nil {
			panic("ERROR WALLET CENT")
		}

		if gU.profile.WalletType != wallet.CategoryHost {
			if a := accounting.Builder().
				SetSecWebSocketKey(gU.secWebSocketKey).
				SetHostExtId(gU.hostExtId).
				SetGuestEnable(gU.profile.GuestEnable == auth.GuestOn).
				SetHostId(gU.profile.HostId).
				SetGameId(gamesettingU.Service.GameId(gU.secWebSocketKey)).
				SetSubgameId(uint32(gamesettingU.Service.SubGameId(gU.secWebSocketKey))).
				SetMemberId(gU.profile.MemberId).
				SetInitCent(cent).
				SetDB(gU.hostExtId).
				SetKind(accounting.PLAYER).
				SetHandler(&accountingU.AccountingU{}).
				Build(); a != nil {

				gU.accountingSn = a.Start.Sn

			}
		}

		if gU.accountingSn != 0 {
			if gU.profile.WalletType != wallet.CategoryHost {
				isDone := make(chan bool)
				flux.Send(twin.ActionTwinAccountingSn, gU.secWebSocketKey, gU.secWebSocketKey, gU.accountingSn, isDone, gU.blacklistValue)
				<-isDone
			}

			switch gU.gameRoomType {
			case banker.FRIEND_ROOM:
				flux.Send(banker.ActionBankerAccountingSn, gU.secWebSocketKey, gU.gameRoomUuid, gU.accountingSn, gU.seat)

			case banker.GAME_ROOM:
				flux.Send(banker.ActionBankerAccountingSn, gU.secWebSocketKey, gU.bankerUuid, gU.accountingSn, gU.seat)

			default:
				logger.Service.Zap.Errorw("ERROR TYPE GAME ROOM",
					"GameUser", gU.secWebSocketKey,
					"GameRoom", gU.gameRoomUuid,
					"BankerUuid", gU.bankerUuid,
					"AccountingSN", gU.accountingSn,
				)
				panic("ERROR TYPE GAME ROOM" + gU.secWebSocketKey)
			}
		}

		if gU.profile.GuestEnable == auth.GuestOn {
			switch gU.gameRoomType {
			case banker.FRIEND_ROOM:
				flux.Send(banker.ActionBankerAccountingSn, gU.secWebSocketKey, gU.gameRoomUuid, gU.accountingSn, gU.seat)

			case banker.GAME_ROOM:
				flux.Send(banker.ActionBankerAccountingSn, gU.secWebSocketKey, gU.bankerUuid, uint64(0), gU.seat)

			default:
				panic("ERROR TYPE GAME ROOM")
			}
		}

		if gU.accountingSn == 0 && gU.profile.GuestEnable == auth.GuestOff {
			logger.Service.Zap.Errorw(GameUserU_ACCOUNTING_SN_ZERO,
				"GameUser", gU.secWebSocketKey,
				"AccountingSn", gU.accountingSn,
				"Guest", gU.profile.GuestEnable,
			)
			errorcode.Service.Fatal(gU.secWebSocketKey, GameUserU_ACCOUNTING_SN_ZERO)
			return
		}

		gamerecoveryU.Service.Update(
			gU.secWebSocketKey,
			gU.gameRoomUuid,
			gU.gameRoomType,
			gU.bankerUuid,
			gU.subGameId,
			int32(gU.seat),
			gamerecoveryU.GAMING,
		)

	case probability.EMSGID_eBroadcastResult:
		g.SendAction(action)

		flux.Send(draw.ActionDrawDelete, gU.secWebSocketKey, draw.Service.Id)
		flux.Send(playcards.ActionPlayCardsDelete, gU.secWebSocketKey, playcards.Service.Id)
		flux.Send(round.ActionRoundDelete, gU.secWebSocketKey, round.Service.Id)

		g.RwMutex.Lock()

		gU.bankerUuid = ""
		gU.isWaiting = false
		gU.isGaming = false
		gU.accountingSn = 0
		gU.canDeleteAccounting = true

		g.RwMutex.Unlock()

	case heartbeat.ActionHeartBeatRecall:
		g.SendAction(action)

	case auth.ActionAuthNotify:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		gU.isWaiting = false
		gU.isGaming = false

		gamerecoveryU.Service.Update(
			gU.secWebSocketKey,
			gU.gameRoomUuid,
			gU.gameRoomType,
			gU.bankerUuid,
			gU.subGameId,
			int32(gU.seat),
			gamerecoveryU.IDLE,
		)
		cent, err := wallet.Service.CentCache(gU.secWebSocketKey)
		if err == nil {
			if wallet.Service.WalletCategory(gU.secWebSocketKey) != wallet.CategoryHost && cent > 0 {
				flux.Send(atm.ActionAtmAutoWithdraw, gU.secWebSocketKey, atm.Service.Id, uint8(100), gU.hostExtId, gU.profile.MemberId, gU.accountingSn)
			}
		}
		g.SendAction(action)

	case waitingroom.EMSGID_eWaitingCountdown:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		gU.isWaiting = true
		gU.isGaming = false
		gU.canDeleteAccounting = true

		if gU.gameRoomUuid != "" {
			g.SendAction(action)
		}

	case auth.EMSGID_eBroadcastPlayerIn:
		fallthrough
	case auth.EMSGID_eBroadcastPlayerOut:
		switch action.Payload()[0].(type) {
		case [][]byte:
			gU.postman(action, g)

		default:
			g.SendAction(action)
		}

	case friendroom.EMSGID_eFriendRoomJoinRecall:
		dataByte := action.Payload()[0].([]byte)

		data := &friend_room_proto.FriendRoomJoinRecall{}

		proto.Unmarshal(dataByte, data)

		if data.StatusCode == common_proto.Status_kSuccess {
			gU.gameRoomUuid = action.Key().From()
			gU.gameRoomType = banker.FRIEND_ROOM
		}

		g.SendAction(action)

	case friendroom.EMSGID_eFriendRoomLeaveRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		flux.Send(gameuser.ActionLeaveGameRoomCall, gU.secWebSocketKey, gU.gameRoomUuid, gU.secWebSocketKey)

		gamerecoveryU.Service.Update(
			gU.secWebSocketKey,
			gU.gameRoomUuid,
			gU.gameRoomType,
			gU.bankerUuid,
			gU.subGameId,
			int32(gU.seat),
			gamerecoveryU.IDLE,
		)

		gU.gameRoomUuid = ""
		gU.gameRoomType = ""
		gU.seat = -1
		gU.isWaiting = false
		gU.isGaming = false
		g.SendAction(action)

	case friendroom.EMSGID_eFriendRoomHostChanged:
		g.SendAction(action)

	case friendroom.EMSGID_eFriendRoomDestroy:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()
		if lobbysettingU.Service.AutoATM(gU.secWebSocketKey) {
			if gU.profile.WalletType != wallet.CategoryHost {
				flux.Send(atm.ActionAtmAutoWithdraw, gU.secWebSocketKey, atm.Service.Id, uint8(100), gU.hostExtId, gU.profile.MemberId, uint64(0))
			} else if gU.accountingSn != 0 {
				wallet.Service.Refund(gU.secWebSocketKey, gU.accountingSn, true)

				flux.Send(accounting.ActionAccountingDelete, gU.secWebSocketKey, accounting.Service.HashId(gU.secWebSocketKey, gU.accountingSn))
			}
		}
		flux.Send(gameuser.ActionLeaveGameRoomCall, gU.secWebSocketKey, gU.gameRoomUuid, gU.secWebSocketKey)

		friendroom.Service.Delete(gU.secWebSocketKey)

		gamerecoveryU.Service.Update(
			gU.secWebSocketKey,
			gU.gameRoomUuid,
			gU.gameRoomType,
			gU.bankerUuid,
			gU.subGameId,
			int32(gU.seat),
			gamerecoveryU.IDLE,
		)

		gU.gameRoomUuid = ""
		gU.gameRoomType = ""
		gU.seat = -1
		gU.isWaiting = false
		gU.isGaming = false

		g.SendAction(action)

	case atm.EMSGID_eAutoTransferRecall:
		g.SendAction(action)
	case atm.EMSGID_eAutoTransferOutRecall:
		g.SendAction(action)

	case waitingroom.EMSGID_eWaitingRoundEnd:
		g.SendAction(action)

	case banker.ActionPlayerResumeGame:
		g.SendAction(action)

	case waitingroom.ActionWaitingRoomDone:
		gU.isGaming = true
		gU.isWaiting = false
		gU.canDeleteAccounting = false
		gamerecoveryU.Service.Update(
			gU.secWebSocketKey,
			gU.gameRoomUuid,
			gU.gameRoomType,
			gU.bankerUuid,
			gU.subGameId,
			int32(gU.seat),
			gamerecoveryU.GAMING,
		)

	case avatar.EMSGID_eAvatarRecall:
		avatar := action.Payload()[1].(int32)
		gU.profile.Avatar = strconv.Itoa(int(avatar))

		g.SendAction(action)

	case gameroom.ActionKickOut:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		gameRoomUuid := action.Payload()[0].(string)
		gU.kickOut(gameRoomUuid)
	}
}

func (gU *GameUserU) postman(action *flux.Action, g *gameuser.GameUser) {
	dataByte := action.Payload()[0].([][]byte)
	g.SendByte(dataByte[0])
}

func (gU *GameUserU) balanceLimit() (cent uint64) {
	if gU.gameRoomUuid == "" {
		return
	}

	balance, balanceErr := wallet.Service.Balance(gU.secWebSocketKey)
	if balanceErr != nil {
		logger.Service.Zap.Errorw(GameUserU_GET_CENT_FAILED,
			"GameUser", gU.secWebSocketKey,
			"BankerUuid", gU.bankerUuid,
			"GameRoomUuid", gU.gameRoomUuid,
			"IsWaiting", gU.isWaiting,
			"IsGaming", gU.isGaming,
		)
		errorcode.Service.Fatal(gU.secWebSocketKey, GameUserU_GET_CENT_FAILED)
		return
	}
	cent, centErr := wallet.Service.Cent(gU.secWebSocketKey)

	if centErr != nil {
		logger.Service.Zap.Errorw(GameUserU_GET_CENT_FAILED,
			"GameUser", gU.secWebSocketKey,
			"BankerUuid", gU.bankerUuid,
			"GameRoomUuid", gU.gameRoomUuid,
			"IsWaiting", gU.isWaiting,
			"IsGaming", gU.isGaming,
		)
		errorcode.Service.Fatal(gU.secWebSocketKey, GameUserU_GET_CENT_FAILED)
		return 0
	}

	l := gamesettingU.Service.BalanceLimit(gU.secWebSocketKey)

	if cent+balance < uint64(l) {
		logger.Service.Zap.Infow("No Money",
			"GameUser", gU.secWebSocketKey,
			"BankerUuid", gU.bankerUuid,
			"Cent", cent,
			"BalanceLimit", l,
			"GameRoomUuid", gU.gameRoomUuid,
			"IsWaiting", gU.isWaiting,
			"IsGaming", gU.isGaming,
		)

		flux.Send(auth.EMSGID_eBroadcastPlayerOut, gU.secWebSocketKey, gU.gameRoomUuid, auth.Service.BroadcastPlayerOut(
			gU.gameRoomUuid,
			gU.secWebSocketKey,
			gU.profile.MemberName,
			gU.profile.Avatar,
			uint32(gU.seat),
			cent,
		))
	} else {
		if balance > 0 {
			//if lobbysettingU.Service.AutoATM(gU.secWebSocketKey) {
			//	flux.Send(atm.ActionAtmAutoDeposit, gU.secWebSocketKey, atm.Service.Id, uint8(100), gU.hostExtId, gU.profile.MemberId)
			//}
		}
	}

	return cent + balance
}

func (gU *GameUserU) gameRecovery(gameId string) (*gamerecoveryU_proto.GameRecovery, bool) {
	if data := gamerecoveryU.Service.Check(
		gamerecovery.Builder().
			SetSecWebSocketKey(gU.secWebSocketKey).
			SetHostId(gU.profile.HostId).
			SetHostExtId(gU.hostExtId).
			SetServerId(gamerecoveryU.Service.ServerId).
			SetGameId(gameId).
			SetMemberId(gU.profile.MemberId).
			SetGuest(gU.profile.GuestEnable == auth.GuestOn).
			SetDB(gU.hostExtId).
			Build(),
	); data != nil {
		logger.Service.Zap.Infow("Check Game Recovery",
			"GameUser", gU.secWebSocketKey,
			"GameRoomUuid", gU.gameRoomUuid,
			"BankerUuid", gU.bankerUuid,
			"Status", data.Snapshot.Status == gamerecoveryU.GAMING,
			"IsGaming", gU.isGaming,
			"IsWaiting", gU.isWaiting,
		)
		return data, data.Snapshot.Status == gamerecoveryU.GAMING
	}
	return nil, false
}

func (gU *GameUserU) CleanDataHandler(g *gameuser.GameUser) {
	if gU.profile != nil {
		session.Service.End(
			gU.secWebSocketKey,
			gU.profile.HostId,
			gU.hostExtId,
			gU.profile.MemberId,
			0, // TODO JOHNNY need implement
		)
	} else {
		logger.Service.Zap.Warnw(gameuser.GameUser_PROFILE_NIL,
			"GameUser", gU.secWebSocketKey,
			"HostExtId", gU.hostExtId,
			"IsGaming", gU.isGaming,
			"IsWaiting", gU.isWaiting,
		)
	}

	if !gU.isGaming {
		flux.Send(twin.ActionTwinDestroy, gU.secWebSocketKey, gU.secWebSocketKey, gU.gameRoomUuid, gU.gameRoomType)
	}
	sessionmanager.Service.End(gU.secWebSocketKey, gU.hostExtId)

	flux.Send(idle.ActionIdleTimeoutStop, gU.secWebSocketKey, idle.Service.Id, gU.secWebSocketKey)
	lobbysetting.Service.Delete(gU.secWebSocketKey)
	mediator.Service.Delete(gU.secWebSocketKey)
}

func (gU *GameUserU) leaveRooms() {
	logger.Service.Zap.Infow("leaveRooms",
		"GameUser", gU.secWebSocketKey,
		"GameRoomUuid", gU.gameRoomUuid,
		"LobbyRoomUuid", gU.lobbyRoomUuid,
	)
	gU.isDestroy = true

	if gU.gameRoomUuid != "" {
		if gU.isWaiting {
			flux.Send(auth.EMSGID_eBroadcastPlayerOut, gU.secWebSocketKey, gU.gameRoomUuid, auth.Service.BroadcastPlayerOut(
				gU.gameRoomUuid,
				gU.secWebSocketKey,
				gU.profile.MemberName,
				gU.profile.Avatar,
				uint32(gU.seat),
				uint64(0),
			))
			flux.Send(gameuser.ActionLeaveGameRoomCall, gU.secWebSocketKey, gU.controllerId, gU.gameRoomUuid)
		}

		if gU.canDeleteAccounting && gU.accountingSn != 0 {
			wallet.Service.Refund(gU.secWebSocketKey, gU.accountingSn, true)

			flux.Send(accounting.ActionAccountingDelete, gU.secWebSocketKey, accounting.Service.HashId(gU.secWebSocketKey, gU.accountingSn))
		}
	} else {
		flux.Send(gameuser.ActionGameUserDelete, gU.secWebSocketKey, gameuser.Service.Id, gU.secWebSocketKey)
	}

	if gU.lobbyRoomUuid != "" {
		flux.Send(gameuser.ActionLeaveLobbyRoomCall, gU.secWebSocketKey, gU.controllerId, gU.lobbyRoomUuid, true)
	} else {
		flux.Send(gameuser.ActionGameUserDelete, gU.secWebSocketKey, gameuser.Service.Id, gU.secWebSocketKey)
	}

	if gU.profile != nil {
		avatar.Service.Update(gU.secWebSocketKey, gU.hostExtId, gU.profile.HostId, gU.profile.MemberId, gU.profile.Avatar)
	}
}

func (gU *GameUserU) kickOut(gameRoomUuid string) {
	if gU.gameRoomUuid != gameRoomUuid {
		return
	}

	cent, centErr := wallet.Service.Cent(gU.secWebSocketKey)

	if centErr != nil {
		logger.Service.Zap.Errorw(GameUserU_GET_CENT_FAILED,
			"GameUser", gU.secWebSocketKey,
			"BankerUuid", gU.bankerUuid,
			"GameRoomUuid", gU.gameRoomUuid,
			"IsWaiting", gU.isWaiting,
			"IsGaming", gU.isGaming,
		)
		errorcode.Service.Fatal(gU.secWebSocketKey, GameUserU_GET_CENT_FAILED)
		return
	}

	flux.Send(auth.EMSGID_eBroadcastPlayerOut, gU.secWebSocketKey, gU.gameRoomUuid, auth.Service.BroadcastPlayerOut(
		gU.gameRoomUuid,
		gU.secWebSocketKey,
		gU.profile.MemberName,
		gU.profile.Avatar,
		uint32(gU.seat),
		cent,
	))
}

func (gU *GameUserU) GetAccountingSnHandler(secWebSocketKey string, balance, cent, sn uint64, depositCheck bool) (accountingSn uint64) {
	if secWebSocketKey == gU.secWebSocketKey {
		accountingSn = gU.accountingSn

		logger.Service.Zap.Infow("Find AccountingSn",
			"GameUser", secWebSocketKey,
			"accountingSn", gU.accountingSn,
		)
	} else {
		accountingSn = 0

		logger.Service.Zap.Warnw(accounting.Accounting_ACCOUNTING_NOT_FOUND,
			"GameUser", secWebSocketKey,
		)
	}

	return accountingSn
}

func (gU *GameUserU) DecreaseHandler(secWebSocketKey, uuid string, balance, cent, accountingSn uint64) {
	// do nothing
}

func (gU *GameUserU) IncreaseHandler(secWebSocketKey, uuid string, balance, cent, accountingSn uint64) {
	// do nothing
}

func (gU *GameUserU) EndAccountingHandler(secWebSocketKey string, checkAccountingEnd bool, walletType int, cent uint64) {
	// do nothing
}

func (gU *GameUserU) BetErrorHandler(secWebSocketKey string, accountingSn uint64) {
	//do nothing
}
