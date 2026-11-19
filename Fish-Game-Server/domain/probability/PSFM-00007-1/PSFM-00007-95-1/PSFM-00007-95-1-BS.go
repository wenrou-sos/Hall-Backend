package PSFM_00007_95_1

import (
	PSFM_00007_1 "fish-game-server/domain/probability/PSFM-00007-1"
	"fish-game-server/models"
	"path/filepath"
)

var bs = "domain/probability/PSFM-00007-1/PSFM-00007-95-1/PSFM-00007-95-1-BS.go"

var RTP95BS = &rtp95bs{
	MathInfo: PSFM_00007_1.MathInfo{
		Docker:   PSFM_00007_1.DOCKER,
		Test:     filepath.Dir(bs),
		Folder:   PSFM_00007_1.FOLDER + PSFM_00007_1.RTP95,
		File:     "PSFM-00007-95-1-BS.json",
		FileType: models.BS,
	},
}

type rtp95bs struct {
	PSFM_00007_1.MathInfo
}

func init() {
	RTP95BS.Deserialization()
}
