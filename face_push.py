# -*- coding: utf-8 -*-
import time
import logging
import sys
import redis
import json
import traceback
import binascii
import config
from utils import mysql
from ios_push import IOSPush
from huawei import HuaWeiPush
from mipush import MiPush
import user
import application

rds = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)
mysql_db = mysql.Mysql.instance(*config.MYSQL)

IOSPush.mysql = mysql_db
HuaWeiPush.mysql = mysql_db
MiPush.mysql = mysql_db

app_names = {}

def get_title(appid):
    if not app_names.has_key(appid):
        name = application.get_app_name(mysql_db, appid)
        if name is not None:
            app_names[appid] = name

    if app_names.has_key(appid):
        return app_names[appid]
    else:
        return ""


def ios_push(appid, u, content):
    token = u.apns_device_token
    sound = "apns.caf"
    badge = 0

    IOSPush.push(appid, token, content, sound, badge)

def receive_offline_message():
    while True:
        item = rds.blpop("voip_push_queue")
        if not item:
            continue
        _, msg = item
        logging.debug("push msg:%s", msg)
        obj = json.loads(msg)
        appid = obj["appid"]
        sender = obj["sender"]
        receiver = obj["receiver"]

        appname = get_title(appid)
        sender_name = user.get_user_name(rds, appid, sender)
        u = user.get_user(rds, appid, receiver)
        if u is None:
            logging.info("uid:%d nonexist", receiver)
            continue
        #找出最近绑定的token
        ts = max(u.apns_timestamp, u.xg_timestamp, u.ng_timestamp, u.mi_timestamp, u.hw_timestamp, u.gcm_timestamp)

        if sender_name:
            sender_name = sender_name.decode("utf8")
            content = "%s:%s"%(sender_name, u"请求与你通话")
        else:
            content = u"你的朋友请求与你通话"

        if u.apns_device_token and u.apns_timestamp == ts:
            ios_push(appid, u, content)
        elif u.mi_device_token and u.mi_timestamp == ts:
            MiPush.push_message(appid, u.mi_device_token, content)
        elif u.hw_device_token and u.hw_timestamp == ts:
            HuaWeiPush.push_message(appid, u.hw_device_token, content)
        else:
            logging.info("uid:%d has't device token", receiver)
            continue

def main():
    IOSPush.start()
    while True:
        try:
            receive_offline_message()
        except Exception, e:
            print_exception_traceback()
            time.sleep(1)
            continue

def print_exception_traceback():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logging.warn("exception traceback:%s", traceback.format_exc())

def init_logger(logger):
    root = logger
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(filename)s:%(lineno)d -  %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

if __name__ == "__main__":
    init_logger(logging.getLogger(''))
    main()
