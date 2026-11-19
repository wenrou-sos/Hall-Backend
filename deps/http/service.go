package http

import (
    "crypto/tls"
    "io/ioutil"
    "net"
    "net/http"
    "strings"
    "time"
)

const (
    timeout = 3 * time.Second
)

var Service = &service{}

type service struct{}

func (s *service) Get(url string) (body []byte, err error) {
    client := &http.Client{
        Transport: &http.Transport{
            Dial: (&net.Dialer{
                Timeout:   timeout,
                KeepAlive: timeout,
            }).Dial,
            TLSClientConfig: &tls.Config{
                InsecureSkipVerify: true,
            },
            TLSHandshakeTimeout: timeout,
            IdleConnTimeout:     timeout,
        },
        Timeout: timeout,
    }
    req, _ := http.NewRequest(http.MethodGet, url, nil)
    req.Header.Set("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36")
    resp, err := client.Do(req)
    //resp, err := client.Get(url)

    defer func() {
        if resp != nil {
            resp.Body.Close()
        }
    }()

    if err != nil {
        return nil, err
    }

    body, err = ioutil.ReadAll(resp.Body)

    if err != nil {
        return nil, err
    }

    return body, nil
}

func (s *service) Post(url string, parameter string) (body []byte, err error) {
    client := &http.Client{
        Transport: &http.Transport{
            Dial: (&net.Dialer{
                Timeout:   timeout,
                KeepAlive: timeout,
            }).Dial,
            TLSClientConfig: &tls.Config{
                InsecureSkipVerify: true,
            },
            TLSHandshakeTimeout: timeout,
            IdleConnTimeout:     timeout,
        },
        Timeout: timeout,
    }

    resp, err := client.Post(url, "application/x-www-form-urlencoded", strings.NewReader(parameter))

    defer func() {
        if resp != nil {
            resp.Body.Close()
        }
    }()

    if err != nil {
        return nil, err
    }

    body, err = ioutil.ReadAll(resp.Body)

    if err != nil {
        return nil, err
    }

    return body, nil
}
