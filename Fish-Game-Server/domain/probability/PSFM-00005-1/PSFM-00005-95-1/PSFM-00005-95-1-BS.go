package PSFM_00005_95_1

import (
	PSFM_00005_1 "fish-game-server/domain/probability/PSFM-00005-1"
	"fish-game-server/models"
	"path/filepath"
)

var bs = "domain/probability/PSFM-00005-1/PSFM-00005-95-1/PSFM-00005-95-1-BS.go"

var RTP95BS = &rtp95bs {
	MathInfo: PSFM_00005_1.MathInfo{
		Docker:   PSFM_00005_1.DOCKER,
		Test:     filepath.Dir(bs),
		Folder:   PSFM_00005_1.FOLDER + PSFM_00005_1.RTP95,
		File:     "PSFM-00005-95-1-BS.json",
		FileType: models.BS,
	},
}

type rtp95bs struct {
	PSFM_00005_1.MathInfo
}

func init() {
	RTP95BS.Deserialization()
}