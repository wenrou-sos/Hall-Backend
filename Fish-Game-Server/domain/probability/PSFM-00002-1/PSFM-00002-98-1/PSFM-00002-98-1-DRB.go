package PSFM_00002_98_1

import (
    PSFM_00002_1 "fish-game-server/domain/probability/PSFM-00002-1"
    "fish-game-server/models"
    "path/filepath"
)

var drb = "domain/probability/PSFM-00002-1/PSFM-00002-98-1/PSFM-00002-98-1-DRB.go"

var RTP98DRB = &rtp98drb{
    MathInfo: PSFM_00002_1.MathInfo{
        Docker:   PSFM_00002_1.DOCKER,
        Test:     filepath.Dir(drb),
        Folder:   PSFM_00002_1.FOLDER + PSFM_00002_1.RTP98,
        File:     "PSFM-00002-98-1-DRB.json",
        FileType: models.DRB,
    },
}

type rtp98drb struct {
    PSFM_00002_1.MathInfo
}

func init() {
    RTP98DRB.Deserialization()
}
