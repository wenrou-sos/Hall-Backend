package PSFM_00007_98_1

import (
	PSFM_00007_1 "fish-game-server/domain/probability/PSFM-00007-1"
	"fish-game-server/models"
	"path/filepath"
)

var drb = "domain/probability/PSFM-00007-1/PSFM-00007-98-1/PSFM-00007-98-1-DRB.go"

var RTP98DRB = &rtp98drb{
	MathInfo: PSFM_00007_1.MathInfo{
		Docker:   PSFM_00007_1.DOCKER,
		Test:     filepath.Dir(drb),
		Folder:   PSFM_00007_1.FOLDER + PSFM_00007_1.RTP98,
		File:     "PSFM-00007-98-1-DRB.json",
		FileType: models.DRB,
	},
}

type rtp98drb struct {
	PSFM_00007_1.MathInfo
}

func init() {
	RTP98DRB.Deserialization()
}
