package wallet

import (
	"encoding/json"
	"errors"
	"fmt"
	macaddress "gitlab.iplaystar.net/game-server/mac-address"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/jinzhu/gorm"
	"gitlab.iplaystar.net/game-server/http"
	"gitlab.iplaystar.net/game-server/logger"
)

const (
	kNon		  = 999
	kAuthenticate = 0
	kBet          = 1
	kResult       = 2
	kRefundBet    = 3
	kBonusAward   = 4
	kLogout       = 5
	kGetBalance   = 6
	CallApiBefore = "Call API Before"
	CallApiAfter  = "Call API After"
)

type walletHost struct {
	secWebSocketKey string
	memberId        string
	hostId          string
	hostExtId       string
	gameId          string
	subGameId       int
	category        int
	balance         uint64
	accType         uint8 // 0:locked 1:regular 2:test 3:vip
	token           string
	db              *gorm.DB
	apiInfo         *ApiInfo
	purpose         int
	betSn           map[uint64]uint64
	resultSn        map[uint64]uint64
}

type hostId struct {
	HostId       string
	WalletType   int
	ApiInfo      string
	GuestEnable  int
	GuestBalance uint64
	Status       int
}

type ApiInfo struct {
	BaseUrl       string `json:"base_url"`
	Auth          string `json:"auth"`
	Logout        string `json:"logout"`
	Bet           string `json:"bet"`
	Result        string `json:"result"`
	RefundBet     string `json:"refundbet"`
	BonusAward    string `json:"bonusaward"`
	ResultEx      string `json:"resultex"`
	GetBalance    string `json:"getbalance"`
	EnableHttpLog bool   `json:"enable_http_log"`
	RetryTimes    int    `json:"retry_times"`
	SignIn        string `json:"signin"`
}

type Balance struct {
	StateCode int    `json:"status_code"`
	Balance   uint64 `json:"balance"`
}

func (w *walletHost) open() (ok bool, action uint, actionKey uint64, errCode int, jsonErr string) {
	// get Api Info
	hostData := &hostId{}
	if rowsAffected := w.db.
		Table("host_id").
		Select("host_id, wallet_type, api_info, guest_enable, guest_balance, status").
		Where("host_ext_id = ?", w.hostExtId).
		Scan(hostData).
		RowsAffected; rowsAffected != 1 {
		return false, kNon, 0, -1, ""
	}

	// get Api Url
	apiInfo := &ApiInfo{}
	if err := json.Unmarshal([]byte(hostData.ApiInfo), apiInfo); err != nil {
		return false, kNon, 0, -1, ""
	}
	w.apiInfo = apiInfo

	parameter := fmt.Sprintf("access_token=%s&step=1", w.token)
	url := fmt.Sprintf("%s/%s?%s", apiInfo.BaseUrl, apiInfo.Auth, parameter)

	w.apiLog(url, CallApiBefore)
	// get balance
	var body []byte
	var err error
	if body, err = http.Service.Get(url); err != nil {
		json_err := fmt.Sprintf("{\"game_id\":\"%s\",\"member_id\":\"%s\",\"url\":\"%s\",\"msg\":\"%s\"}", w.gameId, w.memberId, url, err.Error())
		return false, kAuthenticate, 0, 1, json_err
	}

	getBalance := &Balance{}
	if err := json.Unmarshal(body, getBalance); err != nil {
		json_err := fmt.Sprintf("{\"game_id\":\"%s\",\"member_id\":\"%s\",\"url\":\"%s\",\"msg\":\"%s\"}", w.gameId, w.memberId, url, err.Error())
		return false, kGetBalance, 0, 2, json_err
	}
	w.balance = getBalance.Balance
	w.apiLog(url, CallApiAfter)

	return w.selectMember(), kNon, 0, -1, ""
}

func (w *walletHost) selectMember() (ok bool) {
	data := &member{}

	if rowsAffected := w.db.
		Table("member").
		Select("host_id, id, player_cent, acc_type").
		Where("id = ? AND host_id = ?", w.memberId, w.hostId).
		Scan(data).
		RowsAffected; rowsAffected == 1 {
		w.accType = data.AccType
		return true
	}

	return w.duplicateUpdateMember()
}

func (w *walletHost) duplicateUpdateMember() (ok bool) {
	data := member{
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
		w.accType = data.AccType
		return true
	}

	logger.Service.Zap.Infow("Debug", "step", 5)
	return false
}

func (w *walletHost) selectBalance() (balance uint64, ok bool, action uint, actionKey uint64, errCode int, jsonErr string) {
	parameter := fmt.Sprintf("access_token=%s&step=1", w.token)
	url := fmt.Sprintf("%s/%s?%s", w.apiInfo.BaseUrl, w.apiInfo.GetBalance, parameter)

	w.apiLog(url, CallApiBefore)
	var body []byte
	var err error
	if body, err = http.Service.Get(url); err != nil {
		json_err := fmt.Sprintf("{\"game_id\":\"%s\",\"member_id\":\"%s\",\"url\":\"%s\",\"msg\":\"%s\"}", w.gameId, w.memberId, url, err.Error())
		return 0, false, kAuthenticate, 0, 1, json_err
	}

	apiResult := &Balance{}
	if err := json.Unmarshal(body, apiResult); err != nil {
		json_err := fmt.Sprintf("{\"game_id\":\"%s\",\"member_id\":\"%s\", \"url\":\"%s\",\"msg\":\"%s\"}", w.gameId, w.memberId, url, err.Error())
		return 0, false, kGetBalance, 0, 2, json_err
	}

	if apiResult.StateCode != 0 {
		json_err := fmt.Sprintf("{\"game_id\":\"%s\",\"member_id\":\"%s\", \"url\":\"%s\",\"balance\":\"%s\"}", w.gameId, w.memberId, url, strconv.FormatUint(apiResult.Balance, 10))
		return 0, false, kGetBalance, 0, apiResult.StateCode, json_err
	}
	w.balance = apiResult.Balance
	w.apiLog(url, CallApiAfter)

	return apiResult.Balance, true, kNon, 0, -1, ""
}

func (w *walletHost) increaseBalance(txnId, cent, bonusCent, betAmt, winAmt uint64) (ok bool, action uint, actionKey uint64, errCode int, jsonErr string) {
	parameter := fmt.Sprintf("access_token=%s&txn_id=%d&total_win=%d&game_id=%s&subgame_id=%d&ts=%d&bonus_win=%d&betamt=%d&winamt=%d",
		w.token,
		txnId,
		cent,
		w.gameId,
		w.subGameId,
		time.Now().Unix(),
		bonusCent,
		betAmt,
		winAmt,
	)
	url := fmt.Sprintf("%s/%s?%s", w.apiInfo.BaseUrl, w.apiInfo.Result, parameter)

	w.apiLog(url, CallApiBefore)
	var body []byte
	var err error
	if body, err = http.Service.Get(url); err != nil {
		errorJson := w.getErrorData(w.gameId, w.memberId, url, w.balance, cent, err.Error())
		return false, kAuthenticate, txnId, 1, errorJson
	}
	apiResult := &Balance{}
	if err := json.Unmarshal(body, apiResult); err != nil {
		errorJson := w.getErrorData(w.gameId, w.memberId, url, w.balance, cent, err.Error())
		return false, kResult, txnId, 2, errorJson
	}

	if apiResult.StateCode != 0 {
		errorJson := w.getErrorData(w.gameId, w.memberId, url, w.balance, cent, "")
		logger.Service.Zap.Infow("Debug", "stateCode", apiResult.StateCode)
		return false, kResult, txnId, apiResult.StateCode, errorJson
	}
	w.balance += cent + bonusCent
	w.apiLog(url, CallApiAfter)

	return true, kNon, 0, -1, ""
}

func (w *walletHost) decreaseBalance(txnId, cent uint64) (ok bool, action uint, actionKey uint64, errCode int, jsonErr string) {
	if cent <= 0 {
		return false, kNon, 0, -1, ""
	}

	parameter := fmt.Sprintf("access_token=%s&txn_id=%d&total_bet=%d&game_id=%s&subgame_id=%d&ts=%d",
		w.token,
		txnId,
		cent,
		w.gameId,
		w.subGameId,
		time.Now().Unix(),
	)
	url := fmt.Sprintf("%s/%s?%s", w.apiInfo.BaseUrl, w.apiInfo.Bet, parameter)

	w.apiLog(url, CallApiBefore)
	var body []byte
	var err error
	if body, err = http.Service.Get(url); err != nil {
		json_err := fmt.Sprintf("{\"game_id\":\"%s\",\"member_id\":\"%s\", \"url\":\"%s\",\"msg\":\"%s\"}", w.gameId, w.memberId, url, err.Error())
		return false, kAuthenticate, txnId, 1, json_err
	}
	apiResult := &Balance{}
	if err := json.Unmarshal(body, apiResult); err != nil {
		json_err := fmt.Sprintf("{\"game_id\":\"%s\",\"member_id\":\"%s\",\"url\":\"%s\",\"msg\":\"%s\"}", w.gameId, w.memberId, url, err.Error())
		return false, kBet, txnId, 2, json_err
	}

	if apiResult.StateCode != 0 {
		json_err := fmt.Sprintf("{\"game_id\":\"%s\",\"member_id\":\"%s\",\"url\":\"%s\",\"balance\":\"%s\"}", w.gameId, w.memberId, url, strconv.FormatUint(apiResult.Balance, 10))
		return false, kBet, txnId, apiResult.StateCode, json_err
	}
	w.balance = apiResult.Balance
	w.apiLog(url, CallApiAfter)

	return true, kNon, 0, -1, ""
}

func (w *walletHost) refundBalance(accessToken string, txnId uint64) (cent uint64, ok bool, action uint, actionKey uint64, errCode int, jsonErr string) {
	parameter := fmt.Sprintf("access_token=%s&txn_id=%d", accessToken, txnId)
	url := fmt.Sprintf("%s/%s?%s", w.apiInfo.BaseUrl, w.apiInfo.RefundBet, parameter)

	w.apiLog(url, CallApiBefore)
	var body []byte
	var err error
	if body, err = http.Service.Get(url); err != nil {
		json_err := fmt.Sprintf("{\"game_id\":\"%s\",\"member_id\":\"%s\",\"url\":\"%s\",\"msg\":\"%s\"}", w.gameId, w.memberId, url, err.Error())
		return 0, false, kAuthenticate, txnId, 1, json_err
	}
	apiResult := &Balance{}
	if err := json.Unmarshal(body, apiResult); err != nil {
		json_err := fmt.Sprintf("{\"game_id\":\"%s\",\"member_id\":\"%s\",\"url\":\"%s\",\"msg\":\"%s\"}", w.gameId, w.memberId, url, err.Error())
		return 0, false, kRefundBet, txnId, 2, json_err
	}

	if apiResult.StateCode != 0 {
		json_err := fmt.Sprintf("{\"game_id\":\"%s\",\"member_id\":\"%s\",\"url\":\"%s\",\"balance\":\"%s\"}", w.gameId, w.memberId, url, strconv.FormatUint(apiResult.Balance, 10))
		return 0, false, kRefundBet, txnId, apiResult.StateCode, json_err
	}
	w.balance = apiResult.Balance
	w.apiLog(url, CallApiAfter)

	return apiResult.Balance, true, kNon, 0, -1, ""
}

func (w *walletHost) depositBegin(tx *gorm.DB, cent, txnId uint64) (err error) {
	if cent <= 0 {
		return errors.New(Wallet_CENT_INVALID)
	}

	decreaseCheck, action, actionKey, errCode, jsonErr := w.decreaseBalance(txnId, cent)
	if !decreaseCheck {
		tx.Rollback()

		if action != kNon {
			w.apiErrorLog(action, actionKey, errCode, jsonErr)
		}

		return errors.New(Wallet_DEPOSIT_BALANCE_FAILED)
	}

	sn := ""
	if txnId != 0 {
		sn = strconv.FormatUint(txnId, 10)
	}

	log := &memberWalletLog{
		HostId:    w.hostId,
		MemberId:  w.memberId,
		Purpose:   uint(w.category),
		Action:    logWithdraw,
		TxnId:     sn,
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

	w.addRefundLog(tx, cent, sn)

	return nil
}

func (w *walletHost) withdrawCommit(tx *gorm.DB, cent, txnId, betAmt, winAmt uint64) (err error) {
	if cent <= 0 {
		tx.Rollback()
		return errors.New(Wallet_CENT_INVALID)
	}

	increaseCheck, action, actionKey, errCode, jsonErr := w.increaseBalance(txnId, cent, 0, betAmt, winAmt)
	if !increaseCheck {
		tx.Rollback()

		// Process Fish Game Server Reset Cent Wallet
		if w.checkGameType(w.gameId) {
			w.updateCentWallet(0)
		}

		if action != kNon {
			w.apiErrorLog(action, actionKey, errCode, jsonErr)
		}

		return errors.New(Wallet_WITHDRAW_BALANCE_FAILED)
	}

	sn := ""
	if txnId != 0 {
		sn = strconv.FormatUint(txnId, 10)
	}

	log := &memberWalletLog{
		HostId:    w.hostId,
		MemberId:  w.memberId,
		Purpose:   uint(w.category),
		Action:    logDeposit,
		TxnId:     sn,
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

	return nil
}

func (w *walletHost) refundCommit(tx *gorm.DB, cent, txnId uint64) (err error) {
	if cent <= 0 {
		tx.Rollback()
		return errors.New(Wallet_CENT_INVALID)
	}

	balance, ok, action, actionKey, errCode, jsonErr := w.refundBalance(w.token, txnId)
	if !ok {
		tx.Rollback()

		if action != kNon {
			w.apiErrorLog(action, actionKey, errCode, jsonErr)
		}

		return errors.New(Wallet_REFUND_BALANCE_FAILED)
	}

	sn := ""
	if txnId != 0 {
		sn = strconv.FormatUint(txnId, 10)
	}

	log := &memberWalletLog{
		HostId:    w.hostId,
		MemberId:  w.memberId,
		Purpose:   uint(w.category),
		Action:    logRefund,
		TxnId:     sn,
		Amount:    cent,
		Balance:   balance,
		Note:      logNote + "_" + strconv.Itoa(logDeposit),
		OccurTime: time.Now(),
	}

	if ok := tx.
		Table("member_wallet_log").
		Save(log).
		RowsAffected; ok == 0 {
		tx.Rollback()
		return errors.New(Wallet_INSERT_LOG_FAILED)
	}

	return nil
}

func (w *walletHost) addRefundLog(tx *gorm.DB, cent uint64, sn string) (err error) {
	jsonNote := fmt.Sprintf("{\"base_url\":\"%s\",\"refund_bet\":\"%s\",\"access_token\":\"%s\"}", w.apiInfo.BaseUrl, w.apiInfo.RefundBet, w.token)

	refundLog := &memberWalletRefundLog{
		HostId:    w.hostId,
		GameId:    w.gameId,
		SubgameId: w.subGameId,
		ServerId:  parseServerId(),
		MemberId:  w.memberId,
		TxnId:     sn,
		Bet:       cent,
		Note:      jsonNote,
		Refund:    0,
		OccurTime: time.Now(),
	}

	if ok := tx.
		Table("member_wallet_refund_log").
		Save(refundLog).
		Error; ok != nil {
		tx.Rollback()
		return errors.New(Wallet_INSERT_LOG_FAILED)
	}

	return nil
}

func (w *walletHost) apiLog(url, beforeOrAfter string) {
	logger.Service.Zap.Infow(beforeOrAfter,
		"url", url,
		"game_id", w.gameId,
		"host_id", w.hostId,
		"member_id", w.memberId,
	)
}

func (w *walletHost) apiErrorLog(action uint, actionKey uint64, errCode int, err string) { //isFish bool, cent uint64
	errLog := &hostErrorLog{
		HostId:    w.hostId,
		Action:    action,
		ActionKey: actionKey,
		ErrCode:   errCode,
		ErrDescr:  err,
		OccurTime: time.Now(),
		GameEnd:   0,
	}

	if ok := w.db.
		Table("host_error_log").
		Save(errLog).
		RowsAffected; ok == 0 {
		return
	}
}

func (w *walletHost) checkGameType(gameId string) bool {
	if strings.HasPrefix(gameId, "PSF") || strings.HasPrefix(gameId, "RKF") ||
		strings.HasPrefix(gameId, "PGF") {
		return true
	} else {
		return false
	}
}

func (w *walletHost) getErrorData(gameId, memberId, url string, balance, cent uint64, err string) string {
	if w.checkGameType(gameId) {
		errorJson := fmt.Sprintf("{\"game_id\":\"%s\",\"member_id\":\"%s\",\"cent\":\"%d\",\"url\":\"%s\",\"balance\":\"%s\",\"msg\":\"%s\"}",
			gameId,
			memberId,
			cent, url,
			strconv.FormatUint(balance, 10),
			err,
		)

		return errorJson
	} else {
		errorJson := fmt.Sprintf("{\"game_id\":\"%s\",\"member_id\":\"%s\",\"cent\":\"%d\", \"url\":\"%s\",\"msg\":\"%s\"}",
			gameId,
			memberId,
			cent,
			url,
			err,
		)
		return errorJson
	}
}

func (w *walletHost) updateCentWallet(cent uint64) bool {
	if rowAffected := w.db.
		Table("member_wallet").
		Where("member_id = ? AND host_id = ? AND purpose = ?", w.memberId, w.hostId, w.purpose).
		UpdateColumn("balance", cent).
		RowsAffected; rowAffected == 1 {
			if w, ok := Service.usersWallet[w.secWebSocketKey]; ok {
				w.walletSharedMinor.cent = cent
				return true
			}

			return false
	}

	logger.Service.Zap.Infow("Fish IncreaseBalance updateCentWallet Error",
		"secWebSocketKey", w.secWebSocketKey,
		"balance", w.balance,
	)

	return false
}

func parseServerId() string {
	atoiPort, _ := strconv.Atoi(os.Getenv("HTTP_PORT"))
	macAddr := strings.Replace(macaddress.Get(), ":", "-", -1)
	return fmt.Sprintf("%s-%05d", macAddr, atoiPort)
}