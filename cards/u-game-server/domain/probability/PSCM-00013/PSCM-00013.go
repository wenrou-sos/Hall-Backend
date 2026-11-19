package PSCM_00013

import (
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
	PSC_ON_00013 "u-game-server/domain/probability/PSC-ON-00013"
)

var (
	_, path, _, _ = runtime.Caller(0)
)

var MathU = &mathU{
	Docker: "/data/math",
	test:   filepath.Dir(path),
	folder: "domain/probability/PSCM-00013",
	File:   "PSCM-00013.json",
}

type mathU struct {
	Docker         string
	test           string
	folder         string
	File           string
	PSC_ON_00013   *PSC_ON_00013.MathU
}

func init() {
	MathU.deserialization()
}

func (m *mathU) deserialization() {
	if err := json.NewDecoder(m.open()).Decode(&m.PSC_ON_00013); err != nil {
		panic(err)
	}
}

func (m *mathU) open() *os.File {
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

func (m *mathU) Reload() {
	m.PSC_ON_00013 = nil
	m.deserialization()
}
