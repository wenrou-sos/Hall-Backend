package watchdogfish

import (
    Maintain "fish-game-server/domain/maintain"
    "github.com/fsnotify/fsnotify"
    "gitlab.iplaystar.net/game-server/broadcaster"
    "gitlab.iplaystar.net/game-server/flux"
    jackpot_client "gitlab.iplaystar.net/game-server/jackpot-client"
    "gitlab.iplaystar.net/game-server/logger"
    "gitlab.iplaystar.net/game-server/mysql"
    "path/filepath"
)

func (s *service) maintain_watchdog(event *fsnotify.Event) bool {
    switch event.Name {
    case filepath.Join(Maintain.Service.Docker, Maintain.Service.File):
        logger.Service.Zap.Infow("WatchDog", "Event", event)

        if Maintain.Service.Reload() {
            if Maintain.Service.Shutdown() {
                flux.Send(broadcaster.ActionBroadcasterShutdown, event.Name, broadcaster.Service.Id, Maintain.Service.Message())
            }

            if Maintain.Service.DatabaseReload() {
                mysql.Repository.Reload()
            }
        }
        return true

    case filepath.Join(jackpot_client.Config.Docker, jackpot_client.Config.File):
        logger.Service.Zap.Infow("WatchDog", "Event", event)
        jackpot_client.Config.Reload()

        return true

    default:
        return false

    }
}
