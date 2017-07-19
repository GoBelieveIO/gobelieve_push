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
from models import application
import config
import time
import OpenSSL

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
    def push(cls, appid, token, alert, sound="default", badge=0, content_available=0, extra=None):
        message = Message([token], alert=alert, badge=badge, sound=sound, 
                          content_available=content_available, extra=extra)

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
            except OpenSSL.SSL.Error, e:
                logging.warn("ssl exception:", str(e))
                cls.apns_manager.remove_apns_connection(appid)
                err = e.message[0][2]
                if "certificate expired" in err:
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
    token = "86ac9703925375de83f0023b82f245371a9b58437bd9df441018558c99657b75"
    alert = "测试ios推送"
    badge = 1
    sound = "default"
    #alert = None
    #badge = None
    #sound = None
    print len(p12)

    extra = {"xiaowei":{"new":1}}
    apns = IOSPush.connect_apns_server(True, p12, "", 0)
    #message = Message([token], alert=alert, badge=badge, 
    #sound=sound, extra=extra)

    message = Message([token], content_available=1, extra=extra)
    try:
        result = apns.send(message)
        print result
        time.sleep(1)
    except OpenSSL.SSL.Error, e:
        err = e.message[0][2]
        print "certificate expired" in err
        print "ssl exception:", e, type(e), dir(e), e.args, e.message
    except Exception, e:
        print "exception:", e, type(e), dir(e), e.args, e.message

