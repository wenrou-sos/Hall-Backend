package PSFM_00013_93_1

import (
	PSFM_00013_1 "fish-game-server/domain/probability/PSFM-00013-1"
	"fish-game-server/models"
	"path/filepath"
)

var drb = "domain/probability/PSFM-00013-1/PSFM-00013-93-1/PSFM-00013-93-1-DRB.go"

var RTP93DRB = &rtp93drb{
	MathInfo: PSFM_00013_1.MathInfo{
		Docker:   PSFM_00013_1.DOCKER,
		Test:     filepath.Dir(drb),
		Folder:   PSFM_00013_1.FOLDER + PSFM_00013_1.RTP93,
		File:     "PSFM-00013-93-1-DRB.json",
		FileType: models.DRB,
	},
}

type rtp93drb struct {
	PSFM_00013_1.MathInfo
}

func init() {
	RTP93DRB.Deserialization()
}