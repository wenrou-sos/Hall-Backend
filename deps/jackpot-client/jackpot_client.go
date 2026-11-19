package jackpot_client

import (
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
)

var _, configFile, _, _ = runtime.Caller(0)

var Config = &config{
	Docker: "/data/jackpot",
	folder: "application/jackpot/",
	File:   "jackpot-client.json",
}

type config struct {
	Docker string
	folder string
	File   string
	Client *client
}

type client struct {
	MYS  *clientConfig `json:"MYS"`
	LKD  *clientConfig `json:"LKD"`
	LKD2 *clientConfig `json:"LKD2"`
}

type clientConfig struct {
	Server       string `json:"server"`
	Port         int    `json:"port"`
	RetryTimes   int    `json:"retryTimes"`
	RetryPeriod  int    `json:"retryPeriod"`
	UpdatePeriod int    `json:"updatePeriod"`
	UseSSL       bool   `json:"useSSL"`
}

func init() {
	Config.deserialization()
}

func (c *config) deserialization() {
	if f, ok := c.open(); ok {
		if err := json.NewDecoder(f).Decode(&c.Client); err != nil {
			cc := &clientConfig{
				Server:       "host.docker.internal",
				Port:         82,
				RetryTimes:   -1,
				RetryPeriod:  3,
				UpdatePeriod: 3,
				UseSSL:       false,
			}
			c.Client = &client{
				MYS:  cc,
				LKD:  cc,
				LKD2: cc,
			}
		}
	}
}

func (c *config) open() (f *os.File, ok bool) {
	var file *os.File
	var err error
	defer file.Close()

	if file, err = os.Open(filepath.Join(c.Docker, c.File)); err != nil {
		if file, err = os.Open(filepath.Join(c.folder, c.File)); err != nil {
			if file, err = os.Open(c.File); err != nil {
				return file, false
			}
		}
	}

	return file, true
}

func (c *config) Reload() {
	c.Client = nil
	c.deserialization()
}
