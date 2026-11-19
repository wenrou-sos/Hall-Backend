//go:build staging || prod
// +build staging prod

package lobbysettingU

import (
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	lobbysetting "gitlab.iplaystar.net/game-server/lobby-setting"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/mysql"
)

func (s *service) NewHandler(l *lobbysetting.LobbySetting) *lobbysetting.LobbySetting {
	logger.Service.Zap.Infow("UserLobbySettingStart", "secWebSocketKey", l.SecWebSocketKey, "hostExtId", l.HostExtId)
	defer logger.Service.Zap.Infow("UserLobbySettingEnd", "secWebSocketKey", l.SecWebSocketKey, "hostExtId", l.HostExtId)

	if db, err := mysql.Repository.GameDB(l.HostExtId); err == nil {
		logger.Service.Zap.Infow("UserLobbySettingQueryStart", "secWebSocketKey", l.SecWebSocketKey, "hostExtId", l.HostExtId, "DBStatus", db.DB().Stats())
		if rows, err := db.
			Table("game").
			Select("game.langs, host_89_game.host_id, host_89_game.game_id, host_89_game.subgame_id, host_89_game.bet_list, host_89_game.balance_limit, host_89_game.banker_limit, host_89_game.waiting_time, host_89_game.transfer_credit, host_89_game.panel_config, host_id.session_timeout, host_89_game.ip_config, host_89_game.room_config, host_89_game.banker_config, host_89_game.host_connect_config, host_89_game.fee, host_89_game.room_limit").
			Joins("INNER JOIN host_89_game ON game.enable = 1 AND host_89_game.enable = 1 AND game.id = host_89_game.game_id").
			Joins("INNER JOIN host_id ON host_id.host_id = host_89_game.host_id AND host_id.host_ext_id = ?", l.HostExtId).
			Rows(); err == nil {

			defer rows.Close()

			for rows.Next() {
				game := &hostUGame{}

				if err := rows.Scan(
					&game.Langs,
					&game.HostId,
					&game.GameId,
					&game.SubGameId,
					&game.BetList,
					&game.BalanceLimit,
					&game.BankerLimit,
					&game.WaitingTime,
					&game.TransferCredit,
					&game.PanelConfig,
					&game.SessionTimeout,
					&game.IpConfig,
					&game.RoomConfig,
					&game.BankerConfig,
					&game.HostConnectConfig,
					&game.Fee,
					&game.RoomLimit,
				); err == nil {
					logger.Service.Zap.Infow("Query Game Settings",
						"GameUser", l.SecWebSocketKey,
						"HostExtId", l.HostExtId,
						"HostId", game.HostId,
						"GameId", game.GameId,
						"SubGameId", game.SubGameId,
						"BetList", game.BetList,
						"Languages", game.Langs,
						"BalanceLimit", game.BalanceLimit,
						"BankerLimit", game.BankerLimit,
						"WaitingTime", game.WaitingTime,
						"TransferCredit", game.TransferCredit,
						"PanelConfig", game.PanelConfig,
						"SessionTimeout", game.SessionTimeout,
						"IpConfig", game.IpConfig,
						"RoomConfig", game.RoomConfig,
						"BankerConfig", game.BankerConfig,
						"HostConnectConfig", game.HostConnectConfig,
						"Fee", game.Fee,
					)
					l.AvailableGames[game.GameId] = game
				} else {
					logger.Service.Zap.Errorw(LobbySettingU_QUERY_HOST_U_GAME_FAILED,
						"GameUser", l.SecWebSocketKey,
						"HostExtId", l.HostExtId,
						"Error", err,
					)
					errorcode.Service.Fatal(l.SecWebSocketKey, LobbySettingU_QUERY_HOST_U_GAME_FAILED)
				}
			}
		} else {
			logger.Service.Zap.Errorw(LobbySettingU_QUERY_HOST_U_GAME_FAILED,
				"GameUser", l.SecWebSocketKey,
				"HostExtId", l.HostExtId,
				"Error", err,
			)
			errorcode.Service.Fatal(l.SecWebSocketKey, LobbySettingU_QUERY_HOST_U_GAME_FAILED)
		}

		logger.Service.Zap.Infow("UserLobbySettingQueryEnd", "secWebSocketKey", l.SecWebSocketKey, "hostExtId", l.HostExtId, "DBStatus", db.DB().Stats())
	} else {
		logger.Service.Zap.Errorw(LobbySettingU_GAME_DB_NOT_FOUND,
			"GameUser", l.SecWebSocketKey,
			"HostExtId", l.HostExtId,
			"Error", err,
		)
		errorcode.Service.Fatal(l.SecWebSocketKey, LobbySettingU_GAME_DB_NOT_FOUND)
	}
	return l
}
