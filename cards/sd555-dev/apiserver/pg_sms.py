
import aiohttp
import asyncio
import pg_general
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
from pathlib import Path



async def sendsms1(phone,validate_num):        # every8d
    try:
        # validate_str = '金爽娛樂城 您的驗證碼為 {}'.format(str(validate_num))
        # validate_str = 'Lucky Angkor verification code is {}'.format(str(validate_num))
        validate_str = 'Phone verification code is {}'.format(str(validate_num))
        smsurl = 'https://oms.every8d.com/API21/HTTP/sendSMS.ashx?UID={0}&PWD={1}&SB=&MSG={2}&DEST={3}&ST='
        url = smsurl.format('82766299', 'G8D6QD', validate_str, phone)

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=60) as response:
                if response.status == 200:
                    data = await response.text()
    except:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'pg_sms:sendsms Exception except:{0}'.format(e))


async def sendsms2(phone,validate_num):        # 三竹
    url = 'https://smsapi.mitake.com.tw/api/mtk/SmSend?username={0}&password={1}&dstaddr={2}&smbody={3}&dlvtime=&CharsetURL=UTF-8'
    # url = url.format('82766299','play123',phone,'金爽娛樂城 您的驗證碼為 {}'.format(validate_num))
    # url = url.format('82766299', 'play123', phone, 'Lucky Angkor verification code is {}'.format(validate_num))
    url = url.format('82766299', 'play123', phone, 'Phone verification code is {}'.format(validate_num))
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=60) as response:
            if response.status == 200:
                data = await response.text()

async def sendemail1(email, validate_num):
    try:
        content = MIMEMultipart()
        content["subject"] = "測試123"  # 標題
        content["from"] = "playstar.brian@gmail.com"  # 寄件者
        content["to"] = email  # 收件者

        content.attach(MIMEText("SD555 email validation code is " + validate_num))  # 郵件內容

        with smtplib.SMTP(host="smtp.gmail.com", port="587") as smtp:  # 設定SMTP伺服器
            try:
                smtp.ehlo()  # 驗證SMTP伺服器
                smtp.starttls()  # 建立加密傳輸
                smtp.login("playstar.brian@gmail.com", "qxlhzikfobzbstoy")  # 登入寄件者gmail
                smtp.send_message(content)  # 寄送郵件
            except Exception as e:
                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                    'pg_asqldb:sendemailsmtp Exception except:{0}'.format(e))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'pg_asqldb:sendemail1 Exception except:{0}'.format(e))


async def sendsms(phone,validate_num):
    await sendsms2(phone,validate_num)

async def sendemail(email, validate_num):
    await sendemail1(email, validate_num)
