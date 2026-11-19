import asyncio
import os
import json
import aiohttp
import aiohttp.web

# from routes import setup_routes
from aiojobs.aiohttp import setup, spawn

from PIL import Image, ImageDraw, ImageFont




async def handler(request):
    await asyncio.sleep(5)
    return web.Response(text="OK")



async def handler(request):
    # job = await spawn(request, inner(request))
    # return await job.wait()
    # await asyncio.sleep(3)
    # return web.Response(text='test')
    asyncio.ensure_future(handler(request))

async def testmsm(app):
    url = 'https://oms.every8d.com/API21/HTTP/sendSMS.ashx?UID={0}&PWD={1}&SB=&MSG={2}&DEST={3}&ST='
    url = url.format('82766299','G8D6QD','測試娛樂城 您的驗證碼為 12345678','0977391022')


    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=60) as response:
            if response.status == 200:
                data = await response.text()
                print(data)
            else:
                print('return not 200')
    print('done')

async def testmsg2(app):
    url = 'https://smsapi.mitake.com.tw/api/mtk/SmSend?username={0}&password={1}&dstaddr={2}&smbody={3}&dlvtime=&CharsetURL=UTF-8'
    url = url.format('82766299','play123','0933185356','測試娛樂城 您的驗證碼為 0123456789')

    # url = 'http://smsapi.mitake.com.tw/api/mtk/SmQuery?username=82766299&password=play123&CharsetURL=UTF-8'
    print(url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=60) as response:
            if response.status == 200:
                data = await response.text()
                print(data)
            else:
                print('return not 200')
    print('done')

async def confirmios(app):
    try:

        IOS_IAP_VALIDATE_URL = 'https://buy.itunes.apple.com/verifyReceipt'
        url = IOS_IAP_VALIDATE_URL
        receipt_data = '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'
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"receipt-data": receipt_data}) as response:
                # response = await session.post(url, json={"receipt-data":receipt_data})
                if response.status != 200:
                    result = pg_general.Apiresult.othererror
                    raise ValueError('iap validate error')
                response_data = await response.text()
                response_data = json.loads(response_data)
                statuscode = response_data.get('status')

    except Exception as e:
        print(e)
    pass

def main33():
    loop = asyncio.get_event_loop()
    app = aiohttp.web.Application()

    loop.run_until_complete(confirmios(app))

    # asyncio.ensure_future(testmsg2(app))


    aiohttp.web.run_app(app, host="127.0.0.1", port=81)



def test(content):
    print(content)



if __name__ == '__main__':
    # img = Image.new('RGB', (100, 30), color=(73, 109, 137))
    #
    # fnt = ImageFont.truetype('font-chinese.otf', 15)
    # d = ImageDraw.Draw(img)
    # d.text((10, 10), "中文akdsfk;lasjdfasdfas", font=fnt,  fill=(255, 255, 0))
    #
    # img.save('pil_text_font.png')
    main33()
    pass


