//go:build staging || prod
// +build staging prod

package lobbysettingFS

import (
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	lobbysetting "gitlab.iplaystar.net/game-server/lobby-setting"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/mysql"
)

func (s *service) NewHandler(l *lobbysetting.LobbySetting) *lobbysetting.LobbySetting {

	if db, err := mysql.Repository.GameDB(l.HostExtId); err == nil {
		if rows, err := db.
			Table("game").
			Select("game.langs, host_89_game.host_id, host_89_game.game_id, host_89_game.subgame_id, host_89_game.bet_list, host_89_game.rate_list, host_89_game.balance_limit, host_89_game.banker_limit, host_89_game.waiting_time, host_id.session_timeout, host_89_game.ip_config, host_89_game.room_config, host_89_game.host_connect_config, host_89_game.fee").
			Joins("INNER JOIN host_89_game ON game.enable = 1 AND host_89_game.enable = 1 AND game.id = host_89_game.game_id").
			Joins("INNER JOIN host_id ON host_id.host_id = host_89_game.host_id AND host_id.host_ext_id = ?", l.HostExtId).
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
					&game.Fee,
				); err == nil {
					logger.Service.Zap.Infow("Query Game Settings",
						"GameUser", l.SecWebSocketKey,
						"HostExtId", l.HostExtId,
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
						"Fee", game.Fee,
					)
					l.AvailableGames[game.GameId] = game
				} else {
					logger.Service.Zap.Errorw(LobbySettingFS_QUERY_HOST_FS_GAME_FAILED,
						"GameUser", l.SecWebSocketKey,
						"HostExtId", l.HostExtId,
						"Error", err,
					)
					errorcode.Service.Fatal(l.SecWebSocketKey, LobbySettingFS_QUERY_HOST_FS_GAME_FAILED)
				}
			}
		} else {
			logger.Service.Zap.Errorw(LobbySettingFS_QUERY_HOST_FS_GAME_FAILED,
				"GameUser", l.SecWebSocketKey,
				"HostExtId", l.HostExtId,
				"Error", err,
			)
			errorcode.Service.Fatal(l.SecWebSocketKey, LobbySettingFS_QUERY_HOST_FS_GAME_FAILED)
		}
	} else {
		logger.Service.Zap.Errorw(LobbySettingFS_GAME_DB_NOT_FOUND,
			"GameUser", l.SecWebSocketKey,
			"HostExtId", l.HostExtId,
			"Error", err,
		)
		errorcode.Service.Fatal(l.SecWebSocketKey, LobbySettingFS_GAME_DB_NOT_FOUND)
	}
	return l
}

func (s *service) BotDefaultLobbySetting(hostExtId, gameId string) *HostFSGame {
	if game, ok := s.allHostFSGames[hostExtId+"|"+gameId]; ok {
		return game
	}

	if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
		if rows, err := db.
			Table("game").
			Select("game.langs, host_89_game.host_id, host_89_game.game_id, host_89_game.subgame_id, host_89_game.bet_list, host_89_game.rate_list, host_89_game.balance_limit, host_89_game.banker_limit, host_89_game.waiting_time, host_id.session_timeout, host_89_game.ip_config, host_89_game.room_config, host_89_game.host_connect_config, host_89_game.fee").
			Joins("INNER JOIN host_89_game ON game.enable = 1 AND host_89_game.enable = 1 AND game.id = host_89_game.game_id").
			Joins("INNER JOIN host_id ON host_id.host_id = host_89_game.host_id AND host_id.host_ext_id = ? AND host_89_game.game_id = ?", hostExtId, gameId).
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
					&game.Fee,
				); err == nil {
					logger.Service.Zap.Infow("Query Game Settings",
						"HostExtId", hostExtId,
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
						"Fee", game.Fee,
					)
					s.allHostFSGames[hostExtId+"|"+gameId] = game
					return game
				} else {
					logger.Service.Zap.Errorw(LobbySettingFS_QUERY_HOST_FS_GAME_FAILED,
						"HostExtId", hostExtId,
						"Error", err,
					)
				}
			}
		} else {
			logger.Service.Zap.Errorw(LobbySettingFS_QUERY_HOST_FS_GAME_FAILED,
				"HostExtId", hostExtId,
				"Error", err,
			)
		}
	} else {
		logger.Service.Zap.Errorw(LobbySettingFS_GAME_DB_NOT_FOUND,
			"HostExtId", hostExtId,
			"Error", err,
		)
	}
	return nil
}
