package probability

import (
	"crypto/rand"
	"encoding/json"
	"math/big"
	"os"
	"path/filepath"
	"runtime"
)

const (
	EMSGID_eResult          = "EMSGID_eResult"
	EMSGID_eBroadcastResult = "EMSGID_eBroadcastResult"
	EMSGID_eBroadcastDeal   = "EMSGID_eBroadcastDeal"
)

var (
	_, path, _, _ = runtime.Caller(0)
)

var Service = &service{
	isAllowControl: os.Getenv("ALLOW_CONTROL") == "true",
	Docker:         "/data/math",
	test:           filepath.Dir(path),
	folder:         "domain/probability",
	File:           "roll.json",
	rollControl:    nil,
	controlCount:   0,
}

type service struct {
	isAllowControl bool //是否啟用控骰
	Docker         string
	test           string
	folder         string
	File           string
	rollControl    *rollControl //控骰
	controlCount   int          //控骰計數器
}

//初始化
func init() {
	// if err := json.NewDecoder(getJsonFile(Service)).Decode(&Service.rollControl); err != nil {
	// 	panic(err)
	// }
}

//搖骰
func (s *service) Roll() [3]int32 {

	result := [3]int32{0, 0, 0}

	if s.isAllowControl { //啟用控骰
		//每次開骰都重讀json檔
		if err := json.NewDecoder(getJsonFile(Service)).Decode(&Service.rollControl); err == nil {
			rollControl := s.rollControl.RollControl
			if len(rollControl) > 0 {
				setNums := len(rollControl)                          //組合總數量
				controlResult := rollControl[s.controlCount%setNums] //輪流出現
				s.controlCount++

				result[0] = int32(controlResult[0])
				result[1] = int32(controlResult[1])
				result[2] = int32(controlResult[2])
				return result
			}
		} else {
			panic(err.Error())
		}

	}

	for i := 0; i < 3; i++ {
		randNum, _ := rand.Int(rand.Reader, big.NewInt(int64(6)))
		result[i] = int32(randNum.Int64())
	}

	return result
}

//打開json檔
func getJsonFile(s *service) *os.File {
	var file *os.File
	var err error

	defer file.Close()

	if file, err = os.Open(filepath.Join(s.Docker, s.File)); err != nil {
		if file, err = os.Open(filepath.Join(s.folder, s.File)); err != nil {
			if file, err = os.Open(s.File); err != nil {
				if file, err = os.Open(filepath.Join(s.test, s.File)); err != nil {
					panic(err.Error())
				}
			}
		}
	}

	return file

}
