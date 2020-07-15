# -*- coding: utf-8 -*-
import requests
import json
import time
import logging
from urllib import parse
from models import application

#接口文档
#https://developer.huawei.com/consumer/cn/service/hms/catalog/huaweipush_agent.html?page=hmssdk_huaweipush_api_reference_agent_s2

LOGIN_URL = "https://login.cloud.huawei.com/oauth2/v2/token"
HUAWEI_URL = "https://api.push.hicloud.com/pushsend.do"

class HuaWeiPush:
    session = requests.session()
    mysql = None
    hw_apps = {}
    hw_token = {}
        
    @classmethod
    def get_app(cls, appid):
        now = int(time.time())
        app = cls.hw_apps.get(appid)
        #app不在缓存中或者缓存超时,从数据库获取最新的accessid和secretkey
        if app is None or now - app["timestamp"] > 60:
            hw_appid, hw_app_secret = application.get_hw_key(cls.mysql, appid)
            if hw_appid is None or hw_app_secret is None:
                return None
            package_name = application.get_package_name(cls.mysql, appid)
            if package_name is None:
                return None
            
            app = {}
            app["timestamp"] = now
            app["hw_appid"] = hw_appid
            app["hw_app_secret"] = hw_app_secret
            app["package_name"] = package_name
            app["appid"] = appid
            cls.hw_apps[appid] = app
        return app
    
    @classmethod
    def get_access_token(cls, hw_appid, hw_app_secret):
        hw_token = cls.hw_token
        if "access_token" in hw_token and "expire" in hw_token:
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
        resp = requests.post(LOGIN_URL, data=data, headers=headers)
        if resp.status_code != 200:
            logging.error("hw login error:%s", resp.content)
            return None

        now = int(time.time())
        obj = json.loads(resp.text)
        hw_token["expire"] = now + obj["expires_in"]
        hw_token["access_token"] = obj["access_token"]
        return hw_token["access_token"]

    @classmethod
    def send_payload(cls, access_token, device_token, hw_appid, payload):
        data = {
            "payload":json.dumps(payload),
            "access_token":access_token,
            "device_token_list":json.dumps([device_token]),
            "nsp_ts":str(int(time.time())),
            "nsp_fmt":"JSON",
            "nsp_svc":"openpush.message.api.send",
        }
        headers = {"Content-Type":"application/x-www-form-urlencoded"}
        nsp_ctx = """{"ver":"1", "appId":"%s"}"""%hw_appid
        url = "%s?nsp_ctx=%s"%(HUAWEI_URL, parse.quote_plus(nsp_ctx))
        
        resp = cls.session.post(url, data=data, headers=headers)
        if resp.status_code != 200:
            logging.error("send huawei message error:%s", resp.content)
        else:
            logging.error("send huawei message success:%s", resp.content)

        return resp.status_code == 200        
    
    @classmethod
    def send(cls, access_token, device_token, title, content, hw_appid, package_name):
        payload = {
            "hps":{
                "msg": {
                    "type":3,
                    "body": {
                        "title":title,
                        "content":content
                    },
                    "action":{
                        "type":3,
                        "param":{"appPkgName":package_name}
                    }
                }
            }
        }
        
        return cls.send_payload(access_token, device_token, hw_appid, payload)

    @classmethod
    def send_message(cls, access_token, device_token, msg_body, hw_appid):
        payload = {
            "hps":{
                "msg": {
                    "type":1,
                    "body": msg_body
                }
            }
        }
        
        return cls.send_payload(access_token, device_token, hw_appid, payload)


    @classmethod
    def push(cls, appid, appname, token, content):
        app = cls.get_app(appid)
        if app is None:
            logging.warning("")
            return

        access_token = cls.get_access_token(app["hw_appid"], app["hw_app_secret"])
        if access_token is None:
            return
        
        cls.send(access_token, token, appname, content, app["hw_appid"], app["package_name"])


    @classmethod
    def push_message(cls, appid, token, message):
        app = cls.get_app(appid)
        if app is None:
            logging.warning("")
            return

        access_token = cls.get_access_token(app["hw_appid"], app["hw_app_secret"])
        if access_token is None:
            return
        
        cls.send_message(access_token, token, message, app["hw_appid"])

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    APP_ID = 10417737
    APP_SECRET = "80ungj5bjx00g269oeqs9t2fnkyhe5wr"
    package_name = "io.gobelieve.im.demo"
    token = "AMbVYVLOLNa2ImG1kDS8LqFaEqXLqUz6o0L64_oXLCxbkuFoYEX3OXEagWDrMCtJUC5XHmin4m3PqObIAI4ZflbipE5kLUfKKbtbuaBpiCWjbsAySmAkaVcKhy2iLBZ8YA"
    access_token = HuaWeiPush.get_access_token(APP_ID, APP_SECRET)
    print("token:", access_token)
    HuaWeiPush.send(access_token, token, "test", "测试华为推送", APP_ID, package_name)
    HuaWeiPush.send_message(access_token, token, {"key":"测试华为透传消息"}, APP_ID)
