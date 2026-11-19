package main

import (
	"89-game-server/application/watchdog89"
	"89-game-server/domain/shuffle89"
	"89-game-server/presentation/player89"
	_ "net/http/pprof"

	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/player"
	"gitlab.iplaystar.net/game-server/shuffle"
	Version "gitlab.iplaystar.net/game-server/version"
	"gitlab.iplaystar.net/game-server/watchdog"
	_ "go.uber.org/automaxprocs"
)

func main() {
	flux.Start(logger.Service)
	watchdog.Service.Start(watchdog89.Service)
	shuffle.Service.Start(shuffle89.Service)
	Version.Service.Start("89")

	// must place last
	player.Controller.Start(player89.Controller89)

	defer destroy()
}

func destroy() {
	logger.Service.Destroy()
}
