package playerFS

import (
	"fish-shrimp-crab-game-server/application/botuser"
	"fish-shrimp-crab-game-server/application/gameroom"
	"fish-shrimp-crab-game-server/application/gamesettingFS"
	"fish-shrimp-crab-game-server/application/gameuserFS"
	"fish-shrimp-crab-game-server/application/lobbysettingFS"
	"os"
	"time"

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

var ControllerFS = &controllerFS{
	port:             os.Getenv("HTTP_PORT"),
	startTime:        time.Now().Format("02-Jan-2006 15:04:05"),
	version:          os.Getenv("VERSION"),
	sslPath:          os.Getenv("SSL_PATH"),
	sslCrt:           os.Getenv("SSL_CRT"),
	sslKey:           os.Getenv("SSL_KEY"),
	gorillaUpgrader:  player.Controller.GorillaUpgrader,
	fastHttpUpgrader: player.Controller.FastHttpUpgrader,
}

type controllerFS struct {
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
	ControllerFS.endPoint = "card"
}

func (c *controllerFS) exec(secWebSocketKey, hostExtId, remoteAddr, userAgent string, conn *websocket.Conn) {
	lobbysetting.Service.New(
		lobbysetting.Builder().
			SetSecWebSocketKey(secWebSocketKey).
			SetHostExtId(hostExtId).
			SetRemoteAddr(remoteAddr).
			SetUserAgent(userAgent).
			SetIHandler(lobbysettingFS.Service).
			Build(),
	)

	gamesetting.Service.New(
		gamesetting.Builder().
			SetSecWebSocketKey(secWebSocketKey).
			SetHostExtId(hostExtId).
			SetRemoteAddr(remoteAddr).
			SetUserAgent(userAgent).
			SetIHandler(gamesettingFS.Service).
			Build(),
	)
	logger.Service.Zap.Infow("addusercreate",
		"hostExtId", hostExtId,
	)
	flux.Send(gameuser.ActionGameUserCreate, player.Controller.Id, gameuser.Service.Id,
		hostExtId,
		secWebSocketKey,
		conn,
		gameuserFS.New(player.Controller.Id, secWebSocketKey, hostExtId, remoteAddr),
	)
}

func (c *controllerFS) FluxActionHandler(action *flux.Action) {
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
		lastGameRoomUuid := action.Payload()[3].(string)
		histories := action.Payload()[4].([10][3]int32)
        hostId := action.Payload()[5].(string)
        memberId := action.Payload()[6].(string)
        gameid := action.Payload()[7].(string)
        billCurrency := action.Payload()[8].(string)
        isVipChangeRoom := action.Payload()[9].(bool)

		j := gameroom.JoinBuilder().
			SetControllerId(player.Controller.Id).
			SetSecWebSocketKey(secWebSocketKey).
			SetHostExtId(hostExtId).
			SetIPAddress(ipaddress).
			SetAvatar(avatar).
			SetGameId(gamesettingFS.Service.GameId(secWebSocketKey)).
			SetBetList(gamesettingFS.Service.BetList(secWebSocketKey)).
			SetRateList(gamesettingFS.Service.RateList(secWebSocketKey)).
			SetRate(gamesettingFS.Service.Rate(secWebSocketKey)).
			SetRateIndex(gamesettingFS.Service.RateIndex(secWebSocketKey)).
			SetIpBlock(gamesettingFS.Service.IPConfigEnable(secWebSocketKey)).
			SetHostBlock(gamesettingFS.Service.HostConnectConfigEnable(secWebSocketKey)).
			SetKind(gameroom.PLAYER).
			SetLastRoomId(lastGameRoomUuid).
			SetVipInfo(secWebSocketKey, hostId, memberId, gameid, lastGameRoomUuid, histories, billCurrency, isVipChangeRoom).
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

		logger.Service.Zap.Infow("gameuser leave room", "leave", l)

		flux.Send(gameroom.ActionPlayerDeleteCall, player.Controller.Id, gameRoomUuid, l)

		//flux.Send(gameroom.ActionGameRoomLeaveCall, player.Controller.Id, gameroom.Service.Id, l)

	case botuser.ActionGameRoomJoinCall:
		uuid := action.Key().From()
		gameRoomUuid := action.Payload()[0].(string)
		avatar := action.Payload()[1].(string)

		j := gameroom.JoinBuilder().
			SetControllerId(player.Controller.Id).
			SetSecWebSocketKey(uuid).
			SetGameRoomUuid(gameRoomUuid).
			SetAvatar(avatar).
			SetGameId(gamesettingFS.Service.GameId(uuid)).
			SetBetList(gamesettingFS.Service.BetList(uuid)).
			SetRateList(gamesettingFS.Service.RateList(uuid)).
			SetRate(gamesettingFS.Service.Rate(uuid)).
			SetRateIndex(gamesettingFS.Service.RateIndex(uuid)).
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

	case gameroom.ActionGameRoomCreated:
		// do nothing

	}
}
