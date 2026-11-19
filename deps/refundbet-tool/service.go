package refundbettool

import (
	"encoding/json"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/jinzhu/gorm"
	"gitlab.iplaystar.net/game-server/http"
	"gitlab.iplaystar.net/game-server/logger"
	macaddress "gitlab.iplaystar.net/game-server/mac-address"
	"gitlab.iplaystar.net/game-server/mysql"
)

const (
	kAuthenticate = 0
	kRefundBet    = 3
)

var Service = &service{
	Id: "RefundBetService",
}

type service struct {
	Id string
}

// database table host_error_log
type hostErrorLog struct {
	HostId    string
	Action    uint
	ActionKey uint64
	ErrCode   int
	ErrDescr  string
	OccurTime time.Time
	GameEnd   uint
}

type Balance struct {
	StateCode int    `json:"status_code"`
	Balance   uint64 `json:"balance"`
}

type refundInfo struct {
	Sn          uint64 `json:"sn"`
	HostId      string
	GameId      string
	SubGameId   int
	MemberId    string
	TxnId       uint64
	Note        string
	BaseUrl     string `json:"base_url"`
	RefundBet   string `json:"refund_bet"`
	AccessToken string `json:"access_token"`
	Refund      int    `json:"refund"`
}

type refundRecord struct {
	HostId    string
	GameId    string
	SubgameId int
	ServerId  string
	MemberId  string
	TxnId     uint64
	Bet       uint64
	Note      string
	Refund    int
	OccurTime time.Time
}

func init() {
	logger.Service.Zap.Infow("RefundBet Tool Service start up.",
		"Service", Service.Id,
	)
	Service.refundBet()
}

func (s *service) refundBet() {
	refundList, dbList := s.getRefundList()

	for k, r := range refundList {
		logger.Service.Zap.Warnw("Before Refund Bet",
			"HostId", r.HostId,
			"GameId", r.GameId,
			"SubGameId", r.SubGameId,
			"MemberId", r.MemberId,
			"TxnId", r.TxnId,
		)

		parameter := fmt.Sprintf("access_token=%s&txn_id=%d", r.AccessToken, r.TxnId)
		url := fmt.Sprintf("%s/%s?%s", r.BaseUrl, r.RefundBet, parameter)

		var body []byte
		var err error
		if body, err = http.Service.Get(url); err != nil {
			jsonErr := fmt.Sprintf("{\"game_id\":\"%s\",\"member_id\":\"%s\",\"url\":\"%s\",\"msg\":\"%s\"}", r.GameId, r.MemberId, url, err.Error())
			s.apiErrorLog(dbList[k], r.HostId, kAuthenticate, r.TxnId, 1, jsonErr)
			continue
		}
		apiResult := &Balance{}
		if err := json.Unmarshal(body, apiResult); err != nil {
			jsonErr := fmt.Sprintf("{\"game_id\":\"%s\",\"member_id\":\"%s\",\"url\":\"%s\",\"msg\":\"%s\"}", r.GameId, r.MemberId, url, err.Error())
			s.apiErrorLog(dbList[k], r.HostId, kRefundBet, r.TxnId, apiResult.StateCode, jsonErr)
			continue
		}

		if apiResult.StateCode != 0 {
			jsonErr := fmt.Sprintf("{\"game_id\":\"%s\",\"member_id\":\"%s\",\"url\":\"%s\",\"balance\":\"%s\"}", r.GameId, r.MemberId, url, strconv.FormatUint(apiResult.Balance, 10))
			s.apiErrorLog(dbList[k], r.HostId, kRefundBet, r.TxnId, apiResult.StateCode, jsonErr)
			continue
		}

		logger.Service.Zap.Warnw("After Refund Bet",
			"HostId", r.HostId,
			"GameId", r.GameId,
			"SubGameId", r.SubGameId,
			"MemberId", r.MemberId,
			"TxnId", r.TxnId,
		)

		s.deleteAccounting(dbList[k], r)

		tx := dbList[k].Begin()

		if !s.insertRefundRecord(tx, r) {
			tx.Rollback()
			continue
		}
		if !s.deleteRefundLog(tx, r) {
			tx.Rollback()
			continue
		}

		tx.Commit()
	}
}

func (s *service) getRefundList() (refundList map[uint64]*refundInfo, dbList map[uint64]*gorm.DB) {
	refundList = make(map[uint64]*refundInfo)
	dbList = make(map[uint64]*gorm.DB)

	for k, db := range mysql.Repository.GameDBs() {
		if rows, err1 := db.
			Table("member_wallet_refund_log").
			Select("sn, host_id, game_id, subgame_id, member_id, txn_id, note").
			Where("refund = 0 AND occur_time > ? AND server_id = ?", time.Now().Add(-1*time.Hour), s.parseServerId()).
			Rows(); err1 == nil {
			defer rows.Close()

			for rows.Next() {
				r := &refundInfo{}
				if err2 := rows.Scan(
					&r.Sn,
					&r.HostId,
					&r.GameId,
					&r.SubGameId,
					&r.MemberId,
					&r.TxnId,
					&r.Note,
				); err2 == nil {
					if err3 := json.Unmarshal([]byte(r.Note), r); err3 == nil {
						refundList[r.TxnId] = r
						dbList[r.TxnId] = db
					} else {
						logger.Service.Zap.Warnw("Refund Note Unmarshal Failed",
							"HostId", r.HostId,
							"GameId", r.GameId,
							"SubGameId", r.SubGameId,
							"MemberId", r.MemberId,
							"TxnId", r.TxnId,
							"Error", err3,
						)
					}
				}
			}
		} else {
			logger.Service.Zap.Warnw("Get Refund List Failed",
				"Host", k,
				"Error", err1,
			)
		}
	}

	return refundList, dbList
}

func (s *service) insertRefundRecord(db *gorm.DB, r *refundInfo) bool {
	data := &refundRecord{}
	if ok := db.Table("member_wallet_refund_log").
		Select("host_id, game_id, subgame_id, server_id, member_id, txn_id, bet, note, refund, occur_time").
		Where("sn = ?", r.Sn).
		Scan(data).RowsAffected; ok != 1 {
		logger.Service.Zap.Warnw("Select Refund Log Failed",
			"HostId", r.HostId,
			"GameId", r.GameId,
			"SubGameId", r.SubGameId,
			"MemberId", r.MemberId,
			"TxnId", r.TxnId,
		)
		return false
	}
	data.Refund = 1

	if ok := db.Table("member_wallet_refund_record").Create(data).Error; ok != nil {
		logger.Service.Zap.Warnw("Insert Refund Record Failed",
			"HostId", r.HostId,
			"GameId", r.GameId,
			"SubGameId", r.SubGameId,
			"MemberId", r.MemberId,
			"TxnId", r.TxnId,
			"error", ok,
		)
		return false
	}

	logger.Service.Zap.Infow("Insert Refund Record Success",
		"HostId", r.HostId,
		"GameId", r.GameId,
		"SubGameId", r.SubGameId,
		"MemberId", r.MemberId,
		"TxnId", r.TxnId,
	)

	return true
}

func (s *service) deleteRefundLog(db *gorm.DB, r *refundInfo) bool {
	if ok := db.Exec("DELETE FROM member_wallet_refund_log WHERE sn = ?", r.Sn).RowsAffected; ok == 1 {
		logger.Service.Zap.Infow("Delete RefundLog Success",
			"HostId", r.HostId,
			"GameId", r.GameId,
			"SubGameId", r.SubGameId,
			"MemberId", r.MemberId,
			"TxnId", r.TxnId,
		)
	} else {
		logger.Service.Zap.Warnw("Delete RefundLog Failed",
			"HostId", r.HostId,
			"GameId", r.GameId,
			"SubGameId", r.SubGameId,
			"MemberId", r.MemberId,
			"TxnId", r.TxnId,
		)

		return false
	}

	return true
}

func (s *service) deleteAccounting(db *gorm.DB, r *refundInfo) bool {
	if ok := db.
		Exec("DELETE FROM accounting WHERE sn = ?", r.TxnId).
		RowsAffected; ok == 1 {
		logger.Service.Zap.Infow("Delete Accounting Success",
			"HostId", r.HostId,
			"GameId", r.GameId,
			"SubGameId", r.SubGameId,
			"MemberId", r.MemberId,
			"TxnId", r.TxnId,
		)
	} else {
		logger.Service.Zap.Warnw("Delete Accounting Failed",
			"HostId", r.HostId,
			"GameId", r.GameId,
			"SubGameId", r.SubGameId,
			"MemberId", r.MemberId,
			"TxnId", r.TxnId,
		)

		return false
	}

	return true
}

func (s *service) apiErrorLog(db *gorm.DB, hostId string, action uint, actionKey uint64, errCode int, err string) {
	errLog := &hostErrorLog{
		HostId:    hostId,
		Action:    action,
		ActionKey: actionKey,
		ErrCode:   errCode,
		ErrDescr:  err,
		OccurTime: time.Now(),
		GameEnd:   0,
	}

	tx := db.Begin()

	if ok := tx.
		Table("host_error_log").
		Save(errLog).
		RowsAffected; ok == 0 {
		tx.Rollback()
		return
	}

	tx.Commit()
}

func (s *service) parseServerId() string {
	atoiPort, _ := strconv.Atoi(os.Getenv("HTTP_PORT"))

	macAddr := strings.Replace(macaddress.Get(), ":", "-", -1)

	return fmt.Sprintf("%s-%05d", macAddr, atoiPort)
}
