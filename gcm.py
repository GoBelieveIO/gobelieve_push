# -*- coding: utf-8 -*-
import requests
try:
    import requesocks
except ImportError:
    pass

import json
import logging
import time
from models import application
import config
#文档地址:https://developers.google.com/cloud-messaging/downstream
GCM_URL = "https://gcm-http.googleapis.com/gcm/send"

class GCMPush:
    session = requesocks.session() 
    session.proxies = {
        'http': config.SOCKS5_PROXY,
        'https': config.SOCKS5_PROXY,
    }
    mysql = None
    gcm_apps = {}
        
    @classmethod
    def get_gcm_app(cls, appid):
        now = int(time.time())
        app = cls.gcm_apps[appid] if cls.gcm_apps.has_key(appid) else None
        #app不在缓存中或者缓存超时,从数据库获取最新的accessid和secretkey
        if app is None or now - app["timestamp"] > 60:
            sender_id, api_key = application.get_gcm_key(cls.mysql, appid)
            if sender_id is None or api_key is None:
                return None
            app = {}
            app["timestamp"] = now
            app["sender_id"] = sender_id
            app["api_key"] = api_key
            app["appid"] = appid
            cls.gcm_apps[appid] = app

        return app
    
    @classmethod
    def send(cls, api_key, device_token, title, content):
        obj = {
            "to" : device_token,
            "notification" : {
                "body" : content,
                "title" : title
            }
        }

        headers = {'Content-Type': 'application/json; charset=UTF-8',
                   'Authorization': 'key=' + api_key}



        res = cls.session.post(GCM_URL, data=json.dumps(obj), headers=headers)
        if res.status_code != 200:
            logging.error("send gcm message error")
        else:
            logging.debug("send gcm message success")
        
    @classmethod
    def push(cls, appid, title, token, content):
        app = cls.get_gcm_app(appid)
        if app is None:
            logging.warning("can't read gcm api key")
            return False

        cls.send(app["api_key"], token, title, content)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    token = "fNMMmCwoba0:APA91bGqpKqwMvbxNlAcGj6wILQoCAY59wx3huFculEkUyElnidJvuEgwVVFuD3PKBUoLIop8ivJlXlkJNPYfFAnabHPAn8_o4oeX1b8eIaOQLmVOkXY-sUw-QAY4MF9PG4RL3TDq7e6"
    API_KEY = "AIzaSyDj7XHkwFoox6Ip04DcOnW_RG4IIQcPjvg"
    GCMPush.send(API_KEY, token, "test", "测试GCM推送")
