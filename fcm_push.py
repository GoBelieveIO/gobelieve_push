# -*- coding: utf-8 -*-
import logging
import time
from pyfcm import FCMNotification
from models import application
import config


class FCMPush:
    mysql = None
    fcm_apps = {}
    @classmethod
    def get_gcm_app(cls, appid):
        now = int(time.time())
        app = cls.fcm_apps.get(appid)
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
            app["fcm"] = FCMNotification(api_key=api_key)            
            cls.fcm_apps[appid] = app

        return app


    
    @classmethod
    def send(cls, fcm, device_token, title, content, channel_id=None):
        logging.info("fcm send:%s %s %s %s", device_token, title, content, channel_id)
        res = fcm.notify_single_device(registration_id=device_token, message_title=title,
                                       message_body=content, android_channel_id=channel_id)
        if res["failure"] > 0:
            logging.error("send fcm message error:%s", res)
        else:
            logging.debug("send fcm message success:%s", res)

   
    @classmethod
    def send_batch(cls, fcm, device_tokens, title, content, channel_id=None):
        logging.info("fcm send batch:%s %s %s %s", device_tokens, title, content, channel_id)        
        res = fcm.notify_multiple_devices(registration_ids=device_tokens, message_title=title, message_body=content, android_channel_id=channel_id)
        if res["failure"] > 0:
            logging.error("send fcm message error:%s", res)
        else:
            logging.debug("send fcm message success:%s", res)

            
    @classmethod
    def push(cls, appid, appname, token, content, channel_id=None):
        app = cls.get_gcm_app(appid)
        if app is None:
            logging.warning("can't read gcm api key")
            return False

        cls.send(app["fcm"], token, appname, content, channel_id)

        
    @classmethod
    def push_batch(cls, appid, appname, tokens, content, channel_id=None):
        app = cls.get_gcm_app(appid)
        if app is None:
            logging.warning("can't read gcm api key")
            return False

        cls.send_batch(app["fcm"], tokens, appname, content, channel_id)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    token = "fXux1H5cRLc:APA91bG7w4Mutqt1TSN42JipxME8rwpgA-kDX_7W9tJqx5tpcSJEGVn-QXnslcxK915XI5RCzzMktp_-K1At2xSi6CVhmB7MKedT-2JEbwyv3cEJuUIZIGK5ANHgntmByCaebM45r-wO"
    API_KEY = "AAAAHFTLBsc:APA91bH4nR0revyNzlMUIhrMjlAUKvZvUypeY1uUaJnGWuW-CSYCLyBs88fPTfr9qPyvx34X1UbT4BfDtrQt9PgWKkSEZkUS30XG_gRF3yPMWVre2aDm9ENf43MWB2wboyjO1bjmgKsM"
    FCMPush.send(API_KEY, token, "IMDemo", "test11ddfsf1")
