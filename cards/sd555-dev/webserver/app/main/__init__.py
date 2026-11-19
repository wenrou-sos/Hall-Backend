from flask import Blueprint
import env_setting
main = Blueprint('main', __name__)

if env_setting.LOCAL_SERVER == True:
    API_SERVER_URL = 'http://localhost:81/'
else:
    if env_setting.PRODUCTION_MODE == False:
        API_SERVER_URL = 'http://10.140.0.37:81/'
    else:
        API_SERVER_URL = 'http://production-jinsong-apiserver.playgems.net:81/'

from . import errors
from . import member
from . import login
from . import ecpay
from . import script
from . import service
from . import topup
from . import utility
from . import root
from . import news
from . import rank
from . import Gash
