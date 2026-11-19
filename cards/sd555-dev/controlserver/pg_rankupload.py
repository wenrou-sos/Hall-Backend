from google.cloud import storage
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from google.resumable_media import requests, common
import pg_general
import aiohttp.web
import os
import env_setting
import asyncio
import json
if env_setting.PRODUCTION_MODE == True:

    BUCKET_NAME = 'production_jinsong_webserverstatic'

else:
    BUCKET_NAME = 'innerwebserverstatic'

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
            # self._blob.cache_control = 'application/json'
            self._blob.content_type = 'application/json'
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



class PG_RANKUPLOAD:


    def upload_bucket(self,filename,jsondata):
        result = False
        avatar_url = ""
        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'upload_bucket filename:{0},jsondata:{1}'.format(filename,jsondata))
            credentials = service_account.Credentials.from_service_account_file(os.path.dirname(os.path.abspath(__file__)) + "//cert_bucket_writer.json",scopes=['email','https://www.googleapis.com/auth/devstorage.full_control'])

            storage_client = storage.Client(credentials=credentials, project="playgemsforfunbackend")
            storage_client.credentials = credentials

            errcount = 0
            for _ in range(3):
                try:

                    with GCSObjectStreamUpload(client=storage_client, bucket_name=BUCKET_NAME, blob_name=filename) as s:
                        s.write(json.dumps(jsondata).encode())
                    result = True
                    s.setmetadata()
                    break

                    # await asyncio.sleep(0)
                except Exception as e:
                    # await asyncio.sleep(0)
                    errcount += 1
                    pg_general.writelog(pg_general.PG_LogerLevel.error,
                                        'upload_bucket exception :{0},errcount:{1}'.format(e,errcount))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'upload_bucket exception :{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'upload_bucket done filename:{0}'.format(filename))
            return result,avatar_url

    def upload_suspenselist(self,filename,jsondata):
        result = False

        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'upload_suspenselist filename:{0},jsondata:{1}'.format(filename, jsondata))
            credentials = service_account.Credentials.from_service_account_file(
                os.path.dirname(os.path.abspath(__file__)) + "//cert_bucket_writer.json",
                scopes=['email', 'https://www.googleapis.com/auth/devstorage.full_control'])

            storage_client = storage.Client(credentials=credentials, project="playgemsforfunbackend")
            storage_client.credentials = credentials

            errcount = 0
            for _ in range(3):
                try:

                    with GCSObjectStreamUpload(client=storage_client, bucket_name=BUCKET_NAME, blob_name=filename) as s:
                        s.write(json.dumps(jsondata).encode())
                    result = True
                    s.setmetadata()
                    break

                    # await asyncio.sleep(0)
                except Exception as e:
                    # await asyncio.sleep(0)
                    errcount += 1
                    pg_general.writelog(pg_general.PG_LogerLevel.error,
                                        'upload_suspenselist exception :{0},errcount:{1}'.format(e, errcount))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'upload_suspenselist exception :{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'upload_suspenselist done filename:{0}'.format(filename))
            return

    def upload_newslist(self,filename,jsondata):
        result = False

        try:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'upload_newslist filename:{0},jsondata:{1}'.format(filename, jsondata))
            credentials = service_account.Credentials.from_service_account_file(
                os.path.dirname(os.path.abspath(__file__)) + "//cert_bucket_writer.json",
                scopes=['email', 'https://www.googleapis.com/auth/devstorage.full_control'])

            storage_client = storage.Client(credentials=credentials, project="playgemsforfunbackend")
            storage_client.credentials = credentials

            errcount = 0
            for _ in range(3):
                try:

                    with GCSObjectStreamUpload(client=storage_client, bucket_name=BUCKET_NAME, blob_name=filename) as s:
                        s.write(json.dumps(jsondata).encode())
                    result = True
                    s.setmetadata()
                    break

                    # await asyncio.sleep(0)
                except Exception as e:
                    # await asyncio.sleep(0)
                    errcount += 1
                    pg_general.writelog(pg_general.PG_LogerLevel.error,
                                        'upload_newslist exception :{0},errcount:{1}'.format(e, errcount))

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'upload_newslist exception :{0}'.format(e))
        finally:
            pg_general.writelog(pg_general.PG_LogerLevel.info,
                                'upload_newslist done filename:{0}'.format(filename))
            return

if __name__ == '__main__':
    pg_general.loggerinit()
    obj = PG_RANKUPLOAD()
    obj.upload_bucket('rankdata/test.json',{'test':2})
    print('1')


