package botuser

import (
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
	"runtime/debug"
	"strconv"
	"strings"
	"sync"

	"gitlab.iplaystar.net/game-server/common"
	"gitlab.iplaystar.net/game-server/flux"
	"gitlab.iplaystar.net/game-server/logger"
)

const (
	ActionBotUserCreate = "ActionBotUserCreate"
)

var (
	_, path, _, _ = runtime.Caller(0)
)

var Service = &service{
	Id:       "BotUserService",
	poolSize: os.Getenv("POOL_SIZE"),
	in:       make(chan *flux.Action, common.Service.ChanSize),
	rwMutex:  sync.RWMutex{},
}

type service struct {
	Id       string
	poolSize string
	in       chan *flux.Action
	rwMutex  sync.RWMutex
}

//定義Json檔物件的一些基本位置
type jsonFile struct {
	Docker string
	test   string
	folder string
	File   string
}

//機器人Id初始化
var RobotIdServie = &robotIdService{
	jsonFile: jsonFile{
		Docker: "/data/math",
		test:   filepath.Dir(path),
		folder: "application/botuser",
		File:   "robotId.json",
	},
	robotIds: nil,
}

//賠率物件定義
type robotIdService struct {
	jsonFile jsonFile
	robotIds []string
}

func init() {
	Service.run()

	//機器人ID列表初始化
	if err := json.NewDecoder(getJsonFile(&RobotIdServie.jsonFile)).Decode(&RobotIdServie.robotIds); err != nil {
		panic(err)
	}
}

func (s *service) run() {
	flux.Register(s.Id, s.in)
	allBotUsers := make(map[string]*botUser)

	poolSize := 10

	if s.poolSize != "" {
		if poolSize, _ = strconv.Atoi(s.poolSize); poolSize == 0 {
			poolSize = 10
		}
	}

	for i := 0; i < poolSize; i++ {
		go func() {
			for action := range s.in {
				s.handleAction(action, allBotUsers)
			}
		}()
	}
}

func (s *service) handleAction(action *flux.Action, allBotUsers map[string]*botUser) {
	defer func() {
		if err := recover(); err != nil {
			logger.Service.Zap.Fatalw("999",
				"err", err,
				"stacktrace", string(debug.Stack()),
			)
		}
	}()

	if action.Key().To() != s.Id {
		return
	}

	logger.Service.Zap.Infow(action.Key().Name(),
		"GameUser", action.Key().From(),
	)

	s.rwMutex.Lock()
	defer s.rwMutex.Unlock()

	switch action.Key().Name() {
	case ActionBotUserCreate:
		from := action.Key().From()
		gameRoomUuid := action.Payload()[0].(string)
		rate := action.Payload()[1].(uint32)
		rateIndex := action.Payload()[2].(int)
		betRoundUuid := action.Payload()[3].(string)
		betListStr := action.Payload()[4].(string)
		betListArr := strings.Split(betListStr, ",")

		b := Builder().
			setFrom(from).
			setBetRoundUuid(betRoundUuid).
			setGameRoomUuid(gameRoomUuid).
			setRate(rate).
			setRateIndex(rateIndex).
			setBetList(betListArr).
			build()

		allBotUsers[b.uuid] = b

	case actionDestroy:
		uuid := action.Key().From()

		delete(allBotUsers, uuid)

	}
}

func (s *service) Destroy() {
	flux.UnRegister(s.Id, s.in)
}

//打開json檔
func getJsonFile(s *jsonFile) *os.File {
	var file *os.File
	var err error

	defer file.Close()

	if file, err = os.Open(filepath.Join(s.Docker, s.File)); err != nil {
		if file, err = os.Open(filepath.Join(s.folder, s.File)); err != nil {
			if file, err = os.Open(s.File); err != nil {
				panic(err.Error())
			}
		}
	}

	return file

}
