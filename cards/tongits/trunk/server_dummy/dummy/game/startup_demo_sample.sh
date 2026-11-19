#!/bin/bash
a=`ulimit -n`
echo "ulimit : ${a}"
if [ "$a"  -lt  20000 ]
then
       echo "ulimit no enough"
       exit 0
fi
path=`pwd`
serverid="6108d0e0bb752e7e5c16453af79a26f6"
serverid=$1
baseport=12350
baseport=$2
tableid=9999
mkdir -p log
time=`date +%Y%m%d-%H%M`

portnum=$(( $baseport + $tableid ))
logpath="server-$portnum.log"
nohup python -W${path} -u -m Launcher $serverid $tableid $portnum >> ${path}/log/$logpath 2>&1 &
echo $! >> .pids
sleep 1

