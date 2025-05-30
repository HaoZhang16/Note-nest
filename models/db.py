import pymysql
from config import MYSQL_CONFIG


def get_conn():
    return pymysql.connect(**MYSQL_CONFIG)