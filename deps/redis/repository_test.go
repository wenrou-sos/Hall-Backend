package redis

import (
	"testing"
)

func TestRepository_New(t *testing.T) {
	rs := Builder().
		SetAddr("192.168.10.78").
		SetPort("6379").
		SetPassword("123456").
		SetHostExtId("dd12f3635bc9599ca58012601d07197c").
		Build()

	if rs == nil {
		t.Fail()
	}

	conn := rs.pool.Get()

	if conn == nil {
		t.Fail()
	}

	reply, err := conn.Do("HGET", "PLAYSTAR", "activities")

	if err != nil {
		t.Failed()
	}

	t.Log(string(reply.([]uint8)))

	defer conn.Close()
}
