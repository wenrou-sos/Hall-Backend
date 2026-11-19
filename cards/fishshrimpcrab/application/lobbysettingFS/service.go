package lobbysettingFS

import (
	lobby_settingFS_proto "fish-shrimp-crab-game-server/application/lobbysettingFS/proto"
	"strconv"
	"strings"
	"sync"

	"github.com/gogo/protobuf/proto"
	"gitlab.iplaystar.net/game-server/auth"
	common_proto "gitlab.iplaystar.net/game-server/common/proto"
	errorcode "gitlab.iplaystar.net/game-server/error-code"
	lobbysetting "gitlab.iplaystar.net/game-server/lobby-setting"
	lobby_setting_proto "gitlab.iplaystar.net/game-server/lobby-setting/proto"
	"gitlab.iplaystar.net/game-server/logger"
	"gitlab.iplaystar.net/game-server/session"
	sessionmanager "gitlab.iplaystar.net/game-server/session-manager"
	"gitlab.iplaystar.net/game-server/wallet"
)

var Service = &service{
	Id:             "LobbySettingFSService",
	allHostFSGames: make(map[string]*HostFSGame),
	rwMutex:        &sync.RWMutex{},
}

type service struct {
	Id             string
	allHostFSGames map[string]*HostFSGame
	rwMutex        *sync.RWMutex
}

func (s *service) EMSGID_eLobbyConfigCallHandler(memberId string, guestEnable int, ls *lobbysetting.LobbySetting, cc *lobby_setting_proto.ConfigCall) {
	s.rwMutex.Lock()
	s.allHostFSGames[ls.SecWebSocketKey] = ls.AvailableGames[cc.GameId].(*HostFSGame)

	s.rwMutex.Unlock()

	session.Service.New(
		ls.SecWebSocketKey,
		ls.HostExtId,
		ls.AvailableGames[cc.GameId].(*HostFSGame).HostId,
		memberId,
		cc.GameId,
		cc.SubgameId,
		ls.RemoteAddr,
		ls.UserAgent,
		cc.Version,
		cc.GameVersion,
	)

	if guestEnable == 0 {
		sessionmanager.Service.Start(
			ls.SecWebSocketKey,
			ls.HostExtId,
			ls.AvailableGames[cc.GameId].(*HostFSGame).HostId,
			memberId,
			cc.GameId,
		)
	}

}

func (s *service) EMSGID_eLobbyConfigRecallHandler(ls *lobbysetting.LobbySetting, isTokenValid bool) []byte {
	data := &lobby_settingFS_proto.ConfigRecall{
		Msgid: common_proto.EMSGID_eLobbyConfigRecall,
	}

	if !isTokenValid {
		s.cleanData(ls.SecWebSocketKey, auth.Auth_TOKEN_EXPIRED)
		data.StatusCode = common_proto.Status_kInvalid
		dataByte, _ := proto.Marshal(data)
		return dataByte
	}

	if !wallet.Service.Existed(ls.SecWebSocketKey) {
		s.cleanData(ls.SecWebSocketKey, wallet.Wallet_NOT_FOUND)
		data.StatusCode = common_proto.Status_kInvalid
		dataByte, _ := proto.Marshal(data)
		return dataByte
	}

	go session.Service.Start(ls.SecWebSocketKey)

	data.StatusCode = common_proto.Status_kSuccess

	for i, v := range ls.AvailableGames {

		if i == s.GameId(ls.SecWebSocketKey) {
			game := v.(*HostFSGame)

			for _, rate := range strings.Split(game.RateList, ",") {
				atoiRate, _ := strconv.Atoi(rate)

				r := &lobby_settingFS_proto.ConfigRecall_RoomInfo{
					GameId:                game.GameId,
					Rates:                 []uint32{uint32(atoiRate)},
					Line:                  []uint32{1},
					LanguagesDefaultIndex: 0,
				}

				data.RoomInfo = append(data.RoomInfo, s.parseGameSetting(game, r))
			}
		}
	}

	dataByte, _ := proto.Marshal(data)
	return dataByte
}

func (s *service) parseGameSetting(game *HostFSGame, r *lobby_settingFS_proto.ConfigRecall_RoomInfo) *lobby_settingFS_proto.ConfigRecall_RoomInfo {
	data := &lobby_settingFS_proto.ConfigRecall_Bets{}

	for _, bet := range strings.Split(game.BetList, ",") {
		atoiBet, _ := strconv.Atoi(bet)
		data.Bet = append(data.Bet, uint32(atoiBet))
	}

	r.Levels = append(r.Levels, data)

	for _, v := range strings.Split(game.Langs, ",") {
		r.Languages = append(r.Languages, v)
	}

	return r
}

func (s *service) cleanData(secWebSocketKey, errorCode string) {
	logger.Service.Zap.Errorw(errorCode,
		"GameUser", secWebSocketKey,
	)
	errorcode.Service.Fatal(secWebSocketKey, errorCode)
}

func (s *service) GameId(secWebSocketKey string) string {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allHostFSGames[secWebSocketKey]; ok {
		return v.GameId
	}

	logger.Service.Zap.Errorw(LobbySettingFS_GAME_ID_NOT_FOUND,
		"GameUser", secWebSocketKey)

	errorcode.Service.Fatal(secWebSocketKey, LobbySettingFS_GAME_ID_NOT_FOUND)
	return ""
}

//取得抽水比例
func (s *service) Fee(secWebSocketKey string) (fee uint32) {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allHostFSGames[secWebSocketKey]; ok {
		return v.Fee
	}
	return 0
}

//取得有幾個房間
func (s *service) GetRoomNum(secWebSocketKey string) int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allHostFSGames[secWebSocketKey]; ok {
		return v.GetRoomNum()
	}

	return 0
}

//取得每間幾個機器人
func (s *service) GetBotNumPerRoom(secWebSocketKey string) int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allHostFSGames[secWebSocketKey]; ok {
		return v.GetBotNumPerRoom()
	}

	return 0
}

//取得機器人補房的人數數量條件
func (s *service) GetFillRoomMinPlayerNum(secWebSocketKey string) int {
	s.rwMutex.RLock()
	defer s.rwMutex.RUnlock()

	if v, ok := s.allHostFSGames[secWebSocketKey]; ok {
		return v.GetFillRoomMinPlayerNum()
	}

	return 0
}
