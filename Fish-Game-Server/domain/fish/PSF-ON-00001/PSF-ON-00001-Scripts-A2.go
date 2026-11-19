package PSF_ON_00001

import (
    "fish-game-server/domain/file"
)

var ScriptA2 = &scriptA2{
    ScriptInfo: file.ScriptInfo{
        Model:  make(map[string]interface{}),
        FileInfo: file.FileInfo{
            Docker: "/data/script",
            Folder: "domain/fish/PSF-ON-00001",
            File:   "PSF-ON-00001-Scripts-A2.json",
        },
    },
}

type scriptA2 struct {
    file.ScriptInfo
}

func init() {
    ScriptA2.ScriptInfo.Deserialization()
}