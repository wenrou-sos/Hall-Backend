module fish-game-server

require (
	github.com/360EntSecGroup-Skylar/excelize/v2 v2.3.2
	github.com/fasthttp/websocket v1.4.3
	github.com/fsnotify/fsnotify v1.4.9
	github.com/gogo/protobuf v1.3.1
	github.com/gomodule/redigo v1.8.2
	github.com/google/uuid v1.1.1
	github.com/gorilla/websocket v1.4.2
	github.com/jinzhu/gorm v1.9.16
	github.com/klauspost/compress v1.10.10 // indirect
	github.com/sasha-s/go-deadlock v0.3.1
	github.com/savsgio/gotils v0.0.0-20200616100644-13ff1fd2c28c // indirect
	github.com/valyala/fasthttp v1.15.1
	gitlab.iplaystar.net/game-server/accounting v0.1.3-4
	gitlab.iplaystar.net/game-server/blacklist v0.1.0
	gitlab.iplaystar.net/game-server/broadcaster v0.0.4
	gitlab.iplaystar.net/game-server/common v0.1.3
	gitlab.iplaystar.net/game-server/common-function v0.0.2
	gitlab.iplaystar.net/game-server/error-code v0.0.5
	gitlab.iplaystar.net/game-server/flux v0.0.4
	//gitlab.iplaystar.net/game-server/flux v0.0.5-3
	gitlab.iplaystar.net/game-server/format v0.0.3
	gitlab.iplaystar.net/game-server/heart-beat v0.0.6
	gitlab.iplaystar.net/game-server/http v0.0.5
	gitlab.iplaystar.net/game-server/idle v0.0.5
	gitlab.iplaystar.net/game-server/jackpot-client v0.0.7
	gitlab.iplaystar.net/game-server/logger v0.0.4
	gitlab.iplaystar.net/game-server/maintain v0.0.2
	gitlab.iplaystar.net/game-server/mediator v0.0.8
	gitlab.iplaystar.net/game-server/mysql v0.0.7
	gitlab.iplaystar.net/game-server/player v0.0.2
	gitlab.iplaystar.net/game-server/redis v0.0.2
	gitlab.iplaystar.net/game-server/refundbet-tool v0.0.3
	gitlab.iplaystar.net/game-server/rng v0.0.1
	gitlab.iplaystar.net/game-server/session v0.0.4
	gitlab.iplaystar.net/game-server/session-manager v0.1.2
	gitlab.iplaystar.net/game-server/version v0.0.1
	gitlab.iplaystar.net/game-server/vip v0.0.2
	gitlab.iplaystar.net/game-server/wallet v0.2.28-7
	gitlab.iplaystar.net/game-server/watchdog v0.0.2
	go.uber.org/automaxprocs v1.3.0
	golang.org/x/tools v0.0.0-20200730221956-1ac65761fe2c // indirect
	gopkg.in/yaml.v2 v2.3.0 // indirect
	honnef.co/go/tools v0.0.1-2020.1.5 // indirect
)

go 1.14

replace (
	gitlab.iplaystar.net/game-server/accounting => ../deps/accounting
	gitlab.iplaystar.net/game-server/blacklist => ../deps/blacklist
	gitlab.iplaystar.net/game-server/broadcaster => ../deps/broadcaster
	gitlab.iplaystar.net/game-server/common => ../deps/common
	gitlab.iplaystar.net/game-server/common-function => ../deps/common-function
	gitlab.iplaystar.net/game-server/error-code => ../deps/error-code
	gitlab.iplaystar.net/game-server/flux => ../deps/flux
	gitlab.iplaystar.net/game-server/format => ../deps/format
	gitlab.iplaystar.net/game-server/heart-beat => ../deps/heart-beat
	gitlab.iplaystar.net/game-server/http => ../deps/http
	gitlab.iplaystar.net/game-server/idle => ../deps/idle
	gitlab.iplaystar.net/game-server/jackpot-client => ../deps/jackpot-client
	gitlab.iplaystar.net/game-server/logger => ../deps/logger
	gitlab.iplaystar.net/game-server/mac-address => ../deps/mac-address
	gitlab.iplaystar.net/game-server/maintain => ../deps/maintain
	gitlab.iplaystar.net/game-server/mediator => ../deps/mediator
	gitlab.iplaystar.net/game-server/mysql => ../deps/mysql
	gitlab.iplaystar.net/game-server/player => ../deps/player
	gitlab.iplaystar.net/game-server/redis => ../deps/redis
	gitlab.iplaystar.net/game-server/refundbet-tool => ../deps/refundbet-tool
	gitlab.iplaystar.net/game-server/rng => ../deps/rng
	gitlab.iplaystar.net/game-server/session => ../deps/session
	gitlab.iplaystar.net/game-server/session-manager => ../deps/session-manager
	gitlab.iplaystar.net/game-server/version => ../deps/version
	gitlab.iplaystar.net/game-server/vip => ../deps/vip
	gitlab.iplaystar.net/game-server/wallet => ../deps/wallet
	gitlab.iplaystar.net/game-server/watchdog => ../deps/watchdog
)
