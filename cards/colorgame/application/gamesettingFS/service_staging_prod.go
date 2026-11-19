//go:build staging || prod
// +build staging prod

package gamesettingFS

import (
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	gamesetting "gitlab.iplaystar.net/game-server/game-setting"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/mysql"
)

func (s *service) NewHandler(gs *gamesetting.GameSetting) *gamesetting.GameSetting {
	if db, err := mysql.Repository.GameDB(gs.HostExtId); err == nil {
		if rows, err := db.
			Table("game").
			Select("game.langs, host_89_game.host_id, host_89_game.game_id, host_89_game.subgame_id, host_89_game.bet_list, host_89_game.rate_list, host_89_game.balance_limit, host_89_game.banker_limit, host_89_game.waiting_time, host_id.session_timeout, host_89_game.ip_config, host_89_game.room_config, host_89_game.host_connect_config").
			Joins("INNER JOIN host_89_game ON game.enable = 1 AND host_89_game.enable = 1 AND game.id = host_89_game.game_id").
			Joins("INNER JOIN host_id ON host_id.host_id = host_89_game.host_id AND host_id.host_ext_id = ?", gs.HostExtId).
			Rows(); err == nil {

			defer rows.Close()

			for rows.Next() {
				game := &HostFSGame{}

				if err := rows.Scan(
					&game.Langs,
					&game.HostId,
					&game.GameId,
					&game.SubGameId,
					&game.BetList,
					&game.RateList,
					&game.BalanceLimit,
					&game.BetAreaLimit,
					&game.WaitingTime,
					&game.SessionTimeout,
					&game.IpConfig,
					&game.RoomConfig,
					&game.HostConnectConfig,
				); err == nil {
					logger.Service.Zap.Infow("Query Game Settings",
						"GameUser", gs.SecWebSocketKey,
						"HostExtId", gs.HostExtId,
						"HostId", game.HostId,
						"GameId", game.GameId,
						"SubGameId", game.SubGameId,
						"BetList", game.BetList,
						"RateList", game.RateList,
						"Languages", game.Langs,
						"BalanceLimit", game.BalanceLimit,
						"BetAreaLimit", game.BetAreaLimit,
						"WaitingTime", game.WaitingTime,
						"SessionTimeout", game.SessionTimeout,
						"IpConfig", game.IpConfig,
						"RoomConfig", game.RoomConfig,
						"HostConnectConfig", game.HostConnectConfig,
					)
					gs.AvailableGames[game.GameId] = game
				} else {
					logger.Service.Zap.Fatalw(GameSettingFS_QUERY_HOST_FS_GAME_FAILED,
						"GameUser", gs.SecWebSocketKey,
						"HostExtId", gs.HostExtId,
						"Error", err,
					)
					errorcode.Service.Fatal(gs.SecWebSocketKey, GameSettingFS_QUERY_HOST_FS_GAME_FAILED)
				}
			}
		} else {
			logger.Service.Zap.Errorw(GameSettingFS_QUERY_HOST_FS_GAME_FAILED,
				"GameUser", gs.SecWebSocketKey,
				"HostExtId", gs.HostExtId,
				"Error", err,
			)
			errorcode.Service.Fatal(gs.SecWebSocketKey, GameSettingFS_QUERY_HOST_FS_GAME_FAILED)
		}
	} else {
		logger.Service.Zap.Errorw(GameSettingFS_GAME_DB_NOT_FOUND,
			"GameUser", gs.SecWebSocketKey,
			"HostExtId", gs.HostExtId,
			"Error", err,
		)
		errorcode.Service.Fatal(gs.SecWebSocketKey, GameSettingFS_GAME_DB_NOT_FOUND)
	}
	return gs
}
