package bet

import (
	"fish-shrimp-crab-game-server/application/gamesettingFS"
	bet_proto "fish-shrimp-crab-game-server/domain/bet/proto"
	commonFS_proto "fish-shrimp-crab-game-server/models/proto"
	"sync"
	"time"

	"github.com/gogo/protobuf/proto"
	"github.com/google/uuid"
	common_proto "gitlab.iplaystar.net/game-server/common/proto"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/wallet"
)

const (
	ActionBetRoundStart              = "ActionBetRoundStart"
	ActionBetRoundEnd                = "ActionBetRoundEnd"
	ActionBetRoundJoin               = "ActionBetRoundJoin"
	ActionClearBetStatus             = "ActionClearBetStatus"
	EMSGID_eBetCall                  = "EMSGID_eBetCall"
	EMSGID_eBetRecall                = "EMSGID_eBetRecall"
	EMSGID_eBroadcastBetRecall       = "EMSGID_eBroadcastBetRecall"
	EMSGID_eMultiBetCall             = "EMSGID_eMultiBetCall"
	EMSGID_eMultiBetRecall           = "EMSGID_eMultiBetRecall"
	EMSGID_eBroadcastMultiBetRecall  = "EMSGID_eBroadcastMultiBetRecall"
	EMSGID_eBetRoundCountdown        = "EMSGID_eBetRoundCountdown"
	EMSGID_eBetRoundStart            = "EMSGID_eBetRoundStart"
	EMSGID_eBetRoundEnd              = "EMSGID_eBetRoundEnd"
	EMSGID_eClearBetsCall            = "EMSGID_eClearBetsCall"
	EMSGID_eClearBetsRecall          = "EMSGID_eClearBetsReCall"
	EMSGID_eBroadcastClearBetsRecall = "EMSGID_eBroadcastClearBetsRecall"
	EMSGID_ePlayerStillBetWarn       = "EMSGID_ePlayerStillBetWarn"
	EMSGID_eJoinedBetRoundInfo       = "EMSGID_eJoinedBetRoundInfo"

	BET_ROUND_CHANSIZE = 1024
)

type BetRound struct {
	uuid         uuid.UUID
	gameRoomUuid string
	gameRoomKind string
	timeLimit    int
	bets         map[string][]*bet_proto.BetCall
	rwMutex      *sync.RWMutex
	in           chan *flux.Action
}

func NewBetRound(gameRoomUuid, gameRoomKind string, countTime int) *BetRound {
	//countTime, _ := strconv.Atoi(os.Getenv("BET_ROUND_COUNTDOWN_TIME"))
	return &BetRound{
		uuid:         uuid.New(),
		gameRoomUuid: gameRoomUuid,
		gameRoomKind: gameRoomKind,
		timeLimit:    countTime,
		bets:         make(map[string][]*bet_proto.BetCall),
		rwMutex:      &sync.RWMutex{},
		in:           make(chan *flux.Action, BET_ROUND_CHANSIZE),
	}
}

func (b *BetRound) run() {
	flux.Register(b.uuid.String(), b.in)

	poolSize := 8

	for i := 0; i < poolSize; i++ {
		go func() {
			for action := range b.in {
				b.handleAction(action)
			}
		}()
	}
}

func (b *BetRound) handleAction(action *flux.Action) {
	if b.uuid.String() != action.Key().To() {
		return
	}
	switch action.Key().Name() {
	case flux.ActionFluxRegisterDone:
		b.betRoundStart()

	case EMSGID_eBetCall:
		b.rwMutex.Lock()
		defer b.rwMutex.Unlock()

		secWebSocketKey := action.Key().From()
		betCallBytes := action.Payload()[0].([]byte)

		betCall := &bet_proto.BetCall{}
		_ = proto.Unmarshal(betCallBytes, betCall)

		balance, _ := wallet.Service.Balance(secWebSocketKey)

		betCost :=
			gamesettingFS.Service.Bet(secWebSocketKey, betCall.BetIndex) *
				gamesettingFS.Service.Rate(secWebSocketKey)

		if balance < uint64(betCost) {
			logger.Service.Zap.Errorw(
				Bet_BALANCE_NOT_ENOUGHT,
				"user",
				secWebSocketKey,
				"remain balance",
				balance,
			)
			b.betRecall(betCall, common_proto.Status_kNoEnoughCredit, balance, secWebSocketKey)
			return
		}

		if b.isExceedBetAreaLimit(secWebSocketKey, betCall) {
			b.betRecall(betCall, common_proto.Status_kInvalid, balance, secWebSocketKey)
			return
		}

		if !wallet.Service.DecreaseBalance(secWebSocketKey, b.uuid.String(), uint64(betCost)) {
			return
		}
		b.bets[secWebSocketKey] = append(b.bets[secWebSocketKey], betCall)
		balance, _ = wallet.Service.Balance(secWebSocketKey)
		b.broadcastBetRecall(b.betRecall(betCall, common_proto.Status_kSuccess, balance, secWebSocketKey))

	case EMSGID_eMultiBetCall:
		b.rwMutex.Lock()
		defer b.rwMutex.Unlock()

		secWebSocketKey := action.Key().From()
		betCallBytes := action.Payload()[0].([]byte)

		multiBetCall := &bet_proto.MultiBetCall{}
		_ = proto.Unmarshal(betCallBytes, multiBetCall)

		balance, _ := wallet.Service.Balance(secWebSocketKey)

		var betCost uint32
		for _, betcall := range multiBetCall.BetCalls {
			betCost += gamesettingFS.Service.Bet(secWebSocketKey, betcall.BetIndex) * gamesettingFS.Service.Rate(secWebSocketKey)
		}

		if balance < uint64(betCost) {
			logger.Service.Zap.Errorw(
				Bet_BALANCE_NOT_ENOUGHT,
				"user",
				secWebSocketKey,
				"remain balance",
				balance,
			)
			b.multiBetRecall(multiBetCall, common_proto.Status_kNoEnoughCredit, balance, secWebSocketKey)
			return
		}

		if b.isExceedBetAreaLimit_multi(secWebSocketKey, multiBetCall) {
			b.multiBetRecall(multiBetCall, common_proto.Status_kInvalid, balance, secWebSocketKey)
			return
		}

		if !wallet.Service.DecreaseBalance(secWebSocketKey, b.uuid.String(), uint64(betCost)) {
			return
		}
		for _, betcall := range multiBetCall.BetCalls {
			b.bets[secWebSocketKey] = append(b.bets[secWebSocketKey], betcall)
		}
		balance, _ = wallet.Service.Balance(secWebSocketKey)
		b.broadcastMultiBetRecall(b.multiBetRecall(multiBetCall, common_proto.Status_kSuccess, balance, secWebSocketKey))

	case EMSGID_eClearBetsCall:
		b.rwMutex.Lock()
		defer b.rwMutex.Unlock()
		secWebSocketKey := action.Key().From()

		logger.Service.Zap.Infow("clear bets call", "player", secWebSocketKey)

		if b.bets[secWebSocketKey] == nil {
			return
		}

		clearedBets := []*bet_proto.BetCall{}

		for _, betCall := range b.bets[secWebSocketKey] {
			betCost :=
				gamesettingFS.Service.Bet(secWebSocketKey, betCall.BetIndex) *
					gamesettingFS.Service.Rate(secWebSocketKey)
			wallet.Service.IncreaseBalance(secWebSocketKey, b.uuid.String(), uint64(betCost))
			clearedBets = append(clearedBets, betCall)
		}

		delete(b.bets, secWebSocketKey)

		balance, _ := wallet.Service.Balance(secWebSocketKey)
		b.broadcastClearRecall(b.clearBetRecall(secWebSocketKey, clearedBets, balance), balance)

	case ActionBetRoundJoin:
		secWebSocketKey := action.Payload()[0].(string)
		var betCalls []*bet_proto.BetCall
		for _, calls := range b.bets {
			for _, call := range calls {
				betCalls = append(betCalls, call)
			}
		}
		j := &bet_proto.JoinedBetRoundInfo{
			Msgid:        commonFS_proto.EMSGID_eJoinedBetRoundInfo,
			BetRoundUuid: b.uuid.String(),
			Bets:         betCalls,
		}
		bytes, _ := proto.Marshal(j)
		flux.Send(EMSGID_eJoinedBetRoundInfo, b.uuid.String(), secWebSocketKey, bytes)
	}
}

func (b *BetRound) betRoundStart() {
	data := &bet_proto.BetRoundStart{
		Msgid:        commonFS_proto.EMSGID_eBetRoundStart,
		RoomUuid:     b.gameRoomUuid,
		BetRoundUuid: b.uuid.String(),
	}

	dataByte, _ := proto.Marshal(data)

	flux.Send(EMSGID_eBetRoundStart, b.uuid.String(), b.gameRoomUuid, dataByte, b.uuid.String(), b.gameRoomKind)
	go b.betRoundCountDown(b.timeLimit)
}

func (b *BetRound) betRoundEnd(gameRoomUuid string) {
	b.rwMutex.RLock()
	defer b.rwMutex.RUnlock()

	data := &bet_proto.BetRoundEnd{
		Msgid:    commonFS_proto.EMSGID_eBetRoundEnd,
		RoomUuid: gameRoomUuid,
	}

	dataByte, _ := proto.Marshal(data)

	copyBets := map[string][]bet_proto.BetCall{}

	for uuid, bets := range b.bets {
		for _, bet := range bets {
			copyBets[uuid] = append(copyBets[uuid], *bet)
		}
	}

	flux.Send(EMSGID_eBetRoundEnd, b.uuid.String(), gameRoomUuid, dataByte, copyBets, b.gameRoomKind)

	b.destroy()
}

func (b *BetRound) broadcastBetRoundCountdown(gameRoomUuid string, count int) {
	data := &bet_proto.BetRoundCountdown{
		Msgid:   commonFS_proto.EMSGID_eBetRoundCountdown,
		Timeout: int32(count),
	}

	dataByte, _ := proto.Marshal(data)

	flux.Send(EMSGID_eBetRoundCountdown, b.uuid.String(), gameRoomUuid, dataByte)
}

func (b *BetRound) betRoundCountDown(timeout int) {
	count := b.timeLimit

	if timeout > 0 {
		count = timeout
	}
	t := time.Tick(time.Second)
	for {
		select {
		case <-t:

			count -= 1

			if count < 1 {
				time.Sleep(time.Duration(count) * time.Millisecond) // for web client animation
				b.betRoundEnd(b.gameRoomUuid)
				return
			}

			//logger.Service.Zap.Infow("Bet Round Counting Down",
			//	"time remain:", count)

			b.broadcastBetRoundCountdown(b.gameRoomUuid, count)
		}
	}
}

func (b *BetRound) betRecall(betCall *bet_proto.BetCall, statusCode common_proto.Status_Code, balance uint64, secWebSocketKey string) *bet_proto.BetRecall {
	recall := &bet_proto.BetRecall{
		Msgid:      commonFS_proto.EMSGID_eBetRecall,
		StatusCode: statusCode,
		Seat:       betCall.Seat,
		BetType:    betCall.BetType,
		BetIndex:   betCall.BetIndex,
		Balance:    balance,
	}
	bytes, _ := proto.Marshal(recall)
	flux.Send(EMSGID_eBetRecall, b.uuid.String(), secWebSocketKey, bytes, statusCode)
	return recall
}

func (b *BetRound) multiBetRecall(multiBetCall *bet_proto.MultiBetCall, statusCode common_proto.Status_Code, balance uint64, secWebSocketKey string) *bet_proto.MultiBetRecall {
	recalls := make([]*bet_proto.BetRecall, len(multiBetCall.BetCalls))
	for i, betcall := range multiBetCall.BetCalls {
		recall := &bet_proto.BetRecall{
			Msgid:      commonFS_proto.EMSGID_eBetRecall,
			StatusCode: statusCode,
			Seat:       betcall.Seat,
			BetType:    betcall.BetType,
			BetIndex:   betcall.BetIndex,
			Balance:    balance,
		}
		recalls[i] = recall
	}

	multiRecall := &bet_proto.MultiBetRecall{
		Msgid:      commonFS_proto.EMSGID_eMultiBetRecall,
		BetRecalls: recalls,
	}
	bytes, _ := proto.Marshal(multiRecall)
	flux.Send(EMSGID_eBetRecall, b.uuid.String(), secWebSocketKey, bytes, statusCode)
	return multiRecall
}

func (b *BetRound) broadcastBetRecall(call *bet_proto.BetRecall) {
	broadcastBetRecall := &bet_proto.BroadcastBetRecall{
		Msgid:     commonFS_proto.EMSGID_eBroadcastBetRecall,
		BetRecall: call,
	}
	bytes, _ := proto.Marshal(broadcastBetRecall)

	flux.Send(EMSGID_eBroadcastBetRecall, b.uuid.String(), b.gameRoomUuid, bytes)
}

func (b *BetRound) broadcastMultiBetRecall(call *bet_proto.MultiBetRecall) {
	broadcastMultiBetRecall := &bet_proto.BroadcastMultiBetRecall{
		Msgid:     commonFS_proto.EMSGID_eBroadcastMultiBetRecall,
		BetRecall: call,
	}
	bytes, _ := proto.Marshal(broadcastMultiBetRecall)

	flux.Send(EMSGID_eBroadcastMultiBetRecall, b.uuid.String(), b.gameRoomUuid, bytes)
}

func (b *BetRound) clearBetRecall(secWebSocketKey string, clearedBetCalls []*bet_proto.BetCall, balance uint64) *bet_proto.ClearBetsRecall {
	recall := &bet_proto.ClearBetsRecall{
		Msgid:         commonFS_proto.EMSGID_eClearBetsRecall,
		BetRoundUuid:  b.uuid.String(),
		ClearedBets:   clearedBetCalls,
		PlayerBalance: balance,
	}
	bytes, _ := proto.Marshal(recall)
	flux.Send(EMSGID_eClearBetsRecall, b.uuid.String(), secWebSocketKey, bytes)
	return recall
}

func (b *BetRound) broadcastClearRecall(recall *bet_proto.ClearBetsRecall, playerBalance uint64) {
	broadcastClearBetsRecall := &bet_proto.BroadcastClearBetReall{
		Msgid:           commonFS_proto.EMSGID_eBroadcastClearBetsRecall,
		ClearBetsRecall: recall,
		PlayerBalance:   playerBalance,
	}
	bytes, _ := proto.Marshal(broadcastClearBetsRecall)
	flux.Send(EMSGID_eBroadcastClearBetsRecall, b.uuid.String(), b.gameRoomUuid, bytes)
}

func (b *BetRound) isExceedBetAreaLimit(secWebSocketKey string, betCall *bet_proto.BetCall) bool {
	var totalBetOnTable, totalAreaBetOnTable uint32

	for _, bet := range b.bets[secWebSocketKey] {
		betcost := gamesettingFS.Service.Bet(secWebSocketKey, bet.BetIndex) * gamesettingFS.Service.Rate(secWebSocketKey)
		totalBetOnTable += betcost
		if betCall.BetType == bet.BetType {
			totalAreaBetOnTable += betcost
		}
	}

	betcost := gamesettingFS.Service.Bet(secWebSocketKey, betCall.BetIndex) * gamesettingFS.Service.Rate(secWebSocketKey)
	if totalBetOnTable+betcost > gamesettingFS.Service.BetAreaLimit(secWebSocketKey, 0) || //全桌和超過
		totalAreaBetOnTable+betcost > gamesettingFS.Service.BetAreaLimit(secWebSocketKey, b.betAreaLimitIndex(betCall.BetType)) { //某區和超過
		return true
	}

	return false
}

func (b *BetRound) isExceedBetAreaLimit_multi(secWebSocketKey string, multiBetCall *bet_proto.MultiBetCall) bool {
	var totalBetOnTable uint32
	var totalAreaBetOnTable [24]uint32

	for _, bet := range b.bets[secWebSocketKey] {
		betcost := gamesettingFS.Service.Bet(secWebSocketKey, bet.BetIndex) * gamesettingFS.Service.Rate(secWebSocketKey)
		totalBetOnTable += betcost
		totalAreaBetOnTable[bet.BetType] += betcost
	}

	var totalBet uint32
	var totalAreaBet [24]uint32

	for _, bet := range multiBetCall.BetCalls {
		betcost := gamesettingFS.Service.Bet(secWebSocketKey, bet.BetIndex) * gamesettingFS.Service.Rate(secWebSocketKey)
		totalBet += betcost
		totalAreaBet[bet.BetType] += betcost
	}

	if totalBetOnTable+totalBet > gamesettingFS.Service.BetAreaLimit(secWebSocketKey, 0) {
		return true
	}

	for i := 0; i < 24; i++ {
		if totalAreaBetOnTable[i]+totalAreaBet[i] > gamesettingFS.Service.BetAreaLimit(secWebSocketKey, b.betAreaLimitIndex(uint32(i))) {
			return true
		}
	}

	return false
}

func (b *BetRound) betAreaLimitIndex(betType uint32) uint32 {
	switch {
	case betType < 3:
		return 1
	case betType < 18:
		return 2
	case betType < 24:
		return 3
	}
	return 0 //invalid
}

func (b *BetRound) destroy() {
	flux.UnRegister(b.uuid.String(), b.in)
}

//取得目前所有下注區域的下注
func (b *BetRound) getAllAreaBets() map[int32]map[uint32]map[uint32]uint32 {
	betsMap := make(map[int32]map[uint32]map[uint32]uint32) //<座位 ,<區域 , <籌碼索引,數量>>>

	for _, betCalls := range b.bets {
		for _, betCall := range betCalls {
			if betsMap[betCall.Seat] == nil {
				betsMap[betCall.Seat] = make(map[uint32]map[uint32]uint32)
			}
			if betsMap[betCall.Seat][betCall.BetType] == nil {
				betsMap[betCall.Seat][betCall.BetType] = make(map[uint32]uint32)
			}
			betsMap[betCall.Seat][betCall.BetType][betCall.BetIndex]++
		}
	}

	return betsMap
}
