package rng

import (
	"crypto/rand"
	"errors"
	"math/big"
)

func New(options []Option) *Option {
	return weightedRandom(options)
}

func weightedRandom(options []Option) *Option {
	sum := 0

	for _, o := range options {
		sum += o.Weight
	}

	n, err := rand.Int(rand.Reader, big.NewInt(int64(sum)))

	if err != nil {
		panic(err)
	}

	result := int(n.Int64())

	for _, o := range options {
		result -= o.Weight
		if result < 0 {
			//fmt.Printf("Here is a random %T in [0,%d) : %d\n", n, sum, n)
			//fmt.Println("Here is a random 1 - ", o.Weight)
			//fmt.Println("Here is a random 2 - ", o.Item)
			return &o
		}
	}

	err = errors.New("Internal error - code should not reach this point")
	panic(err)
}
