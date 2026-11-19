package activity

import (
    "sync"
    "time"
)

const (
    status_PREVIEW   = "status_PREVIEW"
    status_START     = "status_START"
    status_STOP      = "status_STOP"
    status_CLOSE     = "status_CLOSE"
    EMSGID_eActivity = "EMSGID_eActivity"
)

var Service = &service{
    Id:         "ActivityService",
    activities: sync.Map{},
}

type service struct {
    Id         string
    activities sync.Map
}

func (s *service) nowUTC() int64 {
    return time.Now().UnixNano() / int64(time.Millisecond)
}

func (s *service) Delete(secWebSocketKey string) {
    s.activities.Delete(secWebSocketKey)
}
