#!/bin/bash

echo "start server..."
a=`ulimit -n`
echo "ulimit : ${a}"
if [ "$a"  -lt  20000 ]
then
    echo "ulimit no enough"
    exit 0
fi
pip install numpy

#assist
if [[ $1 == "assist=1" ]]; then
    cd ./assist
    ./startup.sh
    cd ..
    sleep 1
fi

#center
if [[ $2 == "center=1" ]]; then
    cd ./center
    ./startup.sh
    cd ..
    sleep 1
fi

#game api_key start_port table_count
if [[ $3 =~ ^game=[0-9/]+$ ]]; then
    cd ./game

    IFS='/' read -ra TABLE_IDS <<< "${3#game=}"
    for tableid in "${TABLE_IDS[@]}"; do
      ./startupall.sh "multi_host_key" $(( game_port + 1 )) $tableid
      sleep 1
    done
fi

#demo
if [[ $4 == "demo=1" ]]; then
  ./startup_demo.sh "multi_host_key" game_port
  sleep 1
fi
cd ..

#service
if [[ $5 == "service=1" ]]; then
  cd ./service
  ./startup.sh
  cd ..
  sleep 1
fi

sleep 5

ps aux | grep python
echo "start server done"
echo "----------------------------------------------------------"

#ping -i 600 localhost
