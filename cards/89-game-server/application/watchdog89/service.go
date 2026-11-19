package watchdog89

import (
    "89-game-server/domain/shuffle89"
    "github.com/fsnotify/fsnotify"
    "gitlab.iplaystar.net/game-server/logger"
    "gitlab.iplaystar.net/game-server/watchdog"
    "path/filepath"
)

var Service = &service{}

type service struct{}

func (s *service) AddPathHandler(watcher *fsnotify.Watcher) {
    watchdog.Service.Add(shuffle89.Service.Docker, watcher)
}

func (s *service) FilterPathHandler(event *fsnotify.Event) {
    switch event.Name {

    case filepath.Join(shuffle89.Service.Docker, shuffle89.Service.File):
        logger.Service.Zap.Infow("WatchDog", "Event", event)

        shuffle89.Service.Reload()
    }
}
