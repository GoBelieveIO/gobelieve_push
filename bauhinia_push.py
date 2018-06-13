# -*- coding: utf-8 -*-
import time
import logging
import sys

reload(sys)
sys.setdefaultencoding("utf-8")

import redis
import json
import config
import traceback
import binascii
import requests
from urllib import urlencode

from utils import mysql
from ios_push import IOSPush
from android_push import SmartPush
from xg_push import XGPush
from huawei import HuaWeiPush
from gcm import GCMPush
from mipush import MiPush
from wx_push import WXPush
from ali_push import AliPush

from models import application
from models import user



MSG_CUSTOMER = 24 #顾客->客服
MSG_CUSTOMER_SUPPORT = 25 #客服->顾客


rds = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT, 
                        db=config.REDIS_DB, password=config.REDIS_PASSWORD)
mysql_db = mysql.Mysql.instance(*config.MYSQL)

IOSPush.mysql = mysql_db
SmartPush.mysql = mysql_db
XGPush.mysql = mysql_db
HuaWeiPush.mysql = mysql_db
GCMPush.mysql = mysql_db
MiPush.mysql = mysql_db
AliPush.mysql = mysql_db
WXPush.mysql = mysql_db
WXPush.rds = rds

app_names = {}

class Store(object):
    def __init__(self):
        self.store_id = 0
        self.name = ""

    @classmethod
    def get_store(cls, rds, store_id):
        s = Store()
        key = "stores_%s"%store_id
        s.name = rds.hget(key, "name")
        s.store_id = store_id
        return s

def get_title(appid):
    if not app_names.has_key(appid):
        name = application.get_app_name(mysql_db, appid)
        if name is not None:
            app_names[appid] = name

    if app_names.has_key(appid):
        return app_names[appid]
    else:
        return ""

def push_content(sender_name, body):
    if not sender_name:
        try:
            content = json.loads(body)
            if content.has_key("text"):
                alert = content["text"]
            elif content.has_key("audio"):
                alert = u"你收到了一条消息"
            elif content.has_key("image"):
                alert = u"你收到了一张图片"
            else:
                alert = u"你收到了一条消息"

        except ValueError:
            alert = u"你收到了一条消息"

    else:
        try:
            sender_name = sender_name.decode("utf8")
            content = json.loads(body)
            if content.has_key("text"):
                alert = "%s:%s"%(sender_name, content["text"])
            elif content.has_key("audio"):
                alert = "%s%s"%(sender_name, u"发来一条语音消息")
            elif content.has_key("image"):
                alert = "%s%s"%(sender_name, u"发来一张图片")
            else:
                alert = "%s%s"%(sender_name, u"发来一条消息")

        except ValueError:
            alert = "%s%s"%(sender_name, u"发来一条消息")
    return alert

def ios_push(appid, token, content, badge, sound, extra):
    alert = content
    content_available = 0
    IOSPush.push(appid, token, alert, sound, badge, content_available, extra)

def ios_voip_push(appid, token, extra):
    IOSPush.voip_push(appid, token, extra)
    
def android_push(appid, appname, token, content, extra):
    token = binascii.a2b_hex(token)
    SmartPush.push(appid, appname, token, content, extra)

def xg_push(appid, appname, token, content, extra):
    XGPush.push(appid, appname, token, content, extra)

#发送系统消息的rpc接口
def post_system_message(appid, uid, content):
    params = {
        "appid":appid,
        "uid":uid
    }
    im_url=config.IM_RPC_URL
    url = im_url + "/post_system_message?" + urlencode(params)
    headers = {"Content-Type":"text/plain; charset=UTF-8"}
    resp = requests.post(url, data=content.encode("utf8"), headers=headers)
    logging.debug("post system message:%s", resp.status_code == 200)

    
def push_customer_support_message(appid, appname, u, content, extra):
    receiver = u.uid
    #找出最近绑定的token
    ts = max(u.apns_timestamp, u.xg_timestamp, u.ng_timestamp, 
             u.mi_timestamp, u.hw_timestamp, u.gcm_timestamp,
             u.ali_timestamp)

    if u.apns_device_token and u.apns_timestamp == ts:
        sound = 'default'
        alert = content
        badge = u.unread + 1
        content_available = 1
        IOSPush.push(appid, u.apns_device_token, alert, 
                     sound, badge, content_available, extra)
        user.set_user_unread(rds, appid, receiver, u.unread+1)
    elif u.ng_device_token and u.ng_timestamp == ts:
        android_push(appid, appname, u.ng_device_token, content, extra)
    elif u.xg_device_token and u.xg_timestamp == ts:
        xg_push(appid, appname, u.xg_device_token, content, extra)
    elif u.mi_device_token and u.mi_timestamp == ts:
        MiPush.push(appid, appname, u.mi_device_token, content)
    elif u.hw_device_token and u.hw_timestamp == ts:
        HuaWeiPush.push(appid, appname, u.hw_device_token, content)
    elif u.gcm_device_token and u.gcm_timestamp == ts:
        GCMPush.push(appid, appname, u.gcm_device_token, content)
    elif u.ali_device_token and u.ali_timestamp == ts:
        AliPush.push(appid, appname, u.ali_device_token, content)
        #通过透传消息通知app有新消息到达
        content = json.dumps({"xiaowei":{"new":1}})
        AliPush.push_message(appid, appname, u.ali_device_token, content)
    else:
        logging.info("uid:%d has't device token", receiver)


def push_message_u(appid, appname, u, content, extra):
    receiver = u.uid
    #找出最近绑定的token
    ts = max(u.apns_timestamp, u.xg_timestamp, u.ng_timestamp, u.mi_timestamp, u.hw_timestamp, u.gcm_timestamp,
             u.ali_timestamp)

    if u.apns_device_token and u.apns_timestamp == ts:
        sound = 'default'
        ios_push(appid, u.apns_device_token, content,
                 u.unread + 1, sound, extra)
        user.set_user_unread(rds, appid, receiver, u.unread+1)
    elif u.ng_device_token and u.ng_timestamp == ts:
        android_push(appid, appname, u.ng_device_token, content, extra)
    elif u.xg_device_token and u.xg_timestamp == ts:
        xg_push(appid, appname, u.xg_device_token, content, extra)
    elif u.mi_device_token and u.mi_timestamp == ts:
        MiPush.push(appid, appname, u.mi_device_token, content)
    elif u.hw_device_token and u.hw_timestamp == ts:
        HuaWeiPush.push(appid, appname, u.hw_device_token, content)
    elif u.gcm_device_token and u.gcm_timestamp == ts:
        GCMPush.push(appid, appname, u.gcm_device_token, content)
    elif u.ali_device_token and u.ali_timestamp == ts:
        AliPush.push(appid, appname, u.ali_device_token, content)
    else:
        logging.info("uid:%d has't device token", receiver)

def push_message(appid, appname, receiver, content, extra):
    u = user.get_user(rds, appid, receiver)
    if u is None:
        logging.info("uid:%d nonexist", receiver)
        return

    push_message_u(appid, appname, u, content, extra)

def handle_im_message(msg):
    obj = json.loads(msg)
    if not obj.has_key("appid") or \
       not obj.has_key("sender") or \
       not obj.has_key("receiver"):
        logging.warning("invalid push msg:%s", msg)
        return

    logging.debug("push msg:%s", msg)
    appid = obj["appid"]
    sender = obj["sender"]
    receiver = obj["receiver"]

    appname = get_title(appid)
    sender_name = user.get_user_name(rds, appid, sender)
    content = push_content(sender_name, obj["content"])

    extra = {}
    extra["sender"] = sender

    do_not_disturb = user.get_user_do_not_disturb(rds, appid, receiver, sender)
    if not do_not_disturb:
        push_message(appid, appname, receiver, content, extra)
    else:
        logging.debug("uid:%s set do not disturb :%s", receiver, sender)


def handle_group_message(msg):
    obj = json.loads(msg)
    if not obj.has_key("appid") or not obj.has_key("sender") or \
       not obj.has_key("receivers") or not obj.has_key("group_id"):
        logging.warning("invalid push msg:%s", msg)
        return

    logging.debug("group push msg:%s", msg)

    appid = obj["appid"]
    sender = obj["sender"]
    receivers = obj["receivers"]
    group_id = obj["group_id"]

    appname = get_title(appid)
    sender_name = user.get_user_name(rds, appid, sender)

    content = push_content(sender_name, obj["content"])

    extra = {}
    extra["sender"] = sender

    if group_id:
        extra["group_id"] = group_id

    for receiver in receivers:
        if group_id:
            quiet = user.get_user_notification_setting(rds, appid, receiver, group_id)
            if quiet:
                logging.info("uid:%d group id:%d is in quiet mode", receiver, group_id)
                continue

        push_message(appid, appname, receiver, content, extra)


def handle_customer_message(msg):
    obj = json.loads(msg)
    if not obj.has_key("appid") or not obj.has_key("command") or \
       not obj.has_key("customer_appid") or not obj.has_key("customer") or \
       not obj.has_key("seller") or not obj.has_key("content") or \
       not obj.has_key("store") or not obj.has_key("receiver"):
        logging.warning("invalid customer push msg:%s", msg)
        return

    logging.debug("customer push msg:%s", msg)

    appid = obj["appid"]
    receiver = obj["receiver"]
    command = obj["command"]
    customer_appid = obj["customer_appid"]
    customer = obj["customer"]
    store = obj["store"]
    seller = obj["seller"]
    raw_content = obj["content"]

    appname = get_title(appid)

    extra = {}
    if command == MSG_CUSTOMER:
        sender_name = user.get_user_name(rds, customer_appid, customer)
        content = push_content(sender_name, raw_content)
        push_message(appid, appname, receiver, content, extra)
    elif command == MSG_CUSTOMER_SUPPORT:
        if appid == customer_appid and receiver == customer:
            #客服发给顾客
            u = user.get_user(rds, appid, receiver)
            if u is None:
                logging.info("uid:%d nonexist", receiver)
                return

            if u.wx_openid:
                result = WXPush.push(appid, appname, u.wx_openid, raw_content)
                #errcode=45015,
                #errmsg=response out of time limit or subscription is canceled
                if result and result.get('errcode') == 45015:
                    now = int(time.time())
                    content_obj = {
                        "wechat": {
                            "customer_appid":customer_appid,
                            "customer_id":customer,
                            "timestamp":now,
                            "notification":"微信会话超时"
                        }
                    }
                    post_system_message(config.KEFU_APPID, seller,
                                        json.dumps(content_obj))
            else:
                extra['store_id'] = store
                extra['xiaowei'] = {"new":1}
                store = Store.get_store(rds, store)
                sender_name = store.name
                content = push_content(sender_name, raw_content)
                push_customer_support_message(appid, appname, u, content, extra)
        else:
            #群发到其它客服人员
            sender_name = user.get_user_name(rds, appid, seller)
            content = push_content(sender_name, raw_content)
            push_message(appid, appname, receiver, content, extra)


def handle_system_message(msg):
    obj = json.loads(msg)
    appid = obj["appid"]
    receiver = obj["receiver"]
    
    appname = get_title(appid)
    try:
        content_obj = json.loads(obj.get('content'))
        voip_content = content_obj.get('voip_push')
        content = content_obj.get('push')
        if not voip_content and not content:
            return
        sound = content_obj.get('sound', 'default')
    except Exception, e:
        logging.info("exception:%s", e)
        return
    
    u = user.get_user(rds, appid, receiver)
    if u is None:
        logging.info("uid:%d nonexist", receiver)
        return

    #找出最近绑定的token
    ts = max(u.apns_timestamp, u.xg_timestamp, u.ng_timestamp,
             u.mi_timestamp, u.hw_timestamp, u.gcm_timestamp,
             u.ali_timestamp)

    if u.apns_device_token and u.apns_timestamp == ts:
        if voip_content and u.pushkit_device_token:
            ios_voip_push(appid, u.pushkit_device_token, voip_content)
        elif content:
            ios_push(appid, u.apns_device_token, content,
                     u.unread + 1, sound, {})
            user.set_user_unread(rds, appid, receiver, u.unread+1)
        return
    
    if not content:
        return
    
    if u.mi_device_token and u.mi_timestamp == ts:
        MiPush.push_message(appid, u.mi_device_token, content)
    elif u.hw_device_token and u.hw_timestamp == ts:
        HuaWeiPush.push_message(appid, u.hw_device_token, content)
    elif u.ali_device_token and u.ali_timestamp == ts:
        AliPush.push_message(appid, appname, u.hw_device_token, content)
    else:
        logging.info("uid:%d has't device token", receiver)
        

def receive_offline_message():
    while True:
        logging.debug("waiting...")
        item = rds.blpop(("push_queue", "group_push_queue",
                          "customer_push_queue", 
                          "system_push_queue"))
        if not item:
            continue
        q, msg = item
        logging.debug("queue:%s message:%s", q, msg)
        if q == "push_queue":
            handle_im_message(msg)
        elif q == "group_push_queue":
            handle_group_message(msg)
        elif q == "customer_push_queue":
            handle_customer_message(msg)
        elif q == "system_push_queue":
            handle_system_message(msg)
        else:
            logging.warning("unknown queue:%s", q)


def main():
    logging.debug("startup")
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
