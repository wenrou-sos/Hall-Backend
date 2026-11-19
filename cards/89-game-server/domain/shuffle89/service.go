package shuffle89

import (
    "encoding/json"
    "os"
    "path/filepath"
    "runtime"
)

var (
    _, path, _, _ = runtime.Caller(0)
)

var Service = &service{
    isAllowControl: os.Getenv("ALLOW_CONTROL") == "true",
    Docker:         "/data/math",
    test:           filepath.Dir(path),
    folder:         "domain/shuffle89",
    File:           "shuffle89.json",
    shuffle89:      nil,
}

type service struct {
    isAllowControl bool
    Docker         string
    test           string
    folder         string
    File           string
    shuffle89      *shuffle89
}

func init() {
    if Service.isAllowControl {
        Service.deserialization()
    }
}

func (s *service) deserialization() {
    if err := json.NewDecoder(s.open()).Decode(&s.shuffle89); err != nil {
        panic(err)
    }
}

func (s *service) open() *os.File {
    var file *os.File
    var err error

    defer file.Close()

    if file, err = os.Open(filepath.Join(s.Docker, s.File)); err != nil {
        if file, err = os.Open(filepath.Join(s.folder, s.File)); err != nil {
            if file, err = os.Open(s.File); err != nil {
                if file, err = os.Open(filepath.Join(s.test, s.File)); err != nil {
                    panic(err.Error())
                }
            }
        }
    }
    return file
}

func (s *service) Reload() {
    if s.isAllowControl {
        s.shuffle89 = nil
        s.deserialization()
    }
}

func (s *service) Shuffle52Handler(card52 []int) []int {
    if !s.isAllowControl {
        return card52
    }

    if len(s.shuffle89.Seat0) == 3 {
        card52[0] = s.shuffle89.Seat0[0]
        card52[1] = s.shuffle89.Seat0[1]
        card52[2] = s.shuffle89.Seat0[2]
    }

    if len(s.shuffle89.Seat1) == 3 {
        card52[3] = s.shuffle89.Seat1[0]
        card52[4] = s.shuffle89.Seat1[1]
        card52[5] = s.shuffle89.Seat1[2]
    }

    if len(s.shuffle89.Seat2) == 3 {
        card52[6] = s.shuffle89.Seat2[0]
        card52[7] = s.shuffle89.Seat2[1]
        card52[8] = s.shuffle89.Seat2[2]
    }

    if len(s.shuffle89.Seat3) == 3 {
        card52[9] = s.shuffle89.Seat3[0]
        card52[10] = s.shuffle89.Seat3[1]
        card52[11] = s.shuffle89.Seat3[2]
    }

    if len(s.shuffle89.Seat4) == 3 {
        card52[12] = s.shuffle89.Seat4[0]
        card52[13] = s.shuffle89.Seat4[1]
        card52[14] = s.shuffle89.Seat4[2]
    }

    if len(s.shuffle89.Banker) == 3 {
        card52[15] = s.shuffle89.Banker[0]
        card52[16] = s.shuffle89.Banker[1]
        card52[17] = s.shuffle89.Banker[2]
    }
    return card52
}

func (s *service) Shuffle54Handler(card54 []int) []int {
    return card54
}
