package http

import (
    "testing"
)

func TestService_Get(t *testing.T) {
    token := "fish1123"
    url := "http://gameapiserver.playgems.net:85/apis/authenticate?access_token=" + token + "&step=1"

    if body, err := Service.Get(url); err != nil {
        t.Fatal(err)
    } else {
        t.Log(body)
    }
}

func TestService_Post(t *testing.T) {
    url := "https://dev.iplaystar.net/api/get_balance"
    parameter := "host_id=dd12f3635bc9599ca58012601d07197c&id=jerry&purpose=0"

    if body, err := Service.Post(url, parameter); err != nil {
        t.Fatal(err)
    } else {
        t.Log(string(body))
    }
}