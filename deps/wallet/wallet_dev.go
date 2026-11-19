//+build dev

package wallet

import (
    errorcode "gitlab.iplaystar.net/game-server/error-code"
    "gitlab.iplaystar.net/game-server/logger"
)

func (b *builder) SetDB(hostExtId string) *builder {
    b.db = nil
    return b
}

func (b *builder) Build() *wallet {
    w := &wallet{
        secWebSocketKey:   b.secWebSocketKey,
        hostId:            b.hostId,
        hostExtId:         b.hostExtId,
        memberName:        b.memberName,
        memberId:          b.memberId,
        category:          CategoryGuest,
        isGuest:           b.isGuest,
        iHandler:          b.iHandler,
        token:             b.token,
        walletGuest:       nil,
        walletPlayer:      nil,
        walletSharedMajor: nil,
        walletSharedMinor: nil,
    }

    switch w.category {
    case CategoryGuest:
        w.walletGuest = &walletGuest{
            secWebSocketKey: b.secWebSocketKey,
            hostId:          b.hostId,
            memberId:        b.memberId,
            category:        b.category,
            balance:         b.balance,
            cent:            0,
            accType:         AccountingTypeTest,
        }

        return w

    default:
        logger.Service.Zap.Errorw(Wallet_TYPE_INVALID,
            "GameUser", w.secWebSocketKey,
            "MemberId", b.memberId,
            "MemberName", b.memberName,
            "HostId", b.hostId,
            "HostExtId", b.hostExtId,
            "Category", w.category,
        )
        errorcode.Service.Fatal(w.secWebSocketKey, Wallet_TYPE_INVALID)
        return nil
    }
}
