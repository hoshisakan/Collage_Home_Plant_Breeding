from pymysql.cursors import DictCursor
#TODO 引入mysql模組
import pymysql
import sys
#TODO 返回前兩層目錄
sys.path.append("...")
# TODO 引入配置檔的內容
import instance.config as MySQL
# import config as MySQL
import traceback

class DataBase():
    def __init__(self, *args):
        self.connection = pymysql.connect(
            host=MySQL.MYSQL_HOST,
            user=MySQL.MYSQL_USER,
            database=MySQL.MYSQL_DB,
            password=MySQL.MYSQL_PASSWORD,
            port=MySQL.MYSQL_PORT,
            cursorclass=DictCursor
        )
        self.connection.autocommit(True)
        self.cursor = self.connection.cursor()

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.connection.close()
