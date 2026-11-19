package wallet

import (
    "errors"
    "gitlab.iplaystar.net/game-server/logger"
)

type walletGuest struct {
    secWebSocketKey string
    memberId        string
    hostId          string
    category        int
    balance         uint64
    cent            uint64
    accType         uint8 // 0:locked 1:regular 2:test 3:vip
}

func (w *walletGuest) increaseBalance(cent uint64) (ok bool) {
    if cent <= 0 {
        return false
    }

    w.balance += cent

    return true
}

func (w *walletGuest) decreaseBalance(cent uint64) (ok bool) {
    if cent <= 0 {
        return false
    }

    if w.balance <= cent {
        w.balance = 0
        return true
    }

    w.balance -= cent

    return true
}

func (w *walletGuest) increaseCent(cent uint64) (ok bool) {
    if cent <= 0 {
        return false
    }

    w.cent += cent

    return true
}

func (w *walletGuest) decreaseCent(cent uint64) (ok bool) {
    if cent <= 0 {
        return false
    }

    if w.cent <= cent {
        w.cent = 0
        return true
    }

    w.cent -= cent

    return true
}

func (w *walletGuest) deposit(cent uint64) (err error) {
    if cent <= 0 {
        return errors.New(Wallet_CENT_INVALID)
    }

    if w.balance >= cent {
        w.balance -= cent
        w.cent += cent

        logger.Service.Zap.Infow("Deposit Balance",
            "GameUser", w.secWebSocketKey,
            "Balance", w.balance,
            "Cent", w.cent,
        )

        return nil
    }

    return errors.New(Wallet_DEPOSIT_BALANCE_FAILED)
}

func (w *walletGuest) withdraw(cent uint64) (err error) {
    if cent <= 0 {
        return errors.New(Wallet_CENT_INVALID)
    }

    if w.cent >= cent {
        w.balance += cent
        w.cent -= cent

        logger.Service.Zap.Infow("Withdraw Balance",
            "GameUser", w.secWebSocketKey,
            "Balance", w.balance,
            "Cent", w.cent,
        )

        return nil
    }

    return errors.New(Wallet_WITHDRAW_BALANCE_FAILED)
}
