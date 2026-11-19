package PSFM_00004_95_1

import (
	PSFM_00004_1 "fish-game-server/domain/probability/PSFM-00004-1"
	"fish-game-server/models"
	"path/filepath"
)

var drb = "domain/probability/PSFM-00004-1/PSFM-00004-95-1/PSFM-00004-95-1-DRB.go"

var RTP95DRB = &rtp95drb{
	MathInfo: PSFM_00004_1.MathInfo{
		Docker:   PSFM_00004_1.DOCKER,
		Test:     filepath.Dir(drb),
		Folder:   PSFM_00004_1.FOLDER + PSFM_00004_1.RTP95,
		File:     "PSFM-00004-95-1-DRB.json",
		FileType: models.DRB,
	},
}

type rtp95drb struct {
	PSFM_00004_1.MathInfo
}

func init() {
	RTP95DRB.Deserialization()
}