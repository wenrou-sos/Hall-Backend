import os
from app import create_app
from flask_script import Manager, Server
from flask import request,abort,Response,redirect
from datetime import timedelta
import pg_general
import env_setting
from netaddr import IPNetwork,IPAddress
import time

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
manager = Manager(app)

server = Server(host="0.0.0.0", port=80,threaded=True,use_debugger=False)
manager.add_command("runserver", server)



lb_healthycheck_ip_list = list(IPNetwork('35.191.0.0/16')) + list(IPNetwork('130.211.0.0/22')) + list(IPNetwork('127.0.0.1')) + list(IPNetwork('114.33.71.4'))

@app.before_request
def limit_remote_addr():

    proto = request.headers.get('X-Forwarded-Proto')
    X_Forward_user_ip = request.headers.get('X-Forwarded-For', None)
    remoteaddr = IPAddress(request.remote_addr)

    # if env_setting.PRODUCTION_MODE == False:
    #
    #     if  X_Forward_user_ip is not None:
    #         if X_Forward_user_ip.split(',')[0] not in ("114.33.71.4","125.227.113.163"):
    #
    #             return "404 Not Found", 404
        # elif X_Forward_user_ip is None and remoteaddr not in lb_healthycheck_ip_list:
        #     return "404 Not Found", 404
    if proto == 'http':
        if env_setting.LOCAL_SERVER == True:
            return redirect("https://dev.jinsong.io", code=307)
        elif env_setting.PRODUCTION_MODE == False:
            return redirect("https://inner.jinsong.io",307)
        else:
            return redirect("https://jinsong.io",307)

@app.after_request
def change_server_response(response):
    response.headers['server'] =''
    return response

@manager.command
def test():
    print('test command')
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    pg_general.loggerinit()
    pg_general.writelog(pg_general.PG_LogerLevel.error, "webserver start")
    time.sleep(3)
    manager.run()
