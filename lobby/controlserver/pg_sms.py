
import aiohttp
import asyncio
import pg_general




# async def sendsms1(phone,validate_num):        # every8d
#     try:
#         validate_str = '金爽娛樂城 您的驗證碼為 {}'.format(str(validate_num))
#         smsurl = 'https://oms.every8d.com/API21/HTTP/sendSMS.ashx?UID={0}&PWD={1}&SB=&MSG={2}&DEST={3}&ST='
#         url = smsurl.format('82766299', 'G8D6QD', validate_str, phone)
#
#         async with aiohttp.ClientSession() as session:
#             async with session.get(url, timeout=60) as response:
#                 if response.status == 200:
#                     data = await response.text()
#     except:
#         pg_general.writelog(pg_general.PG_LogerLevel.error,
#                             'pg_sms:sendsms Exception except:{0}'.format(e))


async def sendsms2(phone,content):        # 三竹
    try:
        url = 'https://smsapi.mitake.com.tw/api/mtk/SmSend?username={0}&password={1}&dstaddr={2}&smbody={3}&dlvtime=&CharsetURL=UTF-8'
        url = url.format('82766299','play123',phone,'{}'.format(content))

        result = True
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=60) as response:
                if response.status == 200:
                    data = await response.text()
                    result = True
    except Exception as e:
        pass
    return result

async def sendsms(phone,content):
    await sendsms2(phone,content)

