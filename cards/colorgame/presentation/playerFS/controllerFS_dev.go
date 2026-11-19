//go:build dev
// +build dev

package playerFS

import (
	"colorgame-game-server/application/botroom"
	"fmt"
	"log"
	"net/http"

	"github.com/fasthttp/websocket"
	"github.com/valyala/fasthttp"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/player"
)

func (c *controllerFS) ServeHandler(h player.IHandler) {
	logger.Service.Zap.Info(fmt.Sprintf("  /$$$$$$$   /$$                      /$$$$$$    /$$                           "))
	logger.Service.Zap.Info(fmt.Sprintf(" | $$__  $$ | $$                     /$$__  $$  | $$                           "))
	logger.Service.Zap.Info(fmt.Sprintf(" | $$  \\ $$| $$  /$$$$$$  /$$   /$$| $$  \\__//$$$$$$    /$$$$$$   /$$$$$$    "))
	logger.Service.Zap.Info(fmt.Sprintf(" | $$$$$$$/ | $$ |____  $$| $$  | $$|  $$$$$$ |_  $$_/   |____  $$ /$$__  $$   "))
	logger.Service.Zap.Info(fmt.Sprintf(" | $$____/  | $$  /$$$$$$$| $$  | $$ \\____  $$ | $$      /$$$$$$$| $$ \\__/   "))
	logger.Service.Zap.Info(fmt.Sprintf(" | $$       | $$ /$$__  $$| $$  | $$ /$$  \\ $$ | $$ /$$ /$$__  $$| $$         "))
	logger.Service.Zap.Info(fmt.Sprintf(" | $$       | $$|  $$$$$$$|  $$$$$$$|  $$$$$$/  |  $$$$/|  $$$$$$$| $$         "))
	logger.Service.Zap.Info(fmt.Sprintf(" |__/       |__/ \\_______/ \\____$$ \\______/   \\___/ \\_______/|__/         "))
	logger.Service.Zap.Info(fmt.Sprintf("                           /$$  | $$  Development Http Server Listening %s   ", c.port))
	logger.Service.Zap.Info(fmt.Sprintf("                          |  $$$$$$/          %s             ", c.startTime))
	logger.Service.Zap.Info(fmt.Sprintf("                          \\______/           %s          ", c.version))

	http.HandleFunc(fmt.Sprintf("/%s", c.endPoint), h.HttpHandler)

	botroom.Service.CreateBotLobbies()

	if err := http.ListenAndServe(":"+c.port, nil); err != nil {
		log.Fatal(err)
	}

	//if err := fasthttp.ListenAndServe(":"+c.port, h.FastHttpHandler); err != nil {
	//    log.Fatal(err)
	//}
}

func (c *controllerFS) FastHttpHandler(ctx *fasthttp.RequestCtx) {
	switch string(ctx.Path()) {
	case fmt.Sprintf("/%s", c.endPoint):
		secWebSocketKey := string(ctx.Request.Header.Peek("Sec-WebSocket-Key"))
		hostExtId := "dd12f3635bc9599ca58012601d07197c"
		remoteAddr := ctx.RemoteAddr().String()
		userAgent := string(ctx.UserAgent())

		err := c.fastHttpUpgrader.Upgrade(ctx, func(conn *websocket.Conn) {
			logger.Service.Zap.Infow("----------------Sec-WebSocket-Protocol--------------",
				"GameUser", secWebSocketKey,
				"HostExtId", hostExtId,
				"UserAgent", userAgent,
				"RemoteAddr", remoteAddr,
			)
			conn.EnableWriteCompression(true)
			conn.SetCompressionLevel(9)
			//c.exec(secWebSocketKey, hostExtId, remoteAddr, userAgent, conn)
		})

		if err != nil {
			logger.Service.Zap.Warnw("Websocket Connection Failed",
				"GameUser", ctx.Request.Header.Peek("Sec-WebSocket-Key"),
				"HostExtId", hostExtId,
				"UserAgent", ctx.UserAgent(),
				"RemoteAddr", ctx.RemoteAddr().String(),
				"Error", err,
			)
		}

	default:
		ctx.Error("Unsupported path", fasthttp.StatusNotFound)
	}
}

func (c *controllerFS) HttpHandler(res http.ResponseWriter, req *http.Request) {
	secWebSocketKey := req.Header.Get("Sec-WebSocket-Key")
	hostExtId := "dd12f3635bc9599ca58012601d07197c"
	remoteAddr := req.RemoteAddr
	userAgent := req.UserAgent()

	conn, err := c.gorillaUpgrader.Upgrade(res, req, nil)

	if err != nil {
		logger.Service.Zap.Warnw("websocket connection failed",
			"GameUser", secWebSocketKey,
			"HostExtId", hostExtId,
			"UserAgent", userAgent,
			"RemoteAddr", remoteAddr,
			"Error", err,
		)

		if conn != nil {
			conn.Close()
		}
		return
	}

	logger.Service.Zap.Infow("----------------Sec-WebSocket-Protocol--------------",
		"GameUser", secWebSocketKey,
		"HostExtId", hostExtId,
		"UserAgent", userAgent,
		"RemoteAddr", remoteAddr,
	)

	conn.EnableWriteCompression(true)
	conn.SetCompressionLevel(-2)
	c.exec(secWebSocketKey, hostExtId, remoteAddr, userAgent, conn)
}
