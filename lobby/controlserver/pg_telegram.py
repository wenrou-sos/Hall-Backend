import pg_general
from telebot import TeleBot

import env_setting

app = TeleBot(__name__)

FEEDBACK_CHATROOM = -410370456
API_TOKEN = '1413875566:AAFmKonsnUjVyuue7_F76-nN3sY633hL-oM'

FEEDBACK_STR ='https://api.telegram.org/bot'+API_TOKEN+'/sendMessage?chat_id='+ str(FEEDBACK_CHATROOM)+'&text={}'

app.config['api_key'] = API_TOKEN

class PG_TELEBOT:
    def __init__(self):
        self.app = app

    def __del__(self):
        del self.app

    def sendfeedbackmsg(self,msg,chatroomtype):

        try:
            if env_setting.LOCAL_SERVER == True:
                msg = 'LocalServer_' + msg
            elif env_setting.PRODUCTION_MODE == False:
                msg = 'InnerTest_' + msg
            if chatroomtype == 'feedback':
                self.app.send_message(FEEDBACK_CHATROOM,msg)
            elif chatroomtype == 'apiadmin':
                self.app.send_message(FEEDBACK_CHATROOM,msg)


        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'PG_TELEBOT:sendfeedbackmsg except:{0},msg:{1},chatroomtype:{2}'.format(e,msg,chatroomtype))




    def senddailyreport(self,chatroomid,msg):
        try:
            if chatroomid is None:
                raise Exception('chatroom id is None')

            chatroomid = chatroomid.strip()
            if len(chatroomid) <=0:
                raise Exception('chatroom id is null')

            listchatroomid = chatroomid.split(',')
            for item in listchatroomid:
                self.app.send_message(int(item), msg)

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'PG_TELEBOT:senddailyreport except:{0},msg:{1}'.format(e, msg))

def main():
    chat_dest = FEEDBACK_CHATROOM
    msg = 'test gorden msg'
    app.send_message(chat_dest, msg)
    print('done')
if __name__ == '__main__':
    main()

