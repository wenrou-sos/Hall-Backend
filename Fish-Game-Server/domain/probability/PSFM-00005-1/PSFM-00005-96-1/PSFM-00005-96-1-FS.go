package PSFM_00005_96_1

import (
	PSFM_00005_1 "fish-game-server/domain/probability/PSFM-00005-1"
	"fish-game-server/models"
	"path/filepath"
)

var fs = "domain/probability/PSFM-00005-1/PSFM-00005-96-1/PSFM-00005-96-1-FS.go"

var RTP96FS = &rtp96fs{
	MathInfo: PSFM_00005_1.MathInfo{
		Docker:   PSFM_00005_1.DOCKER,
		Test:     filepath.Dir(fs),
		Folder:   PSFM_00005_1.FOLDER + PSFM_00005_1.RTP96,
		File:     "PSFM-00005-96-1-FS.json",
		FileType: models.FS,
	},
}

type rtp96fs struct {
	PSFM_00005_1.MathInfo
}

func init() {
	RTP96FS.Deserialization()
}