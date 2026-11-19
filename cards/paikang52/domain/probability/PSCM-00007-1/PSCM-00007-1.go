package PSCM_00007_1

import (
	PSC_ON_00007_1 "52-game-server/domain/probability/PSC-ON-00007-1"
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
)

var (
	_, path, _, _ = runtime.Caller(0)
)

var Math52 = &math52{
	Docker: "/data/math",
	test:   filepath.Dir(path),
	folder: "domain/probability/PSCM-00007-1",
	File:   "PSCM-00007-1.json",
}

type math52 struct {
	Docker         string
	test           string
	folder         string
	File           string
	PSC_ON_00007_1 *PSC_ON_00007_1.Math52
}

func init() {
	Math52.deserialization()
}

func (m *math52) deserialization() {
	if err := json.NewDecoder(m.open()).Decode(&m.PSC_ON_00007_1); err != nil {
		panic(err)
	}
}

func (m *math52) open() *os.File {
	var file *os.File
	var err error

	defer file.Close()

	if file, err = os.Open(filepath.Join(m.Docker, m.File)); err != nil {
		if file, err = os.Open(filepath.Join(m.folder, m.File)); err != nil {
			if file, err = os.Open(m.File); err != nil {
				if file, err = os.Open(filepath.Join(m.test, m.File)); err != nil {
					panic(err.Error())
				}
			}
		}
	}
	return file
}

func (m *math52) Reload() {
	m.PSC_ON_00007_1 = nil
	m.deserialization()
}
