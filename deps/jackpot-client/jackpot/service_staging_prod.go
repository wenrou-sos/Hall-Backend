//+build staging prod

package jackpot

import (
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	jackpot_proto "gitlab.iplaystar.net/game-server/jackpot-client/proto"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/mysql"
	"gitlab.iplaystar.net/game-server/wallet"
)

func (s *service) InsertJackpot(jackpot *jackpot, hostExtId, secWebSocketKey string) {
	if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
		if ok := db.Table("accounting_jackpot").Create(jackpot).RowsAffected; ok == 1 {
			logger.Service.Zap.Infow("Insert Accounting Jackpot",
				"AccountingSn", jackpot.AccountingSn,
				"JackpotSn", jackpot.JackpotSn,
				"HostId", jackpot.HostId,
				"HostExtId", hostExtId,
				"JackpotType", jackpot.JackpotType,
				"JackpotGroup", jackpot.JackpotGroup,
				"JackpotPool", jackpot.JackpotPool,
				"JackpotName", jackpot.JackpotName,
				"JackpotWin", jackpot.JackpotWin,
				"JackpotData", jackpot.JackpotData,
			)
		} else {
			logger.Service.Zap.Errorw(Jackpot_INSERT_ACCOUNTING_JACKPOT_FAILED,
				"AccountingSn", jackpot.AccountingSn,
				"JackpotSn", jackpot.JackpotSn,
				"HostId", jackpot.HostId,
				"HostExtId", hostExtId,
				"JackpotType", jackpot.JackpotType,
				"JackpotGroup", jackpot.JackpotGroup,
				"JackpotPool", jackpot.JackpotPool,
				"JackpotName", jackpot.JackpotName,
				"JackpotWin", jackpot.JackpotWin,
				"JackpotData", jackpot.JackpotData,
			)
			errorcode.Service.Fatal(secWebSocketKey, Jackpot_INSERT_ACCOUNTING_JACKPOT_FAILED)
		}
	} else {
		logger.Service.Zap.Errorw(Jackpot_GAME_DB_NOT_FOUND,
			"HostExtId", hostExtId,
		)
		errorcode.Service.Fatal(secWebSocketKey, Jackpot_GAME_DB_NOT_FOUND)
	}
}

func (s *service) InsertVp1(accountingSn uint64, contributeValue float64, hostExtId, secWebSocketKey string) {
	if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
		if ok := db.Exec("UPDATE `accounting_vp1` SET `jp_contrib` = ?, `game_time` = NOW() WHERE `sn` = ?",
			contributeValue,
			accountingSn,
		).RowsAffected; ok == 0 {
			if ok := db.Exec("INSERT INTO `accounting_vp1` (sn,jp_contrib,bonus_type,game_time) VALUES(?,?,?,NOW())",
				accountingSn,
				contributeValue,
				0,
			).RowsAffected; ok == 0 {
				logger.Service.Zap.Infow(Jackpot_INSERT_ACCOUNTING_VP1_FAILED,
					"AccountingSn", accountingSn,
				)
			}
		}
	} else {
		logger.Service.Zap.Errorw(Jackpot_GAME_DB_NOT_FOUND,
			"HostExtId", hostExtId,
		)
		errorcode.Service.Fatal(secWebSocketKey, Jackpot_GAME_DB_NOT_FOUND)
	}
}

func (s *service) UpdateJackpot(jackpot *jackpot, hostExtId, secWebSocketKey string) {
	if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
		if ok := db.Exec("UPDATE `accounting_jackpot` SET `is_paid` = 1 WHERE `accounting_sn` = ? AND `jackpot_sn` = ?",
			jackpot.AccountingSn,
			jackpot.JackpotSn,
		).RowsAffected; ok == 1 {
			logger.Service.Zap.Infow("Update Accounting Jackpot",
				"AccountingSn", jackpot.AccountingSn,
				"JackpotSn", jackpot.JackpotSn,
			)
		} else {
			logger.Service.Zap.Infow(Jackpot_UPDATE_ACCOUNTING_JACKPOT_FAILED,
				"AccountingSn", jackpot.AccountingSn,
				"JackpotSn", jackpot.JackpotSn,
			)
			errorcode.Service.Fatal(secWebSocketKey, Jackpot_UPDATE_ACCOUNTING_JACKPOT_FAILED)
		}
	} else {
		logger.Service.Zap.Errorw(Jackpot_GAME_DB_NOT_FOUND,
			"HostExtId", hostExtId,
		)
		errorcode.Service.Fatal(secWebSocketKey, Jackpot_GAME_DB_NOT_FOUND)
	}
}

func (s *service) Award(hitInfo *jackpot_proto.HitInfo) {
	// todo dd call wallet api (BonusAward in game-server)
	secWebSocketKey := hitInfo.ClientInfo.SessionId
	walletType := wallet.Service.WalletCategory(secWebSocketKey)
	switch walletType {
	case wallet.CategoryHost:
		wallet.Service.IncreaseCent(secWebSocketKey, hitInfo.JackpotData, hitInfo.WinningCent)
	default:
		wallet.Service.IncreaseBalance(secWebSocketKey, hitInfo.JackpotData, hitInfo.WinningCent, 0, 0)
	}
}
