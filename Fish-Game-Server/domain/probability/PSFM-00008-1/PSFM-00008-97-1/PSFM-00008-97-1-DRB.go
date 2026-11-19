package PSFM_00008_97_1

import (
	PSFM_00008_1 "fish-game-server/domain/probability/PSFM-00008-1"
	"fish-game-server/models"
	"path/filepath"
)

var drb = "domain/probability/PSFM-00008-1/PSFM-00008-97-1/PSFM-00008-97-1-DRB.go"

var RTP97DRB = &rtp97drb{
	MathInfo: PSFM_00008_1.MathInfo{
		Docker:   PSFM_00008_1.DOCKER,
		Test:     filepath.Dir(drb),
		Folder:   PSFM_00008_1.FOLDER + PSFM_00008_1.RTP97,
		File:     "PSFM-00008-97-1-DRB.json",
		FileType: models.DRB,
	},
}

type rtp97drb struct {
	PSFM_00008_1.MathInfo
}

func init() {
	RTP97DRB.Deserialization()
}