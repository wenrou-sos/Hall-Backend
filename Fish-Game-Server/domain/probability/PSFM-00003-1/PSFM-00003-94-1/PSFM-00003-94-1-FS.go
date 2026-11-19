package PSFM_00003_94_1

import (
	PSFM_00003_1 "fish-game-server/domain/probability/PSFM-00003-1"
	"fish-game-server/models"
	"path/filepath"
)

var fs = "domain/probability/PSFM-00003-1/PSFM-00003-94-1/PSFM-00003-94-1-FS.go"

var RTP94FS = &rtp94fs{
	MathInfo: PSFM_00003_1.MathInfo{
		Docker:   PSFM_00003_1.DOCKER,
		Test:     filepath.Dir(fs),
		Folder:   PSFM_00003_1.FOLDER + PSFM_00003_1.RTP94,
		File:     "PSFM-00003-94-1-FS.json",
		FileType: models.FS,
	},
}

type rtp94fs struct {
	PSFM_00003_1.MathInfo
}

func init() {
	RTP94FS.Deserialization()
}