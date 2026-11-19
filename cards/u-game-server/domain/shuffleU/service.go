package shuffleU

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
	folder:         "domain/shuffleU",
	File:           "shuffleU.json",
	shuffleU:      nil,
}

type service struct {
	isAllowControl bool
	Docker         string
	test           string
	folder         string
	File           string
	shuffleU      *shuffleU
}

func init() {
	if Service.isAllowControl {
		Service.deserialization()
	}
}

func (s *service) deserialization() {
	if err := json.NewDecoder(s.open()).Decode(&s.shuffleU); err != nil {
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
		s.shuffleU = nil
		s.deserialization()
	}
}

func (s *service) ShuffleUHandler(cardU []int) []int {
	if !s.isAllowControl {
		return cardU
	}

	index := 0

	if len(s.shuffleU.Seat0) == 7 {
		for i := 0; i < 7; i++ {
			cardU[index] = s.shuffleU.Seat0[i]
			index++
		}
	}

	if len(s.shuffleU.Seat1) == 7 {
		for i := 0; i < 7; i++ {
			cardU[index] = s.shuffleU.Seat1[i]
			index++
		}
	}

	if len(s.shuffleU.Seat2) == 7 {
		for i := 0; i < 7; i++ {
			cardU[index] = s.shuffleU.Seat2[i]
			index++
		}
	}

	if len(s.shuffleU.Seat3) == 7 {
		for i := 0; i < 7; i++ {
			cardU[index] = s.shuffleU.Seat3[i]
			index++
		}
	}

	for i := 0; i < len(s.shuffleU.Deck); i++ {
		if index >= len(cardU) {
			break
		}
		cardU[index] = s.shuffleU.Deck[i]
		index++
	}

	return cardU
}

func (s *service) Shuffle52Handler(card52 []int) []int {
	return card52
}

func (s *service) Shuffle54Handler(card54 []int) []int {
	return card54
}

func (s *service) StartSeat() int {
	if !s.isAllowControl {
		return -1
	}
	return s.shuffleU.StartSeat
}

func (s *service) StartCard() int {
	if !s.isAllowControl {
		return -1
	}
	return s.shuffleU.StartCard
}

func (s *service) LuckyCard() int {
	if !s.isAllowControl {
		return -1
	}
	return s.shuffleU.LuckyCard
}
