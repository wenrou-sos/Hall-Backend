import env_setting

if env_setting.LOCAL_SERVER == False:
    from fcntl import ioctl
import socket
import struct
import sys

def get_self_ip():
    if env_setting.LOCAL_SERVER == False:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            ip = ioctl(sock.fileno(), 0x8915, struct.pack('64s', b'eth0'))
            ip = socket.inet_ntoa(ip[20:24])
            return ip
        except:
            return None
    else:
        return '127.0.0.1'
if __name__ == '__main__':
    print(get_self_ip())