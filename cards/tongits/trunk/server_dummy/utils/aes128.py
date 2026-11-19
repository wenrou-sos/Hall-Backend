import hashlib
import json
from utils import *
from Crypto.Cipher import AES

def AES128Encrypt(key, content):
    txt = ""
    if isinstance(content, dict):
        try:
            txt = json.dumps(content, separators = (',', ':'))
        except:
            PrintEXC()
            return b''
    elif isinstance(content, str):
        txt = content
    elif isinstance(content, bytes):
        txt = content
    else:
        Warn("Not a valid type to be encrypted!")
        return b''
    Log("AES128Encrypt content:", txt)

    key = hashlib.md5(key.encode("utf8")).hexdigest()
    Log("AES128Encrypt md5 key:", key)

    cpt = AES.new(bytes.fromhex(key), AES.MODE_ECB)

    padding = AES.block_size - len(txt) % AES.block_size
    if padding == 0:
        txt = txt + chr(AES.block_size) * AES.block_size
    else:
        txt = txt + chr(padding) * padding

    r = cpt.encrypt(txt)
    return ''.join(["%02x" % d for d in r])

def AES128Decrypt(key, content):
    if not isinstance(content, bytes) and not isinstance(content, str):
        Warn("Not a valid type to be decrypted!")
        return b''

    key = hashlib.md5(key.encode("utf8")).hexdigest()
    Log("AES128Decrypt md5 key:", key)
    cpt = AES.new(bytes.fromhex(key), AES.MODE_ECB)
    data = cpt.decrypt(content)
    padding = int.from_bytes(data[-1:], byteorder='little')
    return data[:-padding]

if __name__ == "__main__":
    key = "xdr56yhn"
    content = {"timestamp":"1111","userName":"mina1234561"}
    r = AES128Encrypt(key, content)
    print(r)
    print(AES128Decrypt(key, bytes.fromhex(r)).decode())