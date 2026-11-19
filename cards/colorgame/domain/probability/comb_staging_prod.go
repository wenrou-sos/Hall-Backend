//go:build staging || prod
// +build staging prod

package probability

import (
	"fmt"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/mysql"
)

func GetFilePath(hostextid string) string {
	var RTP string

	if db, err := mysql.Repository.GameDB(hostextid); err == nil {
		if rows, err := db.
			Table("game").
			Select("host_89_game.math_id").
			Joins("INNER JOIN host_89_game ON game.enable = 1 AND host_89_game.enable = 1 AND game.id = host_89_game.game_id").
			Joins("INNER JOIN host_id ON host_id.host_id = host_89_game.host_id AND host_id.host_ext_id = ? AND id = ?", hostextid, "PSC-ON-00016").
			Rows(); err == nil {
			defer rows.Close()

			for rows.Next() {
				if err := rows.Scan(
					&RTP,
				); err == nil {
					result := fmt.Sprintf("PSCM00016-COLORGAME-%s.json", RTP)
					logger.Service.Zap.Infow("Use RTP", "result", result)
					return result
				} else {
					logger.Service.Zap.Infow("Use Default RTP", "err", err)

					return "PSCM00016-COLORGAME-95.json"
				}

			}
		} else {
			logger.Service.Zap.Infow("Use Default RTP", "err", err)

			return "PSCM00016-COLORGAME-95.json"
		}
	} else {
		logger.Service.Zap.Infow("Use Default RTP", "err", err)

		return "PSCM00016-COLORGAME-95.json"
	}

	logger.Service.Zap.Infow("Use Default RTP")

	return "PSCM00016-COLORGAME-95.json"
}
