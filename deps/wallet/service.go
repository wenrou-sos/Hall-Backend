package wallet

import (
	sync "github.com/sasha-s/go-deadlock"
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	"gitlab.iplaystar.net/game-server/logger"
)

const (
	ActionWalletOpened    = "ActionWalletOpened"
	GuestOn               = 1
	GuestOff              = 0
	AccountingTypeLocked  = 0
	AccountingTypeRegular = 1
	AccountingTypeTest    = 2
	AccountingTypeVip     = 3
)

var Service = &service{
	id:          "WalletService",
	usersWallet: make(map[string]*wallet),
	rwMutex:     &sync.RWMutex{},
}

type service struct {
	id          string
	usersWallet map[string]*wallet
	rwMutex     *sync.RWMutex
}

func (s *service) Existed(secWebSocketKey string) bool {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if _, ok := s.usersWallet[secWebSocketKey]; ok {
		return true
	} else {
		return false
	}
}

func (s *service) Close(secWebSocketKey string) {
	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	delete(s.usersWallet, secWebSocketKey)
}

func (s *service) MemberId(secWebSocketKey string) (memberId string) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.usersWallet[secWebSocketKey]; ok {
		return v.memberId
	} else {
		logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
			"GameUser", secWebSocketKey,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
		return ""
	}
}

func (s *service) MemberName(secWebSocketKey string) (memberName string) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.usersWallet[secWebSocketKey]; ok {
		return v.memberName
	} else {
		logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
			"GameUser", secWebSocketKey,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
		return ""
	}
}

func (s *service) Guest(secWebSocketKey string) (isGuest bool) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.usersWallet[secWebSocketKey]; ok {
		return v.isGuest
	} else {
		logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
			"GameUser", secWebSocketKey,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
		return true
	}
}

func (s *service) AccountingType(secWebSocketKey string) uint8 {
	if v, ok := s.usersWallet[secWebSocketKey]; ok {
		return v.accType
	} else {
		logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
			"GameUser", secWebSocketKey,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
		return AccountingTypeTest
	}
}

func (s *service) WalletCategory(secWebSocketKey string) int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.usersWallet[secWebSocketKey]; ok {
		return v.category
	} else {
		logger.Service.Zap.Errorw(Wallet_NOT_FOUND,
			"GameUser", secWebSocketKey,
		)
		errorcode.Service.Fatal(secWebSocketKey, Wallet_NOT_FOUND)
		return -1
	}
}
