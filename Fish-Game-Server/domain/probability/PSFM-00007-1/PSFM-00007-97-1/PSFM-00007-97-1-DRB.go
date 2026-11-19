package PSFM_00007_97_1

import (
	PSFM_00007_1 "fish-game-server/domain/probability/PSFM-00007-1"
	"fish-game-server/models"
	"path/filepath"
)

var drb = "domain/probability/PSFM-00007-1/PSFM-00007-97-1/PSFM-00007-97-1-DRB.go"

var RTP97DRB = &rtp97drb{
	MathInfo: PSFM_00007_1.MathInfo{
		Docker:   PSFM_00007_1.DOCKER,
		Test:     filepath.Dir(drb),
		Folder:   PSFM_00007_1.FOLDER + PSFM_00007_1.RTP97,
		File:     "PSFM-00007-97-1-DRB.json",
		FileType: models.DRB,
	},
}

type rtp97drb struct {
	PSFM_00007_1.MathInfo
}

func init() {
	RTP97DRB.Deserialization()
}
