#!/bin/bash
a=`ulimit -n`
echo "ulimit : ${a}"
if [ "$a"  -lt  20000 ]
then
       echo "ulimit no enough"
       exit 0
fi
path=`pwd`
serverid="8482c6afb2b6f032f3ab245346077c74"
serverid=$1
baseport=12360
baseport=$2
tableid=9999
mkdir -p log
time=`date +%Y%m%d-%H%M`

portnum=$baseport
logpath="server-$portnum.log"
nohup python -W${path} -u -m Launcher $serverid $tableid $portnum >> ${path}/log/$logpath 2>&1 &
echo $! >> .pids
sleep 1
