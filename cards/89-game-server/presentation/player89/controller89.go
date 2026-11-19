package player89

import (
	"89-game-server/application/banker"
	"89-game-server/application/botuser"
	"89-game-server/application/gameroom"
	"89-game-server/application/gamesetting89"
	"89-game-server/application/gameuser89"
	"89-game-server/application/lobbysetting89"
	"os"
	"time"

	fastHttpWebsocket "github.com/fasthttp/websocket"
	"github.com/gorilla/websocket"
	"gitlab.iplaystar.net/game-server/flux"
	gamesetting "gitlab.iplaystar.net/game-server/game-setting"
	gameuser "gitlab.iplaystar.net/game-server/game-user"
	lobbyroom "gitlab.iplaystar.net/game-server/lobby-room"
	lobbysetting "gitlab.iplaystar.net/game-server/lobby-setting"
	"gitlab.iplaystar.net/game-server/player"
)

var Controller89 = &controller89{
	port:             os.Getenv("HTTP_PORT"),
	startTime:        time.Now().Format("02-Jan-2006 15:04:05"),
	version:          os.Getenv("VERSION"),
	sslPath:          os.Getenv("SSL_PATH"),
	sslCrt:           os.Getenv("SSL_CRT"),
	sslKey:           os.Getenv("SSL_KEY"),
	gorillaUpgrader:  player.Controller.GorillaUpgrader,
	fastHttpUpgrader: player.Controller.FastHttpUpgrader,
}

type controller89 struct {
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
	Controller89.endPoint = "card"
}

func (c89 *controller89) exec(secWebSocketKey, hostExtId, remoteAddr, userAgent string, conn *websocket.Conn) {
	lobbysetting.Service.New(
		lobbysetting.Builder().
			SetSecWebSocketKey(secWebSocketKey).
			SetHostExtId(hostExtId).
			SetRemoteAddr(remoteAddr).
			SetUserAgent(userAgent).
			SetIHandler(lobbysetting89.Service).
			Build(),
	)

	gamesetting.Service.New(
		gamesetting.Builder().
			SetSecWebSocketKey(secWebSocketKey).
			SetHostExtId(hostExtId).
			SetRemoteAddr(remoteAddr).
			SetUserAgent(userAgent).
			SetIHandler(gamesetting89.Service).
			Build(),
	)
	flux.Send(gameuser.ActionGameUserCreate, player.Controller.Id, gameuser.Service.Id,
		hostExtId,
		secWebSocketKey,
		conn,
		gameuser89.New(player.Controller.Id, secWebSocketKey, hostExtId, remoteAddr),
	)
}

func (c89 *controller89) FluxActionHandler(action *flux.Action) {
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

		j := gameroom.JoinBuilder().
			SetControllerId(player.Controller.Id).
			SetSecWebSocketKey(secWebSocketKey).
			SetHostExtId(hostExtId).
			SetIPAddress(ipaddress).
			SetAvatar(avatar).
			SetGameId(gamesetting89.Service.GameId(secWebSocketKey)).
			SetBetList(gamesetting89.Service.BetList(secWebSocketKey)).
			SetRateList(gamesetting89.Service.RateList(secWebSocketKey)).
			SetRate(gamesetting89.Service.Rate(secWebSocketKey)).
			SetIpBlock(gamesetting89.Service.IPConfigEnable(secWebSocketKey)).
			SetHostBlock(gamesetting89.Service.HostConnectConfigEnable(secWebSocketKey)).
			SetKind(gameroom.PLAYER).
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
			SetGameId(gamesetting89.Service.GameId(uuid)).
			SetBetList(gamesetting89.Service.BetList(uuid)).
			SetRateList(gamesetting89.Service.RateList(uuid)).
			SetRate(gamesetting89.Service.Rate(uuid)).
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

			// TODO JOHNNY 目前沒有搶莊寫死
			if j.Seat == banker.BANKER_SEAT {
				// TODO JOHNNY 這裡直接發送搶到莊家

				flux.Send(banker.ActionBankerCreate, player.Controller.Id, banker.Service.Id,
					j.SecWebSocketKey,
					j.GameRoomUuid,
					banker.GAME_ROOM,
					j.Seat,
					int32(6), // 一桌6人
				)
			}

		case gameroom.PLAYER:
			// TODO JOHNNY 改同步
			//flux.Send(gameuser.ActionJoinGameRoomRecall, player.Controller.Id, j.SecWebSocketKey,
			//j.GameRoomUuid,
			//j.Seat,
			//banker.GAME_ROOM,
			//)
		}

	case gameroom.ActionGameRoomCreated:
		// do nothing

	case gameroom.ActionPlayersReady:
		availableSeats := action.Payload()[0].(int)
		gameRoomUuid := action.Payload()[1].(string)
		rate := action.Payload()[2].(uint32)
		secWebSocketKey := action.Payload()[3].(string)

		for i := 0; i < availableSeats; i++ {
			flux.Send(botuser.ActionBotUserCreate, player.Controller.Id, botuser.Service.Id,
				gameRoomUuid,
				rate,
				secWebSocketKey,
				banker.GAME_ROOM,
			)
		}

	}
}
