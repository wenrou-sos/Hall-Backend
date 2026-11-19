module colorgame-game-server

go 1.15

require (
	github.com/fasthttp/websocket v1.4.3
	github.com/gogo/protobuf v1.3.2
	github.com/google/uuid v1.1.1
	github.com/gorilla/websocket v1.4.2
	github.com/jinzhu/gorm v1.9.16
	github.com/joho/godotenv v1.3.0
	github.com/klauspost/compress v1.10.8 // indirect
	github.com/valyala/fasthttp v1.14.0
	gitlab.iplaystar.net/game-server/accounting v0.1.9
	gitlab.iplaystar.net/game-server/auth v0.3.0
	gitlab.iplaystar.net/game-server/common v0.1.2
	gitlab.iplaystar.net/game-server/error-code v0.0.5
	gitlab.iplaystar.net/game-server/flux v0.0.5
	gitlab.iplaystar.net/game-server/format v0.0.3
	gitlab.iplaystar.net/game-server/game-setting v0.1.0
	gitlab.iplaystar.net/game-server/game-user v0.1.7
	gitlab.iplaystar.net/game-server/heart-beat v0.0.6
	gitlab.iplaystar.net/game-server/idle v0.0.5
	gitlab.iplaystar.net/game-server/lobby-room v0.0.1
	gitlab.iplaystar.net/game-server/lobby-setting v0.1.4
	gitlab.iplaystar.net/game-server/logger v1.0.1
	gitlab.iplaystar.net/game-server/maintain v0.0.2
	gitlab.iplaystar.net/game-server/mysql v0.0.7
	gitlab.iplaystar.net/game-server/player v0.0.2
	gitlab.iplaystar.net/game-server/postman v0.0.3
	gitlab.iplaystar.net/game-server/refundbet-tool v0.0.3
	gitlab.iplaystar.net/game-server/rng v0.0.1
	gitlab.iplaystar.net/game-server/session v0.0.4
	gitlab.iplaystar.net/game-server/session-manager v1.0.0
	gitlab.iplaystar.net/game-server/wallet v1.0.1
	go.uber.org/automaxprocs v1.3.0
)

replace (
	gitlab.iplaystar.net/game-server/accounting => ../../deps_colorgame/accounting
	gitlab.iplaystar.net/game-server/auth => ../../deps_colorgame/auth
	gitlab.iplaystar.net/game-server/broadcaster => ../../deps_colorgame/broadcaster
	gitlab.iplaystar.net/game-server/common => ../../deps_colorgame/common
	gitlab.iplaystar.net/game-server/error-code => ../../deps_colorgame/error-code
	gitlab.iplaystar.net/game-server/flux => ../../deps_colorgame/flux
	gitlab.iplaystar.net/game-server/format => ../../deps_colorgame/format
	gitlab.iplaystar.net/game-server/game-setting => ../../deps_colorgame/game-setting
	gitlab.iplaystar.net/game-server/game-user => ../../deps_colorgame/game-user
	gitlab.iplaystar.net/game-server/heart-beat => ../../deps_colorgame/heart-beat
	gitlab.iplaystar.net/game-server/http => ../../deps_colorgame/http
	gitlab.iplaystar.net/game-server/idle => ../../deps_colorgame/idle
	gitlab.iplaystar.net/game-server/lobby-room => ../../deps_colorgame/lobby-room
	gitlab.iplaystar.net/game-server/lobby-setting => ../../deps_colorgame/lobby-setting
	gitlab.iplaystar.net/game-server/logger => ../../deps_colorgame/logger
	gitlab.iplaystar.net/game-server/mac-address => ../../deps_colorgame/mac-address
	gitlab.iplaystar.net/game-server/maintain => ../../deps_colorgame/maintain
	gitlab.iplaystar.net/game-server/mysql => ../../deps_colorgame/mysql
	gitlab.iplaystar.net/game-server/player => ../../deps_colorgame/player
	gitlab.iplaystar.net/game-server/postman => ../../deps_colorgame/postman
	gitlab.iplaystar.net/game-server/redis => ../../deps_colorgame/redis
	gitlab.iplaystar.net/game-server/refundbet-tool => ../../deps_colorgame/refundbet-tool
	gitlab.iplaystar.net/game-server/rng => ../../deps_colorgame/rng
	gitlab.iplaystar.net/game-server/session => ../../deps_colorgame/session
	gitlab.iplaystar.net/game-server/session-manager => ../../deps_colorgame/session-manager
	gitlab.iplaystar.net/game-server/wallet => ../../deps_colorgame/wallet
)
