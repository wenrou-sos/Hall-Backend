package main

import (
	"colorgame-game-server/presentation/playerFS"
	_ "net/http/pprof"

	_ "github.com/joho/godotenv/autoload"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/player"
	_ "go.uber.org/automaxprocs"
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
