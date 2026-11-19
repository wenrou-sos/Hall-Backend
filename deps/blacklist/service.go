package blacklist

import (
	"time"

	"github.com/jinzhu/gorm"
	"gitlab.iplaystar.net/game-server/mysql"
)

const (
	Dev_Test_Open = "BLACKLIST_BAN_OPEN"
)

var (
	database *gorm.DB
)

var Service = &service{
	Id: "BlacklistService",
}

type service struct {
	Id string
}

func (s *service) Check(hostExtId, hostId, memberId, gameType, gameId string) uint64 {
	if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
		result := &BlackList{}

		if rowsAffected := db.
			Table("member_blacklist").
			Select("value").
			Where("host_id = ? AND member_id = ? AND game = ?", hostId, memberId, gameId).
			Scan(result).
			RowsAffected; rowsAffected == 1 {
			return result.Value
		}

		if rowsAffected := db.
			Table("member_blacklist").
			Select("value").
			Where("host_id = ? AND member_id = ? AND game = ?", hostId, memberId, gameType).
			Scan(result).
			RowsAffected; rowsAffected == 1 {
			return result.Value
		}

		if rowsAffected := db.
			Table("host_blacklist").
			Select("value").
			Where("host_id = ? AND game = ?", hostId, gameId).
			Scan(result).
			RowsAffected; rowsAffected == 1 {
			return result.Value
		}

		if rowsAffected := db.
			Table("host_blacklist").
			Select("value").
			Where("host_id = ? AND game = ?", hostId, gameType).
			Scan(result).
			RowsAffected; rowsAffected == 1 {
			return result.Value
		}
	}

	return 0
}

func (s *service) UpdateMemberBlacklist(hostExtId, hostId, memberId, game string, value uint64, accountingSn uint64) bool {
	if hostId == "" || memberId == "" || game == "" {
		return false
	}

	if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
		result := &BlackList{}

		if rowsAffected := db.Table("member_blacklist").
			Select("data").
			Where("host_id = ? AND member_id = ? AND game = ?", hostId, memberId, game).
			Scan(result).RowsAffected; rowsAffected == 0 {
			result.HostId = hostId
			result.MemberId = memberId
			result.Game = game
			result.Value = value
			if rowsAffected := db.Table("member_blacklist").Create(result).RowsAffected; rowsAffected == 1 {
				s.createBlacklistLog(db, hostId, memberId, game, value, "GS(create)", accountingSn)
				return true
			}
		} else {
			if err := db.Table("member_blacklist").
				Where("host_id = ? AND member_id = ? AND game = ?", hostId, memberId, game).
				UpdateColumn("value", value).
				Error; err == nil {
				s.createBlacklistLog(db, hostId, memberId, game, value, "GS(update)", accountingSn)
				return true
			}
		}
	}

	return false
}

func (s *service) createBlacklistLog(db *gorm.DB, hostId, memberId, game string, value uint64, note string, accountingSn uint64) {
	log := &blacklistLog{
		HostId:       hostId,
		MemberId:     memberId,
		Game:         game,
		Value:        value,
		Note:         note,
		OccurTime:    time.Now(),
		AccountingSn: accountingSn,
	}

	db.Table("blacklist_log").Create(log)
}
