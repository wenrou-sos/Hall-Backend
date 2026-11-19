#!/bin/bash

# for redis
#echo 'echo never > /sys/kernel/mm/transparent_hugepage/enabled' > /etc/rc.local

#echo vm.overcommit_memory = 1 >> /etc/sysctl.conf
echo net.core.somaxconn=32768 >> /etc/sysctl.conf
echo "session required        pam_limits.so" >> /etc/pam.d/common-session
echo "root soft nofile 200000" >> /etc/security/limits.conf
echo "root hard nofile 200000" >> /etc/security/limits.conf
echo "root soft nproc 100000" >> /etc/security/limits.conf
echo "root hard nproc 100000" >> /etc/security/limits.conf

# for mysql
echo "mysql soft nofile 200000" >> /etc/security/limits.conf
echo "mysql hard nofile 200000" >> /etc/security/limits.conf
echo "mysql soft nproc 100000" >> /etc/security/limits.conf
echo "mysql hard nproc 100000" >> /etc/security/limits.conf

# for redis
echo "redis-server soft nofile 200000" >> /etc/security/limits.conf
echo "redis-server hard nofile 200000" >> /etc/security/limits.conf
echo "redis-server soft nproc 100000" >> /etc/security/limits.conf
echo "redis-server hard nproc 100000" >> /etc/security/limits.conf

apt update
apt install libevent-dev zlib1g zlib1g-dev libpcre3 libpcre3-dev libssl-dev build-essential gdebi zip unzip wget -y
wget https://www.python.org/ftp/python/3.6.3/Python-3.6.3.tar.xz
tar -xvf Python-3.6.3.tar.xz && cd Python-3.6.3
./configure --prefix=/usr/local/python3
make -j8 && make install && cd ..
mv /usr/bin/python /usr/bin/python_bak
ln -sf /usr/local/python3/bin/python3 /usr/bin/python

wget https://files.pythonhosted.org/packages/93/ab/f86b61bef7ab14909bd7ec3cd2178feb0a1c86d451bc9bccd5a1aedcde5f/pip-19.1.1.tar.gz
tar -xvf pip-19.1.1.tar.gz && cd pip-19.1.1
python setup.py install
python -m pip install --upgrade pip && cd ..
mv /usr/bin/pip /usr/bin/pip_bak
ln -sf /usr/local/python3/bin/pip3 /usr/bin/pip

python -m pip install protobuf tornado pymysql redis hiredis numpy
python -m pip install xxtea xxtea-py cffi pycrypto pathlib apscheduler
