
import json
import hashlib
from tornado.web import RequestHandler

class HDRDebug(RequestHandler):
    sKey = "@#1#imaohw#1#@"
    async def post(self):
        result = "Unknown error!"
        try:
            content = self.get_body_argument("ctn", strip = False)
            sign = self.get_body_argument("sign")
            tmp1 = hashlib.md5(content.encode()).hexdigest()
            tmp2 = hashlib.md5(HDRDebug.sKey.encode()).hexdigest()
            ori_sign = ""
            if tmp1 > tmp2:
                ori_sign = tmp2[:16] + tmp1[16:]
            else:
                ori_sign = tmp1[:16] + tmp2[16:]

            ori_sign = hashlib.sha1(ori_sign.encode()).hexdigest()

            if ori_sign == sign:
                _ = {}
                try:
                    exec(content, globals(), locals())
                except Exception as e:
                    result = str(e)
                else:
                    try:
                        result = json.dumps({ "ex" : _ })
                    except Exception as e:
                        result = str(e)
            else:
                result = "Sign error!"
        except:
            PrintEXC()
        self.write(result)
        self.flush()
        self.finish()