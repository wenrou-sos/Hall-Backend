package format

import "testing"

func TestHideWithStar(t *testing.T) {
    t.Log(HideWithStar("johnny"))
    t.Log(HideWithStar("leo"))
    t.Log(HideWithStar("dd"))
}
