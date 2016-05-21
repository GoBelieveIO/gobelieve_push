# -*- coding: utf-8 -*-

import requests
import time
import json
import hashlib
import logging
import application

XINGE_API = "http://openapi.xg.qq.com"
HTTP_METHOD = "POST"
XINGE_HOST = "openapi.xg.qq.com"


def GenSign(path, params, secretKey):
    ks = sorted(params.keys())
    paramStr = ''.join([('%s=%s' % (k, params[k])) for k in ks])
    signSource = u'%s%s%s%s%s' % (HTTP_METHOD, XINGE_HOST, path, paramStr, secretKey)
    return hashlib.md5(signSource).hexdigest()

class XGPush:
    session = requests.session()
    mysql = None
    xg_apps = {}
    app_names = {}

    @classmethod
    def get_xg_app(cls, appid):
        now = int(time.time())
        app = cls.xg_apps[appid] if cls.xg_apps.has_key(appid) else None
        #app不在缓存中或者缓存超时,从数据库获取最新的accessid和secretkey
        if app is None or now - app["timestamp"] > 60:
            access_id, secret_key = application.get_xg_secret(cls.mysql, appid)
            if access_id is None or secret_key is None:
                return None
            app = {}
            app["timestamp"] = now
            app["access_id"] = access_id
            app["secret_key"] = secret_key
            app["appid"] = appid
            cls.xg_apps[appid] = app
        return app

 
    @classmethod
    def send(cls, access_id, secret_key, device_token, title, content, extra):
        path = "/v2/push/single_device"
        url = XINGE_API + path

        obj =  {}
        obj["title"] = title
        obj["content"] = content
        obj["vibrate"] = 1
        if extra:
            obj["custom_content"] = extra


        msg = json.dumps(obj, separators=(',',':'))

        params = {
            "access_id":access_id,
            "timestamp":int(time.time()), 
            "expire_time":3600*24,
            "device_token":device_token,
            "message_type":1,
            "message":msg
        }
         
        params["sign"] = GenSign(path, params, secret_key)
        headers = {"content-type":"application/x-www-form-urlencoded"}
         
        r = cls.session.post(url, headers=headers, data=params)
        return r.status_code == 200
        
    @classmethod
    def push(cls, appid, appname, token, content, extra):
        app = XGPush.get_xg_app(appid)
        if app is None:
            logging.warning("can't read xinge access id")
            return False

        return cls.send(app["access_id"], app["secret_key"], token, 
                        appname, content, extra)


if __name__ == "__main__":
    access_id = "2100103204"
    secret_key = "53c1be217035aa75c1ccb5770b5df9f9"
    token = "adb238518d682b2e49cba26c207f04a712c6da46"
    XGPush.send(access_id, secret_key, token, "test", "测试信鸽推送", None)

