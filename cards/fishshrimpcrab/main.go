package main

import (
	"fish-shrimp-crab-game-server/presentation/playerFS"
	_ "github.com/joho/godotenv/autoload"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/player"
	_ "go.uber.org/automaxprocs"
	_ "net/http/pprof"
)

func main() {
	flux.Start(logger.Service)
	// PLAYSTAR START
	// DELETE
	// PLAYSTAR END

	// must place last
	player.Controller.Start(playerFS.ControllerFS)

	defer destroy()
}

func destroy() {
	logger.Service.Destroy()
}
