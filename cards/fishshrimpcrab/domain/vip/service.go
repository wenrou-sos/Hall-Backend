package vip

import (
	"fish-shrimp-crab-game-server/domain/alarm"

	errorcode "gitlab.iplaystar.net/game-server/error-code"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/mysql"

	"time"

	"github.com/jinzhu/gorm"
)

const (
	VIP_OFF         = 0
	VIP_ON          = 1
	ENFORCE_AUTO    = 0
	ENFORCE_FORCE   = 1
	ENFORCE_DISABLE = 2
)

var Service = &service{
	Id:       "VipService",
	currency: make(map[string]map[string]*CurrencySetting),
}

type service struct {
	Id       string
	currency map[string]map[string]*CurrencySetting
}

func init() {
	logger.Service.Zap.Infow("VIP Service created.",
		"Service", Service.Id,
	)
}

func (s *service) CheckVip(needUpdate bool, secWebSocketKey, hostExtId, hostId, memberId, gameId, billCurrency string, totalBet, totalWin, accountingSn uint64) uint32 {
	if s.currency[hostExtId] == nil {
		s.currency[hostExtId] = s.settingCurrency(secWebSocketKey, hostExtId)
	}
	gameType, vipSetting := s.settingVIP(secWebSocketKey, hostExtId, hostId, gameId)
	
	autoVip := s.updateVip(needUpdate, secWebSocketKey, hostExtId, hostId, memberId, gameType, totalBet, totalWin, s.currency[hostExtId][billCurrency].Normalize, accountingSn, vipSetting)
	if autoVip == nil || autoVip.EnforceVipType == ENFORCE_DISABLE {
		return 0
	}

	if autoVip.EnforceVipType == ENFORCE_FORCE { //強制VIP為進入LEVEL1
		if autoVip.LimitType < 1 {
			s.setVip(secWebSocketKey, hostExtId, hostId, memberId, gameType, gameId, billCurrency, 1, autoVip, accountingSn)
			autoVip.LimitType = 1
		}
	} else {
		// level 0 -> 3 or 1 -> 3 or 2 -> 3
		if autoVip.LimitType < 3 && (autoVip.AllTotalTimes % vipSetting.JudgeCycle3 == 0) {
			if netWinLimit3 := s.currency[hostExtId]["TWD"].Value * vipSetting.NetwinRatio3; vipSetting.LogicalJudgment3 == 1 {
				if autoVip.NowRtp > vipSetting.UpperRtpLimit3 || (autoVip.AllTotalWin > autoVip.AllTotalBet && (autoVip.AllTotalWin-autoVip.AllTotalBet) > netWinLimit3) {
					s.setVip(secWebSocketKey, hostExtId, hostId, memberId, gameType, gameId, billCurrency, 3, autoVip, accountingSn)
					autoVip.LimitType = 3
				}
			} else if vipSetting.LogicalJudgment3 == 0 {
				if autoVip.NowRtp > vipSetting.UpperRtpLimit3 && (autoVip.AllTotalWin > autoVip.AllTotalBet && (autoVip.AllTotalWin-autoVip.AllTotalBet) > netWinLimit3) {
					s.setVip(secWebSocketKey, hostExtId, hostId, memberId, gameType, gameId, billCurrency, 3, autoVip, accountingSn)
					autoVip.LimitType = 3
				}
			} else {
				logger.Service.Zap.Errorw(VIP_SETTING_LOGICALJUDGMENT_3_FAILED,
					"GameUser", secWebSocketKey,
					"HostExtId", hostExtId,
				)
				errorcode.Service.Fatal(secWebSocketKey, VIP_SETTING_LOGICALJUDGMENT_3_FAILED)
			}
		}
		// level 0 -> 2 or 1 -> 2
		if autoVip.LimitType < 2 && (autoVip.AllTotalTimes % vipSetting.JudgeCycle2 == 0) {
			if netWinLimit2 := s.currency[hostExtId]["TWD"].Value * vipSetting.NetwinRatio2; vipSetting.LogicalJudgment2 == 1 {
				if autoVip.NowRtp > vipSetting.UpperRtpLimit2 || (autoVip.AllTotalWin > autoVip.AllTotalBet && (autoVip.AllTotalWin-autoVip.AllTotalBet) > netWinLimit2) {
					s.setVip(secWebSocketKey, hostExtId, hostId, memberId, gameType, gameId, billCurrency, 2, autoVip, accountingSn)
					autoVip.LimitType = 2
				}
			} else if vipSetting.LogicalJudgment2 == 0 {
				if autoVip.NowRtp > vipSetting.UpperRtpLimit2 && (autoVip.AllTotalWin > autoVip.AllTotalBet && (autoVip.AllTotalWin-autoVip.AllTotalBet) > netWinLimit2) {
					s.setVip(secWebSocketKey, hostExtId, hostId, memberId, gameType, gameId, billCurrency, 2, autoVip, accountingSn)
					autoVip.LimitType = 2
				}
			} else {
				logger.Service.Zap.Errorw(VIP_SETTING_LOGICALJUDGMENT_2_FAILED,
					"GameUser", secWebSocketKey,
					"HostExtId", hostExtId,
				)
				errorcode.Service.Fatal(secWebSocketKey, VIP_SETTING_LOGICALJUDGMENT_2_FAILED)
			}
		}
		// level 0 -> 1
		if autoVip.LimitType == 0 && (autoVip.AllTotalTimes % vipSetting.JudgeCycle1 == 0) {
			if netWinLimit1 := s.currency[hostExtId]["TWD"].Value * vipSetting.NetwinRatio1; vipSetting.LogicalJudgment1 == 1 {
				if autoVip.NowRtp > vipSetting.UpperRtpLimit1 || (autoVip.AllTotalWin > autoVip.AllTotalBet && (autoVip.AllTotalWin-autoVip.AllTotalBet) > netWinLimit1) {
					s.setVip(secWebSocketKey, hostExtId, hostId, memberId, gameType, gameId, billCurrency, 1, autoVip, accountingSn)
					autoVip.LimitType = 1
				}
			} else if vipSetting.LogicalJudgment1 == 0 {
				if autoVip.NowRtp > vipSetting.UpperRtpLimit1 && (autoVip.AllTotalWin > autoVip.AllTotalBet && (autoVip.AllTotalWin-autoVip.AllTotalBet) > netWinLimit1) {
					s.setVip(secWebSocketKey, hostExtId, hostId, memberId, gameType, gameId, billCurrency, 1, autoVip, accountingSn)
					autoVip.LimitType = 1
				}
			} else {
				logger.Service.Zap.Errorw(VIP_SETTING_LOGICALJUDGMENT_1_FAILED,
					"GameUser", secWebSocketKey,
					"HostExtId", hostExtId,
				)
				errorcode.Service.Fatal(secWebSocketKey, VIP_SETTING_LOGICALJUDGMENT_1_FAILED)
			}

		}
		// level 3 -> 0 or 2 -> 0 or 1 -> 0
		if autoVip.LimitType > 0 && (autoVip.NowRtp < vipSetting.LowerRtpLimit) {
			s.cleanVip(secWebSocketKey, hostExtId, hostId, memberId, gameType, autoVip, accountingSn)
			autoVip.LimitType = 0
		}
	}

	switch autoVip.LimitType {
	case 0:
		return 0
	case 1:
		return vipSetting.LevelValue1
	case 2:
		return vipSetting.LevelValue2
	case 3:
		return vipSetting.LevelValue3
	default:
		return 0
	}

}

func (s *service) updateVip(needUpdate bool, secWebSocketKey, hostExtId, hostId, memberId, gameType string, totalBet, totalWin, ratio uint64, accountingSn uint64, vipSetting *VipSetting) *VipMember {
	autoVip := s.selectVip(secWebSocketKey, hostExtId, hostId, memberId, gameType)

	if autoVip == nil {
		return nil
	}

	if needUpdate {
		autoVip.AllTotalBet += totalBet / uint64(ratio)
		autoVip.AllTotalWin += totalWin / uint64(ratio)
		autoVip.AllTotalTimes += 1
		if autoVip.AllTotalBet == 0 {
			autoVip.NowRtp = 200
		} else {
			autoVip.NowRtp = uint32(float64(autoVip.AllTotalWin) / float64(autoVip.AllTotalBet) * 100)
		}

		data := map[string]interface{}{
			"all_total_bet":   autoVip.AllTotalBet,
			"all_total_win":   autoVip.AllTotalWin,
			"all_total_times": autoVip.AllTotalTimes,
			"now_RTP":         autoVip.NowRtp,
		}

		if autoVip.AllTotalTimes >= vipSetting.MaxTimes {
			autoVip.LimitType = 0
			s.cleanVip(secWebSocketKey, hostExtId, hostId, memberId, gameType, autoVip, accountingSn)
		} else {
			if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
				if db.Table("auto_vip_member_info").
					Where("host_id = ? AND member_id = ? AND game_type = ?", hostId, memberId, gameType).
					UpdateColumn(data).
					Error == nil {
					logger.Service.Zap.Infow("Update Vip",
						"HostId", hostId,
						"MemberId", memberId,
						"GameType", gameType,
						"TotalBet", autoVip.AllTotalBet,
						"TotalWin", autoVip.AllTotalWin,
						"TotalTimes", autoVip.AllTotalTimes,
						"NowRtp", autoVip.NowRtp,
					)
				} else {
					logger.Service.Zap.Errorw(VIP_GAME_DB_NOT_FOUND,
						"GameUser", secWebSocketKey,
						"HostExtId", hostExtId,
						"Error", err,
					)
					errorcode.Service.Fatal(secWebSocketKey, VIP_GAME_DB_NOT_FOUND)
				}
			}
		}
	}

	return autoVip
}

func (s *service) setVip(secWebSocketKey, hostExtId, hostId, memberId, gameType, gameId, billCurrency string, level int, autoVip *VipMember, accountingSn uint64) {
	data := map[string]interface{}{
		"auto_vip_type": VIP_ON,
		"limit_type":    level,
	}
	if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
		if db.Table("auto_vip_member_info").
			Where("host_id = ? AND member_id = ? AND game_type = ?", hostId, memberId, gameType).
			UpdateColumn(data).
			Error == nil {
			logger.Service.Zap.Infow("Set Vip",
				"HostId", hostId,
				"MemberId", memberId,
				"GameType", gameType,
				"Level", level,
			)
			s.createAutoVipLog(db, hostId, memberId, gameType, level, autoVip, accountingSn)
			if level == 3 {
				alarm.Alarm("Member VIP", "card", hostId, gameId, memberId, billCurrency, level, int(autoVip.AllTotalTimes), int(autoVip.NowRtp), int(accountingSn))
			}
		}
	} else {
		logger.Service.Zap.Errorw(VIP_GAME_DB_NOT_FOUND,
			"GameUser", secWebSocketKey,
			"HostExtId", hostExtId,
			"Error", err,
		)
		errorcode.Service.Fatal(secWebSocketKey, VIP_GAME_DB_NOT_FOUND)
	}
}

func (s *service) settingVIP(secWebSocketKey, hostExtId, hostId, gameId string) (string, *VipSetting) {
	if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
		vipSetting := &VipSetting{}

		if db.Table("auto_vip_setting_new").
			Select("upper_RTP_limit1, upper_RTP_limit2, upper_RTP_limit3, lower_RTP_limit, judge_cycle1, judge_cycle2, judge_cycle3, common_data1_level1, common_data1_level2, common_data1_level3, netwin_ratio1, netwin_ratio2, netwin_ratio3, logical_judgment1, logical_judgment2, logical_judgment3, max_times").
			Where("host_id = ? AND game_type = ?", hostId, gameId).
			Scan(vipSetting).
			RowsAffected == 1 {
			return gameId, vipSetting
		}

		if db.Table("auto_vip_setting_new").
			Select("upper_RTP_limit1, upper_RTP_limit2, upper_RTP_limit3, lower_RTP_limit, judge_cycle1, judge_cycle2, judge_cycle3, common_data1_level1, common_data1_level2, common_data1_level3, netwin_ratio1, netwin_ratio2, netwin_ratio3, logical_judgment1, logical_judgment2, logical_judgment3, max_times").
			Where("host_id = ? AND game_type = ?", hostId, "card").
			Scan(vipSetting).
			RowsAffected == 1 {
			return "card", vipSetting
		}
		logger.Service.Zap.Errorw(AUTO_VIP_SETTING_NEW_LOAD_FAILED,
			"GameUser", secWebSocketKey,
			"HostExtId", hostExtId,
			"Error", err,
		)
		errorcode.Service.Fatal(secWebSocketKey, AUTO_VIP_SETTING_NEW_LOAD_FAILED)

		return "", nil
	} else {
		logger.Service.Zap.Errorw(VIP_GAME_DB_NOT_FOUND,
			"GameUser", secWebSocketKey,
			"HostExtId", hostExtId,
			"Error", err,
		)
		errorcode.Service.Fatal(secWebSocketKey, VIP_GAME_DB_NOT_FOUND)
		return "", nil
	}
}

func (s *service) settingCurrency(secWebSocketKey, hostExtId string) map[string]*CurrencySetting {
	if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
		if rows, err := db.
			Table("auto_vip_currency_setting").
			Select("bill_currency, value, normalize").
			Rows(); err == nil {

			defer rows.Close()

			allCurrency := make(map[string]*CurrencySetting)

			for rows.Next() {
				currency := &CurrencySetting{}

				if err := rows.Scan(
					&currency.BillCurrency,
					&currency.Value,
					&currency.Normalize,
				); err == nil {
					allCurrency[currency.BillCurrency] = currency
				} else {
					logger.Service.Zap.Errorw(VIP_SETTING_CURRENCY_FAILED,
						"GameUser", secWebSocketKey,
						"HostExtId", hostExtId,
						"Error", err,
					)
					errorcode.Service.Fatal(secWebSocketKey, VIP_SETTING_CURRENCY_FAILED)
					return nil
				}
			}
			return allCurrency
		}
	} else{
		logger.Service.Zap.Errorw(VIP_GAME_DB_NOT_FOUND,
			"GameUser", secWebSocketKey,
			"HostExtId", hostExtId,
		)
		errorcode.Service.Fatal(secWebSocketKey, VIP_GAME_DB_NOT_FOUND)
	}

	return nil
}

func (s *service) selectVip(secWebSocketKey, hostExtId, hostId, memberId, gameType string) *VipMember {
	autoVip := &VipMember{}
	if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
		if db.Table("auto_vip_member_info").
			Select("auto_vip_type, enforce_VIP_type, limit_type, all_total_bet, all_total_win, all_total_times, now_RTP").
			Where("host_id = ? AND member_id = ? AND game_type = ?", hostId, memberId, gameType).
			Scan(autoVip).
			RowsAffected == 1 {
			return autoVip
		} else {
			model := defaultVip{
				HostId:   hostId,
				MemberId: memberId,
				GameType: gameType,
			}
			db.Table("auto_vip_member_info").Create(model).Scan(autoVip)
		}
	} else {
		logger.Service.Zap.Errorw(VIP_GAME_DB_NOT_FOUND,
			"GameUser", secWebSocketKey,
			"HostExtId", hostExtId,
		)
		errorcode.Service.Fatal(secWebSocketKey, VIP_GAME_DB_NOT_FOUND)
	}

	return nil	
}

func (s *service) cleanVip(secWebSocketKey, hostExtId, hostId, memberId, gameType string, autoVip *VipMember, accountingSn uint64) {
	data := map[string]interface{}{
		"auto_vip_type":   VIP_OFF,
		"limit_type":     0,
		"all_total_bet":   0,
		"all_total_win":   0,
		"all_total_times": 0,
		"now_RTP":         100,
	}
	if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
		if db.Table("auto_vip_member_info").
			Where("host_id = ? AND member_id = ? AND game_type = ?", hostId, memberId, gameType).
			UpdateColumn(data).
			Error == nil {
			logger.Service.Zap.Infow("Clean Vip",
				"HostId", hostId,
				"MemberId", memberId,
				"GameType", gameType,
			)
			s.updateAutoVipLog(db, hostId, memberId, gameType, autoVip, accountingSn)
		}
	} else {
		logger.Service.Zap.Errorw(VIP_GAME_DB_NOT_FOUND,
			"GameUser", secWebSocketKey,
			"HostExtId", hostExtId,
			"Error", err,
		)
		errorcode.Service.Fatal(secWebSocketKey, VIP_GAME_DB_NOT_FOUND)
	}
}

func (s *service) createAutoVipLog(db *gorm.DB, hostId, memberId, gameType string, level int, autoVip *VipMember, accountingSn uint64) {
	log := &VipLog{
		HostId:     hostId,
		MemberId:   memberId,
		GameType:   gameType,
		VipType:    int8(level),
		EnterSn:    accountingSn,
		EnterBet:   autoVip.AllTotalBet,
		EnterWin:   autoVip.AllTotalWin,
		EnterTimes: autoVip.AllTotalTimes,
		EnterTime:  time.Now(),
	}

	db.Table("auto_vip_log").Create(log)
}

func (s *service) updateAutoVipLog(db *gorm.DB, hostId, memberId, gameType string, autoVip *VipMember, accountingSn uint64) {
	data := map[string]interface{}{
		"leave_sn":    accountingSn,
		"leave_bet":   autoVip.AllTotalBet,
		"leave_win":   autoVip.AllTotalWin,
		"leave_times": autoVip.AllTotalTimes,
		"leave_time":  time.Now(),
		"log_end":     1,
	}
	if db.Table("auto_vip_log").
		Where("host_id = ? AND member_id = ? AND game_type = ? AND log_end = ?", hostId, memberId, gameType, 0).
		UpdateColumn(data).
		Error == nil {
		logger.Service.Zap.Infow("Update Auto_Vip_Log",
			"HostId", hostId,
			"MemberId", memberId,
			"GameType", gameType,
		)
	}
}
