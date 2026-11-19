package watchdogfish

import (
	"fish-game-server/domain/fish"
	"github.com/fsnotify/fsnotify"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
	"reflect"
)

func (s *service) mathReload(event *fsnotify.Event, file interface{}) bool {
	logger.Service.Zap.Infow("WatchDog", "Event", event)
	reflect.ValueOf(file).MethodByName("Reload").Call([]reflect.Value{})

	return true
}

func (s *service) scriptReload(event *fsnotify.Event, check bool) bool {
	logger.Service.Zap.Infow("WatchDog", "Event", event)
	if check {
		flux.Send(fish.ActionFishRestart, event.Name, fish.Service.Id, "")
	}

	return true
}