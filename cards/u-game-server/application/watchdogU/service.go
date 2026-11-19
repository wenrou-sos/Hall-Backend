package watchdogU

import (
	"u-game-server/domain/shuffleU"
	"path/filepath"

	"github.com/fsnotify/fsnotify"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/watchdog"
)

var Service = &service{}

type service struct{}

func (s *service) AddPathHandler(watcher *fsnotify.Watcher) {
	watchdog.Service.Add(shuffleU.Service.Docker, watcher)
}

func (s *service) FilterPathHandler(event *fsnotify.Event) {
	switch event.Name {

	case filepath.Join(shuffleU.Service.Docker, shuffleU.Service.File):
		logger.Service.Zap.Infow("WatchDog", "Event", event)

		shuffleU.Service.Reload()
	}
}
