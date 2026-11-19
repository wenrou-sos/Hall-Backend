package PSFM_00003_98_1

import (
    PSFM_00003_1 "fish-game-server/domain/probability/PSFM-00003-1"
    "fish-game-server/models"
    "path/filepath"
)

var bs = "domain/probability/PSFM-00003-1/PSFM-00003-98-1/PSFM-00003-98-1-BS.go"

var RTP98BS = &rtp98bs{
    MathInfo: PSFM_00003_1.MathInfo{
        Docker:   PSFM_00003_1.DOCKER,
        Test:     filepath.Dir(bs),
        Folder:   PSFM_00003_1.FOLDER + PSFM_00003_1.RTP98,
        File:     "PSFM-00003-98-1-BS.json",
        FileType: models.BS,
    },
}

type rtp98bs struct {
    PSFM_00003_1.MathInfo
}

func init() {
    RTP98BS.Deserialization()
}