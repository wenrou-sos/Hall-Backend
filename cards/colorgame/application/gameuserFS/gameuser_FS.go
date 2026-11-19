package gameuserFS

import (
	"colorgame-game-server/application/accountingFS"
	"colorgame-game-server/application/filter"
	"colorgame-game-server/application/gameroom"
	gameroom_proto "colorgame-game-server/application/gameroom/proto"
	"colorgame-game-server/application/gamesettingFS"
	game_settingFS_proto "colorgame-game-server/application/gamesettingFS/proto"
	"colorgame-game-server/application/lobbysettingFS"
	lobby_settingFS_proto "colorgame-game-server/application/lobbysettingFS/proto"
	"colorgame-game-server/application/lottery"
	lottery_proto "colorgame-game-server/application/lottery/proto"
	"colorgame-game-server/application/playerdata"
	playdata_proto "colorgame-game-server/application/playerdata/proto"
	"colorgame-game-server/application/playerstate"
	"colorgame-game-server/application/twin"
	"colorgame-game-server/domain/avatar"
	avatar_proto "colorgame-game-server/domain/avatar/proto"
	"colorgame-game-server/domain/bet"
	bet_proto "colorgame-game-server/domain/bet/proto"
	"colorgame-game-server/domain/probability"
	"colorgame-game-server/domain/vip"
	"colorgame-game-server/domain/walletFS"
	walletFS_proto "colorgame-game-server/domain/walletFS/proto"
	commonFS_proto "colorgame-game-server/models/proto"
	"crypto/rand"
	"math/big"
	"runtime/debug"
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
	lobby_setting_proto "gitlab.iplaystar.net/game-server/lobby-setting/proto"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/maintain"
	"gitlab.iplaystar.net/game-server/mysql"
	"gitlab.iplaystar.net/game-server/postman"
	"gitlab.iplaystar.net/game-server/session"
	sessionmanager "gitlab.iplaystar.net/game-server/session-manager"
	"gitlab.iplaystar.net/game-server/wallet"
)

const (
	CHANGE_ROOM_COUNTDOWN_TIME = 600 //換房倒數的時間(秒)
	ActionCreateAccounting     = "ActionCreateAccounting"
)

type GameUserFS struct {
	controllerId        string
	secWebSocketKey     string
	hostExtId           string
	gameRoomUuid        string
	lobbyRoomUuid       string
	gameRoomType        string
	ipAddress           string
	seat                int
	profile             *auth.MemberInfo
	gameConfigRecall    *game_settingFS_proto.ConfigRecall
	isDestroy           bool
	accountingSn        uint64
	leavingRoom         string
	leavingSeat         int
	startBalance        uint64 //for accounting
	changeRoomTimer     *changeRoomTimer
	lastGameRoomUuid    string
	currentBetRoundUuid string
	histories           [10][3]int32
	isVipChangeRoom     bool
	roomKind            string
	isGaming            bool
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
		isGaming:         false,
	}
}

func (gFS *GameUserFS) MsgHandler(g *gameuser.GameUser, msg []byte) {
	defer func() {
		if err := recover(); err != nil {
			logger.Service.Zap.Fatalw("999",
				"err", err,
				"stacktrace", string(debug.Stack()),
			)
		}
	}()

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
			//refundbet-tool新增 : 第一次進大廳清除遊戲錢包金額
			data := &lobby_setting_proto.ConfigCall{}

			if err := proto.Unmarshal(msg, data); err != nil {
				logger.Service.Zap.Errorw(lobbysetting.LobbySetting_CONFIG_CALL_PROTO_INVALID,
					"GameUser", gFS.secWebSocketKey,
					"MemberId", gFS.profile.MemberId,
					"GuestEnable", gFS.profile.GuestEnable,
				)
				errorcode.Service.Fatal(gFS.secWebSocketKey, lobbysetting.LobbySetting_CONFIG_CALL_PROTO_INVALID)
				return
			}
			hasSessionMap := gFS.checkSessionMap(gFS.hostExtId, gFS.profile.HostId, gFS.profile.MemberId, data.GameId)

			flux.Send(lobbysetting.EMSGID_eLobbyConfigRecall, gFS.secWebSocketKey, gFS.secWebSocketKey,
				lobbysetting.Service.EMSGID_eLobbyConfigCall(
					gFS.secWebSocketKey,
					gFS.profile.MemberId,
					gFS.profile.GuestEnable,
					msg,
				), hasSessionMap,
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

		state := playerstate.Service.GetState(gFS.profile.HostId, gFS.secWebSocketKey)

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
			logger.Service.Zap.Warnw(gamesetting.EMSGID_eGameConfigCall,
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
			betCall.BetType < 0 || betCall.BetType >= lottery.MAX_BET_TYPE ||
			betCall.Seat != int32(gFS.seat) ||
			betCall.Seat < 0 || betCall.Seat >= 11 ||
			gFS.isGaming == false {

			errorcode.Service.Error("bet call invalid", bet.Bet_PROTO_BET_CALL_INVAILD)
			logger.Service.Zap.Warnw("bet call invalid",
				"player secWebSocketKey", gFS.secWebSocketKey,
				"betCall index", betCall.BetIndex,
				"betCall Type", betCall.BetType,
				"betCall seat", betCall.Seat,
				"isGaming", gFS.isGaming,
			)
			return
		}

		logger.Service.Zap.Infow(v,
			"GameUserFS", gFS.secWebSocketKey,
			"HostExtId", gFS.hostExtId,
			"Seat", gFS.seat,
			"LobbyRoomUuid", gFS.lobbyRoomUuid,
			"GameRoomUuid", gFS.gameRoomUuid,
			"BetIndex", betCall.BetIndex,
			"BetType", betCall.BetType,
			"BetRoundUuid", betCall.BetRoundUuid,
		)

		flux.Send(bet.EMSGID_eBetCall, gFS.secWebSocketKey, betCall.BetRoundUuid, msg)

	case bet.EMSGID_eMultiBetCall:
		multiBetCall := &bet_proto.MultiBetCall{}
		_ = proto.Unmarshal(msg, multiBetCall)

		for _, betCall := range multiBetCall.BetCalls {
			if betCall.BetIndex < 0 || betCall.BetIndex > 3 ||
				betCall.BetType < 0 || betCall.BetType >= lottery.MAX_BET_TYPE ||
				betCall.Seat != int32(gFS.seat) ||
				gFS.isGaming == false {

				errorcode.Service.Error("bet call invalid", bet.Bet_PROTO_BET_CALL_INVAILD)
				logger.Service.Zap.Warnw("bet call invalid",
					"player secWebSocketKey", gFS.secWebSocketKey,
					"betCall index", betCall.BetIndex,
					"betCall Type", betCall.BetType,
					"betCall seat", betCall.Seat,
					"isGaming", gFS.isGaming,
				)
				return
			}
		}

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
		playerState := playerstate.Service.GetState(gFS.profile.HostId, gFS.secWebSocketKey)
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

func (gFS *GameUserFS) DeferRunReadMessageHandler(g *gameuser.GameUser) {

}

func (gFS *GameUserFS) DeferRunWriteMessageHandler(g *gameuser.GameUser) {
	g.RwMutex.Lock()
	defer g.RwMutex.Unlock()

	gFS.disconnectedFromRoom()
}

func (gFS *GameUserFS) FluxActionHandler(action *flux.Action, g *gameuser.GameUser) {
	defer func() {
		if err := recover(); err != nil {
			logger.Service.Zap.Fatalw("999",
				"err", err,
				"stacktrace", string(debug.Stack()),
			)
		}
	}()

	if gFS.secWebSocketKey != action.Key().To() {
		return
	}

	logger.Service.Zap.Infow(action.Key().Name(),
		"GameUser", gFS.secWebSocketKey,
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
			"BillCurrency", gFS.profile.BillCurrency,
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
				SetPurposeMinor(7).
				SetGuest(gFS.profile.GuestEnable).
				SetHandler(gFS).
				SetDB(gFS.hostExtId).
				SetToken(gFS.profile.Token).
				Build(),
		)

		if playerstate.Service.GetState(gFS.profile.HostId, gFS.secWebSocketKey) == nil {
			flux.Send(playerstate.ActionCreateState, gFS.secWebSocketKey, playerstate.Service.Id,
				gFS.secWebSocketKey,
				gFS.profile.HostId,
			)
		} else {
			flux.Send(playerstate.ActionUpdateConnectionState, gFS.secWebSocketKey, playerstate.Service.Id,
				gFS.secWebSocketKey,
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

		twin.New(
			gFS.secWebSocketKey,
			gFS.gameRoomUuid,
			gFS.controllerId,
			gFS.hostExtId,
			gFS.profile.MemberId,
			gFS.profile.MemberName,
			gFS.profile.HostId,
			gFS.profile.BillCurrency,
			gFS.profile.GuestEnable == auth.GuestOn,
			gFS.profile.Avatar,
		)

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
			//fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatInt(int64(wallet.WalletSharedCard89), 10)))
			fluxData.Payload = append(fluxData.Payload, []byte(strconv.FormatInt(int64(7), 10)))
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
			state := playerstate.Service.GetState(gFS.profile.HostId, gFS.secWebSocketKey)
			if state != nil {
				if state.BetRoundUuid == "" || gFS.currentBetRoundUuid != state.BetRoundUuid {
					if gFS.accountingSn != 0 {
						accountingSn := gFS.accountingSn
						gFS.accountingSn = 0
						wallet.Service.Refund(gFS.secWebSocketKey, accountingSn, true)
						flux.Send(accounting.ActionAccountingDelete, gFS.secWebSocketKey, accounting.Service.HashId(gFS.secWebSocketKey, accountingSn))
					}

					gFS.leaveRoom(gFS.seat)
				} else {
					logger.Service.Zap.Infow("delay leaving",
						"secWebSocketKey", gFS.secWebSocketKey)
					gFS.leavingRoom = gFS.gameRoomUuid
					gFS.leavingSeat = gFS.seat
				}
			}
		} else {
			switch wallet.Service.WalletCategory(gFS.secWebSocketKey) {
			case wallet.CategoryHost:
				hasSessionMap := action.Payload()[1].(bool)
				if cent, err := wallet.Service.Cent(gFS.secWebSocketKey); err == nil { //重複登入 : 重讀錢包
					if cent > 0 && !hasSessionMap {
						wallet.Service.UpdateCent(gFS.secWebSocketKey, gameid, 0)
					}
				} else {
					logger.Service.Zap.Errorw("BUG",
						"GameUser", gFS.secWebSocketKey,
						"Error", err,
					)
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
			logger.Service.Zap.Errorw("Status Error",
				"GameUser", gFS.secWebSocketKey,
				"StatusCode", data.StatusCode,
			)

			g.SendByte(dataByte)
			return
		}

		gameid := lobbysettingFS.Service.GameId(gFS.secWebSocketKey)
		if maintain.Service.CheckMaintain(gFS.secWebSocketKey, gameid, gFS.hostExtId, maintain.Card) {
			logger.Service.Zap.Errorw("maintain",
				"GameUser", gFS.secWebSocketKey,
			)
			return
		}

		balance, err := wallet.Service.BalanceCache(gFS.secWebSocketKey)

		if err != nil {
			logger.Service.Zap.Errorw(GameUserFS_GET_BALANCE_FAILED,
				"GameUser", gFS.secWebSocketKey,
				"Error", err,
			)
			errorcode.Service.Fatal(gFS.secWebSocketKey, GameUserFS_GET_BALANCE_FAILED)
		}

		gFS.startBalance = balance
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

		gFS.isGaming = true
		gFS.lobbyRoomUuid = ""
		gFS.gameRoomUuid = action.Payload()[0].(string)
		gFS.seat = action.Payload()[1].(int)
		gFS.lastGameRoomUuid = action.Payload()[2].(string)
		gFS.roomKind = action.Payload()[3].(string)
		gFS.currentBetRoundUuid = action.Payload()[4].(string)

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
		gFS.isGaming = false

		g.SendAction(action)

	case ActionCreateAccounting:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		if gFS.accountingSn != 0 {
			logger.Service.Zap.Infow("CreateAccounting Error", "GameUser", gFS.secWebSocketKey)
			return
		}

		if gFS.isGaming == false {
			logger.Service.Zap.Infow("CreateAccounting isGaming False", "GameUser", gFS.secWebSocketKey)
			return
		}

		balance, err := wallet.Service.Balance(gFS.secWebSocketKey)
		if err != nil {
			logger.Service.Zap.Errorw(gameroom.GameRoom_GET_BALANCE_FAILED, "GameUser", gFS.secWebSocketKey, "Error", err)
			errorcode.Service.Fatal(gFS.secWebSocketKey, GameUserFS_GET_BALANCE_FAILED)
			return
		}

		if a := accounting.Builder().
			SetSecWebSocketKey(gFS.secWebSocketKey).
			SetHostExtId(gFS.hostExtId).
			SetGuestEnable(gFS.profile.GuestEnable == auth.GuestOn).
			SetHostId(gFS.profile.HostId).
			SetGameId(gamesettingFS.Service.GameId(gFS.secWebSocketKey)).
			SetSubgameId(gamesettingFS.Service.RateIndex(gFS.secWebSocketKey)).
			SetMemberId(gFS.profile.MemberId).
			SetInitCent(balance).
			SetDenom(0).
			SetDB(gFS.hostExtId).
			SetKind(accounting.PLAYER).
			SetHandler(&accountingFS.AccountingFS{}).
			Build(); a != nil {
			gFS.accountingSn = a.Start.Sn
			wallet.Service.SetGameIdAndSubGameId(gFS.secWebSocketKey, gamesettingFS.Service.GameId(gFS.secWebSocketKey), int(gamesettingFS.Service.RateIndex(gFS.secWebSocketKey)))
		}
		preBet := uint64(gamesettingFS.Service.BetAreaLimit(gFS.secWebSocketKey, 0))
		if balance < preBet { //玩家金額小於預扣金額
			preBet = balance
		}
		wallet.Service.Deposit(gFS.secWebSocketKey, preBet, 0)

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

		if wallet.Service.WalletCategory(gFS.secWebSocketKey) == wallet.CategoryHost && !gFS.isVipChangeRoom {
			flux.Send(ActionCreateAccounting, gFS.secWebSocketKey, gFS.secWebSocketKey)
		}

	case bet.EMSGID_eBetRoundStart:
		/*flux.Send(idle.ActionIdleTimeoutReset,
			gFS.secWebSocketKey,
			idle.Service.HashId(gFS.secWebSocketKey),
			gFS.secWebSocketKey,
			gamesettingFS.Service.Idle(gFS.secWebSocketKey),
		)*/

		betRoundUuid := action.Payload()[1].(string)
		gFS.currentBetRoundUuid = betRoundUuid

		balance, err := wallet.Service.Balance(gFS.secWebSocketKey)

		if err != nil {
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
				gFS.secWebSocketKey,
				gFS.profile.HostId,
				betRoundUuid)
		}
		g.SendAction(action)

	case bet.EMSGID_eMultiBetRecall:
		betRoundUuid := action.Key().From()
		status := action.Payload()[1].(common_proto.Status_Code)
		if status == common_proto.Status_kSuccess {
			flux.Send(playerstate.ActionSaveBetState, gFS.secWebSocketKey, playerstate.Service.Id,
				gFS.secWebSocketKey,
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
			gFS.secWebSocketKey,
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

		if wallet.Service.WalletCategory(gFS.secWebSocketKey) == wallet.CategoryHost && gFS.accountingSn != 0 { //共用錢包
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
		gameRoomUuid := action.Payload()[3].(string)
		if gameRoomUuid == "" {
			gameRoomUuid = gFS.gameRoomUuid
		}
		data1 := &lottery_proto.BroadcastResult{} //braodcastResult
		if err := proto.Unmarshal(dataByte, data1); err != nil {
			logger.Service.Zap.Errorw(gamesetting.GameSetting_CONFIG_RECALL_PROTO_INVALID,
				"GameUser", gFS.secWebSocketKey,
				"GameRoomUuid", gFS.gameRoomUuid,
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
				flux.Send(accounting.ActionAccountingEnd, gFS.secWebSocketKey, accounting.Service.HashId(gFS.secWebSocketKey, accountingSn), data1, data2, data3, memberName, balance, gameRoomUuid)
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
				logger.Service.Zap.Warnw("EMSGID_eBroadcastLotteryResult Steps Warn",
					"GameUser", gFS.secWebSocketKey,
					"GameRoomUuid", gFS.gameRoomUuid,
				)
				gFS.accountingSn = 0
				data3 := action.Payload()[2].([3]int32) //dice
				memberName := wallet.Service.MemberName(gFS.secWebSocketKey)
				balance, _ := wallet.Service.BalanceCache(gFS.secWebSocketKey)
				flux.Send(accounting.ActionAccountingEnd, gFS.secWebSocketKey, accounting.Service.HashId(gFS.secWebSocketKey, a.Start.Sn), data1, data2, data3, memberName, balance, gameRoomUuid)
			}
		} else {
			logger.Service.Zap.Warnw("EMSGID_eBroadcastLotteryResult BetCall nil",
				"GameUser", gFS.secWebSocketKey,
				"GameRoomUuid", gFS.gameRoomUuid,
			)
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
			gFS.secWebSocketKey,
			gFS.profile.HostId,
		)

	case gameroom.EMSGID_eKickOutWarn:
		g.RwMutex.Lock()
		defer g.RwMutex.Unlock()

		gFS.isGaming = false

		state := playerstate.Service.GetState(gFS.profile.HostId, gFS.secWebSocketKey)
		if state == nil || state.BetRoundUuid == "" || gFS.currentBetRoundUuid != state.BetRoundUuid {
			if gFS.accountingSn != 0 {
				accountingSn := gFS.accountingSn
				gFS.accountingSn = 0
				wallet.Service.Refund(gFS.secWebSocketKey, accountingSn, true)
				flux.Send(accounting.ActionAccountingDelete, gFS.secWebSocketKey, accounting.Service.HashId(gFS.secWebSocketKey, accountingSn))
			}
		}

		g.SendAction(action)

	case bet.EMSGID_eJoinedBetRoundInfo:
		g.SendAction(action)

	case gameroom.EMSGID_eJoinedRoomInfo:
		//共用錢包->進房預扣
		if wallet.Service.WalletCategory(gFS.secWebSocketKey) == wallet.CategoryHost {
			flux.Send(ActionCreateAccounting, gFS.secWebSocketKey, gFS.secWebSocketKey)
		}

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
		state := playerstate.Service.GetState(gFS.profile.HostId, gFS.secWebSocketKey)

		if state != nil {
			if state.BetRoundUuid == "" || gFS.currentBetRoundUuid != state.BetRoundUuid {
				flux.Send(twin.ActionTwinDestroy, gFS.secWebSocketKey, gFS.secWebSocketKey)
			}
		}

	} else {
		logger.Service.Zap.Warnw(gameuser.GameUser_PROFILE_NIL,
			"GameUser", gFS.secWebSocketKey,
			"HostExtId", gFS.hostExtId,
		)
	}
	sessionmanager.Service.End(gFS.secWebSocketKey, gFS.hostExtId)

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
	gFS.isGaming = false

	logger.Service.Zap.Infow("disconnected from room",
		"GameUser", gFS.secWebSocketKey,
		"GameRoomUuid", gFS.gameRoomUuid,
		"LobbyRoomUuid", gFS.lobbyRoomUuid,
	)

	if gFS.gameRoomUuid != "" {
		state := playerstate.Service.GetState(gFS.profile.HostId, gFS.secWebSocketKey)
		if state == nil || state.BetRoundUuid == "" || gFS.currentBetRoundUuid != state.BetRoundUuid {
			if gFS.accountingSn != 0 {
				accountingSn := gFS.accountingSn
				gFS.accountingSn = 0
				wallet.Service.Refund(gFS.secWebSocketKey, accountingSn, true)
				flux.Send(accounting.ActionAccountingDelete, gFS.secWebSocketKey, accounting.Service.HashId(gFS.secWebSocketKey, accountingSn))
			}

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
		} else { //有下注
			if gFS.accountingSn != 0 { //共用錢包 or 獨立錢包(EMSGID_eLotteryResult後)
				flux.Send(twin.ActionTwinActive, gFS.secWebSocketKey, gFS.secWebSocketKey, gFS.accountingSn)
			} else { //獨立錢包(EMSGID_eLotteryResult前)
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
			gFS.secWebSocketKey,
			gFS.profile.HostId,
		)
	}
}

func (gFS *GameUserFS) DecreaseHandler(secWebSocketKey, uuid string, balance, cent, accountingSn uint64) {
	// do nothing
}

func (gFS *GameUserFS) IncreaseHandler(secWebSocketKey, uuid string, balance, cent, accountingSn uint64) {
	// do nothing
}

func (gFS *GameUserFS) EndAccountingHandler(secWebSocketKey string, checkAccountingEnd bool, walletType int, cent uint64) {
	// do nothing
}

func (gFS *GameUserFS) BetErrorHandler(secWebSocketKey string, accountingSn uint64) {
	// do nothing
}

func (gFS *GameUserFS) GetAccountingSnHandler(secWebSocketKey string, balance, cent, sn uint64, depositCheck bool) (accountingSn uint64) {
	if secWebSocketKey == gFS.secWebSocketKey {
		accountingSn = gFS.accountingSn

		logger.Service.Zap.Infow("Find AccountingSn",
			"GameUser", secWebSocketKey,
			"accountingSn", gFS.accountingSn,
		)
	} else {
		accountingSn = 0

		logger.Service.Zap.Warnw(accounting.Accounting_ACCOUNTING_NOT_FOUND,
			"GameUser", secWebSocketKey,
		)
	}

	return accountingSn
}

func (gFS *GameUserFS) checkSessionMap(hostExtId, host_id, member_id, game_id string) bool {
	if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
		rows, err := db.Table("session_map").Where("host_id = ? AND member_id = ? AND game_id = ?", host_id, member_id, game_id).Rows()
		if err != nil {
			return false
		} else {
			defer rows.Close()
			result := false

			for rows.Next() {
				result = true
				break
			}
			return result
		}
	}
	return false
}
