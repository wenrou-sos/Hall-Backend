package rng

import "testing"

func TestNew(t *testing.T) {
	options := make([]Option, 0, 3)
	options = append(options, Option{11, "Play"})
	options = append(options, Option{22, "Star"})
	options = append(options, Option{33, "Fish"})
	options = append(options, Option{44, "Johnny"})

	a := 0
	b := 0
	c := 0
	d := 0

	for i := 0; i < 1100000; i++ {
		o := weightedRandom(options)

		switch o.Item.(string) {
		case "Play":
			a++
		case "Star":
			b++
		case "Fish":
			c++
		case "Johnny":
			d++
		}
	}

	t.Log("a - ", a)
	t.Log("b - ", b)
	t.Log("c - ", c)
	t.Log("d - ", d)
}

func BenchmarkNew(b *testing.B) {
	options := make([]Option, 0, 3)
	options = append(options, Option{11, "Play"})
	options = append(options, Option{22, "Star"})
	options = append(options, Option{33, "Fish"})
	options = append(options, Option{44, "Johnny"})

	for i := 0; i < b.N; i++ {
		weightedRandom(options)
	}
}
