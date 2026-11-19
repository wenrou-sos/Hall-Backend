package PSFM_00002_97_1

import (
    PSFM_00002_1 "fish-game-server/domain/probability/PSFM-00002-1"
    "fish-game-server/models"
    "path/filepath"
)

var fs = "domain/probability/PSFM-00002-1/PSFM-00002-97-1/PSFM-00002-97-1-FS.go"

var RTP97FS = &rtp97fs{
    MathInfo: PSFM_00002_1.MathInfo{
        Docker:   PSFM_00002_1.DOCKER,
        Test:     filepath.Dir(fs),
        Folder:   PSFM_00002_1.FOLDER + PSFM_00002_1.RTP97,
        File:     "PSFM-00002-97-1-FS.json",
        FileType: models.FS,
    },
}

type rtp97fs struct {
    PSFM_00002_1.MathInfo
}

func init() {
    RTP97FS.Deserialization()
}
