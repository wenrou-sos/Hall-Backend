# import jwt
import pg_general
import asyncio
#
#
# SECRET = '-----BEGIN PUBLIC KEY-----\n' \
#          'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4dGQ7bQK8LgILOdLsYzf' \
#          'ZjkEAoQeVC/aqyc8GC6RX7dq/KvRAQAWPvkam8VQv4GK5T4ogklEKEvj5ISBamdD' \
#          'Nq1n52TpxQwI2EqxSk7I9fKPKhRt4F8+2yETlYvye+2s6NeWJim0KBtOVrk0gWvE' \
#          'Dgd6WOqJl/yt5WBISvILNyVg1qAAM8JeX6dRPosahRVDjA52G2X+Tip84wqwyRpU' \
#          'lq2ybzcLh3zyhCitBOebiRWDQfG26EH9lTlJhll+p/Dg8vAXxJLIJ4SNLcqgFeZe' \
#          '4OfHLgdzMvxXZJnPp/VgmkcpUdRotazKZumj6dBPcXI/XID4Z4Z3OM1KrZPJNdUh' \
#          'xwIDAQAB' \
#          '\n-----END PUBLIC KEY-----'
#
# # https://appleid.apple.com/auth/keys
#
# def apple_sign_in_check(logintoken,auserid,atoken,aauthcode):
#     result = False
#     data = {}
#     try:
#         pg_general.writelog(pg_general.PG_LogerLevel.error,
#                             'apple_sign_in_check start logintoken:{},userid:{},atoken:{},authcode:{}'.format(logintoken,auserid,atoken,aauthcode ))
#
#         return_data = jwt.decode(atoken, SECRET, algorithms=['RS256'], options={'verify_exp': True},audience='com.slots.casino.jinsong')
#
#         cmp_auserid = return_data.get('sub')
#         email = return_data.get('email')
#         iss = return_data.get('iss')
#         if iss != 'https://appleid.apple.com':
#             return result,data
#
#         if cmp_auserid != auserid:
#             return result,data
#
#         data = {
#             "email": email
#         }
#         result = True
#
#     except Exception as e:
#         pg_general.writelog(pg_general.PG_LogerLevel.error,
#                             'apple_sign_in_check error logintoken:{0},e:{1}'.format(logintoken,e))
#
#     return result,data



import jwt
from jwt.algorithms import RSAAlgorithm
import requests
import aiohttp.web
from time import time
import json
import os


APPLE_PUBLIC_KEY_URL = "https://appleid.apple.com/auth/keys"
APPLE_PUBLIC_KEY = None
APPLE_KEY_CACHE_EXP = 60 * 60 * 24
APPLE_LAST_KEY_FETCH = 0

#
# class AppleUser(object):
#     def __init__(self, apple_id, email=None):
#         self.id = apple_id
#         self.email = email
#         self.full_user = False
#
#         if email is not None:
#             self.full_user = True
#
#     def __repr__(self):
#         return "<AppleUser {}>".format(self.id)


async def _fetch_apple_public_key():
    # Check to see if the public key is unset or is stale before returning
    global APPLE_LAST_KEY_FETCH
    global APPLE_PUBLIC_KEY

    if (APPLE_LAST_KEY_FETCH + APPLE_KEY_CACHE_EXP) < int(time()) or APPLE_PUBLIC_KEY is None:
        url = APPLE_PUBLIC_KEY_URL
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=60) as response:
                if response.status == 200:
                    data = await response.json()

                    APPLE_PUBLIC_KEY = RSAAlgorithm.from_jwk(json.dumps(data["keys"][0]))
                    APPLE_LAST_KEY_FETCH = int(time())
                else:
                    data = await response.text()
        # key_payload = requests.get(APPLE_PUBLIC_KEY_URL).json()




    return APPLE_PUBLIC_KEY


async def _decode_apple_user_token(apple_user_token):
    public_key = await _fetch_apple_public_key()

    print(public_key)
    try:
        token_decode = jwt.decode(apple_user_token, public_key, audience="com.slots.casino.jinsong", algorithm="RS256",verify=False)
    except jwt.exceptions.ExpiredSignatureError as e:
        raise Exception("That token has expired")
    except jwt.exceptions.InvalidAudienceError as e:
        raise Exception("That token's audience did not match")
    except Exception as e:

        raise Exception("An unexpected error occoured")

    return token_decode


async def apple_sign_in_check(logintoken,auserid,atoken,aauthcode):
    try:
        pg_general.writelog(pg_general.PG_LogerLevel.info, 'apple_sign_in_check start logintoken:{},userid:{},atoken:{},authcode:{}'.format(logintoken,auserid,atoken,aauthcode ))

        result = False
        data = {}

        return_data = await _decode_apple_user_token(atoken)



        cmp_auserid = return_data.get('sub')
        email = return_data.get('email')
        iss = return_data.get('iss')
        if iss != 'https://appleid.apple.com':
            return result,data

        if cmp_auserid != auserid:
            return result,data

        data = {
            "email": email
        }
        result = True

    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error,
                            'apple_sign_in_check error logintoken:{0},e:{1}'.format(logintoken, e))
    return result,data




async def testmain():
    userid = '001660.e2b69c06e90f408eacef98b8bb8b1fd0.0301'
    authcode = 'c3924fd4b3d3146f4bf013e591a61ade5.0.nrwwq.Om2e1JhZJt2eiBtOXb_DaA'
    token = 'eyJraWQiOiJlWGF1bm1MIiwiYWxnIjoiUlMyNTYifQ.eyJpc3MiOiJodHRwczovL2FwcGxlaWQuYXBwbGUuY29tIiwiYXVkIjoiY29tLnNsb3RzLmNhc2luby5qaW5zb25nIiwiZXhwIjoxNTk2NjIxMTM0LCJpYXQiOjE1OTY2MjA1MzQsInN1YiI6IjAwMTY2MC5lMmI2OWMwNmU5MGY0MDhlYWNlZjk4YjhiYjhiMWZkMC4wMzAxIiwiY19oYXNoIjoiOFVkTWNSR1FQV01zQk15RU1TWW1MZyIsImVtYWlsIjoicGxheWdlbXMuZGV2LmlvczFAaWNsb3VkLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjoidHJ1ZSIsImF1dGhfdGltZSI6MTU5NjYyMDUzNCwibm9uY2Vfc3VwcG9ydGVkIjp0cnVlfQ.wBx275tTXVHG4YIa8w-JeXFMoawu1PsnZTjl2YAC0r5Fv3zyUQIlHwm1T7OK29lRtQYLqzEZ1fcwFMayjgInPjKMnYGK0iMcFG0mkw-Q1kp78ADk97JkymYMJ_JOFfNK8Z1yfCS7X43ms1AQ8e8QIAMWALTLzICoydWQb2c6D0lxQ7CLDjTgxswNtKQ6xPydngfhpn1W3jV8dAzXnv-35lBxyQYQYnZ8xlGZTQejx1Wj-6p4G8zVOgpQE37gWpey5E6-VuKL2i5wrVXLOsVVlAV1T1cH-Qv0c2ZoadZj_8muxxv3y42T61ktLdIfyI3WBp-3UkvlJrwzgXY-gDcIOg'
    # result , resultdata = apple_sign_in_check('123',userid,token,authcode)
    apple_user = await apple_sign_in_check('123', userid, token, authcode)
    print(1)









if __name__ == '__main__':


    pg_general.loggerinit()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(testmain())