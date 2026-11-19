package friendroom

import (
    "testing"
)

func Test_Leave(t *testing.T) {
    r := &room{
        Uuid:   "A",
        Number: 123456789,
        Size:   6,
        Status: IDLE,
    }

    Leave.do(
        "552e233a0fa3d97d4ff2bc93812a04e4",
        "FRIEND_ROOM:HashId",
        r.Number,
        0,
    )
}
