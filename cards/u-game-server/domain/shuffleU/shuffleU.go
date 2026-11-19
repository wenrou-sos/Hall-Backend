package shuffleU

type shuffleU struct {
	Seat0 []int 	`json:"Seat0"`
	Seat1 []int 	`json:"Seat1"`
	Seat2 []int 	`json:"Seat2"`
	Seat3 []int 	`json:"Seat3"`
	Deck  []int 	`json:"Deck"`
	StartSeat int   `json:"StartSeat"`
	StartCard int   `json:"StartCard"`
	LuckyCard int   `json:"LuckyCard"`
}
