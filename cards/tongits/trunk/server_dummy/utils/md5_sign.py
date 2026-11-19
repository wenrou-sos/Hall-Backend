
import hashlib
import json

class MD5Sign(object):
    """MD5签名和验签"""
    @classmethod
    def __data_proc(cls, data):
        """
            param data: 需要签名的数据，字典类型
            return: 处理后的字符串，格式为：参数名称=参数值，并用&连接
        """
        if "sign" in data:
            del data["sign"]
        if "sign_type" in data:
            del data["sign_type"]
        dataList = []
        for key in sorted(data):
            if len(str(data[key])) > 0:
                dataList.append("%s=%s" % (key, data[key]))
        return "&".join(dataList).strip()

    @classmethod
    def md5_sign(cls, data, api_key):
        """
            MD5签名
            param api_key: MD5签名需要的字符串
            return: 签名后的字符串sign
        """
        data = cls.__data_proc(data) + api_key.strip()
        print(data)
        md5 = hashlib.md5()
        md5.update(data.encode(encoding='UTF-8'))
        return md5.hexdigest()

    @classmethod
    def md5_verify(cls, data, api_key):
        """
            md5验签
            param data: 接收到的数据
            param signature: 接收到的sign
            return: 验签结果,布尔值
        """
        if "sign" not in data:
            return False
        sign = data["sign"]
        return cls.md5_sign(data, api_key) == sign

if __name__ == "__main__":

    # data = {}
    # data["_input_charset"] = "utf-8"
    # data["action"] = "login"
    # data["channel"] = "apple"
    # data["uuid"] = "a1234"
    # data["nickname"] = "testnickname"
    # data["money"] = 100.0
    # data["source"] = "pc"
    # data["headurl"] = "http://xxxx"


    # data = {}
    # data["_input_charset"] = "utf-8"
    # data["action"] = "gamelist"
    # data["channel"] = "apple"
    #data["uuid"] = 9385
    tmp = "4aca75305d29e2936d9d14dbcdcc5f130a58fd39041a35efc7b05c3f8035e46b59da3651807e8d2fd13c54815dbcf9de57f8f92af48e6f466d170decc68b5098"
    if isinstance(tmp, str):
        print(tmp.encode())

    # sign = MD5Sign.md5_sign(data, "n78he6awvxubs4gdpqc3")
    # print(sign)
    # data["sign"] = sign
    # data["sign_type"] = "md5"
    # print(MD5Sign.md5_verify(data, "n78he6awvxubs4gdpqc3"))

