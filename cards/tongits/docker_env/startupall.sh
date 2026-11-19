#!/bin/bash
a=`ulimit -n`
echo "ulimit : ${a}"
if [ "$a"  -lt  20000 ]
then
       echo "ulimit no enough"
       exit 0
fi
sleep 2
pip uninstall numpy -y
pip install numpy==1.19.2
path=`pwd`
#serverid="67511e0adfe5af8d6359240708035f42"
serverid=$1
#baseport=12361
baseport=$2
#tablecnt=4
tablecnt=$3
echo "table cnt: $tablecnt"

for((c=1; c<=$tablecnt - 1; c++))
do
	portnum=$(( $baseport + $c ))
	tableid=$(( $c - 1 ))
	logpath="server-$portnum.log"
	#secho "port=$portnum"
	#echo "table_id=$tableid"
	#echo "log_path=$logpath"
	nohup python -W${path} -u -m Launcher $serverid $tableid $portnum > ${path}/log/$logpath 2>&1 &
	
	echo $! >> .pids
	sleep 1
done

portnum=$(( $baseport + $tablecnt ))
tableid=$(( $tablecnt - 1 ))
logpath="server-$portnum.log"
echo "port2=$portnum"
echo "table_id2=$tableid"
echo "log_path2=$logpath"
nohup python -W${path} -u -m Launcher $serverid $tableid $portnum > ${path}/log/$logpath 2>&1
#python test.py


