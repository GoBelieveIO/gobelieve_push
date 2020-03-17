# -*- coding: utf-8 -*-
import requests
import requesocks
import json
import logging
import time
from fcm import FCMNotification
from models import application
import config

proxy_dict = {
    "http":config.SOCKS5_PROXY,
    "https":config.SOCKS5_PROXY
}

class FCMPush:
    fcm = FCMNotification(proxy_dict=proxy_dict)    
    mysql = None
    fcm_apps = {}
    @classmethod
    def get_fcm_app(cls, appid):
        now = int(time.time())
        app = cls.fcm_apps[appid] if cls.fcm_apps.has_key(appid) else None
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
            cls.fcm_apps[appid] = app

        return app
    
    @classmethod
    def send(cls, api_key, device_token, title, content):
        res = cls.fcm.notify_single_device(api_key=api_key, registration_id=device_token, message_title=title, message_body=content)
        if res["failure"] > 0:
            logging.error("send fcm message error:%s", res)
        else:
            logging.debug("send fcm message success:%s", res)

   
    @classmethod
    def send_batch(cls, api_key, device_tokens, title, content):
        res = cls.fcm.notify_multiple_device(api_key=api_key, registration_ids=device_tokens, message_title=title, message_body=content)
        if res["failure"] > 0:
            logging.error("send fcm message error:%s", res)
        else:
            logging.debug("send fcm message success:%s", res)

            
    @classmethod
    def push(cls, appid, appname, token, content):
        app = cls.get_gcm_app(appid)
        if app is None:
            logging.warning("can't read gcm api key")
            return False

        cls.send(app["api_key"], token, appname, content)

        
    @classmethod
    def push_batch(cls, appid, appname, tokens, content):
        app = cls.get_gcm_app(appid)
        if app is None:
            logging.warning("can't read gcm api key")
            return False

        cls.send_batch(app["api_key"], tokens, appname, content)

        

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    token = "ebo_XvqtoRY:APA91bFFeWTiHA2_nJAQTYaYRRk9Cwxoeod2taiIH8lKp5gNyPMnwvaQ6JU7ShwZAj5aI-7iTZjoFX98z-GlnDjlZ4MtDybIaRVQIw3vgUk0hnNmY9ZoALmLyPFRI6ZbrJ9tSfvmJlaT"
    API_KEY = "AIzaSyDj7XHkwFoox6Ip04DcOnW_RG4IIQcPjvg"
    FCMPush.send(API_KEY, token, "test", "测试FCM推送")
