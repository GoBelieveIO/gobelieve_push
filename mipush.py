# -*- coding: utf-8 -*-
import requests
import json
import logging
from models import application
import time

#文档地址:http://dev.xiaomi.com/doc/?p=533#d5e824
MI_URL = "https://api.xmpush.xiaomi.com/v2/message/regid"

class MiPush:
    session = requests.session()
    mysql = None
    mi_apps = {}
        
    @classmethod
    def get_app(cls, appid):
        now = int(time.time())
        app = cls.mi_apps[appid] if cls.mi_apps.has_key(appid) else None
        #app不在缓存中或者缓存超时,从数据库获取最新的app_secret
        if app is None or now - app["timestamp"] > 60:
            mi_appid, mi_app_secret = application.get_mi_key(cls.mysql, appid)
            if mi_appid is None or mi_app_secret is None:
                return None
            app = {}
            app["timestamp"] = now
            app["mi_appid"] = mi_appid
            app["mi_app_secret"] = mi_app_secret
            app["appid"] = appid
            cls.mi_apps[appid] = app
        return app

    @classmethod
    def send(cls, mi_app_secret, device_token, title, content):
        obj = {
            "registration_id":device_token,
            'title':title,
            'description':content,
            'pass_through':0,
            'notify_type':-1,
            'extra.notify_effect':1,
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded',
                   'Authorization': 'key=' + mi_app_secret}

        res = cls.session.post(MI_URL, data=obj, headers=headers)
        if res.status_code != 200:
            logging.error("send xiaomi message error")
        else:
            obj = json.loads(res.content)
            if obj.has_key("code") and obj["code"] == 0:
                logging.debug("send xiaomi message success")
            else:
                logging.error("send xiaomi message error:%s", res.content)                
        print res.content
        
    @classmethod
    def send_message(cls, mi_app_secret, device_token, payload):
        obj = {
            "registration_id":device_token,
            'payload':payload,
            'pass_through':1,
            'notify_type':-1,
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded',
                   'Authorization': 'key=' + mi_app_secret}

        res = cls.session.post(MI_URL, data=obj, headers=headers)
        if res.status_code != 200:
            logging.error("send xiaomi message error")
        else:
            obj = json.loads(res.content)
            if obj.has_key("code") and obj["code"] == 0:
                logging.debug("send xiaomi message success")
            else:
                logging.error("send xiaomi message error:%s", res.content)                
        print res.content

    @classmethod
    def push(cls, appid, appname, token, content):
        app = cls.get_app(appid)
        if app is None:
            logging.warning("can't read mi app secret")
            return False

        mi_app_secret = app["mi_app_secret"]
        logging.debug("mi app secret:%s", mi_app_secret)
        cls.send(mi_app_secret, token, appname, content)

    @classmethod
    def push_message(cls, appid, token, payload):
        app = cls.get_app(appid)
        if app is None:
            logging.warning("can't read mi app secret")
            return False

        mi_app_secret = app["mi_app_secret"]
        logging.debug("mi app secret:%s", mi_app_secret)
        cls.send_message(mi_app_secret, token, payload)
        
    
if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    APP_SECRET = "Ef5FbgNVYkYMZTcWKMcFMw=="
    token = "d//igwEhgBGCI2TG6lWqlK6K4Hj3Sl6/2Nc9jD9LA018krvxcm4oKGNqe1ofP/pGVM0VdJCikIdBg60xmLneOhvqeVRvR5s2JUhkG1qBTMY="

    MiPush.send(APP_SECRET, token, "test", "测试小米推送")
    MiPush.send_message(APP_SECRET, token, "测试小米透传消息")
