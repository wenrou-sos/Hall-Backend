package watchdog52

import (
	"52-game-server/domain/shuffle52"
	"path/filepath"

	"github.com/fsnotify/fsnotify"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/watchdog"
)

var Service = &service{}

type service struct{}

func (s *service) AddPathHandler(watcher *fsnotify.Watcher) {
	watchdog.Service.Add(shuffle52.Service.Docker, watcher)
}

func (s *service) FilterPathHandler(event *fsnotify.Event) {
	switch event.Name {

	case filepath.Join(shuffle52.Service.Docker, shuffle52.Service.File):
		logger.Service.Zap.Infow("WatchDog", "Event", event)

		shuffle52.Service.Reload()
	}
}
