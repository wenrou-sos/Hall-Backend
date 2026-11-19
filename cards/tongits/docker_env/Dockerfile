FROM python:3.6.3
#運行 tongits dummy 的容器範本
FROM 125.227.113.163:5000/dummy_env:v1


RUN pip install apscheduler
RUN mkdir dummy
COPY trunk /dummy
WORKDIR /dummy/server_dummy/dummy/
#port for assist
# EXPOSE 9302
#port for center
# EXPOSE 9312
#port for service
# EXPOSE 9500
RUN chmod 777 start_server.sh close_server.sh \
/dummy/server_dummy/dummy/assist/startup.sh \
/dummy/server_dummy/dummy/assist/shutdown.sh \
/dummy/server_dummy/dummy/center/startup.sh \
/dummy/server_dummy/dummy/center/shutdown.sh \
/dummy/server_dummy/dummy/game/startupall.sh \
/dummy/server_dummy/dummy/game/startup_demo.sh \
/dummy/server_dummy/dummy/game/shutdownall.sh \
/dummy/server_dummy/dummy/service/startup.sh \
/dummy/server_dummy/dummy/service/shutdown.sh


CMD [ "./start_server.sh" ]
