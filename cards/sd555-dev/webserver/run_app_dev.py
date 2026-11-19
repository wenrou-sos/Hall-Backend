#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from app import create_app
from datetime import timedelta
import pg_general
from flask import request


app = create_app(os.getenv('FLASK_CONFIG') or 'default')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)

@app.before_request
def limit_remote_addr():
    pass

if __name__ == '__main__':
    pg_general.loggerinit()
    pg_general.writelog(pg_general.PG_LogerLevel.error,
                        "webserver start")
    app.run(debug=False ,ssl_context='adhoc',port=443,host='0.0.0.0')

