# -*- coding: utf-8 -*-
import time
import logging
import sys
import redis
from apnsclient import Message, APNs, Session
import json
import uuid
import subprocess
from OpenSSL import crypto
import os
import traceback
import threading
import application
import config
import time

sandbox = config.SANDBOX

class APNSConnectionManager:
    def __init__(self):
        self.apns_connections = {}
        #上次访问的时间戳,丢弃超过20m未用的链接
        self.connection_timestamps = {}
        self.lock = threading.Lock()

    def get_apns_connection(self, appid):
        self.lock.acquire()
        try:
            connections = self.apns_connections
            apns = connections[appid] if connections.has_key(appid) else None
            if apns:
                ts = self.connection_timestamps[appid]
                now = int(time.time())
                # > 10minute
                if (now - ts) > 20*60:
                    apns = None
                else:
                    self.connection_timestamps[appid] = now
        finally:
            self.lock.release()
        return apns

    def remove_apns_connection(self, appid):
        self.lock.acquire()
        try:
            connections = self.apns_connections
            if connections.has_key(appid):
                logging.debug("pop client:%s", appid)
                connections.pop(appid)
        finally:
            self.lock.release()

    def set_apns_connection(self, appid, connection):
        self.lock.acquire()
        try:
            self.apns_connections[appid] = connection
            self.connection_timestamps[appid] = int(time.time())
        finally:
            self.lock.release()


class IOSPush(object):
    mysql = None
    apns_manager = APNSConnectionManager()

    @staticmethod
    def gen_pem(p12, secret):
        p12 = crypto.load_pkcs12(p12, str(secret))
        priv_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())
        pub_key = crypto.dump_certificate(crypto.FILETYPE_PEM, p12.get_certificate())
        return  pub_key, priv_key

    @classmethod 
    def connect_apns_server(cls, sandbox, p12, secret, timestamp):
        pub_key, priv_key = cls.gen_pem(p12, secret)
        session = Session(read_tail_timeout=1)
        address = 'push_sandbox' if sandbox else 'push_production'
        conn = session.get_connection(address, cert_string=pub_key, key_string=priv_key)
        apns = APNs(conn)
        return apns

    @classmethod
    def get_connection(cls, appid):
        apns = cls.apns_manager.get_apns_connection(appid)
        if not apns:
            p12, secret, timestamp = application.get_p12(cls.mysql, sandbox, appid)
            if not p12:
                logging.warn("get p12 fail client id:%s", appid)
                return None
            
            apns = cls.connect_apns_server(sandbox, p12, secret, timestamp)
            cls.apns_manager.set_apns_connection(appid, apns)
        return apns

    @classmethod
    def push(cls, appid, token, alert, sound="default", badge=0, extra=None):
        message = Message([token], alert=alert, badge=badge, sound=sound, extra=extra)

        for i in range(3):
            if i > 0:
                logging.warn("resend notification")

            apns = cls.get_connection(appid)
             
            try:
                logging.debug("send apns:%s %s %s", message.tokens, alert, badge)
                result = apns.send(message)
             
                for token, (reason, explanation) in result.failed.items():
                    # stop using that token
                    logging.error("failed token:%s", token)
             
                for reason, explanation in result.errors:
                    # handle generic errors
                    logging.error("send notification fail: reason = %s, explanation = %s", reason, explanation)
             
                if result.needs_retry():
                    # extract failed tokens as new message
                    message = result.retry()
                    # re-schedule task with the new message after some delay
                    continue
                else:
                    break
            
            except Exception, e:
                logging.warn("send notification exception:%s", str(e))
                cls.apns_manager.remove_apns_connection(appid)


    @classmethod
    def receive_p12_update_message(cls):
        chan_rds = redis.StrictRedis(host=config.CHAN_REDIS_HOST, 
                                     port=config.CHAN_REDIS_PORT, 
                                     db=config.CHAN_REDIS_DB,
                                     password=config.CHAN_REDIS_PASSWORD)
        sub = chan_rds.pubsub()
        sub.subscribe("apns_update_p12_channel")
        for msg in sub.listen():
            if msg['type'] == 'message':
                data = msg['data']
                try:
                    appid = int(data)
                except:
                    logging.warn("invalid app id:%s", data)
                    continue
                logging.info("update app:%s p12", appid)
                cls.apns_manager.remove_apns_connection(appid)

    @classmethod
    def update_p12_thread(cls):
        while True:
            try:
                cls.receive_p12_update_message()
            except Exception, e:
                logging.exception(e)

    @classmethod
    def start(cls):
        t = threading.Thread(target=cls.update_p12_thread, args=())
        t.setDaemon(True)
        t.start()


if __name__ == "__main__":
    f = open("imdemo_dev.p12", "rb")
    p12 = f.read()
    f.close()

    token = "177bbe6da89125b84bfad60ff3d729005792fad4ebbbf5729a8cecc79365a218"
    alert = "测试ios推送"
    badge = 0
    sound = "default"
    #alert = None
    #badge = None
    #sound = None

    extra = {"test":1, "test2":2}
    apns = IOSPush.connect_apns_server(True, p12, "", 0)
    message = Message([token], alert=alert, badge=badge, 
                      sound=sound, extra=extra)
    result = apns.send(message)
    print result
    

