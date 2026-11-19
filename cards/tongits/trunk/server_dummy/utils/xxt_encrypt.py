# -*- coding: utf8 -*-
import xxtea
import base64

class XXTEncrypt(object):
    sKey = None

    @classmethod
    def SetKey(cls, k):
        cls.sKey = k

    @classmethod
    def Encrypt(cls, encrypt_src):
        return base64.b64encode(xxtea.encrypt(encrypt_src, cls.sKey))

    @classmethod
    def Decrypt_utf8(cls, encrypt_data):
        return xxtea.decrypt_utf8(base64.b64decode(encrypt_data), cls.sKey)

if __name__ == "__main__":
    XXTEncrypt.SetKey("1234567890111111")
    ss = XXTEncrypt.Encrypt( "Hello World!")
    print(ss)
    #print(base64.b64encode(ss))
    print(XXTEncrypt.Decrypt_utf8(ss))
