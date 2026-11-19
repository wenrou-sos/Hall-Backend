package wallet

import (
    "errors"
    "github.com/jinzhu/gorm"
    "gitlab.iplaystar.net/game-server/logger"
    "time"
)

type walletPlayer struct {
    secWebSocketKey string
    memberId        string
    hostId          string
    category        int
    balance         uint64
    accType         uint8 // 0:locked 1:regular 2:test 3:vip
    db              *gorm.DB
}

func (w *walletPlayer) open() (ok bool) {
    data := &member{}

    if rowsAffected := w.db.
        Table("member").
        Select("host_id, id, player_cent, acc_type").
        Where("id = ? AND host_id = ?", w.memberId, w.hostId).
        Scan(data).
        RowsAffected; rowsAffected == 1 {
        w.balance = data.PlayerCent
        w.accType = data.AccType
        return true
    }

    return w.duplicateUpdateMember()
}

func (w *walletPlayer) duplicateUpdateMember() (ok bool) {
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
        w.balance = data.PlayerCent
        w.accType = data.AccType
        return true
    }

    return false
}

func (w *walletPlayer) selectBalance() (balance uint64, ok bool) {
    data := &member{}

    if rowsAffected := w.db.
        Table("member").
        Select("player_cent").
        Where("id = ? AND host_id = ?", w.memberId, w.hostId).
        Scan(data).
        RowsAffected; rowsAffected == 1 {
        w.balance = data.PlayerCent

        logger.Service.Zap.Infow("Get Balance",
            "GameUser", w.secWebSocketKey,
            "MemberId", w.memberId,
            "hostId", w.hostId,
            "Balance", w.balance,
        )

        return data.PlayerCent, true
    }

    return 0, false
}

func (w *walletPlayer) increaseBalance(cent uint64) (ok bool) {
    if cent <= 0 {
        return false
    }

    if rowsAffected := w.db.
        Table("member").
        Where("id = ? AND host_id = ?", w.memberId, w.hostId).
        UpdateColumn("player_cent", gorm.Expr("player_cent + ?", cent)).
        RowsAffected; rowsAffected == 1 {
        w.balance += cent
        return true
    }

    return false
}

func (w *walletPlayer) decreaseBalance(cent uint64) (ok bool) {
    if cent <= 0 {
        return false
    }

    if rowsAffected := w.db.
        Table("member").
        Where("id = ? AND host_id = ? AND player_cent >= ?", w.memberId, w.hostId, cent).
        UpdateColumn("player_cent", gorm.Expr("player_cent - ?", cent)).
        RowsAffected; rowsAffected == 1 {
        w.balance -= cent
        return true
    }

    return false
}

func (w *walletPlayer) depositBegin(tx *gorm.DB, cent uint64) (err error) {
    if cent <= 0 {
        tx.Rollback()
        return errors.New(Wallet_CENT_INVALID)
    }

    if ok := tx.
        Table("member").
        Where("id = ? AND host_id = ? AND player_cent >= ?", w.memberId, w.hostId, cent).
        UpdateColumn("player_cent", gorm.Expr("player_cent - ?", cent)).
        RowsAffected; ok == 0 {
        tx.Rollback()
        return errors.New(Wallet_DEPOSIT_BALANCE_FAILED)
    }

    log := &memberWalletLog{
        HostId:    w.hostId,
        MemberId:  w.memberId,
        Purpose:   uint(w.category),
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

func (w *walletPlayer) withdrawCommit(tx *gorm.DB, cent uint64) (err error) {
    if cent <= 0 {
        tx.Rollback()
        return errors.New(Wallet_CENT_INVALID)
    }

    if ok := tx.
        Table("member").
        Where("id = ? AND host_id = ? AND player_cent >= 0", w.memberId, w.hostId).
        UpdateColumn("player_cent", gorm.Expr("player_cent + ?", cent)).
        RowsAffected; ok == 0 {
        tx.Rollback()
        return errors.New(Wallet_WITHDRAW_BALANCE_FAILED)
    }

    log := &memberWalletLog{
        HostId:    w.hostId,
        MemberId:  w.memberId,
        Purpose:   uint(w.category),
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
