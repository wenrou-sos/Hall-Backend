import requests
content = '親愛的玩家您好，\n ' \
          '謝謝您的回饋問卷,可以讓金爽更好更進步,您的回饋問卷贈禮百萬銀幣,已經放入您的信箱中,請至信箱中領取.\n '
content2 = '再次感謝您的支持與回饋鼓勵,我們會重視您的意見與回饋,如果可行將會納入未來修改方向,謝謝您, 祝您身體健康,中大獎喔!!'


listmember =[
]

listmember2 = [
    10685,10685
]
for item in listmember:
    r = requests.get('http://34.80.63.60:81/jinsong/servicetouser/?content={}&memberid={}'.format(content,item))
    print(r)
    r = requests.get('http://34.80.63.60:81/jinsong/servicetouser/?content={}&memberid={}'.format(content2, item))
    print(r)