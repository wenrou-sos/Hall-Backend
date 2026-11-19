package PSFM_00003_94_1

import (
	PSFM_00003_1 "fish-game-server/domain/probability/PSFM-00003-1"
	"fish-game-server/models"
	"path/filepath"
)

var drb = "domain/probability/PSFM-00003-1/PSFM-00003-94-1/PSFM-00003-94-1-DRB.go"

var RTP94DRB = &rtp94drb{
	MathInfo:PSFM_00003_1.MathInfo{
		Docker:   PSFM_00003_1.DOCKER,
		Test:     filepath.Dir(drb),
		Folder:   PSFM_00003_1.FOLDER + PSFM_00003_1.RTP94,
		File:     "PSFM-00003-94-1-DRB.json",
		FileType: models.DRB,
	},
}

type rtp94drb struct {
	PSFM_00003_1.MathInfo
}

func init() {
	RTP94DRB.Deserialization()
}