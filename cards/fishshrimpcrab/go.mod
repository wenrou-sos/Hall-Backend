module fish-shrimp-crab-game-server

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
	gitlab.iplaystar.net/game-server/accounting v0.1.5
	gitlab.iplaystar.net/game-server/auth v0.2.7
	gitlab.iplaystar.net/game-server/common v0.1.2
	gitlab.iplaystar.net/game-server/error-code v0.0.5
	gitlab.iplaystar.net/game-server/flux v0.0.5
	gitlab.iplaystar.net/game-server/format v0.0.3
	gitlab.iplaystar.net/game-server/game-setting v0.1.0
	gitlab.iplaystar.net/game-server/game-user v0.1.0
	gitlab.iplaystar.net/game-server/heart-beat v0.0.6
	gitlab.iplaystar.net/game-server/idle v0.0.5
	gitlab.iplaystar.net/game-server/lobby-room v0.0.1
	gitlab.iplaystar.net/game-server/lobby-setting v0.1.0
	gitlab.iplaystar.net/game-server/logger v0.0.4
	gitlab.iplaystar.net/game-server/maintain v0.0.2
	gitlab.iplaystar.net/game-server/mysql v0.0.7
	gitlab.iplaystar.net/game-server/player v0.0.2
	gitlab.iplaystar.net/game-server/postman v0.0.3
	gitlab.iplaystar.net/game-server/session v0.0.4
	gitlab.iplaystar.net/game-server/session-manager v0.1.2
	gitlab.iplaystar.net/game-server/wallet v0.1.6
	go.uber.org/automaxprocs v1.3.0
)

replace (
	gitlab.iplaystar.net/game-server/accounting => ../../deps_fishshrimpcrab/accounting
	gitlab.iplaystar.net/game-server/auth => ../../deps_fishshrimpcrab/auth
	gitlab.iplaystar.net/game-server/broadcaster => ../../deps_fishshrimpcrab/broadcaster
	gitlab.iplaystar.net/game-server/common => ../../deps_fishshrimpcrab/common
	gitlab.iplaystar.net/game-server/error-code => ../../deps_fishshrimpcrab/error-code
	gitlab.iplaystar.net/game-server/flux => ../../deps_fishshrimpcrab/flux
	gitlab.iplaystar.net/game-server/format => ../../deps_fishshrimpcrab/format
	gitlab.iplaystar.net/game-server/game-setting => ../../deps_fishshrimpcrab/game-setting
	gitlab.iplaystar.net/game-server/game-user => ../../deps_fishshrimpcrab/game-user
	gitlab.iplaystar.net/game-server/heart-beat => ../../deps_fishshrimpcrab/heart-beat
	gitlab.iplaystar.net/game-server/http => ../../deps_fishshrimpcrab/http
	gitlab.iplaystar.net/game-server/idle => ../../deps_fishshrimpcrab/idle
	gitlab.iplaystar.net/game-server/lobby-room => ../../deps_fishshrimpcrab/lobby-room
	gitlab.iplaystar.net/game-server/lobby-setting => ../../deps_fishshrimpcrab/lobby-setting
	gitlab.iplaystar.net/game-server/logger => ../../deps_fishshrimpcrab/logger
	gitlab.iplaystar.net/game-server/mac-address => ../../deps_fishshrimpcrab/mac-address
	gitlab.iplaystar.net/game-server/maintain => ../../deps_fishshrimpcrab/maintain
	gitlab.iplaystar.net/game-server/mysql => ../../deps_fishshrimpcrab/mysql
	gitlab.iplaystar.net/game-server/player => ../../deps_fishshrimpcrab/player
	gitlab.iplaystar.net/game-server/postman => ../../deps_fishshrimpcrab/postman
	gitlab.iplaystar.net/game-server/redis => ../../deps_fishshrimpcrab/redis
	gitlab.iplaystar.net/game-server/session => ../../deps_fishshrimpcrab/session
	gitlab.iplaystar.net/game-server/session-manager => ../../deps_fishshrimpcrab/session-manager
	gitlab.iplaystar.net/game-server/wallet => ../../deps_fishshrimpcrab/wallet
)
