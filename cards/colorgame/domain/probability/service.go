package probability

import (
	"crypto/rand"
	"encoding/json"
	"math/big"
	"os"
	"path/filepath"
	"runtime"

	"gitlab.iplaystar.net/game-server/logger"
)

const (
	EMSGID_eResult          = "EMSGID_eResult"
	EMSGID_eBroadcastResult = "EMSGID_eBroadcastResult"
	EMSGID_eBroadcastDeal   = "EMSGID_eBroadcastDeal"
)

var (
	_, path, _, _ = runtime.Caller(0)
)

//控骰物件初始化
var ControllRiceService = &controllRiceService{
	isAllowControl: os.Getenv("ALLOW_CONTROL") == "true",
	jsonFile: jsonFile{
		Docker: "/data/math",
		test:   filepath.Dir(path),
		folder: "domain/probability",
		File:   "roll.json",
	},
	rollControl:  nil,
	controlCount: 0,
}

//控骰物件定義
type controllRiceService struct {
	isAllowControl bool //是否啟用控骰
	jsonFile       jsonFile
	rollControl    *rollControl //控骰
	controlCount   int          //控骰計數器
}

//賠率物件初始化
var CombServie = &combService{
	jsonFile: jsonFile{
		Docker: "/data/math",
		test:   filepath.Dir(path),
		folder: "domain/probability",
		File:   "comb.json",
	},
	combControl: nil,
}

//賠率物件定義
type combService struct {
	jsonFile    jsonFile
	combControl *combControl
}

//定義Json檔物件的一些基本位置
type jsonFile struct {
	Docker string
	test   string
	folder string
	File   string
}

//初始化
func init() {
	// if err := json.NewDecoder(getJsonFile(Service)).Decode(&Service.rollControl); err != nil {
	// 	panic(err)
	// }
}

//搖骰
func (s *controllRiceService) Roll() [3]int32 {
	result := [3]int32{0, 0, 0}

	if s.isAllowControl { //啟用控骰
		//每次都重讀json檔
		if err := json.NewDecoder(getJsonFile(&ControllRiceService.jsonFile)).Decode(&ControllRiceService.rollControl); err != nil {
			panic(err)
		}

		rollControl := s.rollControl.RollControl

		if len(rollControl) > 0 {

			setNums := len(rollControl)                          //組合總數量
			controlResult := rollControl[s.controlCount%setNums] //輪流出現
			s.controlCount++

			result[0] = int32(controlResult[0])
			result[1] = int32(controlResult[1])
			result[2] = int32(controlResult[2])

		} else {
			for i := 0; i < 3; i++ {
				randNum, _ := rand.Int(rand.Reader, big.NewInt(int64(6)))
				result[i] = int32(randNum.Int64())
			}
		}

	} else {
		for i := 0; i < 3; i++ {
			randNum, _ := rand.Int(rand.Reader, big.NewInt(int64(6)))
			result[i] = int32(randNum.Int64())
		}
	}

	return result
}

//取得賠率
func (s *combService) GetCombControl(jsonPath string) *combControl {

	//每次都重讀json檔
	CombServie.jsonFile.File = jsonPath
	
	if err := json.NewDecoder(getJsonFile(&CombServie.jsonFile)).Decode(&CombServie.combControl); err != nil {
		panic(err)
	}

	logger.Service.Zap.Infow("賠率參數",
		"combControl", CombServie.combControl,
	)

	return s.combControl
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
