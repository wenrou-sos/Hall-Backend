package main

import (
    "fish-game-server/application/watchdogfish"
    broadcasterFish "fish-game-server/domain/broadcaster"
    "fish-game-server/presentation/playerfish"
    "gitlab.iplaystar.net/game-server/broadcaster"
    "gitlab.iplaystar.net/game-server/flux"
    "gitlab.iplaystar.net/game-server/logger"
    "gitlab.iplaystar.net/game-server/mysql"
    "gitlab.iplaystar.net/game-server/player"
    "gitlab.iplaystar.net/game-server/version"
    "gitlab.iplaystar.net/game-server/watchdog"
    _ "go.uber.org/automaxprocs"
    _ "net/http/pprof"
)

func main() {
    flux.Start(logger.Service)
    watchdog.Service.Start(watchdogfish.Service)
    broadcaster.Service.Start(broadcasterFish.Service)
    Version.Service.Start()
    //jackpot.Service.Start()

    // must place last
    player.Controller.Start(playerfish.ControllerFish)

    defer destroy()
}

func destroy() {
    logger.Service.Destroy()
    mysql.Repository.Destroy()
}
