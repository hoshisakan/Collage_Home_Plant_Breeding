import datetime as dt


class DateTime():
    @staticmethod
    def GetDate():
        #TODO 返回當前的日期
        today = dt.datetime.now().strftime("%Y-%m-%d")
        return today

    @staticmethod
    def GetDateTime():
        #TODO 返回當前的日期與時分秒
        today = dt.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        return today

    @staticmethod
    def GetDateTimeCurrent():
        today = dt.datetime.now()
        return today
