# -*- coding: utf-8 -*-

DEBUG=True

SANDBOX=True

CHAN_REDIS_HOST="192.168.33.10"
CHAN_REDIS_PORT=6379
CHAN_REDIS_DB=0
CHAN_REDIS_PASSWORD=""

REDIS_HOST="192.168.33.10"
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=""

MYSQL_HOST = "192.168.33.10"
MYSQL_PORT = 3306
MYSQL_AUTOCOMMIT = True
MYSQL_CHARSET = 'utf8'

MYSQL_USER = "im"
MYSQL_PASSWD = "123456"


MYSQL_IM_DATABASE = "gobelieve"
MYSQL_GB_DATABASE = "gobelieve"


# host,port,user,password,db,auto_commit,charset
MYSQL_IM = (MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWD, MYSQL_IM_DATABASE, MYSQL_AUTOCOMMIT, MYSQL_CHARSET)

MYSQL = (MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWD, MYSQL_GB_DATABASE, MYSQL_AUTOCOMMIT, MYSQL_CHARSET)


SOCKS5_PROXY = 'socks5://127.0.0.1:7778'


#平台appid
#平台appsecret
WX_APPID = "wx8ec7ea1fab1fbbf2"
WX_APPSECRET = "a27fb4d3ee36978b5288df1843a29c88"