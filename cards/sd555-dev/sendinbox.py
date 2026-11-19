import requests
import json
import sys

sendinbox = {
    "title": "我是房卡",
    "content": "我是房卡",
    "uri": "uri",
    "promotionid": "71",
    "amount": 99999,
    "dateline": "2022-07-26 00:00:00",
    "member_list": [91447]
}

headers = {'Content-Type': 'application/json'}
domain = 'http://34.87.72.250:81/sendinboxtomember/'

for i in range(100):
    r = requests.post(domain, data = json.dumps(sendinbox))

print('sendinbox success')

# domain以及host-api-key要帶多代理商資訊，只能連同其他商戶一起踢除，沒辦法只踢單一商戶
