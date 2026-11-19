package PSFM_00005_96_1

import (
	PSFM_00005_1 "fish-game-server/domain/probability/PSFM-00005-1"
	"fish-game-server/models"
	"path/filepath"
)

var drb = "domain/probability/PSFM-00005-1/PSFM-00005-96-1/PSFM-00005-96-1-DRB.go"

var RTP96DRB = &rtp96drb{
	MathInfo: PSFM_00005_1.MathInfo{
		Docker:   PSFM_00005_1.DOCKER,
		Test:     filepath.Dir(drb),
		Folder:   PSFM_00005_1.FOLDER + PSFM_00005_1.RTP96,
		File:     "PSFM-00005-96-1-DRB.json",
		FileType: models.DRB,
	},
}

type rtp96drb struct {
	PSFM_00005_1.MathInfo
}

func init() {
	RTP96DRB.Deserialization()
}