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
tablecnt=12
tablecnt=$3
tableid=$3
mkdir -p log
time=`date +%Y%m%d-%H%M`
echo "table cnt: $tablecnt"
#for((c=1; c<=$tablecnt; c++))
#do
	portnum=$(( $baseport + $tableid ))
#	tableid=$(( $c - 1 ))
	logpath="server-$portnum.log"
	#echo "port=$portnum"
	#echo "table_id=$tableid"
	#echo "log_path=$logpath"
	nohup python -W${path} -u -m Launcher $serverid $tableid $portnum >> ${path}/log/$logpath 2>&1 &
	echo $! >> .pids
	sleep 1
#done
