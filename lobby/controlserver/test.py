# from apscheduler.scheduler.。asyncio import AsyncIOScheduler
import os
import asyncio
import aiohttp.web
# from datetime import datetime
# sched = AsyncIOScheduler()

urllist = [("sseat_PSS-APP-00019_54","PSS-APP-00019"),
("sseat_PSS-APP-00028_81","PSS-APP-00028"),
("sseat_PSS-APP-00065_37","PSS-APP-00065"),
("sseat_PSS-APP-00108_60","PSS-APP-00108"),
("sseat_PSS-APP-00019_11","PSS-APP-00019"),
("sseat_PSS-APP-00028_89","PSS-APP-00028"),
("sseat_PSS-APP-00019_1","PSS-APP-00019"),
("sseat_PSS-APP-00092_75","PSS-APP-00092"),
("sseat_PSS-APP-00092_3","PSS-APP-00092"),
("sseat_PSS-APP-00092_28","PSS-APP-00092"),
("sseat_PSS-APP-00092_19","PSS-APP-00092"),
("sseat_PSS-APP-00092_24","PSS-APP-00092"),
("sseat_PSS-APP-00092_17","PSS-APP-00092"),
("sseat_PSS-APP-00112_70","PSS-APP-00112"),
("sseat_PSS-APP-00107_40","PSS-APP-00107"),
("sseat_PSS-APP-00092_5","PSS-APP-00092"),
("sseat_PSS-APP-00099_21","PSS-APP-00099"),
("sseat_PSS-APP-00107_3","PSS-APP-00107"),
("sseat_PSS-APP-00044_11","PSS-APP-00044"),
("sseat_PSS-APP-00025_51","PSS-APP-00025"),
("3703","PSS-APP-00009")

]

#
#
# @sched.scheduled_job('interval', seconds=3)
# def timed_job():
#     print('This job is run every three minutes.')
#
# @sched.scheduled_job('cron', day_of_week='mon-fri', hour='0-9', minute='30-59', second='*/3')
# def scheduled_job():
#     print('This job is run every weekday at 5pm.')
#     print('before the start funciton')
#     sched.start()
#     print("let us figure out the situation")
#


#
# async def tick():
#     print('Tick! The time is: %s' % datetime.now())

HSOT_ID = 'a7f2403adb0fd1fb885828b253f709cf'

# PS_FORCE_DELETE_GAME = 'http://pg-api.playgems.net/admin/clearrecovery/?host_id=12c68ff93b5607c5465413b403aaa8d2&member_id={}&game_id={}&force_delete=true'
PS_FORCE_DELETE_GAME = 'https://dev-api.iplaystar.net/admin/clearrecovery/?host_id={}&member_id={}&game_id={}&force_delete=true'
async def testmain():

        for tmpurl in urllist:
            try:
                url = PS_FORCE_DELETE_GAME.format(HSOT_ID,tmpurl[0],tmpurl[1])
                async with aiohttp.ClientSession() as session:
                    print('url : {}'.format(url))
                    async with session.get(url, timeout=60) as response:
                        if response.status == 200:
                            data1 = await response.json()
                            # result1 = pg_general.Apiresult.success
                            print('response: {}'.format(data1))

                        else:

                            print("not 200 : {}".format(response.status))
                            await asyncio.sleep(0)

            except Exception as e:

                # pg_general.writelog(pg_general.PG_LogerLevel.error,
                #                     'pg_asqldb:force_delete_game exception 1: {0},errcount:{1}'.format(e, errcount))
                print('exceptipn: {}'.format(e))
if __name__ == '__main__':
    # scheduler = AsyncIOScheduler()
    # scheduler.add_job(tick, 'cron', second='0-59')
    # scheduler.start()
    # print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
    #
    # # Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
    # try:
    #     asyncio.get_event_loop().run_forever()
    # except (KeyboardInterrupt, SystemExit):
    #     pass
    loop = asyncio.get_event_loop()
    loop.run_until_complete(testmain())