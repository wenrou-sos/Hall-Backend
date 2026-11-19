a=`ulimit -n`
echo "ulimit : ${a}"
if [ "$a"  -lt  20000 ]
then
       echo "ulimit no enough"
       exit 0
fi
rm -fr service.log
path=`pwd`
mkdir -p log
time=`date +%Y%m%d-%H%M`
nohup python -W${path} -u -m Launcher 9301 >> ${path}/log/service.log 2>&1 &
