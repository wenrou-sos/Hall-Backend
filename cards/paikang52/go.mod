module 52-game-server

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
	gitlab.iplaystar.net/game-server/accounting v0.1.5
	gitlab.iplaystar.net/game-server/auth v0.2.5
	gitlab.iplaystar.net/game-server/avatar v0.0.2
	gitlab.iplaystar.net/game-server/blacklist v0.1.0
	gitlab.iplaystar.net/game-server/common v0.1.4
	gitlab.iplaystar.net/game-server/error-code v0.0.5
	gitlab.iplaystar.net/game-server/flux v0.0.5
	gitlab.iplaystar.net/game-server/format v0.0.3
	gitlab.iplaystar.net/game-server/game-recovery-v2 v0.0.6
	gitlab.iplaystar.net/game-server/game-setting v0.1.0
	gitlab.iplaystar.net/game-server/game-user v0.1.3
	gitlab.iplaystar.net/game-server/heart-beat v0.0.6
	gitlab.iplaystar.net/game-server/idle v0.0.5
	gitlab.iplaystar.net/game-server/lobby-room v0.0.1
	gitlab.iplaystar.net/game-server/lobby-setting v0.1.1
	gitlab.iplaystar.net/game-server/logger v0.0.4
	gitlab.iplaystar.net/game-server/mac-address v0.0.1
	gitlab.iplaystar.net/game-server/maintain v0.0.2
	gitlab.iplaystar.net/game-server/mediator v0.0.8
	gitlab.iplaystar.net/game-server/mysql v0.0.8
	gitlab.iplaystar.net/game-server/player v0.0.2
	gitlab.iplaystar.net/game-server/postman v0.0.3
	gitlab.iplaystar.net/game-server/redis v0.0.2
	gitlab.iplaystar.net/game-server/rng v0.0.1
	gitlab.iplaystar.net/game-server/session v0.0.4
	gitlab.iplaystar.net/game-server/session-manager v0.1.2
	gitlab.iplaystar.net/game-server/shuffle v0.0.2
	gitlab.iplaystar.net/game-server/version v0.0.2
	gitlab.iplaystar.net/game-server/wallet v0.2.31
	gitlab.iplaystar.net/game-server/watchdog v0.0.2
	go.uber.org/automaxprocs v1.3.0
)

replace (
	gitlab.iplaystar.net/game-server/accounting => ../../deps_paikang52/accounting
	gitlab.iplaystar.net/game-server/auth => ../../deps_paikang52/auth
	gitlab.iplaystar.net/game-server/avatar => ../../deps_paikang52/avatar
	gitlab.iplaystar.net/game-server/blacklist => ../../deps_paikang52/blacklist
	gitlab.iplaystar.net/game-server/broadcaster => ../../deps_paikang52/broadcaster
	gitlab.iplaystar.net/game-server/common => ../../deps_paikang52/common
	gitlab.iplaystar.net/game-server/error-code => ../../deps_paikang52/error-code
	gitlab.iplaystar.net/game-server/flux => ../../deps_paikang52/flux
	gitlab.iplaystar.net/game-server/format => ../../deps_paikang52/format
	gitlab.iplaystar.net/game-server/game-recovery-v2 => ../../deps_paikang52/game-recovery-v2
	gitlab.iplaystar.net/game-server/game-setting => ../../deps_paikang52/game-setting
	gitlab.iplaystar.net/game-server/game-user => ../../deps_paikang52/game-user
	gitlab.iplaystar.net/game-server/heart-beat => ../../deps_paikang52/heart-beat
	gitlab.iplaystar.net/game-server/http => ../../deps_paikang52/http
	gitlab.iplaystar.net/game-server/idle => ../../deps_paikang52/idle
	gitlab.iplaystar.net/game-server/lobby-room => ../../deps_paikang52/lobby-room
	gitlab.iplaystar.net/game-server/lobby-setting => ../../deps_paikang52/lobby-setting
	gitlab.iplaystar.net/game-server/logger => ../../deps_paikang52/logger
	gitlab.iplaystar.net/game-server/mac-address => ../../deps_paikang52/mac-address
	gitlab.iplaystar.net/game-server/maintain => ../../deps_paikang52/maintain
	gitlab.iplaystar.net/game-server/mediator => ../../deps_paikang52/mediator
	gitlab.iplaystar.net/game-server/mysql => ../../deps_paikang52/mysql
	gitlab.iplaystar.net/game-server/player => ../../deps_paikang52/player
	gitlab.iplaystar.net/game-server/postman => ../../deps_paikang52/postman
	gitlab.iplaystar.net/game-server/redis => ../../deps_paikang52/redis
	gitlab.iplaystar.net/game-server/rng => ../../deps_paikang52/rng
	gitlab.iplaystar.net/game-server/session => ../../deps_paikang52/session
	gitlab.iplaystar.net/game-server/session-manager => ../../deps_paikang52/session-manager
	gitlab.iplaystar.net/game-server/shuffle => ../../deps_paikang52/shuffle
	gitlab.iplaystar.net/game-server/version => ../../deps_paikang52/version
	gitlab.iplaystar.net/game-server/wallet => ../../deps_paikang52/wallet
	gitlab.iplaystar.net/game-server/watchdog => ../../deps_paikang52/watchdog
)
