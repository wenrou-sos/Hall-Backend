package accounting

import (
	"time"

	"github.com/jinzhu/gorm"
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
)

const (
	ActionAccountingStop     = "ActionAccountingStop"
	ActionAccountingPause    = "ActionAccountingPause"
	ActionAccountingContinue = "ActionAccountingContinue"
	ActionAccountingEnd      = "ActionAccountingEnd"
	ActionAccountingDelete   = "ActionAccountingDelete"
	PLAYER                   = "PLAYER"
	BOT                      = "BOT"
	GUEST                    = "GUEST"
	regular                  = 0
	test                     = 1
)

func Builder() *builder {
	return &builder{
		secWebSocketKey: "",
		hostExtId:       "",
		guestEnable:     true,
		period:          0,
		hostId:          "",
		gameId:          "",
		subgameId:       0,
		memberId:        "",
		initCent:        0,
		bet:             0,
		denom:           0,
		gameData:        "",
		gameResult:      "",
		gameModule:      "",
		testAccount:     regular, // 0:regular 1:test
		kind:            "",
		iHandler:        nil,
		db:              nil,
	}
}

type builder struct {
	secWebSocketKey string
	hostExtId       string
	guestEnable     bool
	period          uint32
	hostId          string
	gameId          string
	subgameId       uint32
	memberId        string
	initCent        uint64
	bet             uint64
	denom           uint64
	gameData        string
	gameResult      string
	gameModule      string
	testAccount     uint8 // 0:regular 1:test
	kind            string
	iHandler        IHandler
	db              *gorm.DB
}

type IHandler interface {
	FluxActionHandler(action *flux.Action, a *Accounting, isOk chan bool)
	RotationHandler(a *Accounting)
}

type Accounting struct {
	SecWebSocketKey string
	hostExtId       string
	guestEnable     bool
	period          uint32
	kind            string
	db              *gorm.DB
	in              chan *flux.Action
	CtrlRotation    chan bool
	PauseTimer      chan bool
	ContinueTimer   chan bool
	IsStop          bool
	TimerStop       bool
	iHandler        IHandler
	Start           *Start
	end             *end
}

// database table `accounting`
type Start struct {
	Sn          uint64 `gorm:"PRIMARY_KEY;AUTO_INCREMENT"`
	MachineId   int
	HostId      string
	HostLevel   int
	GameId      string
	SubgameId   uint32
	MemberId    string
	InitCent    uint64
	Bet         uint64
	Denom       uint64
	TotalWin    int64
	BonusWin    uint64
	GambleWin   uint64
	JackpotWin  uint64
	GameData    string
	GameResult  string
	EndCent     uint64
	GameModule  string
	TestAccount uint8 // 0:regular 1:test
}

// database table `accounting`
type end struct {
	Sn         uint64    `gorm:"PRIMARY_KEY;AUTO_INCREMENT"`
	GameTime   time.Time `gorm:"default:CURRENT_TIMESTAMP"` // not used yet
	Bet        uint64
	Denom      uint64
	TotalWin   int64
	BonusWin   uint64
	JackpotWin uint64
	EndCent    uint64
	GameData   string
	GameResult string
	GameEnd    int
}

func (b *builder) SetSecWebSocketKey(secWebSocketKey string) *builder {
	b.secWebSocketKey = secWebSocketKey
	return b
}

func (b *builder) SetHostExtId(hostExtId string) *builder {
	b.hostExtId = hostExtId
	return b
}

func (b *builder) SetGuestEnable(guestEnable bool) *builder {
	b.guestEnable = guestEnable
	return b
}

func (b *builder) SetPeriod(period uint32) *builder {
	b.period = period
	return b
}

func (b *builder) SetHostId(hostId string) *builder {
	b.hostId = hostId
	return b
}

func (b *builder) SetGameId(gameId string) *builder {
	b.gameId = gameId
	return b
}

func (b *builder) SetSubgameId(subgameId uint32) *builder {
	b.subgameId = subgameId
	return b
}

func (b *builder) SetMemberId(memberId string) *builder {
	b.memberId = memberId
	return b
}

func (b *builder) SetInitCent(balance uint64) *builder {
	b.initCent = balance
	return b
}

func (b *builder) SetBet(bet uint64) *builder {
	b.bet = bet
	return b
}

func (b *builder) SetDenom(denom uint64) *builder {
	b.denom = denom
	return b
}

func (b *builder) SetGameData(gameData string) *builder {
	b.gameData = gameData
	return b
}

func (b *builder) SetGameResult(gameResult string) *builder {
	b.gameResult = gameResult
	return b
}

func (b *builder) SetGameModule(gameModule string) *builder {
	b.gameModule = gameModule
	return b
}

func (b *builder) SetTestAccount(walletAccType uint8) *builder {
	switch walletAccType {
	case 0: // locked
		b.testAccount = test

	case 1: // regular
		b.testAccount = regular

	case 2: // test
		b.testAccount = test

	case 3: // vip
		b.testAccount = regular

	default:
		b.testAccount = test
	}
	return b
}

func (b *builder) SetKind(kind string) *builder {
	b.kind = kind
	return b
}

func (b *builder) SetHandler(iHandler IHandler) *builder {
	b.iHandler = iHandler
	return b
}

func (b *builder) Build() *Accounting {
	a := &Accounting{
		SecWebSocketKey: b.secWebSocketKey,
		hostExtId:       b.hostExtId,
		guestEnable:     b.guestEnable,
		period:          b.period,
		kind:            b.kind,
		db:              b.db,
		in:              make(chan *flux.Action, 1024),
		CtrlRotation:    make(chan bool, 1024),
		PauseTimer:      make(chan bool),
		ContinueTimer:   make(chan bool),
		IsStop:          false,
		TimerStop:       false,
		iHandler:        b.iHandler,
		Start: &Start{
			MachineId:   -1,
			HostId:      b.hostId,
			HostLevel:   0,
			GameId:      b.gameId,
			SubgameId:   b.subgameId,
			MemberId:    b.memberId,
			InitCent:    b.initCent,
			Bet:         b.bet,
			Denom:       b.denom,
			TotalWin:    0,
			BonusWin:    0,
			GambleWin:   0,
			JackpotWin:  0,
			GameData:    b.gameData,
			GameResult:  b.gameResult,
			EndCent:     0,
			GameModule:  b.gameModule,
			TestAccount: b.testAccount,
		},
		end: &end{
			Denom:   b.denom,
			GameEnd: 1,
		},
	}

	if a.create() {
		flux.Send(actionAccountingStart, a.HashId(), Service.Id, a)
		return a
	}

	close(a.CtrlRotation)
	close(a.PauseTimer)
	close(a.ContinueTimer)

	return nil
}

func (a *Accounting) run(isOk chan bool) {
	flux.Register(a.HashId(), a.in)

	for action := range a.in {
		a.iHandler.FluxActionHandler(action, a, isOk)
	}
}

func (a *Accounting) create() bool {
	if a.guestEnable {
		return false
	}

	accountingTable, logAccountTableName := a.chooseTableName()

	if ok := a.db.Table(accountingTable).Create(a.Start).RowsAffected; ok == 1 {
		a.end.Sn = a.Start.Sn

		if a.period > 0 {
			go a.rotation()
		}

		logger.Service.Zap.Infow("Create "+logAccountTableName,
			"GameUser", a.SecWebSocketKey,
			"AccountingSn", a.Start.Sn,
			"HostId", a.Start.HostId,
			"HostExtId", a.hostExtId,
			"HostLevel", a.Start.HostLevel,
			"GameId", a.Start.GameId,
			"SubgameId", a.Start.SubgameId,
			"MemberId", a.Start.MemberId,
			"InitBalance", a.Start.InitCent,
			"TotalBet", a.Start.Bet,
			"TotalBonusWin", a.Start.BonusWin,
			"TotalWin", a.Start.TotalWin,
			"EndBalance", a.Start.EndCent,
			"Denom", a.Start.Denom,
			"GameModule", a.Start.GameModule,
			"GameData", a.Start.GameData,
			"GameResult", a.Start.GameResult,
		)

		isOk := make(chan bool)

		go a.run(isOk)

		<-isOk

		close(isOk)

		return true
	}

	logger.Service.Zap.Errorw(Accounting_START_ACCOUNTING_FAILED,
		"GameUser", a.SecWebSocketKey,
		"AccountingSn", a.Start.Sn,
		"HostId", a.Start.HostId,
		"HostExtId", a.hostExtId,
		"HostLevel", a.Start.HostLevel,
		"GameId", a.Start.GameId,
		"SubgameId", a.Start.SubgameId,
		"MemberId", a.Start.MemberId,
		"InitBalance", a.Start.InitCent,
		"TotalBet", a.Start.Bet,
		"TotalBonusWin", a.Start.BonusWin,
		"TotalWin", a.Start.TotalWin,
		"EndBalance", a.Start.EndCent,
		"Denom", a.Start.Denom,
		"GameModule", a.Start.GameModule,
		"GameData", a.Start.GameData,
		"GameResult", a.Start.GameResult,
	)
	errorcode.Service.Fatal(a.SecWebSocketKey, Accounting_START_ACCOUNTING_FAILED)

	return false
}

func (a *Accounting) End(totalBet, totalBonusWin uint64, totalWin int64, jackpotWin uint64, gameData, gameResult string) bool {
	if gameData != "" {
		a.end.GameData = gameData
	}

	if gameResult != "" {
		a.end.GameResult = gameResult
	}

	a.end.Bet = totalBet
	a.end.BonusWin = totalBonusWin
	a.end.TotalWin = totalWin
	a.end.JackpotWin = jackpotWin

	if a.Start.InitCent < a.end.Bet {
		loseCent := a.end.Bet - a.Start.InitCent

		if totalWin >= int64(loseCent) {
			a.end.EndCent = uint64(totalWin) - loseCent
		} else {
			a.end.EndCent = 0
		}
	} else {
		a.end.EndCent = a.Start.InitCent - a.end.Bet + uint64(a.end.TotalWin)
	}

	accountingTable, logAccountTableName := a.chooseTableName()

	// prevent empty accounting
	if a.end.Bet == 0 && a.end.BonusWin == 0 && a.end.TotalWin == 0 && a.end.JackpotWin == 0 {
		a.Delete(a.end.Sn)
		return true
	}

	if ok := a.db.Exec("UPDATE `"+accountingTable+"` SET `game_time` = NOW(), `bet` = ?, `denom` = ?, `total_win` = ?, `bonus_win` = ?, `jackpot_win` = ?, `end_cent` = ?, `game_data` = ?, `game_result` = ?, `game_end` = ?  WHERE `"+accountingTable+"`.`sn` = ?",
		a.end.Bet,
		a.end.Denom,
		a.end.TotalWin-int64(a.end.JackpotWin),
		a.end.BonusWin,
		a.end.JackpotWin,
		a.end.EndCent,
		a.end.GameData,
		a.end.GameResult,
		a.end.GameEnd,
		a.end.Sn,
	).RowsAffected; ok == 1 {
		logger.Service.Zap.Infow("End "+logAccountTableName,
			"GameUser", a.SecWebSocketKey,
			"AccountingSn", a.end.Sn,
			"IsStop", a.IsStop,
			"HostId", a.Start.HostId,
			"HostExtId", a.hostExtId,
			"HostLevel", a.Start.HostLevel,
			"GameId", a.Start.GameId,
			"SubgameId", a.Start.SubgameId,
			"MemberId", a.Start.MemberId,
			"InitBalance", a.Start.InitCent,
			"GameTime", a.end.GameTime,
			"TotalBet", a.end.Bet,
			"TotalBonusWin", a.end.BonusWin,
			"TotalWin", a.end.TotalWin,
			"JackpotWin", a.end.JackpotWin,
			"EndBalance", a.end.EndCent,
			"Denom", a.end.Denom,
			"MathModuleId", a.Start.GameModule,
			"GameData", a.end.GameData,
			"GameResult", a.end.GameResult,
		)

		flux.Send(actionAccountingDelete, a.HashId(), Service.Id, a.SecWebSocketKey, a.Start.Sn)

		return true
	}

	logger.Service.Zap.Warnw(Accounting_END_ACCOUNTING_FAILED,
		"GameUser", a.SecWebSocketKey,
		"AccountingSn", a.end.Sn,
		"IsStop", a.IsStop,
		"HostId", a.Start.HostId,
		"HostExtId", a.hostExtId,
		"HostLevel", a.Start.HostLevel,
		"GameId", a.Start.GameId,
		"SubgameId", a.Start.SubgameId,
		"MemberId", a.Start.MemberId,
		"InitBalance", a.Start.InitCent,
		"GameTime", a.end.GameTime,
		"TotalBet", a.end.Bet,
		"TotalBonusWin", a.end.BonusWin,
		"TotalWin", a.end.TotalWin,
		"JackpotWin", a.end.JackpotWin,
		"EndBalance", a.end.EndCent,
		"Denom", a.end.Denom,
		"MathModuleId", a.Start.GameModule,
		"GameData", a.end.GameData,
		"GameResult", a.end.GameResult,
	)

	return false
}

func (a *Accounting) rotation() {
	duration := time.Duration(a.period) * time.Minute
	timer := time.NewTimer(duration)
	start := time.Now()
	var elapsed time.Duration
	isTimerPause := false

	defer timer.Stop()

	for {
		select {
		case <-timer.C:
			a.TimerStop = true
			a.iHandler.RotationHandler(a)
			return

		case is, ok := <-a.CtrlRotation:
			if !ok || is {
				a.TimerStop = true
				return
			}
		case <-a.PauseTimer:
			isTimerPause = true
			elapsed = time.Since(start)
			timer.Stop()
			logger.Service.Zap.Infow("Pause Timer Success",
				"accountingSn", a.Start.Sn,
				"Start Time", start,
				"Elapsed Time", elapsed,
			)

		case <-a.ContinueTimer:
			if !isTimerPause {
				continue
			}
			remainingDuration := duration - elapsed
			logger.Service.Zap.Infow("Continue Timer Success",
				"accountingSn", a.Start.Sn,
				"elapsed", elapsed,
				"remainingDuration ", remainingDuration,
			)
			timer.Reset(remainingDuration)
			duration = remainingDuration
			start = time.Now()
		}
	}
}

func (a *Accounting) DeleteRefundLog() {
	if ok := a.db.
		Exec("DELETE FROM member_wallet_refund_log WHERE txn_id = ?", a.end.Sn).
		RowsAffected; ok == 1 {
		logger.Service.Zap.Infow("Delete Refund Log",
			"GameUser", a.SecWebSocketKey,
			"HostId", a.Start.HostId,
			"GameId", a.Start.GameId,
			"SubGameId", a.Start.SubgameId,
			"MemberId", a.Start.MemberId,
			"TxnId", a.end.Sn,
		)
	}
}

func (a *Accounting) Delete(accountingSn uint64) {
	accountingTable, logAccountTableName := a.chooseTableName()
	if ok := a.db.Exec("DELETE FROM `"+accountingTable+"` WHERE `"+accountingTable+"`.`sn` = ?", accountingSn).RowsAffected; ok == 1 {
		logger.Service.Zap.Infow("Delete "+logAccountTableName,
			"GameUser", a.SecWebSocketKey,
			"AccountingSn", a.Start.Sn,
			"HostId", a.Start.HostId,
			"HostExtId", a.hostExtId,
			"HostLevel", a.Start.HostLevel,
			"GameId", a.Start.GameId,
			"SubgameId", a.Start.SubgameId,
			"MemberId", a.Start.MemberId,
			"InitBalance", a.Start.InitCent,
			"TotalBet", a.Start.Bet,
			"TotalBonusWin", a.Start.BonusWin,
			"TotalWin", a.Start.TotalWin,
			"EndBalance", a.Start.EndCent,
			"Denom", a.Start.Denom,
			"GameModule", a.Start.GameModule,
			"GameData", a.Start.GameData,
			"GameResult", a.Start.GameResult,
		)

		flux.Send(actionAccountingDelete, a.HashId(), Service.Id, a.SecWebSocketKey, accountingSn)
	}
}

func (a *Accounting) HashId() string {
	return Service.HashId(a.SecWebSocketKey, a.Start.Sn)
}

func (a *Accounting) destroy() {
	flux.UnRegister(a.HashId(), a.in)
}

func (a *Accounting) chooseTableName() (tableName, logActionName string) {
	tableName = "accounting"
	logActionName = "Accounting"
	if a.kind == BOT {
		tableName = "accounting_robot"
		logActionName = "Robot Accounting"
	}

	return tableName, logActionName
}
