package PSFM_00002_96_1

import (
    PSFM_00002_1 "fish-game-server/domain/probability/PSFM-00002-1"
    "fish-game-server/models"
    "path/filepath"
)

var bs = "domain/probability/PSFM-00002-1/PSFM-00002-96-1/PSFM-00002-96-1-BS.go"

var RTP96BS = &rtp96bs{
    MathInfo: PSFM_00002_1.MathInfo{
        Docker:   PSFM_00002_1.DOCKER,
        Test:     filepath.Dir(bs),
        Folder:   PSFM_00002_1.FOLDER + PSFM_00002_1.RTP96,
        File:     "PSFM-00002-96-1-BS.json",
        FileType: models.BS,
    },
}

type rtp96bs struct {
    PSFM_00002_1.MathInfo
}

func init() {
    RTP96BS.Deserialization()
}