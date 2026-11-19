package PSFM_00013_93_1

import (
	PSFM_00013_1 "fish-game-server/domain/probability/PSFM-00013-1"
	"fish-game-server/models"
	"path/filepath"
)

var bs = "domain/probability/PSFM-00013-1/PSFM-00013-93-1/PSFM-00013-93-1-BS.go"

var RTP93BS = &rtp93bs{
	MathInfo: 	  PSFM_00013_1.MathInfo{
		Docker:   PSFM_00013_1.DOCKER,
		Test: 	  filepath.Dir(bs),
		Folder:   PSFM_00013_1.FOLDER + PSFM_00013_1.RTP93,
		File: 	  "PSFM-00013-93-1-BS.json",
		FileType: models.BS,
	},
}

type rtp93bs struct {
	PSFM_00013_1.MathInfo
}

func init() {
	RTP93BS.Deserialization()
}