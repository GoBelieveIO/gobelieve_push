# -*- coding: utf-8 -*-
import requests
import json
import time
import logging
from models import application

#接口文档:http://developer.huawei.com/cn/consumer/wiki/index.php?title=%E6%8E%A5%E5%8F%A3%E6%96%87%E6%A1%A3
#http://developer.huawei.com/cn/consumer/wiki/index.php?title=%E5%BC%80%E6%94%BE%E5%B9%B3%E5%8F%B0%E9%89%B4%E6%9D%83
LOGIN_URL="https://login.vmall.com/oauth2/token";
HUAWEI_URL = "https://api.vmall.com/rest.php";

class HuaWeiPush:
    session = requests.session()
    mysql = None
    hw_apps = {}
    hw_token = {}
        
    @classmethod
    def get_app(cls, appid):
        now = int(time.time())
        app = cls.hw_apps[appid] if cls.hw_apps.has_key(appid) else None
        #app不在缓存中或者缓存超时,从数据库获取最新的accessid和secretkey
        if app is None or now - app["timestamp"] > 60:
            hw_appid, hw_app_secret = application.get_hw_key(cls.mysql, appid)
            if hw_appid is None or hw_app_secret is None:
                return None
            app = {}
            app["timestamp"] = now
            app["hw_appid"] = hw_appid
            app["hw_app_secret"] = hw_app_secret
            app["appid"] = appid
            cls.hw_apps[appid] = app
        return app
    
    @classmethod
    def get_access_token(cls, hw_appid, hw_app_secret):
        hw_token = cls.hw_token
        if hw_token.has_key("access_token") and hw_token.has_key("expire"):
            now = int(time.time())
            #未过期,预留10秒
            if hw_token["expire"] > now + 10:
                return hw_token["access_token"]
        headers = {"Content-Type":"application/x-www-form-urlencoded"}
        data = {
            "grant_type":"client_credentials",
            "client_id":hw_appid,
            "client_secret":hw_app_secret
        }
        resp = requests.post(LOGIN_URL, data=data, headers=headers, verify=False)
        if resp.status_code != 200:
            logging.error("hw login error:%s", resp.content)
            return None

        now = int(time.time())
        obj = json.loads(resp.text)
        hw_token["expire"] = now + obj["expires_in"]
        hw_token["access_token"] = obj["access_token"]
        return hw_token["access_token"]

    @classmethod
    def send(cls, access_token, device_token, title, content):
        android = {
            "notification_title":title,
            "notification_content":content,
            "doings":1
        }
        
        data = {
            "push_type":1,
            "access_token":access_token,
            "tokens":device_token,
            "android":json.dumps(android),
            "nsp_ts":str(int(time.time())),
            "nsp_fmt":"JSON",
            "nsp_svc":"openpush.openapi.notification_send"
        }
        headers = {"Content-Type":"application/x-www-form-urlencoded"}
        resp = cls.session.post(HUAWEI_URL, data=data, headers=headers, verify=False)
        if resp.status_code != 200:
            logging.error("send huawei message error:%s", resp.content)
        else:
            logging.error("send huawei message success:%s", resp.content)

        return resp.status_code == 200

    @classmethod
    def send_message(cls, access_token, device_token, msg_type, cache_mode, message):
        #cache mode 0：不缓存 1：缓存
        #msg_type 标识消息类型（缓存机制），由调用端赋值，取值范围（1~100）。当TMID+msgType的值一样时，仅缓存最新的一条消息
        data = {
            "access_token":access_token,
            "deviceToken":device_token,
            'message':message,
            'msgType':msg_type,
            'cacheMode':cache_mode,
            'priority':1,
            "nsp_ts":str(int(time.time())),
            "nsp_fmt":"JSON",
            "nsp_svc":"openpush.message.single_send"
        }
        headers = {"Content-Type":"application/x-www-form-urlencoded"}
        resp = cls.session.post(HUAWEI_URL, data=data, headers=headers, verify=False)
        if resp.status_code != 200:
            logging.error("send huawei message error:%s", resp.content)
        else:
            logging.error("send huawei message success:%s", resp.content)

        return resp.status_code == 200

    @classmethod
    def push(cls, appid, appname, token, content):
        app = cls.get_app(appid)
        if app is None:
            logging.warning("")
            return

        access_token = cls.get_access_token(app["hw_appid"], app["hw_app_secret"])
        if access_token is None:
            return
        
        cls.send(access_token, token, appname, content)


    @classmethod
    def push_message(cls, appid, token, message):
        app = cls.get_app(appid)
        if app is None:
            logging.warning("")
            return

        access_token = cls.get_access_token(app["hw_appid"], app["hw_app_secret"])
        if access_token is None:
            return
        
        cls.send_message(access_token, token, 1, 0, message)

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    APP_ID = 10417737
    APP_SECRET = "80ungj5bjx00g269oeqs9t2fnkyhe5wr"
    token = "08645870275867432000000638000001"
    access_token = HuaWeiPush.get_access_token(APP_ID, APP_SECRET)
    print "token:", access_token
    HuaWeiPush.send(access_token, token, "test", "测试华为推送")
    HuaWeiPush.send_message(access_token, token, 1, 0, "测试华为消息推送")
