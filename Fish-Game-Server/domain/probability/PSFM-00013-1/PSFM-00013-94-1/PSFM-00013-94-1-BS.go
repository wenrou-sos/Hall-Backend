package PSFM_00013_94_1

import (
	PSFM_00013_1 "fish-game-server/domain/probability/PSFM-00013-1"
	"fish-game-server/models"
	"path/filepath"
)

var bs = "domain/probability/PSFM-00013-1/PSFM-00013-94-1/PSFM-00013-94-1-BS.go"

var RTP94BS = &rtp94bs{
	MathInfo: PSFM_00013_1.MathInfo{
		Docker:   PSFM_00013_1.DOCKER,
		Test:     filepath.Dir(bs),
		Folder:   PSFM_00013_1.FOLDER + PSFM_00013_1.RTP94,
		File:     "PSFM-00013-94-1-BS.json",
		FileType: models.BS,
	},
}

type rtp94bs struct {
	PSFM_00013_1.MathInfo
}

func init() {
	RTP94BS.Deserialization()
}