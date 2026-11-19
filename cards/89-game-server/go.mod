module 89-game-server

go 1.15

require (
	github.com/fasthttp/websocket v1.4.3
	github.com/fsnotify/fsnotify v1.4.9
	github.com/gogo/protobuf v1.3.1
	github.com/gomodule/redigo v1.8.2
	github.com/google/uuid v1.1.1
	github.com/gorilla/websocket v1.4.2
	github.com/klauspost/compress v1.10.8 // indirect
	github.com/valyala/fasthttp v1.14.0
	gitlab.iplaystar.net/game-server/accounting v0.1.1
	gitlab.iplaystar.net/game-server/auth v0.1.7
	gitlab.iplaystar.net/game-server/common v0.1.2
	gitlab.iplaystar.net/game-server/error-code v0.0.5
	gitlab.iplaystar.net/game-server/flux v0.0.5
	gitlab.iplaystar.net/game-server/format v0.0.3
	gitlab.iplaystar.net/game-server/game-recovery-v2 v0.0.6
	gitlab.iplaystar.net/game-server/game-setting v0.1.0
	gitlab.iplaystar.net/game-server/game-user v0.1.0
	gitlab.iplaystar.net/game-server/heart-beat v0.0.6
	gitlab.iplaystar.net/game-server/idle v0.0.5
	gitlab.iplaystar.net/game-server/lobby-room v0.0.1
	gitlab.iplaystar.net/game-server/lobby-setting v0.1.0
	gitlab.iplaystar.net/game-server/logger v0.0.4
	gitlab.iplaystar.net/game-server/mac-address v0.0.1
	gitlab.iplaystar.net/game-server/mediator v0.0.8
	gitlab.iplaystar.net/game-server/mysql v0.0.7
	gitlab.iplaystar.net/game-server/player v0.0.2
	gitlab.iplaystar.net/game-server/postman v0.0.3
	gitlab.iplaystar.net/game-server/redis v0.0.2
	gitlab.iplaystar.net/game-server/session v0.0.4
	gitlab.iplaystar.net/game-server/session-manager v0.1.2
	gitlab.iplaystar.net/game-server/shuffle v0.0.1
	gitlab.iplaystar.net/game-server/version v0.0.2
	gitlab.iplaystar.net/game-server/wallet v0.1.6
	gitlab.iplaystar.net/game-server/watchdog v0.0.2
	go.uber.org/automaxprocs v1.3.0
)

replace (
	gitlab.iplaystar.net/game-server/accounting => ../../deps_card/accounting
	gitlab.iplaystar.net/game-server/auth => ../../deps_card/auth
	gitlab.iplaystar.net/game-server/broadcaster => ../../deps_card/broadcaster
	gitlab.iplaystar.net/game-server/common => ../../deps_card/common
	gitlab.iplaystar.net/game-server/error-code => ../../deps_card/error-code
	gitlab.iplaystar.net/game-server/flux => ../../deps_card/flux
	gitlab.iplaystar.net/game-server/format => ../../deps_card/format
	gitlab.iplaystar.net/game-server/game-recovery-v2 => ../../deps_card/game-recovery-v2
	gitlab.iplaystar.net/game-server/game-setting => ../../deps_card/game-setting
	gitlab.iplaystar.net/game-server/game-user => ../../deps_card/game-user
	gitlab.iplaystar.net/game-server/heart-beat => ../../deps_card/heart-beat
	gitlab.iplaystar.net/game-server/http => ../../deps_card/http
	gitlab.iplaystar.net/game-server/idle => ../../deps_card/idle
	gitlab.iplaystar.net/game-server/lobby-room => ../../deps_card/lobby-room
	gitlab.iplaystar.net/game-server/lobby-setting => ../../deps_card/lobby-setting
	gitlab.iplaystar.net/game-server/logger => ../../deps_card/logger
	gitlab.iplaystar.net/game-server/mac-address => ../../deps_card/mac-address
	gitlab.iplaystar.net/game-server/mediator => ../../deps_card/mediator
	gitlab.iplaystar.net/game-server/mysql => ../../deps_card/mysql
	gitlab.iplaystar.net/game-server/player => ../../deps_card/player
	gitlab.iplaystar.net/game-server/postman => ../../deps_card/postman
	gitlab.iplaystar.net/game-server/redis => ../../deps_card/redis
	gitlab.iplaystar.net/game-server/session => ../../deps_card/session
	gitlab.iplaystar.net/game-server/session-manager => ../../deps_card/session-manager
	gitlab.iplaystar.net/game-server/shuffle => ../../deps_card/shuffle
	gitlab.iplaystar.net/game-server/version => ../../deps_card/version
	gitlab.iplaystar.net/game-server/wallet => ../../deps_card/wallet
	gitlab.iplaystar.net/game-server/watchdog => ../../deps_card/watchdog
)
