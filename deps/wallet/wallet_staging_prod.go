//+build staging prod

package wallet

import (
    errorcode "gitlab.iplaystar.net/game-server/error-code"
    "gitlab.iplaystar.net/game-server/logger"
    "gitlab.iplaystar.net/game-server/mysql"
)

func (b *builder) SetDB(hostExtId string) *builder {
    if db, err := mysql.Repository.GameDB(hostExtId); err == nil {
        b.db = db
    } else {
        logger.Service.Zap.Errorw(Wallet_GAME_DB_NOT_FOUND,
            "GameUser", b.secWebSocketKey,
            "MemberId", b.memberId,
            "MemberName", b.memberName,
            "HostId", b.hostId,
            "HostExtId", hostExtId,
            "Error", err,
        )
        errorcode.Service.Fatal(b.secWebSocketKey, Wallet_GAME_DB_NOT_FOUND)
    }
    return b
}

func (b *builder) Build() *wallet {
    w := &wallet{
        secWebSocketKey:   b.secWebSocketKey,
        hostId:            b.hostId,
        hostExtId:         b.hostExtId,
        memberName:        b.memberName,
        memberId:          b.memberId,
        category:          b.category,
        isGuest:           b.isGuest,
        iHandler:          b.iHandler,
        accType:           AccountingTypeRegular,
        token:             b.token,
        walletGuest:       nil,
        walletPlayer:      nil,
        walletSharedMajor: nil,
        walletSharedMinor: nil,
        walletHost:        nil,
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

    case CategoryShared:
        if b.purposeMajor > CategoryHost {
            w.walletSharedMajor = &walletSharedMajor{
                secWebSocketKey: b.secWebSocketKey,
                hostId:          b.hostId,
                memberId:        b.memberId,
                category:        b.category,
                purpose:         b.purposeMajor,
                balance:         0,
                db:              b.db,
            }
        }

        if b.purposeMinor > CategoryHost {
            w.walletSharedMinor = &walletSharedMinor{
                secWebSocketKey: b.secWebSocketKey,
                hostId:          b.hostId,
                memberId:        b.memberId,
                category:        b.category,
                purpose:         b.purposeMinor,
                cent:            0,
                db:              b.db,
            }
        }

        return w

    case CategoryPlayer:
        w.walletPlayer = &walletPlayer{
            secWebSocketKey: b.secWebSocketKey,
            hostId:          b.hostId,
            memberId:        b.memberId,
            category:        b.category,
            balance:         b.balance,
            db:              b.db,
        }

        if b.purposeMinor > CategoryHost {
            w.walletSharedMinor = &walletSharedMinor{
                secWebSocketKey: b.secWebSocketKey,
                hostId:          b.hostId,
                memberId:        b.memberId,
                category:        b.category,
                purpose:         b.purposeMinor,
                cent:            0,
                db:              b.db,
            }
        }

        return w

    case CategoryHost:
        w.walletHost = &walletHost{
            secWebSocketKey: b.secWebSocketKey,
            hostId:          b.hostId,
            hostExtId:       b.hostExtId,
            memberId:        b.memberId,
            gameId:          b.gameId,
            subGameId:       b.subGameId,
            category:        b.category,
            token:           b.token,
            balance:         0,
            db:              b.db,
            purpose:         b.purposeMinor,
            betSn:           make(map[uint64]uint64),
            resultSn:        make(map[uint64]uint64),
        }

        if b.purposeMinor > CategoryHost {
            w.walletSharedMinor = &walletSharedMinor{
                secWebSocketKey: b.secWebSocketKey,
                hostId:          b.hostId,
                memberId:        b.memberId,
                category:        b.category,
                purpose:         b.purposeMinor,
                cent:            0,
                db:              b.db,
            }
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
