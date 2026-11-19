package PSFM_00004_96_1

import (
	PSFM_00004_1 "fish-game-server/domain/probability/PSFM-00004-1"
	"fish-game-server/models"
	"path/filepath"
)

var bs = "domain/probability/PSFM-00004-1/PSFM-00004-96-1/PSFM-00004-96-1-BS.go"

var RTP96BS = &rtp96bs{
	MathInfo: PSFM_00004_1.MathInfo{
		Docker:   PSFM_00004_1.DOCKER,
		Test:     filepath.Dir(bs),
		Folder:   PSFM_00004_1.FOLDER + PSFM_00004_1.RTP96,
		File:     "PSFM-00004-96-1-BS.json",
		FileType: models.BS,
	},
}

type rtp96bs struct {
	PSFM_00004_1.MathInfo
}

func init() {
	RTP96BS.Deserialization()
}