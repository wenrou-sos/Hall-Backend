package PSFM_00003_95_1

import (
    PSFM_00003_1 "fish-game-server/domain/probability/PSFM-00003-1"
    "fish-game-server/models"
    "path/filepath"
)

var fs = "domain/probability/PSFM-00003-1/PSFM-00003-95-1/PSFM-00003-95-1-FS.go"

var RTP95FS = &rtp95fs{
    MathInfo: PSFM_00003_1.MathInfo{
        Docker:   PSFM_00003_1.DOCKER,
        Test:     filepath.Dir(fs),
        Folder:   PSFM_00003_1.FOLDER + PSFM_00003_1.RTP95,
        File:     "PSFM-00003-95-1-FS.json",
        FileType: models.FS,
    },
}

type rtp95fs struct {
    PSFM_00003_1.MathInfo
}

func init() {
    RTP95FS.Deserialization()
}