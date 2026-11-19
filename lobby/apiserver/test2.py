from hanziconv import HanziConv
print(HanziConv.toSimplified('繁簡轉換器a'))
# 繁简转换器
print(HanziConv.toTraditional('繁简转换器'))

print(HanziConv.toTraditional('繁簡轉換器'))

original = '繁簡轉換器1'
transform = HanziConv.toTraditional(original)
print('is same: {}'.format(original==transform))


# 繁簡轉換器
print(HanziConv.same('繁簡轉換器', '繁简转换器'))
# True

def strQ2B(ustring):
    """把字串全形轉半形"""
    rstring = ""
    for uchar in ustring:
        inside_code=ord(uchar)
        if inside_code==0x3000:
            inside_code=0x0020
        else:
            inside_code-=0xfee0
        if inside_code<0x0020 or inside_code>0x7e:   #轉完之後不是半形字元返回原來的字元
            rstring  = uchar
            rstring  = chr(inside_code)
    return rstring

import re


def check_chinese(str1):

    for item in str1:
        code = ord(item)
        if code < 0x4e00 or code > 0x9fa5:
            return False

    return True



r1 = '[a-zA-Z0-9’!"#$%&\'()*+,-./:;<=>?@，。?★、 …【】《》？“”‘’！[\\]^_`{|}~]+'

prog = re.compile(r1)
# result = prog.search(strQ2B('我是ｋ'))
# print('kkk' + result)

print(ord('我'))

print(check_chinese('我'))


