package blacklist

import "time"

type BlackList struct {
	HostId   string
	MemberId string
	Data     string
	Game     string
	Value    uint64
}

// database table blacklist_log
type blacklistLog struct {
	Sn           uint64 `gorm:"PRIMARY_KEY;AUTO_INCREMENT"`
	HostId       string
	MemberId     string
	Game         string
	Value        uint64
	Note         string
	OccurTime    time.Time
	AccountingSn uint64
}
