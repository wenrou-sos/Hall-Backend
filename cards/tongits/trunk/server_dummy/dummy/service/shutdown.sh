
#!/bin/bash

while read line
do
    kill -12 $line
done < "./.pids"

rm -rf .pids
echo "关闭完成"
