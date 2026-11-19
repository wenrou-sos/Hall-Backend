#!/bin/bash

echo "start server..."
a=`ulimit -n`
echo "ulimit : ${a}"
if [ "$a"  -lt  20000 ]
then
       echo "ulimit no enough"
       exit 0
fi
#assist
cd ./assist
./startup.sh
cd ..
sleep 1

#center
cd ./center
./startup.sh
cd ..
sleep 1

#service
cd ./service
./startup.sh
cd ..
sleep 1

#game api_key start_port table_count
cnt=6
cd ./game
./startupall.sh "6108d0e0bb752e7e5c16453af79a26f6" 12350 $cnt
cd ..
sleep $cnt

sleep 5

ps aux | grep python
echo "start server done"
echo "----------------------------------------------------------"
