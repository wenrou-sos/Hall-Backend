package accounting89

import (
    bet_proto "89-game-server/domain/bet/proto"
    probability_proto "89-game-server/domain/probability/proto"
    "fmt"
    "github.com/gogo/protobuf/proto"
    "gitlab.iplaystar.net/game-server/accounting"
    errorcode "gitlab.iplaystar.net/game-server/error-code"
    "gitlab.iplaystar.net/game-server/flux"
    "gitlab.iplaystar.net/game-server/logger"
    "strconv"
)

type Accounting89 struct {
}

func (a89 *Accounting89) FluxActionHandler(action *flux.Action, a *accounting.Accounting, isOk chan bool) {
    switch action.Key().Name() {
    case flux.ActionFluxRegisterDone:
        isOk <- true

    case accounting.ActionAccountingStop:
        // do nothing

    case accounting.ActionAccountingEnd:
        var results map[string]*probability_proto.Card
        var betCent map[string]uint64
        var bankerUuid string

        switch action.Payload()[0].(type) {
        case []byte:
            data := &probability_proto.ResultMap{}
            proto.Unmarshal(action.Payload()[0].([]byte), data)
            results = data.ResultMap

        default:
            results = action.Payload()[0].(map[string]*probability_proto.Card)
        }

        switch action.Payload()[1].(type) {
        case []byte:
            data := &bet_proto.BetCentMap{}
            proto.Unmarshal(action.Payload()[1].([]byte), data)
            betCent = data.BetCentMap

        default:
            betCent = action.Payload()[1].(map[string]uint64)
        }

        switch action.Payload()[2].(type) {
        case []byte:
            bankerUuid = string(action.Payload()[2].([]byte))

        default:
            bankerUuid = action.Payload()[2].(string)
        }

        bet := betCent[a.SecWebSocketKey]
        player := results[a.SecWebSocketKey]
        banker := results[bankerUuid]

        playerGameResult := ""
        playerCard3 := "-"

        if len(player.Hand) == 3 {
            playerCard3 = strconv.Itoa(int(player.Hand[2]))
        }

        playerGameResult = fmt.Sprintf("%d/%d/%s/%d/%d/%d/%d/%d/%d/%d",
            player.Hand[0],
            player.Hand[1],
            playerCard3,
            player.SumPoint,
            player.Pay,
            player.Status,
            player.Rule,
            bet,
            player.Cent,
            player.PlayerCent,
        )

        bankerGameResult := ""
        bankerCard3 := "-"

        if len(banker.Hand) == 3 {
            bankerCard3 = strconv.Itoa(int(banker.Hand[2]))
        }

        bankerGameResult = fmt.Sprintf("%d/%d/%s/%d/%d/%d/%d/%s/%d/%d",
            banker.Hand[0],
            banker.Hand[1],
            bankerCard3,
            banker.SumPoint,
            banker.Pay,
            banker.Status,
            banker.Rule,
            "-",
            banker.Cent,
            banker.PlayerCent,
        )

        gameResult := fmt.Sprintf("%s|%s", playerGameResult, bankerGameResult)

        gameData0, gameData1, gameData2, gameData3, gameData4 := "", "", "", "", ""

        for k, v := range results {
            if k != a.SecWebSocketKey && k != bankerUuid {

                card3 := "-"

                switch v.Seat {
                case 0:
                    if len(v.Hand) == 3 {
                        card3 = strconv.Itoa(int(v.Hand[2]))
                    }

                    gameData0 = fmt.Sprintf("%d/%d/%s/%d/%d/%d/%d/%d/%d/%d",
                        v.Hand[0],
                        v.Hand[1],
                        card3,
                        v.SumPoint,
                        v.Pay,
                        v.Status,
                        v.Rule,
                        betCent[k],
                        v.Cent,
                        v.PlayerCent,
                    )

                case 1:
                    if len(v.Hand) == 3 {
                        card3 = strconv.Itoa(int(v.Hand[2]))
                    }

                    gameData1 = fmt.Sprintf("%d/%d/%s/%d/%d/%d/%d/%d/%d/%d",
                        v.Hand[0],
                        v.Hand[1],
                        card3,
                        v.SumPoint,
                        v.Pay,
                        v.Status,
                        v.Rule,
                        betCent[k],
                        v.Cent,
                        v.PlayerCent,
                    )

                case 2:
                    if len(v.Hand) == 3 {
                        card3 = strconv.Itoa(int(v.Hand[2]))
                    }

                    gameData2 = fmt.Sprintf("%d/%d/%s/%d/%d/%d/%d/%d/%d/%d",
                        v.Hand[0],
                        v.Hand[1],
                        card3,
                        v.SumPoint,
                        v.Pay,
                        v.Status,
                        v.Rule,
                        betCent[k],
                        v.Cent,
                        v.PlayerCent,
                    )

                case 3:
                    if len(v.Hand) == 3 {
                        card3 = strconv.Itoa(int(v.Hand[2]))
                    }

                    gameData3 = fmt.Sprintf("%d/%d/%s/%d/%d/%d/%d/%d/%d/%d",
                        v.Hand[0],
                        v.Hand[1],
                        card3,
                        v.SumPoint,
                        v.Pay,
                        v.Status,
                        v.Rule,
                        betCent[k],
                        v.Cent,
                        v.PlayerCent,
                    )

                case 4:
                    if len(v.Hand) == 3 {
                        card3 = strconv.Itoa(int(v.Hand[2]))
                    }

                    gameData4 = fmt.Sprintf("%d/%d/%s/%d/%d/%d/%d/%d/%d/%d",
                        v.Hand[0],
                        v.Hand[1],
                        card3,
                        v.SumPoint,
                        v.Pay,
                        v.Status,
                        v.Rule,
                        betCent[k],
                        v.Cent,
                        v.PlayerCent,
                    )
                }
            }
        }

        gameData := ""

        switch {
        case gameData0 == "":
            gameData = fmt.Sprintf("%s", gameData1+"|"+gameData2+"|"+gameData3+"|"+gameData4)

        case gameData1 == "":
            gameData = fmt.Sprintf("%s", gameData2+"|"+gameData3+"|"+gameData4+"|"+gameData0)

        case gameData2 == "":
            gameData = fmt.Sprintf("%s", gameData3+"|"+gameData4+"|"+gameData0+"|"+gameData1)

        case gameData3 == "":
            gameData = fmt.Sprintf("%s", gameData4+"|"+gameData0+"|"+gameData1+"|"+gameData2)

        case gameData4 == "":
            gameData = fmt.Sprintf("%s", gameData0+"|"+gameData1+"|"+gameData2+"|"+gameData3)
        }

        switch player.Status {
        case probability_proto.Card_LOSE:
            if loseCent := results[a.SecWebSocketKey].Cent; loseCent >= bet {
                a.End(bet, 0, int64(bet-loseCent), gameData, gameResult)
            } else {
                logger.Service.Zap.Errorw(Accounting89_INCORRECT_LOSE_CENT,
                    "GameUser", a.SecWebSocketKey,
                    "AccountingSn", a.Start.Sn,
                    "LoseCent", results[a.SecWebSocketKey].Cent,
                    "Bet", bet,
                )

                errorcode.Service.Fatal(a.SecWebSocketKey, Accounting89_INCORRECT_LOSE_CENT)
            }

        case probability_proto.Card_WIN:
            winCent := results[a.SecWebSocketKey].Cent
            a.End(bet, 0, int64(winCent+bet), gameData, gameResult)

        case probability_proto.Card_TIE:
            a.End(bet, 0, int64(bet), gameData, gameResult)

        default:
            panic("ERROR LOTTERY STATUS")
        }

    }
}

func (a89 *Accounting89) RotationHandler(a *accounting.Accounting) {
    // do nothing
}
