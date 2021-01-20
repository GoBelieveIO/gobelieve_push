# -*- coding: utf-8 -*-

import json
import logging
from models import application
import time

from utils.ali_push import Push


# 文档地址: https://help.aliyun.com/product/30047.html


class AliPush:
    mysql = None
    apps = {}

    @classmethod
    def get_app(cls, appid):
        now = int(time.time())
        app = cls.apps[appid] if cls.apps.has_key(appid) else None
        # app不在缓存中或者缓存超时,从数据库获取最新的app_secret
        if app is None or now - app["timestamp"] > 60:
            ali_access_id, ali_access_secret, ali_app_key = application.get_ali_key(cls.mysql, appid)
            if ali_access_id is None or ali_access_secret is None or ali_app_key is None:
                return None

            app = {}
            app["timestamp"] = now
            app["ali_access_key_id"] = ali_access_id
            app["ali_access_secret"] = ali_access_secret
            app["ali_app_key"] = ali_app_key
            app["appid"] = appid
            cls.apps[appid] = app
        return app

    @classmethod
    def send(cls, client, device_token, title, content):
        return client.send(
            target=Push.TARGET_DEVICE,
            accounts=device_token,
            title=title,
            body=content,
            push_type=Push.TYPE_NOTICE,
        )

    @classmethod
    def send_message(cls, client, device_token, title, content):
        return client.send(
            target=Push.TARGET_DEVICE,
            title=title,
            body=content,
            accounts=device_token,
            push_type=Push.TYPE_MESSAGE,
        )

    @classmethod
    def push(cls, appid, appname, token, content):
        app = cls.get_app(appid)
        if app is None:
            logging.warning("can't read ali app secret")
            return False

        client = Push(app['ali_access_key_id'], app['ali_access_secret'], app["ali_app_key"])

        cls.send(client, token, appname, content)

    @classmethod
    def push_message(cls, appid, appname, token, payload):
        app = cls.get_app(appid)
        if app is None:
            logging.warning("can't read ali app secret")
            return False

        client = Push(app['ali_access_key_id'], app['ali_access_secret'], app["ali_app_key"])
        cls.send_message(client, token, appname, payload)


if __name__ == "__main__":
    import os

    logging.getLogger().setLevel(logging.DEBUG)
    token = "4b899662464d4e3580d48a56893d146f"

    push = Push(os.getenv('ACCESS_KEY_ID'), os.getenv('ACCESS_SECRET'), os.getenv('APP_KEY'))

    r = AliPush.send(push, token, u"SDK测试", u"测试")
    print(r)
    r = AliPush.send_message(push, token, "测试透传标题", json.dumps({"xiaowei": {"new": 1}}))
    print(r)
