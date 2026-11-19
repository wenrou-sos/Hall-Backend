package shuffle52

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
	folder:         "domain/shuffle52",
	File:           "shuffle52.json",
	shuffle52:      nil,
}

type service struct {
	isAllowControl bool
	Docker         string
	test           string
	folder         string
	File           string
	shuffle52      *shuffle52
}

func init() {
	if Service.isAllowControl {
		Service.deserialization()
	}
}

func (s *service) deserialization() {
	if err := json.NewDecoder(s.open()).Decode(&s.shuffle52); err != nil {
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
		s.shuffle52 = nil
		s.deserialization()
	}
}

func (s *service) Shuffle52Handler(card52 []int) []int {
	if !s.isAllowControl {
		return card52
	}

	index := 0

	if len(s.shuffle52.Seat0) == 5 {
		for i := 0; i < 5; i++ {
			card52[index] = s.shuffle52.Seat0[i]
			index++
		}
	}

	if len(s.shuffle52.Seat1) == 5 {
		for i := 0; i < 5; i++ {
			card52[index] = s.shuffle52.Seat1[i]
			index++
		}
	}

	if len(s.shuffle52.Seat2) == 5 {
		for i := 0; i < 5; i++ {
			card52[index] = s.shuffle52.Seat2[i]
			index++
		}
	}

	if len(s.shuffle52.Seat3) == 5 {
		for i := 0; i < 5; i++ {
			card52[index] = s.shuffle52.Seat3[i]
			index++
		}
	}

	if len(s.shuffle52.Seat4) == 5 {
		for i := 0; i < 5; i++ {
			card52[index] = s.shuffle52.Seat4[i]
			index++
		}
	}

	for i := 0; i < len(s.shuffle52.Deck); i++ {
		if index >= 52 {
			break
		}
		card52[index] = s.shuffle52.Deck[i]
		index++
	}

	return card52
}

func (s *service) Shuffle54Handler(card54 []int) []int {
	return card54
}

func (s *service) StartSeat() int {
	if !s.isAllowControl {
		return -1
	}
	return s.shuffle52.Start
}
