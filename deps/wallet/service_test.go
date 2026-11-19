package wallet

import (
	"github.com/jinzhu/gorm"
	"gitlab.iplaystar.net/game-server/mysql"
	"testing"
)

func TestService_walletHost(t *testing.T) {
	var dataBase *gorm.DB
	if db, err := mysql.Repository.GameDB("dd12f3635bc9599ca58012601d07197c"); err == nil {
		dataBase = db
	}

	w := &wallet{
		secWebSocketKey:   "jerryKey",
		hostId:            "dd12f3635bc9599ca58012601d07197c",
		hostExtId:         "dd12f3635bc9599ca58012601d07197c",
		memberName:        "jerry",
		memberId:          "1",
		category:          CategoryHost,
		isGuest:           false,
		iHandler:          nil,
		walletGuest:       nil,
		walletPlayer:      nil,
		walletSharedMajor: nil,
		walletSharedMinor: &walletSharedMinor{
			secWebSocketKey: "jerryKey",
			memberId: 		 "1",
			hostId:   		 "dd12f3635bc9599ca58012601d07197c",
			category: 		 2,
			db: 	  		 dataBase,
		},
		walletHost: 	   &walletHost{
			secWebSocketKey: "jerryKey",
			hostId:          "dd12f3635bc9599ca58012601d07197c",
			memberId:        "1",
			gameId: 		 "PSF-ON-00003",
			subGameId:       0,
			category:        2,
			balance:         0,
			token: 			 "eyJpdiI6IjhsVWlCQ0IxRE5PYXZOKzRcLzlXYitnPT0iLCJ2YWx1ZSI6Ik9VU25TQmxqUk5VaVZxM3U2Yk4zR2c9PSIsIm1hYyI6IjJkZDFhMTU1NzNlMGI0NTNjM2Y3ODQwODY5OTM3N2UyZjQ2NjU4ZTRhYWEyNGZiMjA1NjE1MmE2YzgzNDA2NGYifQ%3d%3d",
			db:              dataBase,
		},
	}

	Service.Open(w)
	//t.Log(w.walletHost.open())
	// 扣款
	//t.Log(w.walletHost.selectBalance())
	//t.Log(w.walletHost.decreaseBalance(0,10))

	//t.Log(w.walletHost.selectBalance())
	// 增加金額
	//t.Log(w.walletHost.increaseBalance(61457, 10, 0))
	//t.Log(w.walletHost.selectBalance())

	// 退還下注
	//t.Log(Service.Refund(w.secWebSocketKey, 0))
	//t.Log(w.walletHost.selectBalance())

	// 轉入
	//centBegin, _ := w.walletSharedMinor.selectCent()
	//balance, balanceBegin := w.walletHost.selectBalance()
	//t.Log(balance, balanceBegin, centBegin)
	//Service.Deposit(w.secWebSocketKey, 10, 0)
	//cent, _ := w.walletSharedMinor.selectCent()
	//balance, balanceCheck := w.walletHost.selectBalance()
	//t.Log(balance, balanceCheck, cent)

	// 轉出
	//centBeginWithdraw, _ := w.walletSharedMinor.selectCent()
	//balanceWithdraw, balanceBeginWithdraw := w.walletHost.selectBalance()
	//t.Log(balanceWithdraw, balanceBeginWithdraw, centBeginWithdraw)
	//Service.Withdraw(w.secWebSocketKey, 10, 0)
	//centWithdraw, _ := w.walletSharedMinor.selectCent()
	//balance, balanceCheckWithdraw := w.walletHost.selectBalance()
	//t.Log(balance, balanceCheckWithdraw, centWithdraw)
}