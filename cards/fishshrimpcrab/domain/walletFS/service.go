package walletFS

import (
	"gitlab.iplaystar.net/game-server/common"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/wallet"
	"strconv"
)

const (
	ActionWalletClosed          = "ActionWalletClosed"
	EMSGID_eWalletBalanceCall   = "EMSGID_eWalletBalanceCall"
	EMSGID_eWalletBalanceRecall = "EMSGID_eWalletBalanceRecall"
)

var Service = &service{
	Id: "WalletFSService",
	in: make(chan *flux.Action, common.Service.ChanSize),
}

type service struct {
	Id string
	in chan *flux.Action
}

func init() {
	go Service.run()
}

func (s *service) run() {
	flux.Register(s.Id, s.in)

	for action := range s.in {
		s.handleAction(action)
	}
}

func (s *service) handleAction(action *flux.Action) {
	if action.Key().To() != s.Id {
		return
	}

	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:
		// do nothing

	case wallet.ActionWalletOpened:
		secWebSocketKey := string(action.Payload()[0].([]byte))

		if wallet.Service.Existed(secWebSocketKey) {
			return
		}

		hostId := string(action.Payload()[1].([]byte))
		hostExtId := string(action.Payload()[2].([]byte))
		memberId := string(action.Payload()[3].([]byte))
		memberName := string(action.Payload()[4].([]byte))

		balance, _ := strconv.ParseUint(string(action.Payload()[5].([]byte)), 10, 64)
		category, _ := strconv.ParseInt(string(action.Payload()[6].([]byte)), 10, 64)
		purposeMajor, _ := strconv.ParseInt(string(action.Payload()[7].([]byte)), 10, 64)
		purposeMinor, _ := strconv.ParseInt(string(action.Payload()[8].([]byte)), 10, 64)
		guestEnable, _ := strconv.ParseInt(string(action.Payload()[9].([]byte)), 10, 64)

		wallet.Service.Open(
			wallet.Builder().
				SetSecWebSocketKey(secWebSocketKey).
				SetHostId(hostId).
				SetHostExtId(hostExtId).
				SetMemberId(memberId).
				SetMemberName(memberName).
				SetBalance(balance).
				SetCategory(int(category)).
				SetPurposeMajor(int(purposeMajor)).
				SetPurposeMinor(int(purposeMinor)).
				SetGuest(int(guestEnable)).
				SetDB(hostExtId).
				Build(),
		)

	case ActionWalletClosed:
		secWebSocketKey := string(action.Payload()[0].([]byte))

		wallet.Service.Close(secWebSocketKey)
	}
}

func (s *service) destroy() {
	flux.UnRegister(s.Id, s.in)
}
