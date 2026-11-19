package wallet

import (
	"errors"
	"fmt"
	"strconv"
	"time"

	"github.com/jinzhu/gorm"
)

type walletSharedMinor struct {
	secWebSocketKey string
	memberId        string
	hostId          string
	category        int
	purpose         int
	cent            uint64
	accType         uint8 // 0:locked 1:regular 2:test 3:vip
	db              *gorm.DB
}

func (w *walletSharedMinor) open() (ok bool) {
	data := &memberWallet{}

	rowsAffected := w.db.
		Table("member_wallet").
		Select("host_id, member_id, purpose, balance").
		Where("member_id = ? AND host_id = ? AND purpose = ?", w.memberId, w.hostId, w.purpose).
		Scan(data).
		RowsAffected

	if rowsAffected == 1 {
		w.cent = data.Balance
		return w.selectMember()
	}

	if rowsAffected == 0 {
		data.HostId = w.hostId
		data.MemberId = w.memberId
		data.Purpose = uint(w.purpose)
		data.Balance = 0

		if rowsAffected := w.db.Create(data).RowsAffected; rowsAffected == 1 {
			return w.selectMember()
		}
	}

	return false
}

func (w *walletSharedMinor) selectMember() (ok bool) {
	data := &member{}

	if rowsAffected := w.db.
		Table("member").
		Select("host_id, id, player_cent, acc_type").
		Where("id = ? AND host_id = ?", w.memberId, w.hostId).
		Scan(data).
		RowsAffected; rowsAffected == 1 {
		w.accType = data.AccType
		return true
	}

	return w.duplicateUpdateMember()
}

func (w *walletSharedMinor) duplicateUpdateMember() (ok bool) {
	data := &member{
		HostId:     w.hostId,
		Id:         w.memberId,
		PlayerCent: 0,
		AccType:    AccountingTypeRegular,
	}

	if rowsAffected := w.db.
		Table("member").
		Set("gorm:insert_option", "ON DUPLICATE KEY UPDATE host_id = VALUES(host_id), id = VALUES(id)").
		Create(data).
		RowsAffected; rowsAffected == 1 {
		w.accType = data.AccType
		return true
	}

	return false
}

func (w *walletSharedMinor) selectCent() (balance uint64, ok bool) {
	data := &memberWallet{}

	if rowsAffected := w.db.
		Table("member_wallet").
		Select("balance").
		Where("member_id = ? AND host_id = ? AND purpose = ?", w.memberId, w.hostId, w.purpose).
		Scan(data).
		RowsAffected; rowsAffected == 1 {
		w.cent = data.Balance
		return data.Balance, true
	}

	return 0, false
}

func (w *walletSharedMinor) increaseCent(cent uint64) (ok bool) {
	if cent <= 0 {
		return false
	}

	if rowsAffected := w.db.
		Table("member_wallet").
		Where("member_id = ? AND host_id = ? AND purpose = ?", w.memberId, w.hostId, w.purpose).
		UpdateColumn("balance", gorm.Expr("balance + ?", cent)).
		RowsAffected; rowsAffected == 1 {
		w.cent += cent
		return true
	}

	return false
}

func (w *walletSharedMinor) decreaseCent(cent uint64) (ok bool) {
	if cent <= 0 {
		return false
	}

	if rowsAffected := w.db.
		Table("member_wallet").
		Where("member_id = ? AND host_id = ? AND purpose = ?", w.memberId, w.hostId, w.purpose).
		UpdateColumn("balance", gorm.Expr("balance - ?", cent)).
		RowsAffected; rowsAffected == 1 {
		w.cent -= cent
		return true
	}

	return false
}

func (w *walletSharedMinor) depositCommit(tx *gorm.DB, cent, txnId uint64) (err error) {
	if cent <= 0 {
		tx.Rollback()
		return errors.New(Wallet_CENT_INVALID)
	}

	if ok := tx.
		Table("member_wallet").
		Where("member_id = ? AND host_id = ? AND purpose = ? AND balance >= 0", w.memberId, w.hostId, w.purpose).
		UpdateColumn("balance", gorm.Expr("balance + ?", cent)).
		RowsAffected; ok == 0 {
		tx.Rollback()
		return errors.New(Wallet_DEPOSIT_CENT_FAILED)
	}

	sn := ""
	if txnId != 0 {
		sn = strconv.FormatUint(txnId, 10)
	}

	log := &memberWalletLog{
		HostId:    w.hostId,
		MemberId:  w.memberId,
		Purpose:   uint(w.purpose),
		Action:    logDeposit,
		TxnId:     sn,
		Amount:    cent,
		Balance:   w.cent,
		Note:      logNote,
		OccurTime: time.Now(),
	}

	if ok := tx.
		Table("member_wallet_log").
		Save(log).
		RowsAffected; ok == 0 {
		tx.Rollback()
		return errors.New(Wallet_INSERT_LOG_FAILED)
	}

	w.cent += cent

	return nil
}

func (w *walletSharedMinor) withdrawBegin(tx *gorm.DB, cent, txnId uint64) (err error) {
	if cent <= 0 {
		tx.Rollback()
		return errors.New(Wallet_CENT_INVALID)
	}

	if ok := tx.
		Table("member_wallet").
		Where("member_id = ? AND host_id = ? AND purpose = ?", w.memberId, w.hostId, w.purpose).
		UpdateColumn("balance", gorm.Expr("balance - ?", cent)).
		RowsAffected; ok == 0 {
		tx.Rollback()
		return errors.New(Wallet_WITHDRAW_CENT_FAILED)
	}

	sn := ""
	if txnId != 0 {
		sn = strconv.FormatUint(txnId, 10)
	}

	log := &memberWalletLog{
		HostId:    w.hostId,
		MemberId:  w.memberId,
		Purpose:   uint(w.purpose),
		Action:    logWithdraw,
		TxnId:     sn,
		Amount:    cent,
		Balance:   w.cent,
		Note:      logNote,
		OccurTime: time.Now(),
	}

	if ok := tx.
		Table("member_wallet_log").
		Save(log).
		RowsAffected; ok == 0 {
		tx.Rollback()
		return errors.New(Wallet_INSERT_LOG_FAILED)
	}

	w.cent -= cent

	return nil
}

func (w *walletSharedMinor) refundBegin(tx *gorm.DB, cent, txnId uint64) (err error) {
	if cent <= 0 {
		tx.Rollback()
		return errors.New(Wallet_CENT_INVALID)
	}

	if ok := tx.
		Table("member_wallet").
		Where("member_id = ? AND host_id = ? AND purpose = ?", w.memberId, w.hostId, w.purpose).
		UpdateColumn("balance", gorm.Expr("balance - ?", cent)).
		RowsAffected; ok == 0 {
		tx.Rollback()
		return errors.New(Wallet_REFUND_CENT_FAILED)
	}

	sn := ""
	if txnId != 0 {
		sn = strconv.FormatUint(txnId, 10)
	}

	log := &memberWalletLog{
		HostId:    w.hostId,
		MemberId:  w.memberId,
		Purpose:   uint(w.purpose),
		Action:    logRefund,
		TxnId:     sn,
		Amount:    cent,
		Balance:   w.cent,
		Note:      logNote + "_" + strconv.Itoa(logWithdraw),
		OccurTime: time.Now(),
	}

	if ok := tx.
		Table("member_wallet_log").
		Save(log).
		RowsAffected; ok == 0 {
		tx.Rollback()
		return errors.New(Wallet_INSERT_LOG_FAILED)
	}

	w.cent -= cent

	return nil
}

func (w *walletSharedMinor) updateCent(cent uint64, gameId string) (ok bool) {
	tx := w.db.Begin()

	if rowAffected := tx.
		Table("member_wallet").
		Where("member_id = ? AND host_id = ? AND purpose = ?", w.memberId, w.hostId, w.purpose).
		UpdateColumn("balance", cent).
		RowsAffected; rowAffected == 1 {
		errLog := &hostErrorLog{
			HostId:    w.hostId,
			Action:    6,
			ActionKey: 0,
			ErrCode:   6,
			ErrDescr:  fmt.Sprintf("{\"game_id\":\"%s\",\"member_id\":\"%s\",\"cent\":\"%d\",\"msg\":\"%s\"}", gameId, w.memberId, w.cent, "登入時遊戲錢包金額大於0"),
			OccurTime: time.Now(),
			GameEnd:   0,
		}
		if ok := tx.Table("host_error_log").Save(errLog).RowsAffected; ok == 0 {
			tx.Rollback()
			return false
		}

		tx.Commit()
		w.cent = cent
		return true
	}

	return false
}
