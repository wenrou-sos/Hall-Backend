import env_setting

from pyga.requests import Tracker, Page, Session, Visitor,Event
import asyncio
from datetime import datetime



if env_setting.PRODUCTION_MODE == True:
    g_ga_tracker = Tracker('UA-146529577-1',"playgems.io")
else:
    g_ga_tracker = Tracker("UA-146433184-1", "playgems.io")

class PG_GA():

    def __init__(self,ip,memberid=None):
        self.session = Session()
        self.visitor = Visitor()
        self.visitor.ip_address = ip
        if memberid is not None:
            self.visitor.unique_id = memberid

    async def a_send_page_view(self,page,title):
        try:
            self.page = Page(page)
            self.page.title = title
            g_ga_tracker.track_pageview(self.page, self.session, self.visitor)
            del self.page
            self.page = None

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'PG_GA send_page_view except:{0}'.format(e))

    def send_page_view(self,page,title):
        # asyncio.ensure_future(self.send_page_view(page,title))
        try:
            self.page = Page(page)
            self.page.title = title
            g_ga_tracker.track_pageview(self.page, self.session, self.visitor)
            del self.page
            self.page = None

        except Exception as e:
            pg_general.writelog(pg_general.PG_LogerLevel.error,
                                'PG_GA send_page_view except:{0}'.format(e))
    def set_ip(self,ip):
        self.visitor.ip_address = ip

    def set_memberid(self,memberid):
        self.visitor.unique_id = memberid

    def send_event_action(self,category,action,value):
        pass

    def __del__(self):
        del self.visitor
        del self.session


def task():

    obj = PG_GA('104.35.10.201')
    obj.send_page_view('/ddd','login_title')
    del obj
    print('del')

def main():
    task()

if __name__ == '__main__':
   main()