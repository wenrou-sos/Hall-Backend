package PSF_ON_00007

import (
	"fish-game-server/domain/file"
)

var ScriptC1 = &scriptC1{
	ScriptInfo: file.ScriptInfo{
		Model:  make(map[string]interface{}),
		FileInfo: file.FileInfo{
			Docker: "/data/script",
			Folder: "domain/fish/PSF-ON-00007",
			File:   "PSF-ON-00007-Scripts-C1.json",
		},
	},
}

type scriptC1 struct {
	file.ScriptInfo
}

func init() {
	ScriptC1.ScriptInfo.Deserialization()
}
