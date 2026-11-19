mysqlassist协程模式用法
1.首先需要使用异步模式创建MySQLProxy，见配置表
2.通过MYPGuard.MYP(proxy_name)获得对应的MYP
3.MYP下有Update和AsyncUpdate,Update函数为同步调用方式（每帧或定时调用），AsyncUpdate调用方式如下：
'''
@gen.coroutine
def RunMYPRecv():
    await MYPGuard.MYP("game").AsyncUpdate()

if __name__ == "__main__":
    RunMYPRecv()
    IOLoop.current().start()
'''