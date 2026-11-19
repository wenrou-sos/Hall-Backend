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
tablecnt=6
tablecnt=$3
mkdir -p log
time=`date +%Y%m%d-%H%M`
echo "table cnt: $tablecnt"
for((c=1; c<=$tablecnt; c++))
do
	portnum=$(( $baseport + $c ))
	tableid=$(( $c - 1 ))
	logpath="server-$portnum.log"
	#echo "port=$portnum"
	#echo "table_id=$tableid"
	#echo "log_path=$logpath"
	nohup python -W${path} -u -m Launcher $serverid $tableid $portnum >> ${path}/log/$logpath 2>&1 &
	echo $! >> .pids
	sleep 1
done
