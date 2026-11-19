//go:build staging
// +build staging

package player52

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"

	"github.com/fasthttp/websocket"
	"github.com/valyala/fasthttp"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/player"
)

func (c52 *controller52) ServeHandler(h player.IHandler) {
	logger.Service.Zap.Info(fmt.Sprintf("  /$$$$$$$   /$$                      /$$$$$$    /$$                           "))
	logger.Service.Zap.Info(fmt.Sprintf(" | $$__  $$ | $$                     /$$__  $$  | $$                           "))
	logger.Service.Zap.Info(fmt.Sprintf(" | $$  \\ $$| $$  /$$$$$$  /$$   /$$| $$  \\__//$$$$$$    /$$$$$$   /$$$$$$    "))
	logger.Service.Zap.Info(fmt.Sprintf(" | $$$$$$$/ | $$ |____  $$| $$  | $$|  $$$$$$ |_  $$_/   |____  $$ /$$__  $$   "))
	logger.Service.Zap.Info(fmt.Sprintf(" | $$____/  | $$  /$$$$$$$| $$  | $$ \\____  $$ | $$      /$$$$$$$| $$ \\__/   "))
	logger.Service.Zap.Info(fmt.Sprintf(" | $$       | $$ /$$__  $$| $$  | $$ /$$  \\ $$ | $$ /$$ /$$__  $$| $$         "))
	logger.Service.Zap.Info(fmt.Sprintf(" | $$       | $$|  $$$$$$$|  $$$$$$$|  $$$$$$/  |  $$$$/|  $$$$$$$| $$         "))
	logger.Service.Zap.Info(fmt.Sprintf(" |__/       |__/ \\_______/ \\____$$ \\______/   \\___/ \\_______/|__/         "))
	logger.Service.Zap.Info(fmt.Sprintf("                           /$$  | $$  Staging Http Server Listening %s       ", c52.port))
	logger.Service.Zap.Info(fmt.Sprintf("                          |  $$$$$$/          %s             ", c52.startTime))
	logger.Service.Zap.Info(fmt.Sprintf("                          \\______/           %s          ", c52.version))

	http.HandleFunc(fmt.Sprintf("/%s", c52.endPoint), h.HttpHandler)

	if err := http.ListenAndServe(":"+c52.port, nil); err != nil {
		log.Fatal(err)
	}

	//if err := fasthttp.ListenAndServe(":"+c52.port, h.FastHttpHandler); err != nil {
	//    log.Fatal(err)
	//}
}

func (c52 *controller52) FastHttpHandler(ctx *fasthttp.RequestCtx) {
	switch string(ctx.Path()) {
	case fmt.Sprintf("/%s", c52.endPoint):
		ss := strings.Split(
			string(ctx.Request.Header.Peek("Sec-WebSocket-Protocol")),
			",",
		)

		// card
		gameType := ss[0]

		secWebSocketKey := string(ctx.Request.Header.Peek("Sec-WebSocket-Key"))
		hostExtId := strings.TrimSpace(ss[1])
		remoteAddr := ctx.RemoteAddr().String()
		userAgent := string(ctx.UserAgent())

		responseHeader := ctx.Response.Header
		responseHeader.Set("Sec-WebSocket-Protocol", gameType)

		err := c52.fastHttpUpgrader.Upgrade(ctx, func(conn *websocket.Conn) {
			logger.Service.Zap.Infow("----------------Sec-WebSocket-Protocol--------------",
				"GameUser", secWebSocketKey,
				"GameType", gameType,
				"HostExtId", hostExtId,
				"UserAgent", userAgent,
				"RemoteAddr", remoteAddr,
			)
			conn.EnableWriteCompression(true)
			conn.SetCompressionLevel(9)
			//c52.exec(secWebSocketKey, hostExtId, remoteAddr, userAgent, conn)
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

func (c52 *controller52) HttpHandler(res http.ResponseWriter, req *http.Request) {
	ss := strings.Split(req.Header.Get("Sec-WebSocket-Protocol"), ",")

	// card
	gameType := ss[0]

	secWebSocketKey := req.Header.Get("Sec-WebSocket-Key")
	//hostExtId := strings.TrimSpace(ss[1])
	hostExtId := os.Getenv("BOT_DEFAULT_HOST_EXT_ID")
	if hostExtId == "" {
		hostExtId = "dd12f3635bc9599ca58012601d07197c"
	}
	remoteAddr := getIPAdress(req)
	userAgent := req.UserAgent()

	responseHeader := http.Header{}
	responseHeader.Set("Sec-WebSocket-Protocol", gameType)

	conn, err := c52.gorillaUpgrader.Upgrade(res, req, responseHeader)

	if err != nil {
		logger.Service.Zap.Warnw("Websocket Connection Failed",
			"GameUser", secWebSocketKey,
			"GameType", gameType,
			"HostExtId", hostExtId,
			"UserAgent", req.UserAgent(),
			"RemoteAddr", req.RemoteAddr,
			"Error", err,
		)

		if conn != nil {
			conn.Close()
		}
		return
	}
	logger.Service.Zap.Infow("----------------Sec-WebSocket-Protocol--------------",
		"GameUser", secWebSocketKey,
		"GameType", gameType,
		"HostExtId", hostExtId,
		"UserAgent", userAgent,
		"RemoteAddr", remoteAddr,
	)

	conn.EnableWriteCompression(true)
	conn.SetCompressionLevel(-2)
	c52.exec(secWebSocketKey, hostExtId, remoteAddr, userAgent, conn)
}
func getIPAdress(r *http.Request) string {
	IPAddress := r.Header.Get("X-Real-Ip")
	if IPAddress == "" {
		IPAddress = r.Header.Get("X-Forwarded-For")
	}
	if IPAddress == "" {
		IPAddress = r.RemoteAddr
	}
	return IPAddress
}
