package atm

import (
	atm_proto "89-game-server/application/atm/proto"
	"89-game-server/application/gamesetting89"
	"89-game-server/domain/bet"
	common89_proto "89-game-server/models/proto"
	"math"
	"os"
	"strconv"
	"sync"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/common"
	common_proto "gitlab.iplaystar.net/game-server/common/proto"
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
	sessionmanager "gitlab.iplaystar.net/game-server/session-manager"
	"gitlab.iplaystar.net/game-server/wallet"
)

const (
	EMSGID_eDepositCall           = "EMSGID_eDepositCall"
	EMSGID_eDepositRecall         = "EMSGID_eDepositRecall"
	EMSGID_eWithdrawCall          = "EMSGID_eWithdrawCall"
	EMSGID_eWithdrawRecall        = "EMSGID_eWithdrawRecall"
	EMSGID_eInquireCall           = "EMSGID_eInquireCall"
	EMSGID_eInquireRecall         = "EMSGID_eInquireRecall"
	EMSGID_eAutoTransferCall      = "EMSGID_eAutoTransferCall"
	EMSGID_eAutoTransferRecall    = "EMSGID_eAutoTransferRecall"
	EMSGID_eAutoTransferOutCall   = "EMSGID_eAutoTransferOutCall"
	EMSGID_eAutoTransferOutRecall = "EMSGID_eAutoTransferOutRecall"

	ActionAtmStart              = "ActionAtmStart"
	ActionAtmDelete             = "ActionAtmDelete"
	ActionAtmAutoDeposit        = "ActionAtmAutoDeposit"
	ActionAtmAutoWithdraw       = "ActionAtmAutoWithdraw"
	ActionAtmAutoWithdrawBlance = "ActionAtmAutoWithdrawBlance"
)

var Service = &service{
	Id:       "AtmService",
	poolSize: os.Getenv("POOL_SIZE"),
	in:       make(chan *flux.Action, common.Service.ChanSize),
	rwMutex:  &sync.RWMutex{},
}

type service struct {
	Id       string
	poolSize string
	in       chan *flux.Action
	rwMutex  *sync.RWMutex
}

func init() {
	Service.run()
}

func (s *service) run() {
	flux.Register(s.Id, s.in)

	atms := make(map[string]*atm)

	poolSize := 10

	if s.poolSize != "" {
		if poolSize, _ = strconv.Atoi(s.poolSize); poolSize == 0 {
			poolSize = 10
		}
	}

	for i := 0; i < poolSize; i++ {
		go func() {
			for action := range s.in {
				s.handleAction(action, atms)
			}
		}()
	}
}

func (s *service) handleAction(action *flux.Action, allAtms map[string]*atm) {

	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	switch action.Key().Name() {
	case ActionAtmStart:
		secWebSocketKey := action.Key().From()
		hostExtId := action.Payload()[0].(string)
		memberId := action.Payload()[1].(string)

		if v, ok := allAtms[s.hashId(hostExtId, memberId)]; ok {
			v.secWebSocketKey = secWebSocketKey
			return
		}

		allAtms[s.hashId(hostExtId, memberId)] = Builder().
			setSecWebSocketKey(secWebSocketKey).
			setHostExtId(hostExtId).
			setMemberId(memberId).
			build()

	case ActionAtmDelete:
		secWebSocketKey := action.Key().From()
		hostExtId := action.Payload()[0].(string)
		memberId := action.Payload()[1].(string)

		if v, ok := allAtms[s.hashId(hostExtId, memberId)]; ok && v.secWebSocketKey == secWebSocketKey {
			delete(allAtms, s.hashId(hostExtId, memberId))
		}

	case ActionAtmAutoDeposit:
		//secWebSocketKey := action.Key().From()

		hostExtId := action.Payload()[1].(string)
		memberId := action.Payload()[2].(string)

		if v, ok := allAtms[s.hashId(hostExtId, memberId)]; ok && !v.lock() {
			percent := action.Payload()[0].(uint8)

			//go v.run()

			s.autoDeposit(v, percent)
		}

	case ActionAtmAutoWithdraw:
		secWebSocketKey := action.Key().From()

		hostExtId := action.Payload()[1].(string)
		memberId := action.Payload()[2].(string)

		if v, ok := allAtms[s.hashId(hostExtId, memberId)]; ok && !v.lock() && v.secWebSocketKey == secWebSocketKey {
			percent := action.Payload()[0].(uint8)
			//go v.run()
			s.autoWithdraw(v, percent)
		}
	case ActionAtmAutoWithdrawBlance:

		hostExtId := action.Payload()[1].(string)
		memberId := action.Payload()[2].(string)

		if v, ok := allAtms[s.hashId(hostExtId, memberId)]; ok && !v.lock() {
			betcent := action.Payload()[0].(uint64)
			s.autoWithdrawBlance(v, betcent*5)
		}

	case EMSGID_eDepositCall:
		//secWebSocketKey := action.Key().From()
		hostExtId := action.Payload()[1].(string)
		memberId := action.Payload()[2].(string)

		if v, ok := allAtms[s.hashId(hostExtId, memberId)]; ok && !v.lock() {
			msg := action.Payload()[0].([]byte)

			//go v.run()

			s.EMSGID_eDepositCall(v, msg)
		}

	case EMSGID_eWithdrawCall:
		//secWebSocketKey := action.Key().From()
		hostExtId := action.Payload()[1].(string)
		memberId := action.Payload()[2].(string)

		if v, ok := allAtms[s.hashId(hostExtId, memberId)]; ok && !v.lock() {
			msg := action.Payload()[0].([]byte)

			//go v.run()

			s.EMSGID_eWithdrawCall(v, msg)
		}

	case EMSGID_eInquireCall:
		//secWebSocketKey := action.Key().From()
		hostExtId := action.Payload()[1].(string)
		memberId := action.Payload()[2].(string)

		if v, ok := allAtms[s.hashId(hostExtId, memberId)]; ok && !v.lock() {
			msg := action.Payload()[0].([]byte)

			//go v.run()

			s.EMSGID_eInquireCall(v, msg)
		}

	case EMSGID_eAutoTransferCall:
		//secWebSocketKey := action.Key().From()
		hostExtId := action.Payload()[1].(string)
		memberId := action.Payload()[2].(string)

		if v, ok := allAtms[s.hashId(hostExtId, memberId)]; ok && !v.lock() {
			msg := action.Payload()[0].([]byte)

			//go v.run()

			s.EMSGID_eAutoTransferCall(v, msg)
		}
	case EMSGID_eAutoTransferOutCall:
		//secWebSocketKey := action.Key().From()
		hostExtId := action.Payload()[1].(string)
		memberId := action.Payload()[2].(string)

		if v, ok := allAtms[s.hashId(hostExtId, memberId)]; ok && !v.lock() {
			msg := action.Payload()[0].([]byte)

			//go v.run()

			s.EMSGID_eAutoTransferOutCall(v, msg)
		}
	case sessionmanager.SessionManager_DUPICATE_SESSION:
		// In this case, we don't need exec ActionAtmAutoWithdraw when disconnected.
		secWebSocketKey := action.Key().From()
		hostExtId := action.Payload()[0].(string)
		memberId := action.Payload()[1].(string)

		if v, ok := allAtms[s.hashId(hostExtId, memberId)]; ok && v.secWebSocketKey == secWebSocketKey {
			delete(allAtms, s.hashId(hostExtId, memberId))
		}
	}
}

func (s *service) EMSGID_eDepositCall(a *atm, msg []byte) {
	data := &atm_proto.DepositCall{}

	if err := proto.Unmarshal(msg, data); err != nil {
		logger.Service.Zap.Errorw(Atm_DEPOSIT_CALL_PROTO_INVALID,
			"GameUser", a.secWebSocketKey,
		)
		errorcode.Service.Fatal(a.secWebSocketKey, Atm_DEPOSIT_CALL_PROTO_INVALID)
		return
	}

	balance, err := wallet.Service.Balance(a.secWebSocketKey)

	if err != nil {
		logger.Service.Zap.Errorw(Atm_GET_BALANCE_FAILED,
			"GameUser", a.secWebSocketKey,
			"Error", err,
		)
		errorcode.Service.Fatal(a.secWebSocketKey, Atm_GET_BALANCE_FAILED)
		return
	}

	if data.Cent <= balance {
		wallet.Service.Deposit(a.secWebSocketKey, data.Cent)
	}

	flux.Send(EMSGID_eDepositRecall, s.Id, a.secWebSocketKey, s.EMSGID_eDepositRecall(a))
}

func (s *service) EMSGID_eDepositRecall(a *atm) []byte {
	data := &atm_proto.DepositRecall{
		Msgid:      common89_proto.EMSGID_eDepositRecall,
		StatusCode: common_proto.Status_kSuccess,
	}

	balance, err := wallet.Service.Balance(a.secWebSocketKey)

	if err != nil {
		data.StatusCode = common_proto.Status_kInvalid

		logger.Service.Zap.Errorw(Atm_GET_BALANCE_FAILED,
			"GameUser", a.secWebSocketKey,
			"Error", err,
		)
		errorcode.Service.Fatal(a.secWebSocketKey, Atm_GET_BALANCE_FAILED)
	} else {
		data.Balance = balance
	}

	cent, err := wallet.Service.Cent(a.secWebSocketKey)

	if err != nil {
		data.StatusCode = common_proto.Status_kInvalid

		logger.Service.Zap.Errorw(Atm_GET_CENT_FAILED,
			"GameUser", a.secWebSocketKey,
			"Error", err,
		)
		errorcode.Service.Fatal(a.secWebSocketKey, Atm_GET_CENT_FAILED)
	} else {
		data.Cent = cent
	}

	dataByte, _ := proto.Marshal(data)
	return dataByte
}

func (s *service) EMSGID_eWithdrawCall(a *atm, msg []byte) {
	data := &atm_proto.WithdrawCall{}

	if err := proto.Unmarshal(msg, data); err != nil {
		logger.Service.Zap.Errorw(Atm_WITHDRAW_CALL_PROTO_INVALID,
			"GameUser", a.secWebSocketKey,
		)
		errorcode.Service.Fatal(a.secWebSocketKey, Atm_WITHDRAW_CALL_PROTO_INVALID)
		return
	}

	wallet.Service.Withdraw(a.secWebSocketKey, data.Cent)

	if dataByte := s.EMSGID_eWithdrawRecall(a); dataByte != nil {
		flux.Send(EMSGID_eWithdrawRecall, s.Id, a.secWebSocketKey, dataByte)
	}
}

func (s *service) EMSGID_eWithdrawRecall(a *atm) []byte {
	data := &atm_proto.WithdrawRecall{
		Msgid:      common89_proto.EMSGID_eWithdrawRecall,
		StatusCode: common_proto.Status_kSuccess,
	}

	balance, err := wallet.Service.Balance(a.secWebSocketKey)

	if err != nil {
		data.StatusCode = common_proto.Status_kInvalid

		logger.Service.Zap.Errorw(Atm_GET_BALANCE_FAILED,
			"GameUser", a.secWebSocketKey,
			"Error", err,
		)
		errorcode.Service.Fatal(a.secWebSocketKey, Atm_GET_BALANCE_FAILED)
	} else {
		data.Balance = balance
	}

	cent, err := wallet.Service.Cent(a.secWebSocketKey)

	if err != nil {
		data.StatusCode = common_proto.Status_kInvalid

		logger.Service.Zap.Errorw(Atm_GET_CENT_FAILED,
			"GameUser", a.secWebSocketKey,
			"Error", err,
		)
		errorcode.Service.Fatal(a.secWebSocketKey, Atm_GET_CENT_FAILED)
	} else {
		data.Cent = cent
	}

	dataByte, _ := proto.Marshal(data)
	return dataByte
}

func (s *service) EMSGID_eInquireCall(a *atm, msg []byte) {

	data := &atm_proto.InquireCall{}

	if err := proto.Unmarshal(msg, data); err != nil {
		logger.Service.Zap.Errorw(Atm_INQUIRE_CALL_PROTO_INVALID,
			"GameUser", a.secWebSocketKey,
		)
		errorcode.Service.Fatal(a.secWebSocketKey, Atm_INQUIRE_CALL_PROTO_INVALID)
		return
	}

	if dataByte := s.EMSGID_eInquireRecall(a); dataByte != nil {
		flux.Send(EMSGID_eInquireRecall, s.Id, a.secWebSocketKey, dataByte)
	}
}

func (s *service) EMSGID_eInquireRecall(a *atm) []byte {
	data := &atm_proto.InquireRecall{
		Msgid:      common89_proto.EMSGID_eInquireRecall,
		StatusCode: common_proto.Status_kSuccess,
	}

	balance, err := wallet.Service.Balance(a.secWebSocketKey)

	if err != nil {
		data.StatusCode = common_proto.Status_kInvalid

		logger.Service.Zap.Errorw(Atm_GET_BALANCE_FAILED,
			"GameUser", a.secWebSocketKey,
			"Error", err,
		)
		errorcode.Service.Fatal(a.secWebSocketKey, Atm_GET_BALANCE_FAILED)
	} else {
		data.Balance = balance
	}

	cent, err := wallet.Service.Cent(a.secWebSocketKey)

	if err != nil {
		data.StatusCode = common_proto.Status_kInvalid

		logger.Service.Zap.Errorw(Atm_GET_CENT_FAILED,
			"GameUser", a.secWebSocketKey,
			"Error", err,
		)
		errorcode.Service.Fatal(a.secWebSocketKey, Atm_GET_CENT_FAILED)
	} else {
		data.Cent = cent
	}

	dataByte, _ := proto.Marshal(data)
	return dataByte
}

func (s *service) EMSGID_eAutoTransferCall(a *atm, msg []byte) {
	data := &atm_proto.AutoTransferCall{}

	if err := proto.Unmarshal(msg, data); err != nil {
		logger.Service.Zap.Errorw(Atm_AUTO_TRANSFER_CALL_PROTO_INVALID,
			"GameUser", a.secWebSocketKey,
		)
		errorcode.Service.Fatal(a.secWebSocketKey, Atm_AUTO_TRANSFER_CALL_PROTO_INVALID)
		return
	}

	// TODO JOHNNY 檢查 TOKEN

	s.EMSGID_eAutoTransferRecall(a, s.autoDeposit(a, 100))
}

func (s *service) EMSGID_eAutoTransferRecall(a *atm, isOk bool) {
	inq := &atm_proto.InquireRecall{}

	proto.Unmarshal(s.EMSGID_eInquireRecall(a), inq)

	data := &atm_proto.AutoTransferRecall{
		Msgid:      common89_proto.EMSGID_eAutoTransferRecall,
		StatusCode: common_proto.Status_kSuccess,
		Cent:       inq.Cent,
		Balance:    inq.Balance,
	}

	if !isOk {
		data.StatusCode = common_proto.Status_kNoEnoughCredit
	}

	dataByte, _ := proto.Marshal(data)
	flux.Send(EMSGID_eAutoTransferRecall, s.Id, a.secWebSocketKey, dataByte)
}
func (s *service) EMSGID_eAutoTransferOutCall(a *atm, msg []byte) {
	data := &atm_proto.AutoTransferOutCall{}

	if err := proto.Unmarshal(msg, data); err != nil {
		logger.Service.Zap.Errorw(Atm_AUTO_TRANSFER_CALL_PROTO_INVALID,
			"GameUser", a.secWebSocketKey,
		)
		errorcode.Service.Fatal(a.secWebSocketKey, Atm_AUTO_TRANSFER_CALL_PROTO_INVALID)
		return
	}

	// TODO JOHNNY 檢查 TOKEN

	s.EMSGID_eAutoTransferOutRecall(a, s.autoWithdraw(a, 100))
}

func (s *service) EMSGID_eAutoTransferOutRecall(a *atm, isOk bool) {
	inq := &atm_proto.InquireRecall{}

	proto.Unmarshal(s.EMSGID_eInquireRecall(a), inq)

	data := &atm_proto.AutoTransferOutRecall{
		Msgid:      common89_proto.EMSGID_eAutoTransferOutRecall,
		StatusCode: common_proto.Status_kSuccess,
		Cent:       inq.Cent,
		Balance:    inq.Balance,
	}

	if !isOk {
		data.StatusCode = common_proto.Status_kNoEnoughCredit
	}

	dataByte, _ := proto.Marshal(data)
	flux.Send(EMSGID_eAutoTransferOutRecall, s.Id, a.secWebSocketKey, dataByte)
}
func (s *service) autoDeposit(a *atm, percent uint8) bool {
	balance, err := wallet.Service.Balance(a.secWebSocketKey)

	if err != nil {
		logger.Service.Zap.Errorw(Atm_GET_BALANCE_FAILED,
			"GameUser", a.secWebSocketKey,
			"Error", err,
		)
		errorcode.Service.Fatal(a.secWebSocketKey, Atm_GET_BALANCE_FAILED)
		return false
	}

	if balance <= 0 {
		return false
	}

	wallet.Service.Deposit(a.secWebSocketKey, uint64(math.Round(float64(balance*uint64(percent)/100))))

	return true
}

func (s *service) autoWithdraw(a *atm, percent uint8) bool {
	cent, err := wallet.Service.Cent(a.secWebSocketKey)

	if err != nil {
		logger.Service.Zap.Errorw(Atm_GET_CENT_FAILED,
			"GameUser", a.secWebSocketKey,
			"Error", err,
		)
		errorcode.Service.Fatal(a.secWebSocketKey, Atm_GET_CENT_FAILED)
		return false
	}

	if cent <= 0 {
		logger.Service.Zap.Errorw(Atm_GET_CENT_FAILED,
			"GameUser", a.secWebSocketKey,
			"Error", err,
		)
		return false
	}
	wallet.Service.Withdraw(a.secWebSocketKey, uint64(math.Round(float64(cent*uint64(percent)/100))))

	return true
}
func (s *service) autoWithdrawBlance(a *atm, betBlance uint64) bool {
	cent, err := wallet.Service.Cent(a.secWebSocketKey)

	if err != nil {
		logger.Service.Zap.Errorw(Atm_GET_CENT_FAILED,
			"GameUser", a.secWebSocketKey,
			"Error", err,
		)
		errorcode.Service.Fatal(a.secWebSocketKey, Atm_GET_CENT_FAILED)
		return false
	}

	if cent <= 0 || cent == betBlance {
		return false
	}
	if cent < betBlance {
		logger.Service.Zap.Warnw(gamesetting89.GameSetting89_NOT_ENOUGH_BALANCE,
			"GameUser", a.secWebSocketKey,
			"MemberId", a.memberId,
			"Cent", cent,
		)
		errorcode.Service.Fatal(a.secWebSocketKey, bet.Bet_CENT_NOT_ENOUGHT)
		return false
	}
	blanceCent := cent - betBlance

	wallet.Service.Withdraw(a.secWebSocketKey, blanceCent)

	return true
}
func (s *service) hashId(hostExtId, memberId string) string {
	return hostExtId + memberId
}

func (s *service) Destroy() {
	flux.UnRegister(s.Id, s.in)
}
