//+build dev

package wallet

import (
	"errors"

	errorcode "gitlab.iplaystar.net/game-server/error-code"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
)

func (s *service) Open(w *wallet) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if _, ok := s.usersWallet[w.secWebSocketKey]; ok {
		s.Close(w.secWebSocketKey)
	}

	switch w.category {
	case CategoryGuest:
		s.usersWallet[w.secWebSocketKey] = w
		w.accType = w.walletGuest.accType
		flux.Send(ActionWalletOpened, s.id, w.secWebSocketKey, "")
		return
	}
}

func (s *service) SetToken(secWebSocketKey, token string) {}

func (s *service) SetPurpose(secWebSocketKey string, purpose int) {}

func (s *service) SetGameIdAndSubGameId(secWebSocketKey, gameId string, subGameId int) {

}

func (s *service) BalanceCache(secWebSocketKey string) (balance uint64, err error) {
	b, err := s.Balance(secWebSocketKey)
	return b, err
}

func (s *service) Balance(secWebSocketKey string) (balance uint64, err error) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		switch w.category {
		case CategoryGuest:
			return w.walletGuest.balance, nil
		}
	}

	logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
		"GameUser", secWebSocketKey,
	)
	errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
	return 0, errors.New(Wallet_NOT_FOUND)
}

func (s *service) IncreaseBalance(secWebSocketKey, uuid string, cent, betAmt, wimAmt uint64) {
	//cent := pay * bet * rate
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if cent <= 0 {
		return
	}

	if w, ok := s.usersWallet[secWebSocketKey]; ok {

		switch w.category {
		case CategoryGuest:
			w.walletGuest.increaseBalance(cent)
		}
		return
	}

	logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
		"GameUser", secWebSocketKey,
		"Cent", cent,
	)
	errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
}

func (s *service) DecreaseBalance(secWebSocketKey, uuid string, cent uint64) bool {
	//cent := bet * rate
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if w, ok := s.usersWallet[secWebSocketKey]; ok {

		switch w.category {
		case CategoryGuest:
			if w.walletGuest.decreaseBalance(cent) {
				return true
			}
		}

		logger.Service.Zap.Errorw(Wallet_DECREASE_BALANCE_FAILED,
			"GameUser", secWebSocketKey,
			"Cent", cent,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_DECREASE_BALANCE_FAILED)
		return false
	}

	logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
		"GameUser", secWebSocketKey,
		"Cent", cent,
	)
	errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
	return false
}

func (s *service) CentCache(secWebSocketKey string) (balance uint64, err error) {
	b, err := s.Cent(secWebSocketKey)
	return b, err
}

func (s *service) Cent(secWebSocketKey string) (balance uint64, err error) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		switch w.category {
		case CategoryGuest:
			return w.walletGuest.cent, nil
		}
	}

	logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
		"GameUser", secWebSocketKey,
	)
	errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
	return 0, errors.New(Wallet_NOT_FOUND)
}

func (s *service) IncreaseCent(secWebSocketKey, uuid string, cent uint64) {
	//cent := pay * bet * rate
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if cent <= 0 {
		return
	}

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		switch w.category {
		case CategoryGuest:
			w.walletGuest.increaseCent(cent)
		}
		return
	}

	logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
		"GameUser", secWebSocketKey,
		"Cent", cent,
	)
	errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
}

func (s *service) DecreaseCent(secWebSocketKey, uuid string, cent uint64) bool {
	//cent := bet * rate
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		switch w.category {
		case CategoryGuest:
			if w.walletGuest.decreaseCent(cent) {
				return true
			}
		}

		logger.Service.Zap.Errorw(Wallet_DECREASE_CENT_FAILED,
			"GameUser", secWebSocketKey,
			"Cent", cent,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_DECREASE_CENT_FAILED)
		return false
	}

	logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
		"GameUser", secWebSocketKey,
		"Cent", cent,
	)
	errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
	return false
}

func (s *service) Deposit(secWebSocketKey string, cent, accountingSn uint64) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if cent <= 0 {
		logger.Service.Zap.Errorw(Wallet_CENT_INVALID,
			"GameUser", secWebSocketKey,
			"Cent", cent,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_CENT_INVALID)
		return
	}

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		switch w.category {
		case CategoryGuest:
			if err := w.walletGuest.deposit(cent); err == nil {
				return
			}
		}

		logger.Service.Zap.Errorw(Wallet_DEPOSIT_BALANCE_FAILED,
			"GameUser", secWebSocketKey,
			"Cent", cent,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_DEPOSIT_BALANCE_FAILED)
		return
	}

	logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
		"GameUser", secWebSocketKey,
		"Cent", cent,
	)
	errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
}

func (s *service) Withdraw(secWebSocketKey string, sn, cent, betAmt, winAmt uint64) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if cent <= 0 {
		logger.Service.Zap.Errorw(Wallet_CENT_INVALID,
			"GameUser", secWebSocketKey,
			"Cent", cent,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_CENT_INVALID)
		return
	}

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		switch w.category {
		case CategoryGuest:
			if err := w.walletGuest.withdraw(cent); err == nil {
				return
			}
		}

		logger.Service.Zap.Errorw(Wallet_WITHDRAW_BALANCE_FAILED,
			"GameUser", secWebSocketKey,
			"Cent", cent,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_WITHDRAW_BALANCE_FAILED)
		return
	}

	logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
		"GameUser", secWebSocketKey,
		"Cent", cent,
	)
	errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
}

func (s *service) Refund(secWebSocketKey string, txnId uint64, doDecreaseCent bool) {
	// do nothing
}

func (s *service) EndAccounting(secWebSocketKey string, bet, sn uint64, checkAccountingEnd bool) {

}

func (s *service) UpdateCent(secWebSocketKey, gameId string, cent uint64) bool {
	return true
}

// --- 本地 dev 补齐 V2 接口（与 staging/prod 签名一致，委托 V1 实现） ---

func (s *service) CentV2(secWebSocketKey string) (balance uint64, err error) {
	return s.Cent(secWebSocketKey)
}

func (s *service) CentCacheV2(secWebSocketKey string) (balance uint64, err error) {
	return s.CentCache(secWebSocketKey)
}

func (s *service) IncreaseBalanceV2(secWebSocketKey, uuid string, cent, betAmt, winAmt uint64) {
	s.IncreaseBalance(secWebSocketKey, uuid, cent, betAmt, winAmt)
}

func (s *service) WithdrawV2(secWebSocketKey string, sn, cent, betAmt, winAmt uint64) {
	s.Withdraw(secWebSocketKey, sn, cent, betAmt, winAmt)
}
