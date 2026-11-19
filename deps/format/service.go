package format

import (
    "fmt"
    "os"
    "strconv"
    "strings"
)

func HideWithStar(str string) string {
    // **** hnny
    // **** *leo
    // **** **dd

    switch len(str) {
    case 0:
        return "********"

    case 1:
        return "*******" + str

    case 2:
        return "******" + str

    case 3:
        return "*****" + str

    case 4:
        return "****" + str

    default:
        return "****" + str[len(str)-4:]
    }
}

func ServerId(macaddress string) string {
    atoiPort, _ := strconv.Atoi(os.Getenv("HTTP_PORT"))

    macAddr := strings.Replace(macaddress, ":", "-", -1)

    return fmt.Sprintf("%s-%05d", macAddr, atoiPort)
}
