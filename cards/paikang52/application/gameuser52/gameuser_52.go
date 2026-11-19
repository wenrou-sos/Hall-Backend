package gameuser52

import (
	"52-game-server/application/accounting52"
	"52-game-server/application/atm"
	atm_proto "52-game-server/application/atm/proto"
	"52-game-server/application/banker"
	banker_proto "52-game-server/application/banker/proto"
	"52-game-server/application/filter"
	"52-game-server/application/friendroom"
	friend_room_proto "52-game-server/application/friendroom/proto"
	"52-game-server/application/gameroom"
	"52-game-server/application/gamesetting52"
	game_settin52_proto "52-game-server/application/gamesetting52/proto"
	"52-game-server/application/lobbysetting52"
	lobby_setting52_proto "52-game-server/application/lobbysetting52/proto"
	"52-game-server/application/playerinfo"
	"52-game-server/application/twin"
	"52-game-server/domain/draw"
	"52-game-server/domain/gamerecovery52"
	gamerecovery52_proto "52-game-server/domain/gamerecovery52/proto"
	"52-game-server/domain/playcards"
	play_cards_proto "52-game-server/domain/playcards/proto"
	"52-game-server/domain/probability"
	"52-game-server/domain/waitingroom"
	"52-game-server/domain/wallet52"
	"crypto/rand"
	"math/big"
	"strconv"
	"time"

	probability_proto "52-game-server/domain/probability/proto"
	common52_proto "52-game-server/models/proto"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/accounting"
	"gitlab.iplaystar.net/game-server/auth"
	auth_proto "gitlab.iplaystar.net/game-server/auth/proto"
	"gitlab.iplaystar.net/game-server/avatar"
	"gitlab.iplaystar.net/game-server/blacklist"
	common_proto "gitlab.iplaystar.net/game-server/common/proto"
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	errorcode_proto "gitlab.iplaystar.net/game-server/error-code/proto"
	"gitlab.iplaystar.net/game-server/flux"
	flux_proto "gitlab.iplaystar.net/game-server/flux/proto"
	gamerecovery "gitlab.iplaystar.net/game-server/game-recovery-v2"
	gamesetting "gitlab.iplaystar.net/game-server/game-setting"
	game_setting_proto "gitlab.iplaystar.net/game-server/game-setting/proto"
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

const (
	STATE_START = "STATE_START"
	STATE_DRAW  = "STATE_DRAW"
	STATE_END   = "STATE_END"
)

type GameUser52 struct {
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
	gameConfigRecall    *game_settin52_proto.ConfigRecall
	isGaming            bool
	isWaiting           bool
	isDestroy           bool
	accountingSn        uint64
	hands               []int
	card                int
	state               string
	blacklistRoundCount uint32
	canDeleteAccounting bool
}

func New(controllerId, secWebSocketKey, hostExtId, remoteAddr string) *GameUser52 {
	return &GameUser52{
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
		state:               STATE_END,
		blacklistRoundCount: 0,
		canDeleteAccounting: false,
	}
}

func (g52 *GameUser52) MsgHandler(g *gameuser.GameUser, msg []byte) {
	v, err := filter.FindActionName(msg)
	if err != nil {
		logger.Service.Zap.Errorw(gameuser.GameUser_MSGID_PROTO_INVALID,
			"GameUser52", g52.secWebSocketKey,
			"Error", err,
		)
		errorcode.Service.Fatal(g52.secWebSocketKey, gameuser.GameUser_MSGID_PROTO_INVALID)
		return
	}

	logger.Service.Zap.Infow(v,
		"GameUser", g52.secWebSocketKey,
		"BankerUuid", g52.bankerUuid,
		"LobbyRoomUuid", g52.lobbyRoomUuid,
		"GameRoomUuid", g52.gameRoomUuid,
		"Seat", g52.seat,
		"ip", g52.ipAddress,
	)
	switch v {
	case auth.EMSGID_eLoginCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		flux.Send(auth.EMSGID_eLoginCall, g52.secWebSocketKey, auth.Service.Id, msg)

	case atm.EMSGID_eDepositCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g52.profile != nil {
			if g52.profile.WalletType == wallet.CategoryHost {
				data := &atm_proto.DepositCall{}

				if err := proto.Unmarshal(msg, data); err != nil {
					logger.Service.Zap.Errorw("3000_5",
						"GameUser", g52.secWebSocketKey,
					)
					errorcode.Service.Fatal(g52.secWebSocketKey, "3000_5")
					return
				}

				if g52.profile.MemberType == 1 {
					data.SubgameId += 6
					msg, _ = proto.Marshal(data)
				}
				wallet.Service.SetGameIdAndSubGameId(g52.secWebSocketKey, data.GameId, int(data.SubgameId))

				balance, balanceerr := wallet.Service.Balance(g52.secWebSocketKey)

				if balanceerr != nil {
					errorcode.Service.Fatal(g52.secWebSocketKey, GameUser52_GET_CENT_FAILED)
					return
				}

				if a := accounting.Builder().
					SetSecWebSocketKey(g52.secWebSocketKey).
					SetHostExtId(g52.hostExtId).
					SetGuestEnable(g52.profile.GuestEnable == auth.GuestOn).
					SetHostId(g52.profile.HostId).
					SetGameId(data.GameId).
					SetSubgameId(data.SubgameId).
					SetMemberId(g52.profile.MemberId).
					SetInitCent(balance).
					SetDB(g52.hostExtId).
					SetKind(accounting.PLAYER).
					SetHandler(&accounting52.Accounting52{}).
					Build(); a != nil {

					g52.accountingSn = a.Start.Sn
				}

				if g52.accountingSn == 0 {
					logger.Service.Zap.Errorw(GameUser52_ACCOUNTING_SN_ZERO,
						"GameUser", g52.secWebSocketKey,
						"AccountingSn", g52.accountingSn,
						"Guest", g52.profile.GuestEnable,
					)
					errorcode.Service.Fatal(g52.secWebSocketKey, GameUser52_ACCOUNTING_SN_ZERO)
					return
				}

				isDone := make(chan bool)
				flux.Send(twin.ActionTwinAccountingSn, g52.secWebSocketKey, g52.secWebSocketKey, g52.accountingSn, isDone)
				<-isDone
			}

			flux.Send(atm.EMSGID_eDepositCall, g52.secWebSocketKey, atm.Service.Id, msg, g52.hostExtId, g52.profile.MemberId)

		} else {
			logger.Service.Zap.Warnw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", g52.secWebSocketKey,
				"HostExtId", g52.hostExtId,
				"IsGaming", g52.isGaming,
				"IsWaiting", g52.isWaiting,
			)
		}

	case atm.EMSGID_eWithdrawCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g52.isGaming || g52.isWaiting || g52.gameRoomUuid != "" {
			logger.Service.Zap.Errorw(GameUser52_WITHDRAW_CALL_INVALID,
				"GameUser", g52.secWebSocketKey,
				"GameRoomUuid", g52.gameRoomUuid,
				"IsGaming", g52.isGaming,
				"IsWaiting", g52.isWaiting,
			)
			errorcode.Service.Fatal(g52.secWebSocketKey, GameUser52_WITHDRAW_CALL_INVALID)
			return
		}

		if g52.profile != nil {
			flux.Send(atm.EMSGID_eWithdrawCall, g52.secWebSocketKey, atm.Service.Id, msg, g52.hostExtId, g52.profile.MemberId)
		} else {
			logger.Service.Zap.Errorw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", g52.secWebSocketKey,
				"HostExtId", g52.hostExtId,
				"GameRoomUuid", g52.gameRoomUuid,
				"IsGaming", g52.isGaming,
				"IsWaiting", g52.isWaiting,
			)
			errorcode.Service.Fatal(g52.secWebSocketKey, gameuser.GameUser_PROFILE_NIL)
		}

	case atm.EMSGID_eInquireCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g52.profile != nil {
			flux.Send(atm.EMSGID_eInquireCall, g52.secWebSocketKey, atm.Service.Id, msg, g52.hostExtId, g52.profile.MemberId)
		} else {
			logger.Service.Zap.Errorw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", g52.secWebSocketKey,
				"HostExtId", g52.hostExtId,
				"GameRoomUuid", g52.gameRoomUuid,
				"IsGaming", g52.isGaming,
				"IsWaiting", g52.isWaiting,
			)
			errorcode.Service.Fatal(g52.secWebSocketKey, gameuser.GameUser_PROFILE_NIL)
		}

	case lobbysetting.EMSGID_eLobbyConfigCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g52.profile != nil {
			flux.Send(lobbysetting.EMSGID_eLobbyConfigRecall, g52.secWebSocketKey, g52.secWebSocketKey,
				lobbysetting.Service.EMSGID_eLobbyConfigCall(
					g52.secWebSocketKey,
					g52.profile.MemberId,
					g52.profile.GuestEnable,
					msg,
				),
			)
		} else {
			logger.Service.Zap.Errorw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", g52.secWebSocketKey,
				"HostExtId", g52.hostExtId,
				"GameRoomUuid", g52.gameRoomUuid,
				"IsGaming", g52.isGaming,
				"IsWaiting", g52.isWaiting,
			)
			errorcode.Service.Fatal(g52.secWebSocketKey, gameuser.GameUser_PROFILE_NIL)
		}

	case gamesetting.EMSGID_eGameConfigCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g52.isGaming || g52.isWaiting || g52.gameRoomUuid != "" {
			logger.Service.Zap.Infow(gamesetting.EMSGID_eGameConfigCall,
				"GameUser", g52.secWebSocketKey,
				"GameRoomUuid", g52.gameRoomUuid,
				"IsGaming", g52.isGaming,
				"IsWaiting", g52.isWaiting,
			)
			return
		}

		if g52.profile != nil {
			if g52.profile.MemberType == 1 {
				data := &game_setting_proto.ConfigCall{}

				if err := proto.Unmarshal(msg, data); err != nil {
					logger.Service.Zap.Errorw("601_0",
						"GameUser", g52.secWebSocketKey,
						"MemberId", g52.profile.MemberId,
					)
					errorcode.Service.Fatal(g52.secWebSocketKey, "601_0")
					return
				}

				data.SubgameId += 6
				msg, _ = proto.Marshal(data)
			}

			flux.Send(gamesetting.EMSGID_eGameConfigRecall, g52.secWebSocketKey, g52.secWebSocketKey,
				gamesetting.Service.EMSGID_eGameConfigCall(
					g52.secWebSocketKey,
					g52.profile.MemberId,
					g52.profile.GuestEnable,
					msg,
				),
			)
		} else {
			logger.Service.Zap.Errorw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", g52.secWebSocketKey,
				"HostExtId", g52.hostExtId,
				"GameRoomUuid", g52.gameRoomUuid,
				"IsGaming", g52.isGaming,
				"IsWaiting", g52.isWaiting,
			)
			errorcode.Service.Fatal(g52.secWebSocketKey, gameuser.GameUser_PROFILE_NIL)
		}

	case heartbeat.ActionHeartBeatCall:
		flux.Send(heartbeat.ActionHeartBeatCall, g52.secWebSocketKey, heartbeat.Service.Id, msg)

	case draw.EMSGID_eDrawCall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		if !g52.isGaming || g52.state != STATE_START {
			return
		}
		g52.state = STATE_DRAW

		flux.Send(draw.EMSGID_eDrawCall, g52.secWebSocketKey, draw.Service.Id, msg)

		flux.Send(idle.ActionIdleTimeoutReset, g52.secWebSocketKey, idle.Service.HashId(g52.secWebSocketKey),
			g52.secWebSocketKey,
			gamesetting52.Service.Idle(g52.secWebSocketKey),
		)

	case playcards.EMSGID_ePlayCardsCall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		if !g52.isGaming {
			return
		}

		data := &play_cards_proto.PlayCardsCall{}

		err := proto.Unmarshal(msg, data)

		if data.RoomUuid != g52.gameRoomUuid || data.Seat != int32(g52.seat) || len(data.Cards) == 0 || err != nil {
			logger.Service.Zap.Errorw(playcards.PlayCards_PROTO_PLAY_CARDS_CALL_INVAILD,
				"GameUser", g52.secWebSocketKey,
				"BankerUuid", g52.bankerUuid,
				"GameRoomUuid", g52.gameRoomUuid,
				"GameRoomType", g52.gameRoomType,
				"Seat", g52.seat,
				"Data", data,
				"Error", err,
			)
			errorcode.Service.Fatal(g52.secWebSocketKey, playcards.PlayCards_PROTO_PLAY_CARDS_CALL_INVAILD)
			return
		}

		ok := false
		for _, c := range g52.hands {
			if data.Cards[0] == int32(c) {
				ok = true
				break
			}
		}
		if !ok {
			logger.Service.Zap.Errorw(playcards.PlayCards_CHECK_CARD_FAILED,
				"PlayCard", data.Cards[0],
				"Hands", g52.hands,
			)
			errorcode.Service.Fatal(g52.secWebSocketKey, playcards.PlayCards_CHECK_CARD_FAILED)
			return
		}

		switch data.Type {
		case playcards.TYPE_CALLCARD:
			if g52.state != STATE_START {
				return
			}
			flux.Send(playcards.ActionCallCards, g52.secWebSocketKey, g52.bankerUuid, g52.secWebSocketKey, int32(g52.seat), data)

		case playcards.TYPE_PLAYCARD:
			if g52.state != STATE_DRAW {
				return
			}
			flux.Send(playcards.ActionPlayCards, g52.secWebSocketKey, g52.bankerUuid, g52.secWebSocketKey, int32(g52.seat), data, int32(-1), false)
		}

		logger.Service.Zap.Infow("PlayCards",
			"GameUser", g52.secWebSocketKey,
			"BankerUuid", g52.bankerUuid,
			"GameRoomUuid", g52.gameRoomUuid,
			"GameRoomType", g52.gameRoomType,
			"Seat", g52.seat,
			"Data", data,
		)
		g52.state = STATE_END

		flux.Send(draw.ActionDrawStop, g52.secWebSocketKey, draw.Service.Id)

		flux.Send(playcards.EMSGID_ePlayCardsCall, g52.secWebSocketKey, playcards.Service.Id, msg)

		flux.Send(idle.ActionIdleTimeoutReset, g52.secWebSocketKey, idle.Service.HashId(g52.secWebSocketKey),
			g52.secWebSocketKey,
			gamesetting52.Service.Idle(g52.secWebSocketKey),
		)

	case atm.EMSGID_eAutoTransferCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g52.isGaming || g52.lobbyRoomUuid == "" {
			logger.Service.Zap.Errorw(GameUser52_AUTO_TRANSFER_CALL_INVALID,
				"GameUser", g52.secWebSocketKey,
				"LobbyRoomUuid", g52.lobbyRoomUuid,
				"GameRoomUuid", g52.gameRoomUuid,
				"IsGaming", g52.isGaming,
				"IsWaiting", g52.isWaiting,
			)
			errorcode.Service.Fatal(g52.secWebSocketKey, GameUser52_AUTO_TRANSFER_CALL_INVALID)
			return
		}

		flux.Send(atm.EMSGID_eAutoTransferCall, g52.secWebSocketKey, atm.Service.Id, msg, g52.hostExtId, g52.profile.MemberId)

	case atm.EMSGID_eAutoTransferOutCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g52.isGaming || g52.lobbyRoomUuid == "" {
			logger.Service.Zap.Errorw(GameUser52_AUTO_TRANSFER_CALL_INVALID,
				"GameUser", g52.secWebSocketKey,
				"LobbyRoomUuid", g52.lobbyRoomUuid,
				"GameRoomUuid", g52.gameRoomUuid,
				"IsGaming", g52.isGaming,
				"IsWaiting", g52.isWaiting,
			)
			errorcode.Service.Fatal(g52.secWebSocketKey, GameUser52_AUTO_TRANSFER_CALL_INVALID)
			return
		}

		flux.Send(atm.EMSGID_eAutoTransferOutCall, g52.secWebSocketKey, atm.Service.Id, msg, g52.hostExtId, g52.profile.MemberId)

	case friendroom.EMSGID_eFriendRoomJoinCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g52.isGaming || g52.gameRoomUuid != "" || g52.profile.GuestEnable == auth.GuestOn {
			logger.Service.Zap.Infow(friendroom.EMSGID_eFriendRoomJoinCall,
				"GameUser", g52.secWebSocketKey,
				"GameRoomUuid", g52.gameRoomUuid,
				"GameRoomType", g52.gameRoomType,
				"IsGaming", g52.isGaming,
				"IsWaiting", g52.isWaiting,
				"GuestEnable", g52.profile.GuestEnable,
			)
			return
		}

		if v := friendroom.Service.Get(g52.secWebSocketKey); v != nil {
			v.EMSGID_eFriendRoomJoinCall(msg, g52.hostExtId, g52.ipAddress)
		} else {
			friendroom.Service.Create(friendroom.Builder().
				SetSecWebSocketKey(g52.secWebSocketKey).
				SetMemberId(g52.profile.MemberId).
				SetMemberName(g52.profile.MemberName).
				SetAvatar(g52.profile.Avatar).
				SetHostExtId(g52.hostExtId).
				SetKind(friendroom.PLAYER).
				SetGuest(g52.profile.GuestEnable).
				Build(),
			).EMSGID_eFriendRoomJoinCall(msg, g52.hostExtId, g52.ipAddress)
		}

	case friendroom.EMSGID_eFriendRoomLeaveCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g52.isGaming || g52.profile.GuestEnable == auth.GuestOn {
			logger.Service.Zap.Infow(friendroom.EMSGID_eFriendRoomLeaveCall,
				"GameUser", g52.secWebSocketKey,
				"GameRoomUuid", g52.gameRoomUuid,
				"GameRoomType", g52.gameRoomType,
				"IsGaming", g52.isGaming,
				"IsWaiting", g52.isWaiting,
				"GuestEnable", g52.profile.GuestEnable,
			)
			return
		}

		if v := friendroom.Service.Get(g52.secWebSocketKey); v != nil {
			v.EMSGID_eFriendRoomLeaveCall(msg)
		}

	case friendroom.EMSGID_eFriendRoomGameStart:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		if g52.profile.GuestEnable == auth.GuestOn {
			logger.Service.Zap.Infow(friendroom.EMSGID_eFriendRoomGameStart,
				"GameUser", g52.secWebSocketKey,
				"GameRoomUuid", g52.gameRoomUuid,
				"GameRoomType", g52.gameRoomType,
				"IsGaming", g52.isGaming,
				"IsWaiting", g52.isWaiting,
				"GuestEnable", g52.profile.GuestEnable,
			)
			return
		}

		if v := friendroom.Service.Get(g52.secWebSocketKey); v != nil {
			v.EMSGID_eFriendRoomGameStart(msg)
		}

	case banker.EMSGID_eShowdownCall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		if !g52.isGaming || g52.state != STATE_START {
			return
		}
		g52.state = STATE_END

		flux.Send(banker.ActionPlayerResult, g52.secWebSocketKey, g52.bankerUuid, msg)

	case avatar.EMSGID_eAvatarCall:
		g.RwMutex.RLock()
		defer g.RwMutex.RUnlock()

		avatar.Service.EMSGID_eAvatarCall(msg, g52.secWebSocketKey, 18)
	}
}

func (g52 *GameUser52) DeferRunReadMessageHandler(g *gameuser.GameUser) {
	if g52.isGaming {
		flux.Send(twin.ActionTwinActive, g52.secWebSocketKey, g52.secWebSocketKey, true)
	}
}

func (g52 *GameUser52) DeferRunWriteMessageHandler(g *gameuser.GameUser) {
	g52.leaveRooms()
}

func (g52 *GameUser52) FluxActionHandler(action *flux.Action, g *gameuser.GameUser) {

	logger.Service.Zap.Infow(action.Key().Name(),
		"GameUser", g52.secWebSocketKey,
		"BankerUuid", g52.bankerUuid,
		"LobbyRoomUuid", g52.lobbyRoomUuid,
		"GameRoomUuid", g52.gameRoomUuid,
		"Seat", g52.seat,
	)
	if g52.secWebSocketKey != action.Key().To() {
		return
	}
	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:
		logger.Service.Zap.Infow("GameUser52 Flux Registered",
			"GameUser52", g52.secWebSocketKey,
			"HostExtId", g52.hostExtId,
		)

	case auth.ActionLoginFailed:
		logger.Service.Zap.Errorw(auth.Auth_LOGIN_FAILED,
			"GameUser52", g52.secWebSocketKey,
		)
		errorcode.Service.Fatal(g52.secWebSocketKey, auth.Auth_LOGIN_FAILED)

	case auth.ActionLoginSuccess:
		g52.profile = action.Payload()[0].(*auth.MemberInfo)

		flux.Send(atm.ActionAtmStart, g52.secWebSocketKey, atm.Service.Id, g52.hostExtId, g52.profile.MemberId)

		logger.Service.Zap.Infow("GameUser52 Login Success",
			"GameUser52", g52.secWebSocketKey,
			"HostId", g52.profile.HostId,
			"HostExtId", g52.hostExtId,
			"MemberId", g52.profile.MemberId,
			"MemberName", g52.profile.MemberName,
			"Avatar", g52.profile.Avatar,
		)

		wallet.Service.Open(
			wallet.Builder().
				SetSecWebSocketKey(g52.secWebSocketKey).
				SetHostId(g52.profile.HostId).
				SetHostExtId(g52.hostExtId).
				SetMemberId(g52.profile.MemberId).
				SetMemberName(g52.profile.MemberName).
				SetBalance(g52.profile.Balance).
				SetCategory(g52.profile.WalletType).
				SetPurposeMajor(wallet.WalletSharedFish).
				SetPurposeMinor(4).
				SetGuest(g52.profile.GuestEnable).
				SetHandler(g52).
				SetDB(g52.hostExtId).
				SetToken(g52.profile.Token).
				Build(),
		)

		if g52.profile.Avatar == "" && g52.profile.GuestEnable == auth.GuestOff {
			g52.profile.Avatar = avatar.Service.Create(
				g52.secWebSocketKey,
				g52.hostExtId,
				g52.profile.HostId,
				g52.profile.MemberId,
			)
		}

		twin.New(
			g52.secWebSocketKey,
			g52.bankerUuid,
			g52.profile.MemberId,
			g52.profile.HostId,
			g52.hostExtId,
			g52.gameRoomUuid,
			g52.controllerId,
			g52.subGameId,
			g52.seat,
			g52.profile.GuestEnable,
			g52.accountingSn,
		)

		if p := playerinfo.Service.GetOrCreate(g52.profile.HostId, g52.profile.MemberId, g52.secWebSocketKey); p != nil {
			wallet.Service.SetToken(p.SecWebSocketKey, g52.profile.Token)
		}

	case wallet.ActionWalletOpened:

		if g52.profile.GuestEnable == auth.GuestOff {
			fluxData := &flux_proto.FluxAction{
				Name: wallet.ActionWalletOpened,
				From: wallet52.Service.Id,
				To:   postman.SERVER_TRIGGER,
			}

			fluxData.Payload = append(fluxData.Payload, []byte(g52.secWebSocketKey))
			fluxData.Payload = append(fluxData.Payload, []byte(g52.profile.HostId))
			fluxData.Payload = append(fluxData.Payload, []byte(g52.hostExtId))
			fluxData.Payload = append(fluxData.Payload, []byte(g52.profile.MemberId))
			fluxData.Payload = append(fluxData.Payload, []byte(g52.profile.MemberName))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatUint(g52.profile.Balance, 10)))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatInt(int64(g52.profile.WalletType), 10)))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatInt(int64(wallet.WalletSharedFish), 10)))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatInt(4, 10)))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatInt(int64(g52.profile.GuestEnable), 10)))

			fluxDataByte, _ := proto.Marshal(fluxData)

			postman.Service.Pub(fluxDataByte)
		}

		flux.Send(auth.EMSGID_eLoginRecall, g52.secWebSocketKey, auth.Service.Id, true)

	case auth.EMSGID_eLoginRecall:
		g.SendAction(action)

	case lobbysetting.EMSGID_eLobbyConfigRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()
		gameid := lobbysetting52.Service.GameId(g52.secWebSocketKey)
		g52.gameID = gameid
		if maintain.Service.CheckMaintain(g52.secWebSocketKey, gameid, g52.hostExtId, maintain.Card) ||
			blacklist.Service.CheckBan(g52.secWebSocketKey, g52.hostExtId, g52.profile.HostId, g52.profile.MemberId) {
			return
		}
		if g52.isGaming {
			return
		}
		recovery, isGaming := g52.gameRecovery(gameid)

		g52.isGaming = isGaming

		if g52.gameRoomUuid != "" && !g52.isGaming {
			if lobbysetting52.Service.AutoATM(g52.secWebSocketKey) {
				if g52.profile.WalletType != wallet.CategoryHost {
					flux.Send(atm.ActionAtmAutoWithdraw, g52.secWebSocketKey, atm.Service.Id, uint8(100), g52.hostExtId, g52.profile.MemberId, uint64(0))
				} else if g52.accountingSn != 0 {
					wallet.Service.Refund(g52.secWebSocketKey, g52.accountingSn, true)
					flux.Send(accounting.ActionAccountingDelete, g52.secWebSocketKey, accounting.Service.HashId(g52.secWebSocketKey, g52.accountingSn))
				}
			}
			flux.Send(auth.EMSGID_eBroadcastPlayerOut, g52.secWebSocketKey, g52.gameRoomUuid, auth.Service.BroadcastPlayerOut(
				g52.gameRoomUuid,
				g52.secWebSocketKey,
				g52.profile.MemberName,
				g52.profile.Avatar,
				uint32(g52.seat),
				uint64(0),
			))

			switch g52.gameRoomType {
			case banker.FRIEND_ROOM:
				flux.Send(gameuser.ActionLeaveGameRoomCall, g52.secWebSocketKey, g52.gameRoomUuid, g52.secWebSocketKey)

			case banker.GAME_ROOM:
				flux.Send(gameuser.ActionLeaveGameRoomCall, g52.secWebSocketKey, g52.controllerId, g52.gameRoomUuid)

			default:
				panic("ERROR GAME ROOM TYPE " + g52.secWebSocketKey)
			}
		}

		cent, errCent := wallet.Service.Cent(g52.secWebSocketKey)
		if errCent != nil {
			logger.Service.Zap.Errorw(atm.Atm_GET_CENT_FAILED,
				"GameUser", g52.secWebSocketKey,
				"Error", errCent,
			)
			errorcode.Service.Fatal(g52.secWebSocketKey, atm.Atm_GET_CENT_FAILED)
		}
		balance, errBalance := wallet.Service.Balance(g52.secWebSocketKey)
		if errBalance != nil {
			logger.Service.Zap.Errorw(GameUser52_GET_CENT_FAILED,
				"GameUser", g52.secWebSocketKey,
				"BankerUuid", g52.bankerUuid,
				"GameRoomUuid", g52.gameRoomUuid,
				"IsWaiting", g52.isWaiting,
				"IsGaming", g52.isGaming,
			)
			errorcode.Service.Fatal(g52.secWebSocketKey, GameUser52_GET_CENT_FAILED)
			return
		}

		dataByte := action.Payload()[0].([]byte)

		data := &lobby_setting52_proto.ConfigRecall{}

		if err := proto.Unmarshal(dataByte, data); err != nil {
			logger.Service.Zap.Errorw(lobbysetting.LobbySetting_CONFIG_RECALL_PROTO_INVALID,
				"GameUser", g52.secWebSocketKey,
			)
			errorcode.Service.Fatal(g52.secWebSocketKey, lobbysetting.LobbySetting_CONFIG_RECALL_PROTO_INVALID)
			return
		}
		totalBalance := balance + cent
		data.Cent = cent
		data.Balance = totalBalance
		data.PlayerInfo = &auth_proto.PlayerInfo{
			Id:       g52.secWebSocketKey,
			Balance:  balance,
			Name:     g52.profile.MemberName,
			Avatar:   g52.profile.Avatar,
			Visible:  nil,
			WinCount: 0,
		}
		data.WalletType = int32(g52.profile.WalletType)

		switch g52.profile.MemberType {
		case 0:
			var roomInfo []*lobby_setting52_proto.ConfigRecall_RoomInfo
			for i := 0; i < 6; i++ {
				if data.RoomInfo[i].BalanceLimit != 0 {
					roomInfo = append(roomInfo, data.RoomInfo[i])
				}
			}
			data.RoomInfo = roomInfo
		case 1:
			var roomInfo []*lobby_setting52_proto.ConfigRecall_RoomInfo
			for i := 6; i < 12; i++ {
				if data.RoomInfo[i].BalanceLimit != 0 {
					roomInfo = append(roomInfo, data.RoomInfo[i])
				}
			}
			data.RoomInfo = roomInfo
		}

		if g52.isGaming {
			data.StatusCode = common_proto.Status_kInvalid
			data.ResumeGame = &lobby_setting52_proto.ConfigRecall_ResumeGame{
				PlayerData:  make([]*probability_proto.PlayerData, 0),
				PlayerInfo:  make([]*auth_proto.PlayerInfo, 0),
				WaitingTime: make([]uint32, 0),
			}
			data.ResumeGame.GameRecovery = recovery
			g52.bankerUuid = recovery.Snapshot.BankerUuid
			g52.gameRoomUuid = recovery.Snapshot.RoomUuid
			g52.gameRoomType = recovery.Snapshot.RoomType
			g52.subGameId = recovery.Snapshot.SubgameId
			g52.seat = int(recovery.Snapshot.Seat)
			g52.isGaming = true
			flux.Send(twin.ActionTwinResume, g52.secWebSocketKey, g52.secWebSocketKey,
				g52.bankerUuid,
				g52.profile.MemberId,
				g52.profile.HostId,
				g52.hostExtId,
				g52.gameRoomUuid,
				g52.gameRoomType,
				g52.controllerId,
				g52.subGameId,
				g52.seat,
				g52.profile.GuestEnable,
				g52.accountingSn,
				g52.blacklistRoundCount,
			)
			flux.Send(banker.ActionPlayerResumeGame, g52.secWebSocketKey, recovery.Snapshot.BankerUuid, data)
			return
		}

		if data.StatusCode == common_proto.Status_kSuccess {
			flux.Send(gameuser.ActionJoinLobbyRoomCall, g52.secWebSocketKey, g52.controllerId, "")
			g52.isWaiting = false
			dataByte, _ := proto.Marshal(data)
			g.SendByte(dataByte)
		}

	case gameuser.ActionJoinLobbyRoomRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		g52.seat = -1
		g52.gameRoomUuid = ""
		g52.gameRoomType = ""
		g52.isWaiting = false
		g52.isGaming = false
		g52.lobbyRoomUuid = action.Payload()[0].(string)

	case gameuser.ActionLeaveLobbyRoomRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		g52.lobbyRoomUuid = ""

	case gamesetting.EMSGID_eGameConfigRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		dataByte := action.Payload()[0].([]byte)

		data := &game_settin52_proto.ConfigRecall{}

		if err := proto.Unmarshal(dataByte, data); err != nil {
			logger.Service.Zap.Errorw(gamesetting.GameSetting_CONFIG_RECALL_PROTO_INVALID,
				"GameUser", g52.secWebSocketKey,
			)
			errorcode.Service.Fatal(g52.secWebSocketKey, gamesetting.GameSetting_CONFIG_RECALL_PROTO_INVALID)
			return
		}

		if data.StatusCode != common_proto.Status_kSuccess {
			g.SendByte(dataByte)
			return
		}
		gameid := lobbysetting52.Service.GameId(g52.secWebSocketKey)
		g52.gameID = gameid
		if maintain.Service.CheckMaintain(g52.secWebSocketKey, gameid, g52.hostExtId, maintain.Card) ||
			blacklist.Service.CheckBan(g52.secWebSocketKey, g52.hostExtId, g52.profile.HostId, g52.profile.MemberId) {
			if lobbysetting52.Service.AutoATM(g52.secWebSocketKey) {
				if g52.profile.WalletType != wallet.CategoryHost {
					flux.Send(atm.ActionAtmAutoWithdraw, g52.secWebSocketKey, atm.Service.Id, uint8(100), g52.hostExtId, g52.profile.MemberId, uint64(0))
				} else if g52.accountingSn != 0 {
					wallet.Service.Refund(g52.secWebSocketKey, g52.accountingSn, true)
					flux.Send(accounting.ActionAccountingDelete, g52.secWebSocketKey, accounting.Service.HashId(g52.secWebSocketKey, g52.accountingSn))
				}
			}
			return
		}
		recovery, isGaming := g52.gameRecovery(gameid)

		g52.isGaming = isGaming

		if recovery != nil {
			recoveryByte, _ := proto.Marshal(data)
			g.SendByte(recoveryByte)
		}

		if g52.lobbyRoomUuid != "" {
			flux.Send(lobbyroom.ActionLobbyRoomLeaveCall, g52.secWebSocketKey, g52.controllerId,
				g52.lobbyRoomUuid,
				false,
			)
		}

		if !g52.isWaiting {

			cent, err := wallet.Service.CentCache(g52.secWebSocketKey)
			balance, err := wallet.Service.BalanceCache(g52.secWebSocketKey)

			if err != nil {
				logger.Service.Zap.Errorw("BUG",
					"GameUser", g52.secWebSocketKey,
					"Error", err,
				)
				panic(g52.secWebSocketKey + err.Error())
			}

			data.Cent = cent
			data.Balance = balance
			data.PlayerInfo = &auth_proto.PlayerInfo{
				Id:       g52.secWebSocketKey,
				Balance:  cent,
				Name:     g52.profile.MemberName,
				Avatar:   g52.profile.Avatar,
				Visible:  nil,
				WinCount: 0,
			}

			g52.gameConfigRecall = data
			g52.isWaiting = true
			g52.canDeleteAccounting = true
			g52.gameRoomType = banker.GAME_ROOM
			blacklistValue := uint32(blacklist.Service.Check(g52.hostExtId, g52.profile.HostId, g52.profile.MemberId, "CARD", g52.gameID))
			r, _ := rand.Int(rand.Reader, big.NewInt(100))
			isIsolated := r.Int64() < int64(gamesetting52.Service.IsolateRate(g52.secWebSocketKey))

			flux.Send(gameuser.ActionJoinGameRoomCall, g52.secWebSocketKey, g52.controllerId,
				g52.hostExtId,
				g52.profile.Avatar,
				g52.ipAddress,
				uint64(data.Bet),
				blacklistValue,
				g52.profile.HostId,
				g52.profile.MemberType,
				isIsolated,
				gamesetting52.Service.BlacklistRoundCount(g52.secWebSocketKey),
				gamesetting52.Service.BlacklistTriggerCount(g52.secWebSocketKey),
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

			gamerecovery52.Service.Update(
				g52.secWebSocketKey,
				"",
				"",
				"",
				-1,
				int32(-1),
				gamerecovery52.IDLE,
				g52.blacklistRoundCount,
			)
		} else {
			g52.lobbyRoomUuid = ""
			g52.gameRoomUuid = gameRoomUuid
			g52.seat = seat
			g52.isWaiting = true
			g52.isGaming = false
			g52.gameRoomType = gameRoomType
			g52.subGameId = gamesetting52.Service.SubGameId(g52.secWebSocketKey)

			gamerecovery52.Service.Update(
				g52.secWebSocketKey,
				g52.gameRoomUuid,
				g52.gameRoomType,
				g52.bankerUuid,
				g52.subGameId,
				int32(g52.seat),
				gamerecovery52.IDLE,
				g52.blacklistRoundCount,
			)
		}

		if g52.gameConfigRecall != nil && gameRoomType == banker.GAME_ROOM {
			g52.gameConfigRecall.RoomUuid = g52.gameRoomUuid
			g52.gameConfigRecall.PlayerInfo.Seat = uint32(g52.seat)
			dataByte, _ := proto.Marshal(g52.gameConfigRecall)
			g.SendByte(dataByte)

			flux.Send(auth.EMSGID_eBroadcastPlayerIn, g52.secWebSocketKey, g52.gameRoomUuid, auth_proto.PLAYER_TYPE_GAME)

			return
		}

	case gameuser.ActionLeaveGameRoomRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		g52.gameRoomUuid = ""
		g52.gameRoomType = ""
		g52.seat = -1
		g52.isWaiting = false
		g52.isGaming = false
		g52.subGameId = -1

		gamerecovery52.Service.Update(
			g52.secWebSocketKey,
			g52.gameRoomUuid,
			g52.gameRoomType,
			g52.bankerUuid,
			g52.subGameId,
			int32(g52.seat),
			gamerecovery52.IDLE,
			g52.blacklistRoundCount,
		)

	case errorcode.ActionErrorCode:
		if g52.profile != nil {
			dataByte := action.Payload()[0].([]byte)

			data := &errorcode_proto.Error{}

			proto.Unmarshal(dataByte, data)

			if data.Code == sessionmanager.SessionManager_DUPICATE_SESSION {
				flux.Send(sessionmanager.SessionManager_DUPICATE_SESSION, g52.secWebSocketKey, atm.Service.Id,
					g52.hostExtId,
					g52.profile.MemberId,
				)
			}
		}

		g.SendAction(action)

		flux.Send(auth.ActionUserDisconnect, g52.secWebSocketKey, gameuser.Service.Id, g52.secWebSocketKey)

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
			logger.Service.Zap.Errorw(GameUser52_ROUND_START_PROTO_INVALID,
				"GameUser", g52.secWebSocketKey,
				"GameRoomUuid", gameRoomUuid,
				"Seat", g52.seat,
				"BankerUuid", g52.bankerUuid,
				"IsGaming", g52.isGaming,
				"IsWaiting", g52.isWaiting,
			)
			errorcode.Service.Fatal(g52.secWebSocketKey, GameUser52_ROUND_START_PROTO_INVALID)
			return
		}

		for _, v := range data.PlayerInfos {
			if v.Id == g52.secWebSocketKey {
				g52.seat = int(v.Seat)
				g52.gameRoomUuid = gameRoomUuid
			}
		}

		if g52.seat < 0 || g52.gameRoomUuid == "" || g52.bankerUuid == "" {
			logger.Service.Zap.Errorw("ERROR SEAT",
				"GameUser", g52.secWebSocketKey,
				"GameRoomUuid", gameRoomUuid,
				"Seat", g52.seat,
				"BankerUuid", g52.bankerUuid,
				"IsGaming", g52.isGaming,
				"IsWaiting", g52.isWaiting,
			)
			panic("ERROR SEAT : " + g52.secWebSocketKey)
			return
		}
		flux.Send(idle.ActionIdleTimeoutReset, g52.secWebSocketKey, idle.Service.HashId(g52.secWebSocketKey),
			g52.secWebSocketKey,
			gamesetting52.Service.Idle(g52.secWebSocketKey),
		)

		g.SendAction(action)

		logger.Service.Zap.Infow("GameUser52 Round Start",
			"GameUser", g52.secWebSocketKey,
			"GameRoomUuid", g52.gameRoomUuid,
			"Seat", g52.seat,
			"BankerUuid", g52.bankerUuid,
			"AccountingSn", g52.accountingSn,
		)
		flux.Send(banker.ActionBankerDeal, g52.secWebSocketKey, g52.bankerUuid, g52.seat)

		d := draw.Builder().
			SetBankerUuid(g52.bankerUuid).
			SetSecWebSocketKey(g52.secWebSocketKey).
			SetGameRoomUuid(g52.gameRoomUuid).
			SetGameRoomType(g52.gameRoomType).
			SetSeat(int32(g52.seat)).
			SetWaitingTime(gamesetting52.Service.DrawCardsWaitingTime(g52.secWebSocketKey)).
			SetKind(draw.PLAYER).
			Build()

		flux.Send(draw.ActionDrawCreate, g52.secWebSocketKey, draw.Service.Id, d)

		p := playcards.Builder().
			SetBankerUuid(g52.bankerUuid).
			SetSecWebSocketKey(g52.secWebSocketKey).
			SetGameRoomUuid(g52.gameRoomUuid).
			SetGameRoomType(g52.gameRoomType).
			SetSeat(int32(g52.seat)).
			SetWaitingTime(gamesetting52.Service.PlayCardsWaitingTime(g52.secWebSocketKey)).
			SetKind(playcards.PLAYER).
			SetPlayType(playcards.TYPE_PLAYCARD).
			Build()

		flux.Send(playcards.ActionPlayCardsCreate, g52.secWebSocketKey, playcards.Service.Id, p)

	case banker.EMSGID_eRoundEnd:
		g.SendAction(action)

		if g52.profile != nil {
			if maintain.Service.CheckMaintain(g52.secWebSocketKey, g52.gameID, g52.hostExtId, maintain.Card) ||
				blacklist.Service.CheckBan(g52.secWebSocketKey, g52.hostExtId, g52.profile.HostId, g52.profile.MemberId) {
				return
			}
		} else {
			logger.Service.Zap.Errorw(gameuser.GameUser_PROFILE_NIL,
				"GameUser", g52.secWebSocketKey,
				"HostExtId", g52.hostExtId,
				"GameRoomUuid", g52.gameRoomUuid,
				"IsGaming", g52.isGaming,
				"IsWaiting", g52.isWaiting,
			)
			errorcode.Service.Fatal(g52.secWebSocketKey, gameuser.GameUser_PROFILE_NIL)
		}

		g52.balanceLimit()

	case banker.EMSGID_ePlayerRoundStart:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		g52.state = STATE_START
		hands := action.Payload()[4].([]int)
		g52.hands = hands
		flux.Send(idle.ActionIdleTimeoutReset, g52.secWebSocketKey, idle.Service.HashId(g52.secWebSocketKey),
			g52.secWebSocketKey,
			gamesetting52.Service.Idle(g52.secWebSocketKey),
		)
		g.SendAction(action)
		flux.Send(draw.ActionDrawReset, g52.secWebSocketKey, draw.Service.Id)

	case banker.EMSGID_eBroadcastPlayerRoundStart:
		g.SendAction(action)

	case draw.EMSGID_eDrawTimeout:
		fallthrough
	case draw.EMSGID_eDrawRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		card := action.Payload()[1].(int)
		g52.hands = append(g52.hands, card)
		g52.state = STATE_DRAW

		g.SendAction(action)
		time.Sleep(1 * time.Second)
		flux.Send(playcards.ActionPlayCardsReset, g52.secWebSocketKey, playcards.Service.Id,
			playcards.TYPE_PLAYCARD,
			gamesetting52.Service.PlayCardsWaitingTime(g52.secWebSocketKey),
			int32(-1), false,
		)

	case draw.EMSGID_eBroadcastDrawTimeout:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()
		g.SendAction(action)

	case draw.EMSGID_eBroadcastDrawRecall:
		g.SendAction(action)

	case playcards.EMSGID_ePlayCardsTimeout:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		g52.state = STATE_END

		g.SendAction(action)
		time.Sleep(banker.PLAYER_ROUND_START_DELAY * time.Second)

		flux.Send(banker.ActionPlayerRoundStart, g52.secWebSocketKey, g52.bankerUuid)

	case playcards.EMSGID_eBroadcastPlayCardsTimeout:
		g.SendAction(action)

	case playcards.EMSGID_ePlayCardsRecall:
		g.SendAction(action)

		time.Sleep(banker.PLAYER_ROUND_START_DELAY * time.Second)

		flux.Send(banker.ActionPlayerRoundStart, g52.secWebSocketKey, g52.bankerUuid)

	case playcards.EMSGID_eBroadcastPlayCardsRecall:
		g.SendAction(action)

	case banker.ActionBankerDeal:
		cards := action.Payload()[0].(*probability_proto.PlayerData)
		pool := action.Payload()[1].(int)
		g52.hands = banker.ToIntArr(cards.Cards.Hands)
		logger.Service.Zap.Infow("Banker Deal",
			"GameUser", g52.secWebSocketKey,
			"BankerUuid", g52.bankerUuid,
			"GameRoomUuid", g52.gameRoomUuid,
			"Seat", g52.seat,
			"pool", pool,
		)

		if g52.seat < 0 {
			// something error
			gamerecovery52.Service.Update(
				g52.secWebSocketKey,
				g52.gameRoomUuid,
				g52.gameRoomType,
				g52.bankerUuid,
				g52.subGameId,
				int32(g52.seat),
				gamerecovery52.IDLE,
				g52.blacklistRoundCount,
			)
		} else {
			data := &banker_proto.Deal{
				Msgid:    common52_proto.EMSGID_eDeal,
				Cards:    cards.Cards,
				RoomUuid: g52.gameRoomUuid,
				Pool:     int32(pool),
				Seat:     int32(g52.seat),
			}
			dataByte, _ := proto.Marshal(data)
			g.SendByte(dataByte)
		}

	case banker.ActionBankerStart:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		g52.isWaiting = false
		g52.isGaming = true

		switch action.Payload()[0].(type) {
		case string:
			g52.bankerUuid = action.Payload()[0].(string)

		case []byte:
			g52.bankerUuid = string(action.Payload()[0].([]byte))
			flux.Send(banker.ActionBankerStart, g52.secWebSocketKey, g52.gameRoomUuid, g52.bankerUuid)
		}

		cent, err := wallet.Service.Cent(g52.secWebSocketKey)

		if err != nil {
			panic("ERROR WALLET CENT")
		}

		if g52.profile.WalletType != wallet.CategoryHost {
			if a := accounting.Builder().
				SetSecWebSocketKey(g52.secWebSocketKey).
				SetHostExtId(g52.hostExtId).
				SetGuestEnable(g52.profile.GuestEnable == auth.GuestOn).
				SetHostId(g52.profile.HostId).
				SetGameId(gamesetting52.Service.GameId(g52.secWebSocketKey)).
				SetSubgameId(uint32(gamesetting52.Service.SubGameId(g52.secWebSocketKey))).
				SetMemberId(g52.profile.MemberId).
				SetInitCent(cent).
				SetDB(g52.hostExtId).
				SetKind(accounting.PLAYER).
				SetHandler(&accounting52.Accounting52{}).
				Build(); a != nil {

				g52.accountingSn = a.Start.Sn
			}
		}

		if g52.accountingSn != 0 {
			if g52.profile.WalletType != wallet.CategoryHost {
				isDone := make(chan bool)
				flux.Send(twin.ActionTwinAccountingSn, g52.secWebSocketKey, g52.secWebSocketKey, g52.accountingSn, isDone)
				<-isDone
			}

			switch g52.gameRoomType {
			case banker.FRIEND_ROOM:
				flux.Send(banker.ActionBankerAccountingSn, g52.secWebSocketKey, g52.gameRoomUuid, g52.accountingSn)

			case banker.GAME_ROOM:
				flux.Send(banker.ActionBankerAccountingSn, g52.secWebSocketKey, g52.bankerUuid, g52.accountingSn)

			default:
				logger.Service.Zap.Errorw("ERROR TYPE GAME ROOM",
					"GameUser", g52.secWebSocketKey,
					"GameRoom", g52.gameRoomUuid,
					"BankerUuid", g52.bankerUuid,
					"AccountingSN", g52.accountingSn,
				)
				panic("ERROR TYPE GAME ROOM" + g52.secWebSocketKey)
			}
		}

		if g52.profile.GuestEnable == auth.GuestOn {
			switch g52.gameRoomType {
			case banker.FRIEND_ROOM:
				flux.Send(banker.ActionBankerAccountingSn, g52.secWebSocketKey, g52.gameRoomUuid, g52.accountingSn)

			case banker.GAME_ROOM:
				flux.Send(banker.ActionBankerAccountingSn, g52.secWebSocketKey, g52.bankerUuid, uint64(0))

			default:
				panic("ERROR TYPE GAME ROOM")
			}
		}

		if g52.accountingSn == 0 && g52.profile.GuestEnable == auth.GuestOff {
			logger.Service.Zap.Errorw(GameUser52_ACCOUNTING_SN_ZERO,
				"GameUser", g52.secWebSocketKey,
				"AccountingSn", g52.accountingSn,
				"Guest", g52.profile.GuestEnable,
			)
			errorcode.Service.Fatal(g52.secWebSocketKey, GameUser52_ACCOUNTING_SN_ZERO)
			return
		}

		gamerecovery52.Service.Update(
			g52.secWebSocketKey,
			g52.gameRoomUuid,
			g52.gameRoomType,
			g52.bankerUuid,
			g52.subGameId,
			int32(g52.seat),
			gamerecovery52.GAMING,
			g52.blacklistRoundCount,
		)

	case probability.EMSGID_eBroadcastResult:
		g.SendAction(action)

		g.RwMutex.Lock()

		g52.bankerUuid = ""
		g52.isWaiting = false
		g52.isGaming = false
		g52.accountingSn = 0
		g52.canDeleteAccounting = true

		g.RwMutex.Unlock()

	case heartbeat.ActionHeartBeatRecall:
		g.SendAction(action)

	case auth.ActionAuthNotify:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		g52.isWaiting = false
		g52.isGaming = false

		gamerecovery52.Service.Update(
			g52.secWebSocketKey,
			g52.gameRoomUuid,
			g52.gameRoomType,
			g52.bankerUuid,
			g52.subGameId,
			int32(g52.seat),
			gamerecovery52.IDLE,
			g52.blacklistRoundCount,
		)
		cent, err := wallet.Service.CentCache(g52.secWebSocketKey)
		if err == nil {
			if wallet.Service.WalletCategory(g52.secWebSocketKey) != wallet.CategoryHost && cent > 0 {
				flux.Send(atm.ActionAtmAutoWithdraw, g52.secWebSocketKey, atm.Service.Id, uint8(100), g52.hostExtId, g52.profile.MemberId, uint64(0))
			}
		}
		g.SendAction(action)

	case waitingroom.EMSGID_eWaitingCountdown:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		g52.isWaiting = true
		g52.isGaming = false
		g52.canDeleteAccounting = true

		if g52.gameRoomUuid != "" {
			g.SendAction(action)
		}

	case auth.EMSGID_eBroadcastPlayerIn:
		fallthrough
	case auth.EMSGID_eBroadcastPlayerOut:
		switch action.Payload()[0].(type) {
		case [][]byte:
			g52.postman(action, g)

		default:
			g.SendAction(action)
		}

	case friendroom.EMSGID_eFriendRoomJoinRecall:
		dataByte := action.Payload()[0].([]byte)

		data := &friend_room_proto.FriendRoomJoinRecall{}

		proto.Unmarshal(dataByte, data)

		if data.StatusCode == common_proto.Status_kSuccess {
			g52.gameRoomUuid = action.Key().From()
			g52.gameRoomType = banker.FRIEND_ROOM
		}

		g.SendAction(action)

	case friendroom.EMSGID_eFriendRoomLeaveRecall:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		flux.Send(gameuser.ActionLeaveGameRoomCall, g52.secWebSocketKey, g52.gameRoomUuid, g52.secWebSocketKey)

		gamerecovery52.Service.Update(
			g52.secWebSocketKey,
			g52.gameRoomUuid,
			g52.gameRoomType,
			g52.bankerUuid,
			g52.subGameId,
			int32(g52.seat),
			gamerecovery52.IDLE,
			g52.blacklistRoundCount,
		)

		g52.gameRoomUuid = ""
		g52.gameRoomType = ""
		g52.seat = -1
		g52.isWaiting = false
		g52.isGaming = false
		g.SendAction(action)

	case friendroom.EMSGID_eFriendRoomHostChanged:
		g.SendAction(action)

	case friendroom.EMSGID_eFriendRoomDestroy:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()
		if lobbysetting52.Service.AutoATM(g52.secWebSocketKey) {
			// TODO JOHNNY 以後可能會有要自動儲值幾%的...
			flux.Send(atm.ActionAtmAutoWithdraw, g52.secWebSocketKey, atm.Service.Id, uint8(100), g52.hostExtId, g52.profile.MemberId, uint64(0))
		}
		flux.Send(gameuser.ActionLeaveGameRoomCall, g52.secWebSocketKey, g52.gameRoomUuid, g52.secWebSocketKey)

		friendroom.Service.Delete(g52.secWebSocketKey)

		gamerecovery52.Service.Update(
			g52.secWebSocketKey,
			g52.gameRoomUuid,
			g52.gameRoomType,
			g52.bankerUuid,
			g52.subGameId,
			int32(g52.seat),
			gamerecovery52.IDLE,
			g52.blacklistRoundCount,
		)

		g52.gameRoomUuid = ""
		g52.gameRoomType = ""
		g52.seat = -1
		g52.isWaiting = false
		g52.isGaming = false

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
		g52.isGaming = true
		g52.isWaiting = false
		g52.canDeleteAccounting = false
		gamerecovery52.Service.Update(
			g52.secWebSocketKey,
			g52.gameRoomUuid,
			g52.gameRoomType,
			g52.bankerUuid,
			g52.subGameId,
			int32(g52.seat),
			gamerecovery52.GAMING,
			g52.blacklistRoundCount,
		)

	case avatar.EMSGID_eAvatarRecall:
		avatar := action.Payload()[1].(int32)
		g52.profile.Avatar = strconv.Itoa(int(avatar))

		g.SendAction(action)

	case gameroom.ActionKickOut:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		gameRoomUuid := action.Payload()[0].(string)
		g52.kickOut(gameRoomUuid)

	case twin.ActionUpdateBlacklistRoundCount:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		g52.blacklistRoundCount = action.Payload()[0].(uint32)
	}
}

func (g52 *GameUser52) postman(action *flux.Action, g *gameuser.GameUser) {
	dataByte := action.Payload()[0].([][]byte)
	g.SendByte(dataByte[0])
}

func (g52 *GameUser52) balanceLimit() (cent uint64) {
	if g52.gameRoomUuid == "" {
		return
	}

	balance, balanceErr := wallet.Service.Balance(g52.secWebSocketKey)
	if balanceErr != nil {
		logger.Service.Zap.Errorw(GameUser52_GET_CENT_FAILED,
			"GameUser", g52.secWebSocketKey,
			"BankerUuid", g52.bankerUuid,
			"GameRoomUuid", g52.gameRoomUuid,
			"IsWaiting", g52.isWaiting,
			"IsGaming", g52.isGaming,
		)
		errorcode.Service.Fatal(g52.secWebSocketKey, GameUser52_GET_CENT_FAILED)
		return
	}
	cent, centErr := wallet.Service.Cent(g52.secWebSocketKey)

	if centErr != nil {
		logger.Service.Zap.Errorw(GameUser52_GET_CENT_FAILED,
			"GameUser", g52.secWebSocketKey,
			"BankerUuid", g52.bankerUuid,
			"GameRoomUuid", g52.gameRoomUuid,
			"IsWaiting", g52.isWaiting,
			"IsGaming", g52.isGaming,
		)
		errorcode.Service.Fatal(g52.secWebSocketKey, GameUser52_GET_CENT_FAILED)
		return 0
	}

	l := gamesetting52.Service.BalanceLimit(g52.secWebSocketKey)

	if cent+balance < uint64(l) {
		logger.Service.Zap.Infow("No Money",
			"GameUser", g52.secWebSocketKey,
			"BankerUuid", g52.bankerUuid,
			"Cent", cent,
			"BalanceLimit", l,
			"GameRoomUuid", g52.gameRoomUuid,
			"IsWaiting", g52.isWaiting,
			"IsGaming", g52.isGaming,
		)

		flux.Send(auth.EMSGID_eBroadcastPlayerOut, g52.secWebSocketKey, g52.gameRoomUuid, auth.Service.BroadcastPlayerOut(
			g52.gameRoomUuid,
			g52.secWebSocketKey,
			g52.profile.MemberName,
			g52.profile.Avatar,
			uint32(g52.seat),
			cent,
		))
	}

	return cent + balance
}

func (g52 *GameUser52) gameRecovery(gameId string) (*gamerecovery52_proto.GameRecovery, bool) {
	if data := gamerecovery52.Service.Check(
		gamerecovery.Builder().
			SetSecWebSocketKey(g52.secWebSocketKey).
			SetHostId(g52.profile.HostId).
			SetHostExtId(g52.hostExtId).
			SetServerId(gamerecovery52.Service.ServerId).
			SetGameId(gameId).
			SetMemberId(g52.profile.MemberId).
			SetGuest(g52.profile.GuestEnable == auth.GuestOn).
			SetDB(g52.hostExtId).
			Build(),
	); data != nil {
		logger.Service.Zap.Infow("Check Game Recovery",
			"GameUser", g52.secWebSocketKey,
			"GameRoomUuid", g52.gameRoomUuid,
			"BankerUuid", g52.bankerUuid,
			"Status", data.Snapshot.Status == gamerecovery52.GAMING,
			"IsGaming", g52.isGaming,
			"IsWaiting", g52.isWaiting,
		)
		return data, data.Snapshot.Status == gamerecovery52.GAMING
	}
	return nil, false
}

func (g52 *GameUser52) CleanDataHandler(g *gameuser.GameUser) {
	if g52.profile != nil {
		session.Service.End(
			g52.secWebSocketKey,
			g52.profile.HostId,
			g52.hostExtId,
			g52.profile.MemberId,
			0, // TODO JOHNNY need implement
		)
	} else {
		logger.Service.Zap.Warnw(gameuser.GameUser_PROFILE_NIL,
			"GameUser", g52.secWebSocketKey,
			"HostExtId", g52.hostExtId,
			"IsGaming", g52.isGaming,
			"IsWaiting", g52.isWaiting,
		)
	}

	if !g52.isGaming {
		flux.Send(twin.ActionTwinDestroy, g52.secWebSocketKey, g52.secWebSocketKey, g52.gameRoomUuid, g52.gameRoomType)
	}
	sessionmanager.Service.End(g52.secWebSocketKey, g52.hostExtId)

	flux.Send(idle.ActionIdleTimeoutStop, g52.secWebSocketKey, idle.Service.Id, g52.secWebSocketKey)
	lobbysetting.Service.Delete(g52.secWebSocketKey)
	mediator.Service.Delete(g52.secWebSocketKey)

}

func (g52 *GameUser52) leaveRooms() {
	logger.Service.Zap.Infow("leaveRooms",
		"GameUser", g52.secWebSocketKey,
		"GameRoomUuid", g52.gameRoomUuid,
		"LobbyRoomUuid", g52.lobbyRoomUuid,
	)
	g52.isDestroy = true

	if g52.gameRoomUuid != "" {
		if g52.isWaiting {
			flux.Send(auth.EMSGID_eBroadcastPlayerOut, g52.secWebSocketKey, g52.gameRoomUuid, auth.Service.BroadcastPlayerOut(
				g52.gameRoomUuid,
				g52.secWebSocketKey,
				g52.profile.MemberName,
				g52.profile.Avatar,
				uint32(g52.seat),
				uint64(0),
			))
			flux.Send(gameuser.ActionLeaveGameRoomCall, g52.secWebSocketKey, g52.controllerId, g52.gameRoomUuid)
		}

		if g52.canDeleteAccounting && g52.accountingSn != 0 {
			wallet.Service.Refund(g52.secWebSocketKey, g52.accountingSn, true)

			flux.Send(accounting.ActionAccountingDelete, g52.secWebSocketKey, accounting.Service.HashId(g52.secWebSocketKey, g52.accountingSn))
		}
	} else {
		flux.Send(gameuser.ActionGameUserDelete, g52.secWebSocketKey, gameuser.Service.Id, g52.secWebSocketKey)
	}

	if g52.lobbyRoomUuid != "" {
		flux.Send(gameuser.ActionLeaveLobbyRoomCall, g52.secWebSocketKey, g52.controllerId, g52.lobbyRoomUuid, true)
	} else {
		flux.Send(gameuser.ActionGameUserDelete, g52.secWebSocketKey, gameuser.Service.Id, g52.secWebSocketKey)
	}

	if g52.profile != nil {
		avatar.Service.Update(g52.secWebSocketKey, g52.hostExtId, g52.profile.HostId, g52.profile.MemberId, g52.profile.Avatar)
	}
}

func (g52 *GameUser52) kickOut(gameRoomUuid string) {
	if g52.gameRoomUuid != gameRoomUuid {
		return
	}

	cent, centErr := wallet.Service.Cent(g52.secWebSocketKey)

	if centErr != nil {
		logger.Service.Zap.Errorw(GameUser52_GET_CENT_FAILED,
			"GameUser", g52.secWebSocketKey,
			"BankerUuid", g52.bankerUuid,
			"GameRoomUuid", g52.gameRoomUuid,
			"IsWaiting", g52.isWaiting,
			"IsGaming", g52.isGaming,
		)
		errorcode.Service.Fatal(g52.secWebSocketKey, GameUser52_GET_CENT_FAILED)
		return
	}

	flux.Send(auth.EMSGID_eBroadcastPlayerOut, g52.secWebSocketKey, g52.gameRoomUuid, auth.Service.BroadcastPlayerOut(
		g52.gameRoomUuid,
		g52.secWebSocketKey,
		g52.profile.MemberName,
		g52.profile.Avatar,
		uint32(g52.seat),
		cent,
	))
}

func (g52 *GameUser52) GetAccountingSnHandler(secWebSocketKey string, balance, cent, sn uint64, depositCheck bool) (accountingSn uint64) {
	if secWebSocketKey == g52.secWebSocketKey {
		accountingSn = g52.accountingSn

		logger.Service.Zap.Infow("Find AccountingSn",
			"GameUser", secWebSocketKey,
			"accountingSn", g52.accountingSn,
		)
	} else {
		accountingSn = 0

		logger.Service.Zap.Warnw(accounting.Accounting_ACCOUNTING_NOT_FOUND,
			"GameUser", secWebSocketKey,
		)
	}

	return accountingSn
}

func (g52 *GameUser52) DecreaseHandler(secWebSocketKey, uuid string, balance, cent, accountingSn uint64) {
	// do nothing
}

func (g52 *GameUser52) IncreaseHandler(secWebSocketKey, uuid string, balance, cent, accountingSn uint64) {
	// do nothing
}

func (g52 *GameUser52) EndAccountingHandler(secWebSocketKey string, checkAccountingEnd bool, walletType int, cent uint64) {
	// do nothing
}

func (g52 *GameUser52) BetErrorHandler(secWebSocketKey string, accountingSn uint64) {
	//do nothing
}
