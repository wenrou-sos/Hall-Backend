package PSC_ON_00013

import (
	"strconv"
)

var Deck = &deck{
	blue:   0,
	yellow: 27,
	red:    54,
	green:  81,
}

type deck struct {
	blue   int
	yellow int
	red    int
	green  int
}

type MathU struct {
	Deck        []int
	Pay2        [][]int
	Pay3        [][]int
	Pay4        [][]int
	LevelOffset []int
	MaxWin      []int
}

func (d *deck) Sum(cards []int) int {
	s := 0
	for _, c := range cards {
		p, _, _ := d.CardInfo(c)
		s += p
	}
	return s
}

func (d *deck) CardInfo(card int) (point, color int, name string) {
	color = card / 27
	name = ""
	switch card % 27 {
	case 0:
		point = 0

	case 1, 2:
		point = 1

	case 3, 4:
		point = 2

	case 5, 6:
		point = 3

	case 7, 8:
		point = 4

	case 9, 10:
		point = 5

	case 11, 12:
		point = 6

	case 13, 14:
		point = 7

	case 15, 16:
		point = 8

	case 17, 18:
		point = 9

	case 19, 20:
		point = 20
		name = "RE"

	case 21, 22:
		point = 20
		name = "SK"

	case 23, 24:
		point = 20
		name = "D"

	case 25:
		point = 50
		name = "W"

	case 26:
		point = 50
		name = "WD"
	}

	return point, color, name
}

func (d *deck) Convert(card int) (point int, str string) {
	p, co, n := d.CardInfo(card)

	if n != "W" && n != "WD" {
		switch co {
		case 0:
			str += "藍"

		case 1:
			str += "黃"

		case 2:
			str += "紅"

		case 3:
			str += "綠"
		}
		if n == "" {
			str += strconv.Itoa(p)
		} else {
			str += n
		}
	} else {
		str += n
	}

	return p, str
}

func (d *deck) ConvertToLog(card []int) []string {
	var log []string
	var point []int
	for _, c := range card {
		p, str := d.Convert(c)
		log = append(log, str)
		point = append(point, p)
	}

	for i, _ := range point {
		for j, _ := range point {
			if point[i] < point[j] {
				point[i], point[j] = point[j], point[i]
				log[i], log[j] = log[j], log[i]
			}
		}
	}

	return log
}
