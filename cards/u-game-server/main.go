package main

import (
	_ "net/http/pprof"
	"u-game-server/application/watchdogU"
	"u-game-server/domain/shuffleU"
	"u-game-server/presentation/playerU"

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
	watchdog.Service.Start(watchdogU.Service)
	shuffle.Service.Start(shuffleU.Service)
	Version.Service.Start("U")

	// must place last
	player.Controller.Start(playerU.ControllerU)

	defer destroy()
}

func destroy() {
	logger.Service.Destroy()
}
