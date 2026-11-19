package lottery

import (
    "89-game-server/domain/probability"
    probability_proto "89-game-server/domain/probability/proto"
    "crypto/rand"
    "github.com/google/uuid"
    "gitlab.iplaystar.net/game-server/shuffle"
    "math/big"
    "testing"
)

const (
    TIMES = 100 * 100 * 100 * 10 // ten million
)

func TestService_Result(t *testing.T) {
    bankerUuid := uuid.New().String()
    playerUuid1 := uuid.New().String()
    playerUuid2 := uuid.New().String()
    playerUuid3 := uuid.New().String()
    playerUuid4 := uuid.New().String()
    playerUuid5 := uuid.New().String()

    var banker1Win1_3, banker2Win1_3, banker3Win1_3, banker4Win1_3, banker5Win1_3 uint64 = 0, 0, 0, 0, 0
    var banker1Win2_4, banker2Win2_4, banker3Win2_4, banker4Win2_4, banker5Win2_4 uint64 = 0, 0, 0, 0, 0
    var banker1Win5_17, banker2Win5_17, banker3Win5_17, banker4Win5_17, banker5Win5_17 uint64 = 0, 0, 0, 0, 0
    var banker1Win18_29, banker2Win18_29, banker3Win18_29, banker4Win18_29, banker5Win18_29 uint64 = 0, 0, 0, 0, 0
    var banker1Win30_41, banker2Win30_41, banker3Win30_41, banker4Win30_41, banker5Win30_41 uint64 = 0, 0, 0, 0, 0
    var banker1Win42_47, banker2Win42_47, banker3Win42_47, banker4Win42_47, banker5Win42_47 uint64 = 0, 0, 0, 0, 0
    var banker1Win48, banker2Win48, banker3Win48, banker4Win48, banker5Win48 uint64 = 0, 0, 0, 0, 0
    var banker1Win49_50, banker2Win49_50, banker3Win49_50, banker4Win49_50, banker5Win49_50 uint64 = 0, 0, 0, 0, 0
    var banker1Win51_52, banker2Win51_52, banker3Win51_52, banker4Win51_52, banker5Win51_52 uint64 = 0, 0, 0, 0, 0

    var player1Win1_3, player2Win1_3, player3Win1_3, player4Win1_3, player5Win1_3 uint64 = 0, 0, 0, 0, 0
    var player1Win2_4, player2Win2_4, player3Win2_4, player4Win2_4, player5Win2_4 uint64 = 0, 0, 0, 0, 0
    var player1Win5_17, player2Win5_17, player3Win5_17, player4Win5_17, player5Win5_17 uint64 = 0, 0, 0, 0, 0
    var player1Win18_29, player2Win18_29, player3Win18_29, player4Win18_29, player5Win18_29 uint64 = 0, 0, 0, 0, 0
    var player1Win30_41, player2Win30_41, player3Win30_41, player4Win30_41, player5Win30_41 uint64 = 0, 0, 0, 0, 0
    var player1Win42_47, player2Win42_47, player3Win42_47, player4Win42_47, player5Win42_47 uint64 = 0, 0, 0, 0, 0
    var player1Win48, player2Win48, player3Win48, player4Win48, player5Win48 uint64 = 0, 0, 0, 0, 0
    var player1Win49_50, player2Win49_50, player3Win49_50, player4Win49_50, player5Win49_50 uint64 = 0, 0, 0, 0, 0
    var player1Win51_52, player2Win51_52, player3Win51_52, player4Win51_52, player5Win51_52 uint64 = 0, 0, 0, 0, 0

    var player1Tie, player2Tie, player3Tie, player4Tie, player5Tie uint64 = 0, 0, 0, 0, 0

    for i := 0; i < TIMES; i++ {
        cards := shuffle.Service.Shuffle52(bankerUuid)

        results := make(map[string]*probability_proto.Card)

        playerCard1 := two(0, cards[0], cards[1])
        playerCard2 := two(1, cards[3], cards[4])
        playerCard3 := two(2, cards[6], cards[7])
        playerCard4 := two(3, cards[9], cards[10])
        playerCard5 := two(4, cards[12], cards[13])
        bankerCard := two(5, cards[15], cards[16])

        // banker got pok8 pok9
        if is89(bankerCard.Rule) {
            results[playerUuid1] = playerCard1
            results[playerUuid2] = playerCard2
            results[playerUuid3] = playerCard3
            results[playerUuid4] = playerCard4
            results[playerUuid5] = playerCard5
            results[bankerUuid] = bankerCard
        } else {
            if (isDraw() && !is89(playerCard1.Rule)) || is03(playerCard1.SumPoint) {
                playerCard1 = three(0, cards[0], cards[1], cards[2])
                results[playerUuid1] = playerCard1
            } else {
                results[playerUuid1] = playerCard1
            }

            if (isDraw() && !is89(playerCard2.Rule)) || is03(playerCard2.SumPoint) {
                playerCard2 = three(1, cards[3], cards[4], cards[5])
                results[playerUuid2] = playerCard2
            } else {
                results[playerUuid2] = playerCard2
            }

            if (isDraw() && !is89(playerCard3.Rule)) || is03(playerCard3.SumPoint) {
                playerCard3 = three(2, cards[6], cards[7], cards[8])
                results[playerUuid3] = playerCard3
            } else {
                results[playerUuid3] = playerCard3
            }

            if (isDraw() && !is89(playerCard4.Rule)) || is03(playerCard4.SumPoint) {
                playerCard4 = three(3, cards[9], cards[10], cards[11])
                results[playerUuid4] = playerCard4
            } else {
                results[playerUuid4] = playerCard4
            }

            if (isDraw() && !is89(playerCard5.Rule)) || is03(playerCard5.SumPoint) {
                playerCard5 = three(4, cards[12], cards[13], cards[14])
                results[playerUuid5] = playerCard5
            } else {
                results[playerUuid5] = playerCard5
            }

            if is03(bankerCard.SumPoint) || is45(bankerCard.SumPoint) {
                bankerCard = three(5, cards[15], cards[16], cards[17])
                results[bankerUuid] = bankerCard
            } else {
                results[bankerUuid] = bankerCard
            }
        }

        for _, v := range Service.Result(results, nil, nil, bankerUuid, "").Cards {
            switch v.Seat {
            case 0:
                switch v.Status {
                case lose:
                    switch bankerCard.Rule {
                    case 1, 3:
                        banker1Win1_3++

                    case 2, 4:
                        banker1Win2_4++

                    case 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17:
                        banker1Win5_17++

                    case 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29:
                        banker1Win18_29++

                    case 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41:
                        banker1Win30_41++

                    case 42, 43, 44, 45, 46, 47:
                        banker1Win42_47++

                    case 48:
                        banker1Win48++

                    case 49, 50:
                        banker1Win49_50++

                    case 51, 52:
                        banker1Win51_52++
                    }

                case win:
                    switch v.Rule {
                    case 1, 3:
                        player1Win1_3++

                    case 2, 4:
                        player1Win2_4++

                    case 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17:
                        player1Win5_17++

                    case 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29:
                        player1Win18_29++

                    case 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41:
                        player1Win30_41++

                    case 42, 43, 44, 45, 46, 47:
                        player1Win42_47++

                    case 48:
                        player1Win48++

                    case 49, 50:
                        player1Win49_50++

                    case 51, 52:
                        player1Win51_52++
                    }

                case tie:
                    player1Tie++
                }

            case 1:
                switch v.Status {
                case lose:
                    switch bankerCard.Rule {
                    case 1, 3:
                        banker2Win1_3++

                    case 2, 4:
                        banker2Win2_4++

                    case 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17:
                        banker2Win5_17++

                    case 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29:
                        banker2Win18_29++

                    case 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41:
                        banker2Win30_41++

                    case 42, 43, 44, 45, 46, 47:
                        banker2Win42_47++

                    case 48:
                        banker2Win48++

                    case 49, 50:
                        banker2Win49_50++

                    case 51, 52:
                        banker2Win51_52++
                    }

                case win:
                    switch v.Rule {
                    case 1, 3:
                        player2Win1_3++

                    case 2, 4:
                        player2Win2_4++

                    case 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17:
                        player2Win5_17++

                    case 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29:
                        player2Win18_29++

                    case 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41:
                        player2Win30_41++

                    case 42, 43, 44, 45, 46, 47:
                        player2Win42_47++

                    case 48:
                        player2Win48++

                    case 49, 50:
                        player2Win49_50++

                    case 51, 52:
                        player2Win51_52++
                    }

                case tie:
                    player2Tie++
                }

            case 2:
                switch v.Status {
                case lose:
                    switch bankerCard.Rule {
                    case 1, 3:
                        banker3Win1_3++

                    case 2, 4:
                        banker3Win2_4++

                    case 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17:
                        banker3Win5_17++

                    case 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29:
                        banker3Win18_29++

                    case 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41:
                        banker3Win30_41++

                    case 42, 43, 44, 45, 46, 47:
                        banker3Win42_47++

                    case 48:
                        banker3Win48++

                    case 49, 50:
                        banker3Win49_50++

                    case 51, 52:
                        banker3Win51_52++
                    }

                case win:
                    switch v.Rule {
                    case 1, 3:
                        player3Win1_3++

                    case 2, 4:
                        player3Win2_4++

                    case 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17:
                        player3Win5_17++

                    case 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29:
                        player3Win18_29++

                    case 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41:
                        player3Win30_41++

                    case 42, 43, 44, 45, 46, 47:
                        player3Win42_47++

                    case 48:
                        player3Win48++

                    case 49, 50:
                        player3Win49_50++

                    case 51, 52:
                        player3Win51_52++
                    }

                case tie:
                    player3Tie++
                }

            case 3:
                switch v.Status {
                case lose:
                    switch bankerCard.Rule {
                    case 1, 3:
                        banker4Win1_3++

                    case 2, 4:
                        banker4Win2_4++

                    case 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17:
                        banker4Win5_17++

                    case 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29:
                        banker4Win18_29++

                    case 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41:
                        banker4Win30_41++

                    case 42, 43, 44, 45, 46, 47:
                        banker4Win42_47++

                    case 48:
                        banker4Win48++

                    case 49, 50:
                        banker4Win49_50++

                    case 51, 52:
                        banker4Win51_52++
                    }

                case win:
                    switch v.Rule {
                    case 1, 3:
                        player4Win1_3++

                    case 2, 4:
                        player4Win2_4++

                    case 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17:
                        player4Win5_17++

                    case 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29:
                        player4Win18_29++

                    case 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41:
                        player4Win30_41++

                    case 42, 43, 44, 45, 46, 47:
                        player4Win42_47++

                    case 48:
                        player4Win48++

                    case 49, 50:
                        player4Win49_50++

                    case 51, 52:
                        player4Win51_52++
                    }

                case tie:
                    player4Tie++
                }

            case 4:
                switch v.Status {
                case lose:
                    switch bankerCard.Rule {
                    case 1, 3:
                        banker5Win1_3++

                    case 2, 4:
                        banker5Win2_4++

                    case 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17:
                        banker5Win5_17++

                    case 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29:
                        banker5Win18_29++

                    case 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41:
                        banker5Win30_41++

                    case 42, 43, 44, 45, 46, 47:
                        banker5Win42_47++

                    case 48:
                        banker5Win48++

                    case 49, 50:
                        banker5Win49_50++

                    case 51, 52:
                        banker5Win51_52++
                    }

                case win:
                    switch v.Rule {
                    case 1, 3:
                        player5Win1_3++

                    case 2, 4:
                        player5Win2_4++

                    case 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17:
                        player5Win5_17++

                    case 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29:
                        player5Win18_29++

                    case 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41:
                        player5Win30_41++

                    case 42, 43, 44, 45, 46, 47:
                        player5Win42_47++

                    case 48:
                        player5Win48++

                    case 49, 50:
                        player5Win49_50++

                    case 51, 52:
                        player5Win51_52++
                    }

                case tie:
                    player5Tie++
                }
            }
        }
    }

    t.Log("player1Lose :", banker1Win1_3, banker1Win2_4, banker1Win5_17, banker1Win18_29, banker1Win30_41, banker1Win42_47, banker1Win48, banker1Win49_50, banker1Win51_52)
    t.Log("player2Lose :", banker2Win1_3, banker2Win2_4, banker2Win5_17, banker2Win18_29, banker2Win30_41, banker2Win42_47, banker2Win48, banker2Win49_50, banker2Win51_52)
    t.Log("player3Lose :", banker3Win1_3, banker3Win2_4, banker3Win5_17, banker3Win18_29, banker3Win30_41, banker3Win42_47, banker3Win48, banker3Win49_50, banker3Win51_52)
    t.Log("player4Lose :", banker4Win1_3, banker4Win2_4, banker4Win5_17, banker4Win18_29, banker4Win30_41, banker4Win42_47, banker4Win48, banker4Win49_50, banker4Win51_52)
    t.Log("player5Lose :", banker5Win1_3, banker5Win2_4, banker5Win5_17, banker5Win18_29, banker5Win30_41, banker5Win42_47, banker5Win48, banker5Win49_50, banker5Win51_52)

    t.Log("player1Win  :", player1Win1_3, player1Win2_4, player1Win5_17, player1Win18_29, player1Win30_41, player1Win42_47, player1Win48, player1Win49_50, player1Win51_52)
    t.Log("player2Win  :", player2Win1_3, player2Win2_4, player2Win5_17, player2Win18_29, player2Win30_41, player2Win42_47, player2Win48, player2Win49_50, player2Win51_52)
    t.Log("player3Win  :", player3Win1_3, player3Win2_4, player3Win5_17, player3Win18_29, player3Win30_41, player3Win42_47, player3Win48, player3Win49_50, player3Win51_52)
    t.Log("player4Win  :", player4Win1_3, player4Win2_4, player4Win5_17, player4Win18_29, player4Win30_41, player4Win42_47, player4Win48, player4Win49_50, player4Win51_52)
    t.Log("player5Win  :", player5Win1_3, player5Win2_4, player5Win5_17, player5Win18_29, player5Win30_41, player5Win42_47, player5Win48, player5Win49_50, player5Win51_52)

    t.Log("player1Tie  :", player1Tie)
    t.Log("player2Tie  :", player2Tie)
    t.Log("player3Tie  :", player3Tie)
    t.Log("player4Tie  :", player4Tie)
    t.Log("player5Tie  :", player5Tie)

}

func is03(point int32) bool {
    return point >= 0 && point <= 3
}

func is45(point int32) bool {
    return point >= 4 && point <= 5
}

func is89(rule int32) bool {
    return rule > 0 && rule < 5
}

func isDraw() bool {
    n, err := rand.Int(rand.Reader, big.NewInt(2))

    if err != nil {
        panic(err)
    }

    return n.Int64() == 1
}

func two(seat, card1, card2 int) *probability_proto.Card {
    result := probability.Service.Calc2Cards(card1, card2)

    return &probability_proto.Card{
        Seat: int32(seat),
        Hand: []int32{
            int32(probability.Service.CardToIndex(card1)),
            int32(probability.Service.CardToIndex(card2)),
        },
        SumPoint:   int32(result.Point),
        Pay:        uint64(result.Pay),
        Rule:       int32(result.Rule),
        Cent:       0,
        Status:     probability_proto.Card_NONE,
        PlayerCent: 0,
    }
}

func three(seat, card1, card2, card3 int) *probability_proto.Card {
    result := probability.Service.Calc3Cards(card1, card2, card3)

    return &probability_proto.Card{
        Seat: int32(seat),
        Hand: []int32{
            int32(probability.Service.CardToIndex(card1)),
            int32(probability.Service.CardToIndex(card2)),
            int32(probability.Service.CardToIndex(card3)),
        },
        SumPoint:   int32(result.Point),
        Pay:        uint64(result.Pay),
        Rule:       int32(result.Rule),
        Cent:       0,
        Status:     probability_proto.Card_NONE,
        PlayerCent: 0,
    }
}
