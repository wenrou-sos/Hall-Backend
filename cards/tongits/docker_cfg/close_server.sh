#!/bin/bash

echo "close server..."

#game
cd ./game
./shutdownall.sh
cd ..
sleep 1

#service
cd ./service
./shutdown.sh
cd ..
sleep 1

#center
cd ./center
./shutdown.sh
cd ..
sleep 1

#assist
cd ./assist
./shutdown.sh
cd ..
sleep 1

sleep 10

echo "close server done"
echo "----------------------------------------------------------"

ps aux | grep python | awk '{print $2}' | xargs kill -9
ps aux | grep python

echo "killed"
