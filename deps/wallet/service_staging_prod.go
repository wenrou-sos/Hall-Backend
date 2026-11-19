//+build staging prod

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

	case CategoryShared:
		if w.walletSharedMajor.open() && w.walletSharedMinor.open() {
			s.usersWallet[w.secWebSocketKey] = w
			w.accType = w.walletSharedMajor.accType
			flux.Send(ActionWalletOpened, s.id, w.secWebSocketKey, "")
			return
		}

	case CategoryPlayer:
		if w.walletPlayer.open() && w.walletSharedMinor.open() {
			s.usersWallet[w.secWebSocketKey] = w
			w.accType = w.walletPlayer.accType
			flux.Send(ActionWalletOpened, s.id, w.secWebSocketKey, "")
			return
		}

	case CategoryHost:
		if ok, action, actionKey, errCode, jsonErr := w.walletHost.open(); ok {
			if w.walletSharedMinor.open() {
				s.usersWallet[w.secWebSocketKey] = w
				w.accType = w.walletHost.accType
				flux.Send(ActionWalletOpened, s.id, w.secWebSocketKey, "")
				return
			}
		} else if action != kNon {
			w.walletHost.apiErrorLog(action, actionKey, errCode, jsonErr)
		}
	}

	logger.Service.Zap.Errorw(Wallet_OPEN_BALANCE_FAILED,
		"GameUser", w.secWebSocketKey,
		"HostId", w.hostId,
		"HostExtId", w.hostExtId,
		"MemberName", w.memberName,
		"MemberId", w.memberId,
		"Category", w.category,
		"IsGuest", w.isGuest,
	)
	errorcode.Service.Fatal(w.secWebSocketKey, Wallet_OPEN_BALANCE_FAILED)
	return
}

func (s *service) SetToken(secWebSocketKey, token string) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		switch w.category {
		case CategoryHost:
			w.walletHost.token = token
		}
	} else {
		logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
			"GameUser", secWebSocketKey,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
	}
}

func (s *service) SetPurpose(secWebSocketKey string, purpose int) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		switch w.category {
		case CategoryHost:
			w.walletHost.purpose = purpose
			w.walletSharedMinor.purpose = purpose

			// Update Cent Wallet
			w.walletSharedMinor.open()
		}
	} else {
		logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
			"GameUser", secWebSocketKey,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
	}
}

func (s *service) SetGameIdAndSubGameId(secWebSocketKey, gameId string, subGameId int) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		switch w.category {
		case CategoryHost:
			w.walletHost.gameId = gameId
			w.walletHost.subGameId = subGameId
		}
	} else {
		logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
			"GameUser", secWebSocketKey,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
	}
}

func (s *service) BalanceCache(secWebSocketKey string) (balance uint64, err error) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		switch w.category {
		case CategoryGuest:
			return w.walletGuest.balance, nil

		case CategoryShared:
			return w.walletSharedMajor.balance, nil

		case CategoryPlayer:
			return w.walletPlayer.balance, nil

		case CategoryHost:
			return w.walletHost.balance, nil
		}
	}

	logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
		"GameUser", secWebSocketKey,
	)
	errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
	return 0, errors.New(Wallet_NOT_FOUND)
}

func (s *service) Balance(secWebSocketKey string) (balance uint64, err error) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if w, ok := s.usersWallet[secWebSocketKey]; ok {

		switch w.category {
		case CategoryGuest:
			return w.walletGuest.balance, nil

		case CategoryShared:
			if balance, ok := w.walletSharedMajor.selectBalance(); ok {
				return balance, nil
			}

		case CategoryPlayer:
			if balance, ok := w.walletPlayer.selectBalance(); ok {
				return balance, nil
			}

		case CategoryHost:
			if balance, ok, action, actionKey, errCode, jsonErr := w.walletHost.selectBalance(); ok {
				return balance, nil
			} else if action != kNon {
				 w.walletHost.apiErrorLog(action, actionKey, errCode, jsonErr)
			}
		}

		logger.Service.Zap.Errorw(Wallet_GET_BALANCE_FAILED,
			"GameUser", secWebSocketKey,
			"MemberId", w.memberId,
			"MemberName", w.memberName,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_GET_BALANCE_FAILED)
		return 0, errors.New(Wallet_GET_BALANCE_FAILED)
	}

	logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
		"GameUser", secWebSocketKey,
	)
	errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
	return 0, errors.New(Wallet_NOT_FOUND)
}

func (s *service) IncreaseBalance(secWebSocketKey, uuid string, cent, betAmt, winAmt uint64) {
	//cent := pay * bet * rate
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		if w.category != CategoryHost {
			if cent <= 0 {
				return
			}
		}

		switch w.category {
		case CategoryGuest:
			if w.walletGuest.increaseBalance(cent) {
				return
			}

		case CategoryShared:
			if w.walletSharedMajor.increaseBalance(cent) {
				logger.Service.Zap.Infow("Increase Balance",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"UUID", uuid,
					"Cent", cent,
				)

				if w.iHandler != nil {
					w.iHandler.IncreaseHandler(secWebSocketKey, uuid, w.walletSharedMajor.balance, cent, 0)
				}
				return
			}

		case CategoryPlayer:
			if w.walletPlayer.increaseBalance(cent) {
				logger.Service.Zap.Infow("Increase Balance",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"UUID", uuid,
					"Cent", cent,
				)

				if w.iHandler != nil {
					w.iHandler.IncreaseHandler(secWebSocketKey, uuid, w.walletPlayer.balance, cent, 0)
				}
				return
			}

		case CategoryHost:
			var txnId uint64 = 0

			if w.iHandler != nil {
				txnId = w.iHandler.GetAccountingSnHandler(secWebSocketKey, w.walletHost.balance, cent, 0, false)
			}

			if _, ok := w.walletHost.resultSn[txnId]; ok {
				logger.Service.Zap.Warnw("Duplicate Increase Balance",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"Sn", txnId,
					"Cent", cent,
				)
				return
			}

			if ok, action, actionKey, errCode, jsonErr := w.walletHost.increaseBalance(txnId, cent, 0, betAmt, winAmt); ok {
				logger.Service.Zap.Infow("Increase Balance",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"UUID", uuid,
					"Cent", cent,
				)

				if w.iHandler != nil && cent != 0{
					w.iHandler.IncreaseHandler(secWebSocketKey, uuid, w.walletHost.balance, cent, txnId)
				}

				w.walletHost.resultSn[txnId] = cent

				return
			} else {
				current_cent, _ := w.walletSharedMinor.selectCent()

				if current_cent > 0 {
					if w.walletSharedMinor.decreaseCent(current_cent) {
						logger.Service.Zap.Infow("Decrease Cent",
							"GameUser", secWebSocketKey,
							"Category", w.category,
							"UUID", uuid,
							"Cent", current_cent,
						)
					}
				}

				if action != kNon {
					w.walletHost.apiErrorLog(action, actionKey, errCode, jsonErr)
				}
			}

		}

		logger.Service.Zap.Errorw(Wallet_INCREASE_BALANCE_FAILED,
			"GameUser", secWebSocketKey,
			"Cent", cent,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_INCREASE_BALANCE_FAILED)
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

	if cent <= 0 {
		return false
	}

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		switch w.category {
		case CategoryGuest:
			if w.walletGuest.decreaseBalance(cent) {
				return true
			}

		case CategoryShared:
			if w.walletSharedMajor.decreaseBalance(cent) {
				logger.Service.Zap.Infow("Decrease Balance",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"UUID", uuid,
					"Cent", cent,
				)

				if w.iHandler != nil {
					w.iHandler.DecreaseHandler(secWebSocketKey, uuid, w.walletSharedMajor.balance, cent, 0)
				}
				return true
			}

		case CategoryPlayer:
			if w.walletPlayer.decreaseBalance(cent) {
				logger.Service.Zap.Infow("Decrease Balance",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"UUID", uuid,
					"Cent", cent,
				)

				if w.iHandler != nil {
					w.iHandler.DecreaseHandler(secWebSocketKey, uuid, w.walletPlayer.balance, cent, 0)
				}
				return true
			}

		case CategoryHost:
			var txnId uint64 = 0

			if w.iHandler != nil {
				txnId = w.iHandler.GetAccountingSnHandler(secWebSocketKey, w.walletHost.balance, cent, 0, false)
			}

			if _, ok := w.walletHost.betSn[txnId]; ok {
				logger.Service.Zap.Warnw("Duplicate Decrease Balance",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"Sn", txnId,
					"Cent", cent,
				)
				return false
			}

			if ok, action, actionKey, errCode, jsonErr := w.walletHost.decreaseBalance(txnId, cent); ok {
				logger.Service.Zap.Infow("Decrease Balance",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"UUID", uuid,
					"Cent", cent,
				)

				if w.iHandler != nil {
					w.iHandler.DecreaseHandler(secWebSocketKey, uuid, w.walletHost.balance, cent, txnId)
				}

				w.walletHost.betSn[txnId] = cent

				return true
			} else {
				if action != kNon {
					w.walletHost.apiErrorLog(action, actionKey, errCode, jsonErr)
				}
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
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		switch w.category {
		case CategoryGuest:
			return w.walletGuest.cent, nil

		case CategoryShared:
			return w.walletSharedMinor.cent, nil

		case CategoryPlayer:
			return w.walletSharedMinor.cent, nil

		case CategoryHost:
			return w.walletSharedMinor.cent, nil
		}
	}

	logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
		"GameUser", secWebSocketKey,
	)
	errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)

	return 0, errors.New(Wallet_NOT_FOUND)
}

func (s *service) Cent(secWebSocketKey string) (balance uint64, err error) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if w, ok := s.usersWallet[secWebSocketKey]; ok {

		switch w.category {
		case CategoryGuest:
			return w.walletGuest.cent, nil

		case CategoryShared:
			balance, _ := w.walletSharedMinor.selectCent()

			return balance, nil

		case CategoryPlayer:
			balance, _ := w.walletSharedMinor.selectCent()

			return balance, nil

		case CategoryHost:
			balance, _ := w.walletSharedMinor.selectCent()

			return balance, nil
		}

		logger.Service.Zap.Errorw(Wallet_CENT_INVALID,
			"GameUser", secWebSocketKey,
			"Category", w.category,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_CENT_INVALID)
	} else {
		logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
			"GameUser", secWebSocketKey,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
	}
	return 0, errors.New(Wallet_GET_CENT_FAILED)
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
			if w.walletGuest.increaseCent(cent) {
				return
			}

		case CategoryShared:
			if w.walletSharedMinor.increaseCent(cent) {
				logger.Service.Zap.Infow("Increase Cent",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"UUID", uuid,
					"Cent", cent,
				)

				if w.iHandler != nil {
					w.iHandler.IncreaseHandler(secWebSocketKey, uuid, w.walletSharedMinor.cent, cent, 0)
				}
				return
			}

		case CategoryPlayer:
			if w.walletSharedMinor.increaseCent(cent) {
				logger.Service.Zap.Infow("Increase Cent",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"UUID", uuid,
					"Cent", cent,
				)

				if w.iHandler != nil {
					w.iHandler.IncreaseHandler(secWebSocketKey, uuid, w.walletSharedMinor.cent, cent, 0)

				}
				return
			}

		case CategoryHost:
			if w.walletSharedMinor.increaseCent(cent) {
				logger.Service.Zap.Infow("Increase Cent",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"UUID", uuid,
					"Cent", cent,
				)

				if w.iHandler != nil {
					w.iHandler.IncreaseHandler(secWebSocketKey, uuid, w.walletSharedMinor.cent, cent, 0)

				}
				return
			}
		}

		logger.Service.Zap.Errorw(Wallet_INCREASE_CENT_FAILED,
			"GameUser", secWebSocketKey,
			"Cent", cent,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_INCREASE_CENT_FAILED)
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

	if cent <= 0 {
		return false
	}

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		switch w.category {
		case CategoryGuest:
			if w.walletGuest.decreaseCent(cent) {
				return true
			}

		case CategoryShared:
			if w.walletSharedMinor.decreaseCent(cent) {
				logger.Service.Zap.Infow("Decrease Cent",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"UUID", uuid,
					"Cent", cent,
				)

				if w.iHandler != nil {
					w.iHandler.DecreaseHandler(secWebSocketKey, uuid, w.walletSharedMinor.cent, cent, 0)
				}
				return true
			}

		case CategoryPlayer:
			if w.walletSharedMinor.decreaseCent(cent) {
				logger.Service.Zap.Infow("Decrease Cent",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"UUID", uuid,
					"Cent", cent,
				)

				if w.iHandler != nil {
					w.iHandler.DecreaseHandler(secWebSocketKey, uuid, w.walletSharedMinor.cent, cent, 0)
				}
				return true
			}

		case CategoryHost:
			if w.walletSharedMinor.decreaseCent(cent) {
				logger.Service.Zap.Infow("Decrease Cent",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"UUID", uuid,
					"Cent", cent,
				)

				if w.iHandler != nil {
					w.iHandler.DecreaseHandler(secWebSocketKey, uuid, w.walletSharedMinor.cent+w.walletHost.balance, cent, 0)
				}
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
			if err := w.walletGuest.deposit(cent); err != nil {
				logger.Service.Zap.Errorw(Wallet_DEPOSIT_BALANCE_FAILED,
					"GameUser", secWebSocketKey,
					"Balance", w.walletGuest.balance,
					"Cent", cent,
				)
				errorcode.Service.Fatal(secWebSocketKey, Wallet_DEPOSIT_BALANCE_FAILED)
			}
			return

		case CategoryShared:
			tx := w.walletSharedMajor.db.Begin()

			if err := w.walletSharedMajor.depositBegin(tx, cent); err != nil {
				logger.Service.Zap.Errorw(Wallet_DEPOSIT_BALANCE_FAILED,
					"GameUser", secWebSocketKey,
					"Balance", w.walletSharedMajor.balance,
					"Cent", cent,
				)
				errorcode.Service.Fatal(secWebSocketKey, Wallet_DEPOSIT_BALANCE_FAILED)
				return
			}

			if err := w.walletSharedMinor.depositCommit(tx, cent, 0); err != nil {
				logger.Service.Zap.Errorw(Wallet_DEPOSIT_CENT_FAILED,
					"GameUser", secWebSocketKey,
					"Balance", w.walletSharedMinor.cent,
					"Cent", cent,
				)
				errorcode.Service.Fatal(secWebSocketKey, Wallet_DEPOSIT_CENT_FAILED)
				return
			}

			tx.Commit()

			logger.Service.Zap.Infow("Deposit Balance",
				"GameUser", secWebSocketKey,
				"BalanceMain", w.walletSharedMajor.balance,
				"BalanceSub", w.walletSharedMinor.cent,
				"Cent", cent,
			)

			return

		case CategoryPlayer:
			tx := w.walletPlayer.db.Begin()

			if err := w.walletPlayer.depositBegin(tx, cent); err != nil {
				logger.Service.Zap.Errorw(Wallet_DEPOSIT_BALANCE_FAILED,
					"GameUser", secWebSocketKey,
					"Balance", w.walletPlayer.balance,
					"Cent", cent,
				)
				errorcode.Service.Fatal(secWebSocketKey, Wallet_DEPOSIT_BALANCE_FAILED)
				return
			}

			if err := w.walletSharedMinor.depositCommit(tx, cent, 0); err != nil {
				logger.Service.Zap.Errorw(Wallet_DEPOSIT_CENT_FAILED,
					"GameUser", secWebSocketKey,
					"Balance", w.walletSharedMinor.cent,
					"Cent", cent,
				)
				errorcode.Service.Fatal(secWebSocketKey, Wallet_DEPOSIT_CENT_FAILED)
				return
			}

			tx.Commit()

			logger.Service.Zap.Infow("Deposit Balance",
				"GameUser", secWebSocketKey,
				"BalanceMain", w.walletPlayer.balance,
				"BalanceSub", w.walletSharedMinor.cent,
				"Cent", cent,
			)

			return

		case CategoryHost:
			var txnId uint64 = 0
			if w.iHandler != nil {
				txnId = w.iHandler.GetAccountingSnHandler(secWebSocketKey, w.walletHost.balance, cent, accountingSn, true)
			}

			if _, ok := w.walletHost.betSn[txnId]; ok {
				logger.Service.Zap.Warnw("Duplicate Deposit",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"Sn", txnId,
					"Cent", cent,
				)
				return
			}

			tx := w.walletHost.db.Begin()

			if err := w.walletHost.depositBegin(tx, cent, txnId); err != nil {
				// Process Delete Accounting
				logger.Service.Zap.Infow("Delete Accounting Record",
					"GameUser", secWebSocketKey,
					"AccountingSn", txnId,
				)
				if w.iHandler != nil {
					w.iHandler.BetErrorHandler(secWebSocketKey, txnId)
				}

				logger.Service.Zap.Errorw(Wallet_DEPOSIT_BALANCE_FAILED,
					"GameUser", secWebSocketKey,
					"Balance", w.walletHost.balance,
					"Cent", cent,
				)
				errorcode.Service.Fatal(secWebSocketKey, Wallet_DEPOSIT_BALANCE_FAILED)
				return
			}

			if err := w.walletSharedMinor.depositCommit(tx, cent, txnId); err != nil {
				logger.Service.Zap.Errorw(Wallet_DEPOSIT_CENT_FAILED,
					"GameUser", secWebSocketKey,
					"Balance", w.walletSharedMinor.cent,
					"Cent", cent,
				)
				errorcode.Service.Fatal(secWebSocketKey, Wallet_DEPOSIT_CENT_FAILED)
				return
			}

			tx.Commit()

			w.walletHost.betSn[txnId] = cent

			logger.Service.Zap.Infow("Deposit Balance",
				"GameUser", secWebSocketKey,
				"BalanceMain", w.walletHost.balance,
				"BalanceSub", w.walletSharedMinor.cent,
				"Cent", cent,
			)

			return
		}

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
			if err := w.walletGuest.withdraw(cent); err != nil {
				logger.Service.Zap.Errorw(Wallet_WITHDRAW_BALANCE_FAILED,
					"GameUser", secWebSocketKey,
					"Balance", w.walletGuest.balance,
					"Cent", cent,
				)
				errorcode.Service.Fatal(secWebSocketKey, Wallet_WITHDRAW_BALANCE_FAILED)
				return
			}
			return

		case CategoryShared:
			tx := w.walletSharedMinor.db.Begin()

			if err := w.walletSharedMinor.withdrawBegin(tx, cent, 0); err != nil {
				logger.Service.Zap.Errorw(Wallet_WITHDRAW_CENT_FAILED,
					"GameUser", secWebSocketKey,
					"Balance", w.walletSharedMinor.cent,
					"Cent", cent,
				)
				errorcode.Service.Fatal(secWebSocketKey, Wallet_WITHDRAW_CENT_FAILED)
				return
			}

			if err := w.walletSharedMajor.withdrawCommit(tx, cent); err != nil {
				logger.Service.Zap.Errorw(Wallet_WITHDRAW_BALANCE_FAILED,
					"GameUser", secWebSocketKey,
					"Balance", w.walletSharedMajor.balance,
					"Cent", cent,
				)
				errorcode.Service.Fatal(secWebSocketKey, Wallet_WITHDRAW_BALANCE_FAILED)
				return
			}

			tx.Commit()

			logger.Service.Zap.Infow("Withdraw Balance",
				"GameUser", secWebSocketKey,
				"BalanceMain", w.walletSharedMajor.balance,
				"BalanceSub", w.walletSharedMinor.cent,
				"Cent", cent,
			)

			return

		case CategoryPlayer:
			tx := w.walletSharedMinor.db.Begin()

			if err := w.walletSharedMinor.withdrawBegin(tx, cent, 0); err != nil {
				logger.Service.Zap.Errorw(Wallet_WITHDRAW_CENT_FAILED,
					"GameUser", secWebSocketKey,
					"Balance", w.walletSharedMinor.cent,
					"Cent", cent,
				)
				errorcode.Service.Fatal(secWebSocketKey, Wallet_WITHDRAW_CENT_FAILED)
				return
			}

			if err := w.walletPlayer.withdrawCommit(tx, cent); err != nil {
				logger.Service.Zap.Errorw(Wallet_WITHDRAW_BALANCE_FAILED,
					"GameUser", secWebSocketKey,
					"Balance", w.walletPlayer.balance,
					"Cent", cent,
				)
				errorcode.Service.Fatal(secWebSocketKey, Wallet_WITHDRAW_BALANCE_FAILED)
				return
			}

			tx.Commit()

			logger.Service.Zap.Infow("Withdraw Balance",
				"GameUser", secWebSocketKey,
				"BalanceMain", w.walletPlayer.balance,
				"BalanceSub", w.walletSharedMinor.cent,
				"Cent", cent,
			)
			return

		case CategoryHost:
			var txnId uint64 = 0
			if w.iHandler != nil {
				if sn == 0 {
					txnId = w.iHandler.GetAccountingSnHandler(secWebSocketKey, w.walletHost.balance, cent, 0, false)
				} else {
					txnId = sn
				}
			}

			if _, ok := w.walletHost.resultSn[txnId]; ok {
				logger.Service.Zap.Warnw("Duplicate WithDraw",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"Sn", txnId,
					"Cent", cent,
				)
				return
			}

			tx := w.walletSharedMinor.db.Begin()

			if err := w.walletSharedMinor.withdrawBegin(tx, cent, txnId); err != nil {
				logger.Service.Zap.Errorw(Wallet_WITHDRAW_CENT_FAILED,
					"GameUser", secWebSocketKey,
					"Balance", w.walletSharedMinor.cent,
					"Cent", cent,
				)
				errorcode.Service.Fatal(secWebSocketKey, Wallet_WITHDRAW_CENT_FAILED)
				return
			}

			if err := w.walletHost.withdrawCommit(tx, cent, txnId, betAmt, winAmt); err != nil {
				logger.Service.Zap.Errorw(Wallet_WITHDRAW_BALANCE_FAILED,
					"GameUser", secWebSocketKey,
					"Balance", w.walletHost.balance,
					"Cent", cent,
				)
				errorcode.Service.Fatal(secWebSocketKey, Wallet_WITHDRAW_BALANCE_FAILED)
				return
			}

			tx.Commit()

			w.walletHost.resultSn[txnId] = cent

			logger.Service.Zap.Infow("Withdraw Balance",
				"GameUser", secWebSocketKey,
				"BalanceMain", w.walletHost.balance,
				"BalanceSub", w.walletSharedMinor.cent,
				"Cent", cent,
			)
			return
		}
	}

	logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
		"GameUser", secWebSocketKey,
		"Cent", cent,
	)
	errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
}

func (s *service) Refund(secWebSocketKey string, txnId uint64, doDecreaseCent bool) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		switch w.category {
		case CategoryGuest:
		case CategoryShared:
		case CategoryPlayer:
		case CategoryHost:
			tx := w.walletSharedMinor.db.Begin()
			cent := w.walletSharedMinor.cent

			if doDecreaseCent {
				if err := w.walletSharedMinor.refundBegin(tx, cent, txnId); err != nil {
					logger.Service.Zap.Errorw(err.Error(),
						"GameUser", secWebSocketKey,
						"Balance", w.walletSharedMinor.cent,
						"Cent", cent,
					)
					errorcode.Service.Fatal(secWebSocketKey, Wallet_REFUND_CENT_FAILED)
					return
				}
			}

			if err := w.walletHost.refundCommit(tx, cent, txnId); err != nil {
				logger.Service.Zap.Errorw(err.Error(),
					"GameUser", secWebSocketKey,
					"Balance", w.walletHost.balance,
					"Cent", cent,
				)
				errorcode.Service.Fatal(secWebSocketKey, Wallet_REFUND_BALANCE_FAILED)
				return
			}

			tx.Commit()

			logger.Service.Zap.Infow("Refund Balance",
				"GameUser", secWebSocketKey,
				"BalanceMain", w.walletHost.balance,
				"BalanceSub", w.walletSharedMinor.cent,
				"DoDecreaseCent", doDecreaseCent,
				"RefendCent", cent,
			)
			return
		}
	}

	logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
		"GameUser", secWebSocketKey,
		"TxnId", txnId,
	)
	errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
}

func (s *service) EndAccounting(secWebSocketKey string, bet, sn uint64, checkAccountingEnd bool) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		switch w.category {
		case CategoryHost:
			cent := w.walletSharedMinor.cent

			if cent <= 0 || cent < bet {
				if w.iHandler != nil {
					w.iHandler.EndAccountingHandler(secWebSocketKey, checkAccountingEnd, w.category, cent, sn)
				}
			}

		}
	}
}

func (s *service) UpdateCent(secWebSocketKey, gameId string, cent uint64) bool {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		switch w.category {
		case CategoryHost:
			if w.walletSharedMinor.updateCent(cent, gameId) {
				logger.Service.Zap.Infow("Reset Cent",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"Cent", cent,
				)

				return true
			}
		}
	}

	logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
		"GameUser", secWebSocketKey,
		"Cent", cent,
	)
	errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)

	return false
}

func (s *service) CentCacheV2(secWebSocketKey string) (balance uint64, err error) {
	s.rwMutex.Lock()

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		switch w.category {
		case CategoryHost:
			return w.walletSharedMinor.cent, nil
		}
	}

	logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
		"GameUser", secWebSocketKey,
	)
	errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)

	return 0, errors.New(Wallet_NOT_FOUND)
}

func (s *service) WithdrawV2(secWebSocketKey string, sn, cent, betAmt, winAmt uint64) {
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
		case CategoryHost:
			var txnId uint64 = 0
			if w.iHandler != nil {
				if sn == 0 {
					txnId = w.iHandler.GetAccountingSnHandler(secWebSocketKey, w.walletHost.balance, cent, 0, false)
				} else {
					txnId = sn
				}
			}

			if _, ok := w.walletHost.resultSn[txnId]; ok {
				logger.Service.Zap.Warnw("Duplicate WithDraw",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"Sn", txnId,
					"Cent", cent,
				)
				return
			}

			tx := w.walletSharedMinor.db.Begin()

			if err := w.walletSharedMinor.withdrawBegin(tx, cent, txnId); err != nil {
				logger.Service.Zap.Errorw(Wallet_WITHDRAW_CENT_FAILED,
					"GameUser", secWebSocketKey,
					"Balance", w.walletSharedMinor.cent,
					"Cent", cent,
				)
				errorcode.Service.Fatal(secWebSocketKey, Wallet_WITHDRAW_CENT_FAILED)
				return
			}

			if err := w.walletHost.withdrawCommit(tx, cent, txnId, betAmt, winAmt); err != nil {
				logger.Service.Zap.Errorw(Wallet_WITHDRAW_BALANCE_FAILED,
					"GameUser", secWebSocketKey,
					"Balance", w.walletHost.balance,
					"Cent", cent,
				)
				errorcode.Service.Fatal(secWebSocketKey, Wallet_WITHDRAW_BALANCE_FAILED)
				return
			}

			tx.Commit()

			w.walletHost.resultSn[txnId] = cent

			logger.Service.Zap.Infow("Withdraw Balance",
				"GameUser", secWebSocketKey,
				"BalanceMain", w.walletHost.balance,
				"BalanceSub", w.walletSharedMinor.cent,
				"Cent", cent,
			)
			return
		}
	}

	logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
		"GameUser", secWebSocketKey,
		"Cent", cent,
	)
	errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
}

func (s *service) CentV2(secWebSocketKey string) (balance uint64, err error) {
	s.rwMutex.Lock()

	if w, ok := s.usersWallet[secWebSocketKey]; ok {

		switch w.category {
		case CategoryHost:
			balance, _ := w.walletSharedMinor.selectCent()

			return balance, nil
		}

		logger.Service.Zap.Errorw(Wallet_CENT_INVALID,
			"GameUser", secWebSocketKey,
			"Category", w.category,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_CENT_INVALID)
	} else {
		logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
			"GameUser", secWebSocketKey,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
	}
	return 0, errors.New(Wallet_GET_CENT_FAILED)
}

func (s *service) IncreaseBalanceV2(secWebSocketKey, uuid string, cent, betAmt, winAmt uint64) {
	defer s.rwMutex.Unlock()

	if w, ok := s.usersWallet[secWebSocketKey]; ok {
		switch w.category {
		case CategoryHost:
			var txnId uint64 = 0

			if w.iHandler != nil {
				txnId = w.iHandler.GetAccountingSnHandler(secWebSocketKey, w.walletHost.balance, cent, 0, false)
			}

			if _, ok := w.walletHost.resultSn[txnId]; ok {
				logger.Service.Zap.Warnw("Duplicate Increase Balance",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"Sn", txnId,
					"Cent", cent,
				)
				return
			}

			if ok, action, actionKey, errCode, jsonErr := w.walletHost.increaseBalance(txnId, cent, 0, betAmt, winAmt); ok {
				logger.Service.Zap.Infow("Increase Balance",
					"GameUser", secWebSocketKey,
					"Category", w.category,
					"UUID", uuid,
					"Cent", cent,
				)

				if w.iHandler != nil && cent != 0{
					w.iHandler.IncreaseHandler(secWebSocketKey, uuid, w.walletHost.balance, cent, txnId)
				}

				w.walletHost.resultSn[txnId] = cent

				return
			} else {
				current_cent, _ := w.walletSharedMinor.selectCent()

				if current_cent > 0 {
					if w.walletSharedMinor.decreaseCent(current_cent) {
						logger.Service.Zap.Infow("Decrease Cent",
							"GameUser", secWebSocketKey,
							"Category", w.category,
							"UUID", uuid,
							"Cent", current_cent,
						)
					}
				}

				if action != kNon {
					w.walletHost.apiErrorLog(action, actionKey, errCode, jsonErr)
				}
			}

		}

		logger.Service.Zap.Errorw(Wallet_INCREASE_BALANCE_FAILED,
			"GameUser", secWebSocketKey,
			"Cent", cent,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_INCREASE_BALANCE_FAILED)
		return
	}

	logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
		"GameUser", secWebSocketKey,
		"Cent", cent,
	)
	errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
}