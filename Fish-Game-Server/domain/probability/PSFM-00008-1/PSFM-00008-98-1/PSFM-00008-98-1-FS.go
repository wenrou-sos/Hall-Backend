package PSFM_00008_98_1

import (
	PSFM_00008_1 "fish-game-server/domain/probability/PSFM-00008-1"
	"fish-game-server/models"
	"path/filepath"
)

var fs = "domain/probability/PSFM-00008-1/PSFM-00008-98-1/PSFM-00008-98-1-FS.go"

var RTP98FS = &rtp98fs{
	MathInfo: PSFM_00008_1.MathInfo{
		Docker:  PSFM_00008_1.DOCKER,
		Test:    filepath.Dir(fs),
		Folder:  PSFM_00008_1.FOLDER + PSFM_00008_1.RTP98,
		File:    "PSFM-00008-98-1-FS.json",
		FileType: models.FS,
	},
}

type rtp98fs struct {
	PSFM_00008_1.MathInfo
}

func init() {
	RTP98FS.Deserialization()
}