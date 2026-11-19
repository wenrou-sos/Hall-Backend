package PSFM_00003_93_1

import (
	PSFM_00003_1 "fish-game-server/domain/probability/PSFM-00003-1"
	"fish-game-server/models"
	"path/filepath"
)

var bs = "domain/probability/PSFM-00003-1/PSFM-00003-93-1/PSFM-00003-93-1-BS.go"

var RTP93BS = &rtp93bs{
	MathInfo: PSFM_00003_1.MathInfo{
		Docker:                PSFM_00003_1.DOCKER,
		Test:                  filepath.Dir(bs),
		Folder:                PSFM_00003_1.FOLDER + PSFM_00003_1.RTP93,
		File:                  "PSFM-00003-93-1-BS.json",
		PSF_ON_00002_1_BsMath: nil,
		FileType:              models.BS,
	},
}

type rtp93bs struct {
	PSFM_00003_1.MathInfo
}

func init() {
	RTP93BS.Deserialization()
}