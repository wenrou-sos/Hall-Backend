package main

import (
	"52-game-server/application/watchdog52"
	"52-game-server/domain/shuffle52"
	"52-game-server/presentation/player52"
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
	watchdog.Service.Start(watchdog52.Service)
	shuffle.Service.Start(shuffle52.Service)
	Version.Service.Start("52")

	// must place last
	player.Controller.Start(player52.Controller52)

	defer destroy()
}

func destroy() {
	logger.Service.Destroy()
}
