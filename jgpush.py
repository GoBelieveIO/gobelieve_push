# -*- coding: utf-8 -*-
import requests
import json
import logging
import time
import base64
import config

#文档地址:http://docs.jpush.io/server/rest_api_v3_push/
JG_URL = "https://api.jpush.cn/v3/push"

class JGPush:
    session = requests.session()
    mysql = None
    jg_apps = {}
    
    @classmethod
    def get_app(cls, appid):
        now = int(time.time())
        app = cls.jg_apps[appid] if cls.jg_apps.has_key(appid) else None
        #app不在缓存中或者缓存超时,从数据库获取最新的app_secret
        if app is None or now - app["timestamp"] > 60:
            jg_app_key, jg_app_secret = application.get_jg_key(cls.mysql, appid)
            if jg_app_key is None or jg_app_secret is None:
                return None
            app = {}
            app["timestamp"] = now
            app["jg_app_key"] = jg_app_key
            app["jg_app_secret"] = jg_app_secret
            app["appid"] = appid
            cls.jg_apps[appid] = app
        return app

    
    @classmethod
    def send(cls, app_key, app_secret, device_tokens, title, content):
        obj = {
            "platform":["android"],
            "notification": {
                "android": {
                    "alert": content,
                    "title": title,
                },
            },
            "audience" : {
                "registration_id" : device_tokens
            }
        }

        auth = base64.b64encode(app_key + ":" + app_secret)
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Basic ' + auth}

        data = json.dumps(obj)
        res = cls.session.post(JG_URL, data=data, headers=headers, timeout=60)
        if res.status_code != 200:
            logging.error("send jg message error:%s", res.status_code)
        else:
            logging.debug("send jg message success:%s", res.content)
                          
        print res.content
        

    @classmethod
    def push(cls, appid, appname, token, content):
        app = cls.get_app(appid)
        if app is None:
            logging.warning("can't read jg app secret")
            return False
            
        jg_app_key = app["jg_app_key"]
        jg_app_secret = app["jg_app_secret"]
        logging.debug("send jg push:%s", content)
        cls.send(jg_app_key, jg_app_secret, token, appname, content)

        
    @classmethod
    def push_batch(cls, appid, appname, tokens, content):
        app = cls.get_app(appid)
        if app is None:
            logging.warning("can't read jg app secret")
            return False
            
        jg_app_key = app["jg_app_key"]
        jg_app_secret = app["jg_app_secret"]
        logging.debug("jg app secret:%s", jg_app_secret)
        logging.debug("send jg push:%s", content)
        for i in range(0, len(tokens), 1000):
            t = tokens[i:i+1000]
            cls.send(jg_app_key, jg_app_secret, t, appname, content)
        
    
if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    APP_KEY = ""
    APP_SECRET = ""
    token = "1a0018970af5778354a"

    JGPush.send(APP_KEY, APP_SECRET, [token], "test", "测试极光推送")

