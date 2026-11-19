module gitlab.iplaystar.net/game-server/jackpot-client

require (
	github.com/gogo/protobuf v1.3.1
	github.com/gorilla/websocket v1.4.2
	gitlab.iplaystar.net/game-server/broadcaster v0.0.3
	gitlab.iplaystar.net/game-server/common v0.1.3
	gitlab.iplaystar.net/game-server/error-code v0.0.5
	gitlab.iplaystar.net/game-server/flux v0.0.4
	gitlab.iplaystar.net/game-server/logger v0.0.4
	gitlab.iplaystar.net/game-server/mysql v0.0.7
	gitlab.iplaystar.net/game-server/wallet v0.1.2
	go.uber.org/zap v1.15.0 // indirect
)

replace gitlab.iplaystar.net/game-server/wallet => ../wallet

go 1.15
