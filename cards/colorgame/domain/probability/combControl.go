package probability

//賠率控制
type combControl struct {
	HITX0 int   `json:"HITX0"`
	HITX1 int   `json:"HITX1"`
	HITX2 int   `json:"HITX2"`
	HITX3 hitx3 `json:"HITX3"`
}

//豹子(3同色)
type hitx3 struct {
	ORIGINAL ColorWeight `json:"ORIGINAL"`
	YELLOW   ColorWeight `json:"YELLOW"`
	RED      ColorWeight `json:"RED"`
	BLUE     ColorWeight `json:"BLUE"`
}

//顏色比重
type ColorWeight struct {
	Weight    int             `json:"weight"`
	Multiples []colorMultiple `json:"multiples"`
}

//顏色倍率
type colorMultiple struct {
	Multiple int `json:"multiple"`
	Weight   int `json:"weight"`
}
