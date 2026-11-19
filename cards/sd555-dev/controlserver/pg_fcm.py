# Send to single device.
from pyfcm import FCMNotification
import pg_general


FCM_API_KEY = 'AAAAQogvqJc:APA91bFO9VPahTzYXA0lzHvLNOM2ysQS30DC436zigWzH3hDhJzXmDHH3FdoUI8Vw0iQZLRhCXlu2FpPnEyZ4FwuEuo9JbY9L2dCvuASp2wOT_iS0r3_hQzXsAqVdlQPksxC40crWSNc'

push_service = FCMNotification(api_key=FCM_API_KEY)

FCM_TOPIC = 'globaljinsong'

def send_notification_multiple_device(title, msg, token=None):  # 信箱獎勵發放 推播
    try:
        if token is not None:
            if len(token) > 0:

                message_title = title
                message_body = msg
                result = push_service.notify_multiple_devices(registration_ids=token, message_title=message_title,
                                                              message_body=message_body)
                pg_general.writelog(pg_general.PG_LogerLevel.error,
                                    "send_notification_multiple_device result: {}".format(result))
    except Exception as e:
        pg_general.writelog(pg_general.PG_LogerLevel.error, "send_notification_multiple_device error: {}".format(e))
        pass

def main():
    push_service = FCMNotification(api_key=FCM_API_KEY)

    registration_id = []

    message_title = "ru;3"
    message_body = "test body"
    # result = push_service.notify_multiple_devices(registration_ids=registration_id, message_title=message_title, message_body=message_body)
    data_message = {
        "title": "Mario",
        "body": "great match!"

    }
    result = push_service.notify_topic_subscribers(topic_name=FCM_TOPIC,message_title=message_title,message_body=message_body)
    # result = push_service.notify_topic_subscribers(topic_name="globaljinsong",data_message=data_message, dry_run=False)

    print(result)

if __name__ == '__main__':
    # main()
    pass
    # send_notification_multiple_device('內購掉單處理','您好,稍早您有發生App內購掉單情況,已經為您補上點數,請至商城兌換區兌換,諸多不便敬請見諒,祝您手氣旺 中大獎',["cbnRKQKLdE9lkkxvlmmgZM:APA91bHy4e_gXktRgDSPwuaTShUOHr4tknGxH_FD1ld6qRLlRi38aOl11bpQmghpUsIvnMYhHCJJM6cnUe07X0GZHJX6ndGd4nvIsP7ru5NX62TyJLjeNPbh4q7i8n0eUA5HL-VdAIKh"])
    # send_notification_multiple_device(["dAn_Fevbt68:APA91bEmpjp9qSseNaDYz694TPzEHdZ6Ouan1InAqJpx9q9yIX6HRaAWe-jbF5BAoffx8Unsb-fz_nWOFkaS1TWu2SP0ZhdoLzKcTjS_gEbi_vzzat86DkqH8mSwEfEn-Mtaexs_EYY9"])