package wallet

import (
    "errors"
    "github.com/jinzhu/gorm"
    "time"
)

type walletSharedMajor struct {
    secWebSocketKey string
    memberId        string
    hostId          string
    category        int
    purpose         int
    balance         uint64
    accType         uint8 // 0:locked 1:regular 2:test 3:vip
    db              *gorm.DB
}

func (w *walletSharedMajor) open() (ok bool) {
    data := &memberWallet{}

    if rowsAffected := w.db.
        Table("member_wallet").
        Select("host_id, member_id, purpose, balance").
        Where("member_id = ? AND host_id = ? AND purpose = ?", w.memberId, w.hostId, w.purpose).
        Scan(data).
        RowsAffected; rowsAffected == 1 {
        w.balance = data.Balance
        return w.selectMember()
    }

    return false
}

func (w *walletSharedMajor) selectMember() (ok bool) {
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

func (w *walletSharedMajor) duplicateUpdateMember() (ok bool) {
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

func (w *walletSharedMajor) selectBalance() (balance uint64, ok bool) {
    data := &memberWallet{}

    if rowsAffected := w.db.
        Table("member_wallet").
        Select("balance").
        Where("member_id = ? AND host_id = ? AND purpose = ?", w.memberId, w.hostId, w.purpose).
        Scan(data).
        RowsAffected; rowsAffected == 1 {
        w.balance = data.Balance
        return data.Balance, true
    }

    return 0, false
}

func (w *walletSharedMajor) increaseBalance(cent uint64) (ok bool) {
    if cent <= 0 {
        return false
    }

    if rowsAffected := w.db.
        Table("member_wallet").
        Where("member_id = ? AND host_id = ? AND purpose = ?", w.memberId, w.hostId, w.purpose).
        UpdateColumn("balance", gorm.Expr("balance + ?", cent)).
        RowsAffected; rowsAffected == 1 {
        w.balance += cent
        return true
    }

    return false
}

func (w *walletSharedMajor) decreaseBalance(cent uint64) (ok bool) {
    if cent <= 0 {
        return false
    }

    if rowsAffected := w.db.
        Table("member_wallet").
        Where("member_id = ? AND host_id = ? AND purpose = ?", w.memberId, w.hostId, w.purpose).
        UpdateColumn("balance", gorm.Expr("balance - ?", cent)).
        RowsAffected; rowsAffected == 1 {
        w.balance -= cent
        return true
    }

    return false
}

func (w *walletSharedMajor) depositBegin(tx *gorm.DB, cent uint64) (err error) {
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
        return errors.New(Wallet_DEPOSIT_BALANCE_FAILED)
    }

    log := &memberWalletLog{
        HostId:    w.hostId,
        MemberId:  w.memberId,
        Purpose:   uint(w.purpose),
        Action:    logWithdraw,
        TxnId:     "",
        Amount:    cent,
        Balance:   w.balance,
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

    w.balance -= cent

    return nil
}

func (w *walletSharedMajor) withdrawCommit(tx *gorm.DB, cent uint64) (err error) {
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
        return errors.New(Wallet_WITHDRAW_BALANCE_FAILED)
    }

    log := &memberWalletLog{
        HostId:    w.hostId,
        MemberId:  w.memberId,
        Purpose:   uint(w.purpose),
        Action:    logDeposit,
        TxnId:     "",
        Amount:    cent,
        Balance:   w.balance,
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

    w.balance += cent

    return nil
}
