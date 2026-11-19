package playerU

import (
	"os"
	"time"
	"u-game-server/application/banker"
	"u-game-server/application/botuser"
	"u-game-server/application/gameroom"
	"u-game-server/application/gamesettingU"
	"u-game-server/application/gameuserU"
	"u-game-server/application/lobbysettingU"

	fastHttpWebsocket "github.com/fasthttp/websocket"
	"github.com/gorilla/websocket"
	"gitlab.iplaystar.net/game-server/flux"
	gamesetting "gitlab.iplaystar.net/game-server/game-setting"
	gameuser "gitlab.iplaystar.net/game-server/game-user"
	lobbyroom "gitlab.iplaystar.net/game-server/lobby-room"
	lobbysetting "gitlab.iplaystar.net/game-server/lobby-setting"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/player"
)

var ControllerU = &controllerU{
	port:             os.Getenv("HTTP_PORT"),
	startTime:        time.Now().Format("02-Jan-2006 15:04:05"),
	version:          os.Getenv("VERSION"),
	sslPath:          os.Getenv("SSL_PATH"),
	sslCrt:           os.Getenv("SSL_CRT"),
	sslKey:           os.Getenv("SSL_KEY"),
	gorillaUpgrader:  player.Controller.GorillaUpgrader,
	fastHttpUpgrader: player.Controller.FastHttpUpgrader,
}

type controllerU struct {
	port             string
	startTime        string
	version          string
	sslPath          string
	sslCrt           string
	sslKey           string
	endPoint         string
	gorillaUpgrader  *websocket.Upgrader
	fastHttpUpgrader *fastHttpWebsocket.FastHTTPUpgrader
}

func init() {
	ControllerU.endPoint = "card"
}

func (cU *controllerU) exec(secWebSocketKey, hostExtId, remoteAddr, userAgent string, conn *websocket.Conn) {
	lobbysetting.Service.New(
		lobbysetting.Builder().
			SetSecWebSocketKey(secWebSocketKey).
			SetHostExtId(hostExtId).
			SetRemoteAddr(remoteAddr).
			SetUserAgent(userAgent).
			SetIHandler(lobbysettingU.Service).
			Build(),
	)

	gamesetting.Service.New(
		gamesetting.Builder().
			SetSecWebSocketKey(secWebSocketKey).
			SetHostExtId(hostExtId).
			SetRemoteAddr(remoteAddr).
			SetUserAgent(userAgent).
			SetIHandler(gamesettingU.Service).
			Build(),
	)

	flux.Send(gameuser.ActionGameUserCreate, player.Controller.Id, gameuser.Service.Id,
		hostExtId,
		secWebSocketKey,
		conn,
		gameuserU.New(player.Controller.Id, secWebSocketKey, hostExtId, remoteAddr),
	)
}

func (cU *controllerU) FluxActionHandler(action *flux.Action) {
	logger.Service.Zap.Infow(action.Key().Name())
	switch action.Key().Name() {
	case gameuser.ActionJoinLobbyRoomCall:
		secWebSocketKey := action.Key().From()
		flux.Send(lobbyroom.ActionLobbyRoomAutoJoinCall, player.Controller.Id, lobbyroom.Service.Id, secWebSocketKey)

	case lobbyroom.ActionLobbyRoomAutoJoinRecall:
		secWebSocketKey := action.Payload()[0].(string)
		lobbyRoomUuid := action.Payload()[1].(string)
		flux.Send(gameuser.ActionJoinLobbyRoomRecall, player.Controller.Id, secWebSocketKey, lobbyRoomUuid)

	case gameuser.ActionJoinGameRoomCall:
		secWebSocketKey := action.Key().From()
		hostExtId := action.Payload()[0].(string)
		avatar := action.Payload()[1].(string)
		ipaddress := action.Payload()[2].(string)
		bet := action.Payload()[3].(uint64)
		blacklistValue := action.Payload()[4].(uint32)
		hostId := action.Payload()[5].(string)
		memberType := action.Payload()[6].(int)
		isIsolated := action.Payload()[7].(bool)

		j := gameroom.JoinBuilder().
			SetControllerId(player.Controller.Id).
			SetSecWebSocketKey(secWebSocketKey).
			SetHostExtId(hostExtId).
			SetIPAddress(ipaddress).
			SetAvatar(avatar).
			SetGameId(gamesettingU.Service.GameId(secWebSocketKey)).
			SetBet(bet).
			SetIpBlock(gamesettingU.Service.IPConfigEnable(secWebSocketKey)).
			SetHostBlock(gamesettingU.Service.HostConnectConfigEnable(secWebSocketKey)).
			SetKind(gameroom.PLAYER).
			SetBlacklistValue(blacklistValue).
			SetHostId(hostId).
			SetFee(gamesettingU.Service.Fee(secWebSocketKey)).
			SetMemberType(memberType).
			SetIsIsolated(isIsolated).
			Build()

		flux.Send(gameroom.ActionGameRoomJoinCall, player.Controller.Id, gameroom.Service.Id, j)

	case gameuser.ActionLeaveGameRoomCall:
		secWebSocketKey := action.Key().From()
		gameRoomUuid := action.Payload()[0].(string)
		l := gameroom.LeaveBuilder().
			SetControllerId(player.Controller.Id).
			SetSecWebSocketKey(secWebSocketKey).
			SetGameRoomUuid(gameRoomUuid).
			SetKind(gameroom.PLAYER).
			Build()

		flux.Send(gameroom.ActionPlayerDeleteCall, player.Controller.Id, gameRoomUuid, l)

		//flux.Send(gameroom.ActionGameRoomLeaveCall, player.Controller.Id, gameroom.Service.Id, l)

	case gameroom.ActionGameRoomLeaveRecall:
		l := action.Payload()[0].(*gameroom.Leave)

		switch l.Kind {
		case gameroom.BOT:
			// do nothing

		case gameroom.PLAYER:
			flux.Send(gameuser.ActionLeaveGameRoomRecall, player.Controller.Id, l.SecWebSocketKey, l.GameRoomUuid)
		}

	case botuser.ActionGameRoomJoinCall:
		uuid := action.Key().From()
		gameRoomUuid := action.Payload()[0].(string)
		avatar := action.Payload()[1].(string)
		j := gameroom.JoinBuilder().
			SetControllerId(player.Controller.Id).
			SetSecWebSocketKey(uuid).
			SetGameRoomUuid(gameRoomUuid).
			SetAvatar(avatar).
			SetGameId(gamesettingU.Service.GameId(uuid)).
			SetKind(gameroom.BOT).
			Build()

		flux.Send(gameroom.ActionGameRoomJoinCall, player.Controller.Id, gameroom.Service.Id, j)

	case botuser.ActionGameRoomLeave:
		uuid := action.Key().From()
		gameRoomUuid := action.Payload()[0].(string)

		l := gameroom.LeaveBuilder().
			SetControllerId(player.Controller.Id).
			SetSecWebSocketKey(uuid).
			SetGameRoomUuid(gameRoomUuid).
			SetKind(gameroom.BOT).
			Build()

		flux.Send(gameroom.ActionGameRoomLeaveCall, player.Controller.Id, gameroom.Service.Id, l)

	case gameroom.ActionGameRoomJoinRecall:
		j := action.Payload()[0].(*gameroom.Join)

		switch j.Kind {
		case gameroom.BOT:
			// TODO JOHNNY 改同步
			flux.Send(botuser.ActionGameRoomJoinRecall, player.Controller.Id, j.SecWebSocketKey, j.Seat)
		}
	case gameroom.ActionGameRoomCreated:
		// do nothing

	case gameroom.ActionPlayersReady:
		availableSeats := action.Payload()[0].(int)
		gameRoomUuid := action.Payload()[1].(string)
		secWebSocketKey := action.Payload()[2].(string)
		hostId := action.Payload()[3].(string)
		hostExtId := action.Payload()[4].(string)
		logger.Service.Zap.Infow("ActionPlayersReady",
			"availableSeats", availableSeats,
			"gameRoomUuid", gameRoomUuid,
			"secWebSocketKey", secWebSocketKey,
		)
		for i := 0; i < availableSeats; i++ {
			flux.Send(botuser.ActionBotUserCreate, player.Controller.Id, botuser.Service.Id,
				gameRoomUuid,
				secWebSocketKey,
				banker.GAME_ROOM,
				hostId,
				hostExtId,
			)
		}

	}
}
