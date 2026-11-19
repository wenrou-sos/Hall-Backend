//go:build staging
// +build staging

package playerU

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

func (cU *controllerU) ServeHandler(h player.IHandler) {
	logger.Service.Zap.Info(fmt.Sprintf("  /$$$$$$$   /$$                      /$$$$$$    /$$                           "))
	logger.Service.Zap.Info(fmt.Sprintf(" | $$__  $$ | $$                     /$$__  $$  | $$                           "))
	logger.Service.Zap.Info(fmt.Sprintf(" | $$  \\ $$| $$  /$$$$$$  /$$   /$$| $$  \\__//$$$$$$    /$$$$$$   /$$$$$$    "))
	logger.Service.Zap.Info(fmt.Sprintf(" | $$$$$$$/ | $$ |____  $$| $$  | $$|  $$$$$$ |_  $$_/   |____  $$ /$$__  $$   "))
	logger.Service.Zap.Info(fmt.Sprintf(" | $$____/  | $$  /$$$$$$$| $$  | $$ \\____  $$ | $$      /$$$$$$$| $$ \\__/   "))
	logger.Service.Zap.Info(fmt.Sprintf(" | $$       | $$ /$$__  $$| $$  | $$ /$$  \\ $$ | $$ /$$ /$$__  $$| $$         "))
	logger.Service.Zap.Info(fmt.Sprintf(" | $$       | $$|  $$$$$$$|  $$$$$$$|  $$$$$$/  |  $$$$/|  $$$$$$$| $$         "))
	logger.Service.Zap.Info(fmt.Sprintf(" |__/       |__/ \\_______/ \\____$$ \\______/   \\___/ \\_______/|__/         "))
	logger.Service.Zap.Info(fmt.Sprintf("                           /$$  | $$  Staging Http Server Listening %s       ", cU.port))
	logger.Service.Zap.Info(fmt.Sprintf("                          |  $$$$$$/          %s             ", cU.startTime))
	logger.Service.Zap.Info(fmt.Sprintf("                          \\______/           %s          ", cU.version))

	http.HandleFunc(fmt.Sprintf("/%s", cU.endPoint), h.HttpHandler)

	if err := http.ListenAndServe(":"+cU.port, nil); err != nil {
		log.Fatal(err)
	}

	//if err := fasthttp.ListenAndServe(":"+cU.port, h.FastHttpHandler); err != nil {
	//    log.Fatal(err)
	//}
}

func (cU *controllerU) FastHttpHandler(ctx *fasthttp.RequestCtx) {
	switch string(ctx.Path()) {
	case fmt.Sprintf("/%s", cU.endPoint):
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

		err := cU.fastHttpUpgrader.Upgrade(ctx, func(conn *websocket.Conn) {
			logger.Service.Zap.Infow("----------------Sec-WebSocket-Protocol--------------",
				"GameUser", secWebSocketKey,
				"GameType", gameType,
				"HostExtId", hostExtId,
				"UserAgent", userAgent,
				"RemoteAddr", remoteAddr,
			)
			conn.EnableWriteCompression(true)
			conn.SetCompressionLevel(9)
			//cU.exec(secWebSocketKey, hostExtId, remoteAddr, userAgent, conn)
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

func (cU *controllerU) HttpHandler(res http.ResponseWriter, req *http.Request) {
	ss := strings.Split(req.Header.Get("Sec-WebSocket-Protocol"), ",")

	// card
	gameType := ss[0]

	secWebSocketKey := req.Header.Get("Sec-WebSocket-Key")
	//hostExtId := strings.TrimSpace(ss[1])
	hostExtId := os.Getenv("HOST_EXT_ID") //"dd12f3635bc9599ca58012601d07197c"
	remoteAddr := getIPAdress(req)
	userAgent := req.UserAgent()

	responseHeader := http.Header{}
	responseHeader.Set("Sec-WebSocket-Protocol", gameType)

	conn, err := cU.gorillaUpgrader.Upgrade(res, req, responseHeader)

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
	cU.exec(secWebSocketKey, hostExtId, remoteAddr, userAgent, conn)
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
