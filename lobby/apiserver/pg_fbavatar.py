from google.cloud import storage
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from google.resumable_media import requests, common
import pg_general
import aiohttp.web
import os
import env_setting
import facebook
import asyncio

if env_setting.PRODUCTION_MODE == True:
    AVATAR_URL = 'https://production-jinsong-resource-avatar.playgems.net/avatar_{0}.png'
    AVATAR_DEFAULT = 'https://production-jinsong-resource-avatar.playgems.net/avatar_camp0_default.png'
    AVATAR_FB_DEFAULT = 'https://production-jinsong-resource-avatar.playgems.net/avatar_fb_default.png'
    AVATAR_SYSTEM = 'https://production-jinsong-resource-avatar.playgems.net/avatar_system.png'
    BUCKET_NAME = 'production_jinsong_resource_avatar'

else:
    AVATAR_URL = 'http://inner-resource-avatar.playgems.net/avatar_{0}.png'
    AVATAR_DEFAULT = 'http://inner-resource-avatar.playgems.net/avatar_camp0_default.png'
    AVATAR_FB_DEFAULT = 'http://inner-resource-avatar.playgems.net/avatar_fb_default.png'
    AVATAR_SYSTEM = 'http://inner-resource-avatar.playgems.net/avatar_system.png'
    BUCKET_NAME = 'resource-avatar'

class GCSObjectStreamUpload(object):
    def __init__(
            self,
            client: storage.Client,
            bucket_name: str,
            blob_name: str,
            chunk_size: int=256 * 1024
        ):
        self._client = client
        self._bucket = self._client.bucket(bucket_name)
        self._blob = self._bucket.blob(blob_name)

        self._buffer = b''
        self._buffer_size = 0
        self._chunk_size = chunk_size
        self._read = 0

        self._transport = AuthorizedSession(
            credentials=self._client.credentials
        )
        self._request = None  # type: requests.ResumableUpload

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, *_):

        if exc_type is None:
            self.stop()

    def start(self):
        url = (
            'https://www.googleapis.com/upload/storage/v1/b/{0}/o?uploadType=resumable'.format(self._bucket.name)

        )
        self._request = requests.ResumableUpload(
            upload_url=url, chunk_size=self._chunk_size
        )
        self._request.initiate(
            transport=self._transport,
            #content_type='application/octet-stream',
            content_type='image/png',
            stream=self,
            stream_final=False,
            metadata={'name': self._blob.name,'cache-control':'public,max-age=60'},
        )

    def stop(self):
        self._request.transmit_next_chunk(self._transport)

    def write(self, data: bytes) -> int:
        data_len = len(data)
        self._buffer_size += data_len
        self._buffer += data
        del data
        while self._buffer_size >= self._chunk_size:
            try:
                self._request.transmit_next_chunk(self._transport)
            except common.InvalidResponse:
                self._request.recover(self._transport)
        return data_len

    def setmetadata(self):
        try:
            self._blob.cache_control = 'public,max-age=3600'
            self._blob.patch()
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'setmetadata exception:{0}'.format(e))
    def read(self, chunk_size: int) -> bytes:
        # I'm not good with efficient no-copy buffering so if this is
        # wrong or there's a better way to do this let me know! :-)
        to_read = min(chunk_size, self._buffer_size)
        memview = memoryview(self._buffer)
        self._buffer = memview[to_read:].tobytes()
        self._read += to_read
        self._buffer_size -= to_read
        return memview[:to_read].tobytes()

    def tell(self) -> int:
        return self._read

class PG_FBAVATAR:
    async def upload_avatar(self,memberid,url):
        result = False
        avatar_url = ""
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'upload_avatar memberid:{0}, url:{1}'.format(memberid, url))
            credentials = service_account.Credentials.from_service_account_file(os.path.dirname(os.path.abspath(__file__)) + "//cert_bucket_writer.json",scopes=['email','https://www.googleapis.com/auth/devstorage.full_control'])

            storage_client = storage.Client(credentials=credentials, project="playgemsforfunbackend")
            storage_client.credentials = credentials

            errcount = 0
            for _ in range(3):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as response:
                            if response.status == 200:
                                with GCSObjectStreamUpload(client=storage_client, bucket_name=BUCKET_NAME, blob_name='avatar_{0}.png'.format(memberid)) as s:

                                    s.write(await response.content.read())

                                    avatar_url = AVATAR_URL.format(memberid)
                                    result = True
                                s.setmetadata()
                                break
                            else:
                                raise Exception("respone is not 200")
                    await asyncio.sleep(0)
                except Exception as e:
                    await asyncio.sleep(0)
                    errcount += 1
                    pg_general.writelog(pg_general.PG_LogerLevel.error,
                                        'upload_avatar exception :{0},errcount:{1}'.format(e,errcount))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'upload_avatar exception :{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'upload_avatar done memberid:{0}'.format(memberid))
            return result,avatar_url



    async def getfbdata(self,logintoken,memberid,fbtoken):
        try:
            result = pg_general.Apiresult.othererror
            resultdata = {
                "id": None,
                "name": None,
                "email": None
            }

            graph = facebook.GraphAPI(fbtoken)
            args = {'fields': 'id,name,email'}
            profile = graph.get_object('me', **args)

            resultdata = profile
            result = pg_general.Apiresult.success
        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'getfbdata getfbdata exception :{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'getfbdata getfbdata done memberid:{0},resultdata:{1}'.format(memberid,resultdata))
            return result, resultdata

def getfbemail():

    graph = facebook.GraphAPI('REDACTED_FB_TOKEN')

    args = {'fields': 'id,name,email'}
    profile = graph.get_object('me', **args)

    # places = graph.search(type='place',
    #                       center='37.4845306,-122.1498183',
    #                       fields='name,location')
    # friends = graph.get_connections(id='me', connection_name='comments')
    print(profile)
if __name__ == '__main__':
    getfbemail()
    print('1')


