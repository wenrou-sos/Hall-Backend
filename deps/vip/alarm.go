package vip

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"strconv"
)

func Alarm(title, gameType, hostId, hostName, gameId, gameName, memberId, billCurrency string, level, allTotalTimes, rtp, accountingSn int) {
	var token string
	if isProductionMode := os.Getenv("RELEASE_FOR_PRODUCTION_MODE"); isProductionMode == "" || isProductionMode == "FALSE" {
		token = "bu01"
	} else {
		token = "cs01"
	}
	values := map[string]string{"title": title, "message": "\nVIP Level : " + strconv.Itoa(level) + "\nGame Type : " + gameType + "\nHost ID : " + hostId + "\nHost Name : " + hostName + "\nGame ID : " + gameId + "\nGame Name : " + gameName + "\nMember ID : " + memberId + "\nBill Currency : " + billCurrency + "\nGame Times : " + strconv.Itoa(allTotalTimes) + "\nRTP : " + strconv.FormatFloat(float64(rtp)/100, 'f', 2, 32) + "\nSN : " + strconv.Itoa(accountingSn), "token": token}

	body, _ := json.Marshal(values)
	fmt.Println("tgalarm: ", bytes.NewBuffer(body))
	resp, err := http.Post("https://2f2rradwgeqj7zo4uxyzcilf7i0putfd.lambda-url.ap-northeast-2.on.aws", "application/json", bytes.NewBuffer(body))

	if err != nil {
		panic(err)
	}
	fmt.Println("resp: ", err)
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusCreated {
		body, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			panic(err)
		}
		jsonStr := string(body)
		fmt.Println("Response: ", jsonStr)

	} else {
		fmt.Println("Get failed with error: ", resp.Status)
	}
}
