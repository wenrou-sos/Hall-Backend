package PSFM_00007_96_1

import (
	PSFM_00007_1 "fish-game-server/domain/probability/PSFM-00007-1"
	"fish-game-server/models"
	"path/filepath"
)

var bs = "domain/probability/PSFM-00007-1/PSFM-00007-96-1/PSFM-00007-96-1-BS.go"

var RTP96BS = &rtp96bs{
	MathInfo: PSFM_00007_1.MathInfo{
		Docker:   PSFM_00007_1.DOCKER,
		Test:     filepath.Dir(bs),
		Folder:   PSFM_00007_1.FOLDER + PSFM_00007_1.RTP96,
		File:     "PSFM-00007-96-1-BS.json",
		FileType: models.BS,
	},
}

type rtp96bs struct {
	PSFM_00007_1.MathInfo
}

func init() {
	RTP96BS.Deserialization()
}
