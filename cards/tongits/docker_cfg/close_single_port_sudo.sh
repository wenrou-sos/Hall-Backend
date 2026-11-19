#!/bin/bash
port_service=$1

if [ $port_service = "9400" ]
then
    port_assist=9301
    assist_url="http://127.0.0.1:${port_assist}/downservice/"
    port_center=9311
    port_game=12360
    table_count=12

    for ((c=1; c<=$table_count; c++))
    do
        portnum=$(( $port_game + $c ))
        pid_game=$( ps aux | grep game | grep $portnum | tr -s ' ' | cut -d ' ' -f 2 )
        sudo kill -9 $pid_game
        sleep 1
    done

    echo " "
    echo "------------------------------"
    echo "close game done"

    sleep 1

    pid_service=$( ps aux | grep service | grep python | grep $port_service | tr -s ' ' | cut -d ' ' -f 2 )

    sudo kill -9 $pid_service

    sleep 1

    echo "close service done"

    sleep 2

    pid_center=$( ps aux | grep center | grep $port_center | tr -s ' ' | cut -d ' ' -f 2 )
    sudo kill -9 $pid_center

    sleep 1

    echo "close center done"

    sleep 1 

    curl $assist_url

    sleep 1

    echo " "
    echo "close assist done"

    sleep 3

    echo "------------------------------"

    command5=$( ps aux | grep python )
    echo "$command5"

    echo "close server done"
    echo "------------------------------"

elif [ $port_service = "9500" ]
then
    port_assist=9302
    assist_url="http://127.0.0.1:${port_assist}/downservice/"
    port_center=9312
    port_game=12460
    table_count=12

    for ((c=1; c<=$table_count; c++))
    do
        portnum=$(( $port_game + $c ))
        pid_game=$( ps aux | grep game | grep $portnum | tr -s ' ' | cut -d ' ' -f 2 )
        sudo kill -9 $pid_game
        sleep 1
    done

    echo " "
    echo "------------------------------"
    echo "close game done"

    sleep 1

    pid_service=$( ps aux | grep service | grep python | grep $port_service | tr -s ' ' | cut -d ' ' -f 2 )
    sudo kill -9 $pid_service

    sleep 1

    echo "close service done"

    sleep 1

    pid_center=$( ps aux | grep center | grep $port_center | tr -s ' ' | cut -d ' ' -f 2 )
    sudo kill -9 $pid_center

    sleep 1

    echo "close center done"

    sleep 1 

    curl $assist_url

    sleep 1

    echo " "
    echo "close assist done"

    sleep 3

    echo "------------------------------"

    command5=$( ps aux | grep python )
    echo "$command5"

    echo "close server done"
    echo "------------------------------"

elif [ $port_service = "9600" ]
then
    port_assist=9303
    assist_url="http://127.0.0.1:${port_assist}/downservice/"
    port_center=9313
    port_game=12560
    table_count=12

    for ((c=1; c<=$table_count; c++))
    do
        portnum=$(( $port_game + $c ))
        pid_game=$( ps aux | grep game | grep $portnum | tr -s ' ' | cut -d ' ' -f 2 )
        sudo kill -9 $pid_game
        sleep 1
    done

    echo " "
    echo "------------------------------"
    echo "close game done"

    sleep 1

    pid_service=$( ps aux | grep service | grep python | grep $port_service | tr -s ' ' | cut -d ' ' -f 2 )
    sudo kill -9 $pid_service

    sleep 1

    echo "close service done"

    sleep 1

    pid_center=$( ps aux | grep center | grep $port_center | tr -s ' ' | cut -d ' ' -f 2 )
    sudo kill -9 $pid_center

    sleep 1

    echo "close center done"

    sleep 1 

    curl $assist_url

    sleep 1

    echo " "
    echo "close assist done"

    sleep 3

    echo "------------------------------"

    command5=$( ps aux | grep python )
    echo "$command5"

    echo "close server done"
    echo "------------------------------"

elif [ $port_service = "9700" ]
then
    port_assist=9304
    assist_url="http://127.0.0.1:${port_assist}/downservice/"
    port_center=9314
    port_game=12660
    table_count=12

    for ((c=1; c<=$table_count; c++))
    do
        portnum=$(( $port_game + $c ))
        pid_game=$( ps aux | grep game | grep $portnum | tr -s ' ' | cut -d ' ' -f 2 )
        sudo kill -9 $pid_game
        sleep 1
    done

    echo " "
    echo "------------------------------"
    echo "close game done"

    sleep 1

    pid_service=$( ps aux | grep service | grep python | grep $port_service | tr -s ' ' | cut -d ' ' -f 2 )
    sudo kill -9 $pid_service

    sleep 1

    echo "close service done"

    sleep 1

    pid_center=$( ps aux | grep center | grep $port_center | tr -s ' ' | cut -d ' ' -f 2 )
    sudo kill -9 $pid_center

    sleep 1

    echo "close center done"

    sleep 1 

    curl $assist_url

    sleep 1

    echo " "
    echo "close assist done"

    sleep 3

    echo "------------------------------"

    command5=$( ps aux | grep python )
    echo "$command5"

    echo "close server done"
    echo "------------------------------"

fi
