package mediator

import (
    "gitlab.iplaystar.net/game-server/logger"
    "sync"
)

var Service = &service{
    Id:        "MediatorService",
    mediators: make(map[string]*mediator),
    mutex:     sync.Mutex{},
}

type service struct {
    Id        string
    mediators map[string]*mediator
    mutex     sync.Mutex
}

func (s *service) New(secWebSocketKey, key string) {
    s.mutex.Lock()
    defer s.mutex.Unlock()

    if _, ok := s.mediators[secWebSocketKey+key]; !ok {
        s.mediators[secWebSocketKey+key] = &mediator{
            secWebSocketKey: secWebSocketKey,
            key:             key,
            works:           0,
            wg:              &sync.WaitGroup{},
        }

        logger.Service.Zap.Debugw("New Mediator",
            "GameUser", secWebSocketKey,
            "Key", key,
            "MediatorSize", len(s.mediators),
        )
    }
}

func (s *service) Add(secWebSocketKey, key string) {
    s.mutex.Lock()
    defer s.mutex.Unlock()

    if v, ok := s.mediators[secWebSocketKey+key]; ok {
        v.works++
        v.wg.Add(1)

        logger.Service.Zap.Debugw("Add Mediator Works",
            "GameUser", v.secWebSocketKey,
            "Key", key,
            "Works", v.works,
            "MediatorSize", len(s.mediators),
            "MediatorMap", s.mediators,
        )
    }
}

func (s *service) Done(secWebSocketKey, key string) {
    s.mutex.Lock()
    defer s.mutex.Unlock()

    if v, ok := s.mediators[secWebSocketKey+key]; ok {
        v.works--

        if v.works < 0 {
            delete(s.mediators, secWebSocketKey+key)
            logger.Service.Zap.Errorw("Negative Mediator Works",
                "GameUser", v.secWebSocketKey,
                "Key", key,
                "Works", v.works,
                "MediatorSize", len(s.mediators),
                "MediatorMap", s.mediators,
            )
            return
        }

        v.wg.Done()

        logger.Service.Zap.Debugw("Done Mediator Works",
            "GameUser", v.secWebSocketKey,
            "Key", key,
            "Works", v.works,
        )

        if v.works == 0 {
            delete(s.mediators, secWebSocketKey+key)

            logger.Service.Zap.Debugw("Delete Mediator After Done",
                "GameUser", v.secWebSocketKey,
                "Key", key,
                "Works", v.works,
                "MediatorSize", len(s.mediators),
                "MediatorMap", s.mediators,
            )
        }
    }
}

func (s *service) Wait(secWebSocketKey, key string) {
    s.mutex.Lock()

    if v, ok := s.mediators[secWebSocketKey+key]; ok {
        logger.Service.Zap.Debugw("Waiting Mediator Works",
            "GameUser", v.secWebSocketKey,
            "Key", key,
            "Works", v.works,
            "MediatorSize", len(s.mediators),
            "MediatorMap", s.mediators,
        )

        s.mutex.Unlock()

        v.wg.Wait()
    } else {
        s.mutex.Unlock()
    }
}

func (s *service) Delete(secWebSocketKey string) {
    s.mutex.Lock()
    defer s.mutex.Unlock()

    for k, v := range s.mediators {
        if v.secWebSocketKey == secWebSocketKey {

            for i := int64(0); i < v.works; i++ {
                v.wg.Done()
            }

            delete(s.mediators, k)

            logger.Service.Zap.Infow("Delete Mediator",
                "GameUser", v.secWebSocketKey,
                "Key", k,
                "Works", v.works,
                "MediatorSize", len(s.mediators),
            )

            logger.Service.Zap.Debugw("Delete Mediator",
                "MediatorMap", s.mediators,
            )
        }
    }
}
