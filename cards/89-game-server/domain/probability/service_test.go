package probability

import "testing"

//"CLUB":    "1,  2,  3,  4,  5,  6,  7,  8,  9,  10, 11, 12, 13",
//"DIAMOND": "17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29",
//"HEART":   "33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45",
//"SPADE":   "49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61",

func TestService_Calc3Cards(t *testing.T) {
    Service.Calc3Cards(1, 61, 43)
}
