//+build staging prod

package gamesettingU

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
			Select("IF(host_89_game.math_id <> '',host_89_game.math_id,game.math_id) math_id, game.langs, host_89_game.host_id, host_89_game.game_id, host_89_game.subgame_id, host_89_game.bet_list, host_89_game.rate_list, host_89_game.balance_limit, host_89_game.banker_limit, host_89_game.waiting_time, host_89_game.transfer_credit, host_id.session_timeout, host_89_game.ip_config, host_89_game.room_config, host_89_game.banker_config, host_89_game.host_connect_config, host_89_game.fee, host_89_game.room_limit, host_89_game.id_block_percent, host_89_game.unlucky_rate, host_89_game.blacklist_condition, host_89_game.isolate_rate, host_89_game.auto_blacklist_value").
			Joins("INNER JOIN host_89_game ON game.enable = 1 AND host_89_game.enable = 1 AND game.id = host_89_game.game_id").
			Joins("INNER JOIN host_id ON host_id.host_id = host_89_game.host_id AND host_id.host_ext_id = ?", gs.HostExtId).
			Rows(); err == nil {

			defer rows.Close()

			for rows.Next() {
				game := &hostUGame{}

				if err := rows.Scan(
					&game.MathId,
					&game.Langs,
					&game.HostId,
					&game.GameId,
					&game.SubGameId,
					&game.BetList,
					&game.RateList,
					&game.BalanceLimit,
					&game.BankerLimit,
					&game.WaitingTime,
					&game.TransferCredit,
					&game.SessionTimeout,
					&game.IpConfig,
					&game.RoomConfig,
					&game.BankerConfig,
					&game.HostConnectConfig,
					&game.Fee,
					&game.RoomLimit,
					&game.IdBlockPercent,
					&game.UnluckyRate,
					&game.BlacklistCondition,
					&game.IsolateRate,
					&game.AutoBlacklistValue,
				); err == nil {
					logger.Service.Zap.Infow("Query Game Settings",
						"GameUser", gs.SecWebSocketKey,
						"HostExtId", gs.HostExtId,
						"HostId", game.HostId,
						"GameId", game.GameId,
						"MathModuleId", game.MathId,
						"SubGameId", game.SubGameId,
						"BetList", game.BetList,
						"RateList", game.RateList,
						"Languages", game.Langs,
						"BalanceLimit", game.BalanceLimit,
						"BankerLimit", game.BankerLimit,
						"WaitingTime", game.WaitingTime,
						"TransferCredit", game.TransferCredit,
						"SessionTimeout", game.SessionTimeout,
						"IpConfig", game.IpConfig,
						"RoomConfig", game.RoomConfig,
						"BankerConfig", game.BankerConfig,
						"HostConnectConfig", game.HostConnectConfig,
						"RoomLimit", game.RoomLimit,
						"Fee", game.Fee,
						"IdBlockPercent", game.IdBlockPercent,
						"UnluckyRate", game.UnluckyRate,
						"BlacklistCondition", game.BlacklistCondition,
						"IsolateRate", game.IsolateRate,
						"AutoBlacklistValue", game.AutoBlacklistValue,
					)
					gs.AvailableGames[game.GameId] = game
				} else {
					logger.Service.Zap.Errorw(GameSettingU_QUERY_HOST_U_GAME_FAILED,
						"GameUser", gs.SecWebSocketKey,
						"HostExtId", gs.HostExtId,
						"Error", err,
					)
					errorcode.Service.Fatal(gs.SecWebSocketKey, GameSettingU_QUERY_HOST_U_GAME_FAILED)
				}
			}
		} else {
			logger.Service.Zap.Errorw(GameSettingU_QUERY_HOST_U_GAME_FAILED,
				"GameUser", gs.SecWebSocketKey,
				"HostExtId", gs.HostExtId,
				"Error", err,
			)
			errorcode.Service.Fatal(gs.SecWebSocketKey, GameSettingU_QUERY_HOST_U_GAME_FAILED)
		}
	} else {
		logger.Service.Zap.Errorw(GameSettingU_GAME_DB_NOT_FOUND,
			"GameUser", gs.SecWebSocketKey,
			"HostExtId", gs.HostExtId,
			"Error", err,
		)
		errorcode.Service.Fatal(gs.SecWebSocketKey, GameSettingU_GAME_DB_NOT_FOUND)
	}
	return gs
}
