//+build staging prod

package blacklist

import (
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	"gitlab.iplaystar.net/game-server/mysql"
	sessionmanager "gitlab.iplaystar.net/game-server/session-manager"
	"time"
)

func (s *service) CheckBan(secWebSocketKey, hostExtId, hostId, memberId string) bool {
	var value int32

	if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
		if rows, err := db.
			Table("member").
			Select("acc_type").
			Where("host_id = ? AND id = ?", hostId, memberId).
			Rows(); err == nil {

			defer rows.Close()
			for rows.Next() {

				if err := rows.Scan(
					&value,
				); err == nil {

				}
			}
		}
	}

	if value == 4 {
		errorcode.Service.Fatal(secWebSocketKey, sessionmanager.SessionManager_DUPICATE_SESSION)
		return true
	}

	return false
}

func (s *service) CheckBanByTime(secWebSocketKey, hostExtId, hostId, memberId string, check chan bool, durationTime int64) {
	if s.CheckBan(secWebSocketKey, hostExtId, hostId, memberId) {
		return
	}

	t := time.NewTicker(time.Duration(durationTime) * time.Second)
	defer t.Stop()

	for {
		select {
		case <- t.C:
			var value int32

			if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
				if rows, err := db.
					Table("member").
					Select("acc_type").
					Where("host_id = ? AND id = ?", hostId, memberId).
					Rows(); err == nil {

					defer rows.Close()
					for rows.Next() {

						if err := rows.Scan(
							&value,
						); err == nil {

						}
					}
				}
			}

			if value == 4 {
				errorcode.Service.Fatal(secWebSocketKey, sessionmanager.SessionManager_DUPICATE_SESSION)
			}

		case <- check:
			return
		}
	}
}