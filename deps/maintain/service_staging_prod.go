//+build staging prod

package maintain

import (
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	"gitlab.iplaystar.net/game-server/mysql"
	sessionmanager "gitlab.iplaystar.net/game-server/session-manager"
	"time"
)

func (s *service) CheckMaintain(secWebSocketKey, gameId, hostExtId, table string) bool {
	var value int32

	if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
		if rows, err := db.
			Table(table).
			Select("maintain").
			Joins("INNER JOIN host_id ON host_id.host_id = "+table+".host_id AND host_id.host_ext_id = ?", hostExtId).
			Where("game_id = ?", gameId).
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

	if value > 0 {
		errorcode.Service.Fatal(secWebSocketKey, sessionmanager.SessionManager_DUPICATE_SESSION)
		return true
	}

	return false
}

func (s *service) CheckMaintainByTime(secWebSocketKey, gameId, hostExtId, table string, check chan bool, durationTime int64) {
	t := time.NewTicker(time.Duration(durationTime) * time.Second)
	defer t.Stop()

	for {
		select {
		case <- t.C:
			var maintain int32

			if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
				if rows, err := db.
					Table(table).
					Select("maintain").
					Joins("INNER JOIN host_id ON host_id.host_id = "+table+".host_id AND host_id.host_ext_id = ?", hostExtId).
					Where("game_id = ?", gameId).
					Rows(); err == nil {

					defer rows.Close()
					for rows.Next() {

						if err := rows.Scan(
							&maintain,
						); err == nil {

						}
					}
				}
			}

			if maintain > 0 {
				errorcode.Service.Fatal(secWebSocketKey, sessionmanager.SessionManager_DUPICATE_SESSION)
			}

		case <- check:
			return
		}
	}
}