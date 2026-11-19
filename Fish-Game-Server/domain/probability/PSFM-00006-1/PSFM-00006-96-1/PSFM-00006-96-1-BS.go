package PSFM_00006_96_1

import (
	PSFM_00006_1 "fish-game-server/domain/probability/PSFM-00006-1"
	"fish-game-server/models"
	"path/filepath"
)

var bs = "domain/probability/PSFM-00006-1/PSFM-00006-96-1/PSFM-00006-96-1-BS.go"

var RTP96BS = &rtp96bs{
	MathInfo: PSFM_00006_1.MathInfo{
		Docker:   PSFM_00006_1.DOCKER,
		Test:     filepath.Dir(bs),
		Folder:   PSFM_00006_1.FOLDER + PSFM_00006_1.RTP96,
		File:     "PSFM-00006-96-1-BS.json",
		FileType: models.BS,
	},
}

type rtp96bs struct {
	PSFM_00006_1.MathInfo
}

func init() {
	RTP96BS.Deserialization()
}