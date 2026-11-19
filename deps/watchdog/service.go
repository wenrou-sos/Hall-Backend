package watchdog

import (
    "github.com/fsnotify/fsnotify"
    "gitlab.iplaystar.net/game-server/logger"
    "os"
)

var Service = &service{
    Id:        "WatchDogService",
    isDestroy: make(chan bool, 1024),
}

type service struct {
    Id        string
    isDestroy chan bool
}

type IHandler interface {
    AddPathHandler(watcher *fsnotify.Watcher)
    FilterPathHandler(event *fsnotify.Event)
}

func (s *service) Start(h IHandler) {
    isAllowControl := os.Getenv("ALLOW_CONTROL")

    if isAllowControl == "true" {
        go s.run(h)
        logger.Service.Zap.Infow("Service created.", "Service", Service.Id)
    } else {
        s.Destroy()
    }
}

func (s *service) run(h IHandler) {
    watcher, err := fsnotify.NewWatcher()

    if err != nil {
        logger.Service.Zap.Fatalw(Watchdog_INIT_ERROR,
            "Error", err,
        )
    }

    defer func() {
        watcher.Close()
        s.Destroy()
    }()

    h.AddPathHandler(watcher)

    for {
        select {
        case event := <-watcher.Events:
            if event.Op&fsnotify.Create == fsnotify.Create ||
                event.Op&fsnotify.Rename == fsnotify.Rename ||
                event.Op&fsnotify.Remove == fsnotify.Remove ||
                event.Op&fsnotify.Write == fsnotify.Write ||
                event.Op&fsnotify.Chmod == fsnotify.Chmod {

                h.FilterPathHandler(&event)
            }
        case err := <-watcher.Errors:
            logger.Service.Zap.Warnw(Watchdog_INTERNAL_ERROR,
                "Error", err,
            )

        case is, ok := <-s.isDestroy:
            if !ok || is {
                return
            }
        }
    }
}

func (s *service) Add(path string, watcher *fsnotify.Watcher) {
    if err := watcher.Add(path); err != nil {
        logger.Service.Zap.Warnw(Watchdog_PATH_NOT_FOUND,
            "Path", path,
            "Error", err,
        )
    }
}

func (s *service) Destroy() {
    close(s.isDestroy)
}
