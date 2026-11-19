//+build dev

package blacklist

import (
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	"gitlab.iplaystar.net/game-server/logger"
	sessionmanager "gitlab.iplaystar.net/game-server/session-manager"
	"os"
	"time"
)

func (s *service) CheckBan(secWebSocketKey, hostExtId, hostId, memberId string) bool {
	open := os.Getenv(Dev_Test_Open)

	if open == "true" {
		errorcode.Service.Fatal(secWebSocketKey, sessionmanager.SessionManager_DUPICATE_SESSION)
		return true
	}

	return false
}

func (s *service) CheckBanByTime(secWebSocketKey, hostExtId, hostId, memberId string, check chan bool, durationTime int64) {
	open := os.Getenv(Dev_Test_Open)

	if open == "true" {
		t := time.NewTicker(time.Duration(durationTime) * time.Second)
		defer t.Stop()

		durationTime := 0
		for {
			select {
			case  <- t.C:
				if durationTime >= 5 {
					errorcode.Service.Fatal(secWebSocketKey, sessionmanager.SessionManager_DUPICATE_SESSION)
				} else {
					logger.Service.Zap.Infow("TEST", "durationTime", durationTime)
					durationTime++
				}

			case <- check:
				return
			}
		}
	}
}