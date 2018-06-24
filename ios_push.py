# -*- coding: utf-8 -*-
import logging
import redis
from OpenSSL import crypto
import os
import threading
from models import application
import config
import time
import tempfile
import OpenSSL
from apns2.client import APNsClient
from apns2.payload import Payload

sandbox = config.SANDBOX

class APNSConnectionManager:
    def __init__(self):
        self.pushkit_connections = {}
        self.pushkit_timestamps = {}
        self.apns_connections = {}
        #上次访问的时间戳,丢弃超过20m未用的链接
        self.connection_timestamps = {}
        self.lock = threading.Lock()

    def get_pushkit_connection(self, appid):
        self.lock.acquire()
        try:
            connections = self.pushkit_connections
            apns = connections[appid] if connections.has_key(appid) else None
            if apns:
                ts = self.pushkit_timestamps[appid]
                now = int(time.time())
                # > 10minute
                if (now - ts) > 20*60:
                    apns = None
                else:
                    self.pushkit_timestamps[appid] = now
        finally:
            self.lock.release()
        return apns

    def remove_pushkit_connection(self, appid):
        self.lock.acquire()
        try:
            connections = self.pushkit_connections
            if connections.has_key(appid):
                logging.debug("pop pushkit connection:%s", appid)
                connections.pop(appid)
        finally:
            self.lock.release()

    def set_pushkit_connection(self, appid, connection):
        self.lock.acquire()
        try:
            self.pushkit_connections[appid] = connection
            self.pushkit_timestamps[appid] = int(time.time())
        finally:
            self.lock.release()

    def get_apns_connection(self, appid):
        self.lock.acquire()
        try:
            connections = self.apns_connections
            apns = connections[appid] if connections.has_key(appid) else None
            if apns:
                ts = self.connection_timestamps[appid]
                now = int(time.time())
                # > 20minute
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
    bundle_ids = {}

    @staticmethod
    def gen_pem(p12, secret):
        p12 = crypto.load_pkcs12(p12, str(secret))
        priv_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())
        pub_key = crypto.dump_certificate(crypto.FILETYPE_PEM, p12.get_certificate())
        return pub_key, priv_key

    @staticmethod
    def check_p12_expired(p12, secret):
        p12 = crypto.load_pkcs12(p12, str(secret))
        return p12.get_certificate().has_expired()

    @classmethod 
    def connect_apns_server(cls, sandbox, p12, secret):
        pub_key, priv_key = cls.gen_pem(p12, secret)
        f, path = tempfile.mkstemp()
        try:
            os.write(f, pub_key)
            os.write(f, priv_key)
            client = APNsClient(path, use_sandbox=sandbox, use_alternative_port=False)
            return client
        finally:
            os.close(f)
            os.remove(path)
    
    @classmethod
    def get_connection(cls, appid):
        apns = cls.apns_manager.get_apns_connection(appid)
        if not apns:
            p12, secret, timestamp = application.get_p12(cls.mysql, sandbox, appid)
            if not p12:
                logging.warn("get p12 fail client id:%s", appid)
                return None
            if cls.check_p12_expired(p12, secret):
                logging.warn("p12 expiry client id:%s", appid)
                return None
            apns = cls.connect_apns_server(sandbox, p12, secret)
            cls.apns_manager.set_apns_connection(appid, apns)
        return apns


    @classmethod
    def get_pushkit_connection(cls, appid):
        return cls.get_connection(appid)

    @classmethod
    def get_bundle_id(cls, appid):
        if appid in cls.bundle_ids:
            return cls.bundle_ids[appid]
        bundle_id = application.get_bundle_id(cls.mysql, appid)
        if bundle_id:
            cls.bundle_ids[appid] = bundle_id
        return bundle_id

    @classmethod
    def voip_push(cls, appid, token, extra=None):
        topic = cls.get_bundle_id(appid)
        if not topic:
            logging.warn("appid:%s no bundle id", appid)
            return

        voip_topic = topic + ".voip"
        payload = Payload(custom=extra)
        client = cls.get_pushkit_connection(appid)
        try:
            client.send_notification(token, payload, voip_topic)
            logging.debug("send voip notification:%s %s %s success", token)
        except OpenSSL.SSL.Error, e:
            logging.warn("ssl exception:%s", str(e))
            cls.apns_manager.remove_apns_connection(appid)
        except Exception, e:
            logging.warn("send notification exception:%s", str(e))
            cls.apns_manager.remove_apns_connection(appid)

    @classmethod
    def push(cls, appid, token, alert, sound="default", badge=0, content_available=0, extra=None):
        topic = cls.get_bundle_id(appid)
        if not topic:
            logging.warn("appid:%s no bundle id", appid)
            return

        payload = Payload(alert=alert, sound=sound, badge=badge, content_available=content_available, custom=extra)
        client = cls.get_connection(appid)
        try:
            client.send_notification(token, payload, topic)
            logging.debug("send apns:%s %s %s success", token, alert, badge)
        except OpenSSL.SSL.Error, e:
            logging.warn("ssl exception:%s", str(e))
            cls.apns_manager.remove_apns_connection(appid)
        except Exception, e:
            logging.warn("send notification exception:%s %s", str(e), type(e))
            cls.apns_manager.remove_apns_connection(appid)

    @classmethod
    def push_batch(cls, appid, notifications):
        topic = cls.get_bundle_id(appid)
        if not topic:
            logging.warn("appid:%s no bundle id", appid)
            return
        client = cls.get_connection(appid)
        try:
            results = client.send_notification_batch(notifications, topic)
            logging.debug("push batch results:%s", results)
        except OpenSSL.SSL.Error, e:
            logging.warn("ssl exception:%s", str(e))
            cls.apns_manager.remove_apns_connection(appid)
        except Exception, e:
            logging.warn("send notification exception:%s %s", str(e), type(e))
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
                cls.apns_manager.remove_pushkit_connection(appid)

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



def test_alert(sandbox):
    f = open("imdemo.p12", "rb")
    p12 = f.read()
    f.close()
    token = "7b2a23d466cf2557fb4fa573e1cc5f63088cd060def124a9eca97ab251be08b5"
    alert = u"测试ios推送"
    badge = 1
    sound = "default"
    topic = "com.beetle.im.demo"
    print "p12", len(p12)

    extra = {"test":"hahah"}
    client = IOSPush.connect_apns_server(sandbox, p12, "")
    payload = Payload(alert=alert, sound=sound, badge=badge, custom=extra)

    try:
        client.send_notification(token, payload, topic)
        time.sleep(1)
    except OpenSSL.SSL.Error, e:
        err = e.message[0][2]
        print "certificate expired" in err
        print "ssl exception:", e, type(e), dir(e), e.args, e.message
        raise e
    except Exception, e:
        print "exception:", e, type(e), dir(e), e.args, e.message
        raise e


def test_content(sandbox):
    f = open("imdemo.p12", "rb")
    p12 = f.read()
    f.close()
    print "p12", len(p12)

    token = "7b2a23d466cf2557fb4fa573e1cc5f63088cd060def124a9eca97ab251be08b5"
    extra = {"xiaowei":{"new":1}}
    topic = "com.beetle.im.demo"

    client = IOSPush.connect_apns_server(sandbox, p12, "")
    payload = Payload(content_available=1, custom=extra)
    try:
        client.send_notification(token, payload, topic)
        time.sleep(1)
    except OpenSSL.SSL.Error, e:
        err = e.message[0][2]
        print "certificate expired" in err
        print "ssl exception:", e, type(e), dir(e), e.args, e.message
        raise e
    except Exception, e:
        print "exception:", e, type(e), dir(e), e.args, e.message
        raise e


def test_pushkit(sandbox):
    f = open("imdemo.p12", "rb")
    p12 = f.read()
    f.close()
    print "p12", len(p12)
    token = "d8ac6543fb492ae56c12c47ba254ee094ce58e1001f28543af9c337d6e674f8c"
    topic = "com.beetle.im.demo.voip"
    extra = {"voip":{"channel_id":"1", "command":"dial"}}
    payload = Payload(custom=extra)

    client = IOSPush.connect_apns_server(sandbox, p12, "")

    try:
        client.send_notification(token, payload, topic)

        time.sleep(1)
    except OpenSSL.SSL.Error, e:
        err = e.message[0][2]
        print "certificate expired" in err
        print "ssl exception:", e, type(e), dir(e), e.args, e.message
        raise e
    except Exception, e:
        print "exception:", e, type(e), dir(e), e.args, e.message
        raise e    

    
if __name__ == "__main__":
    sandbox = True
    test_pushkit(sandbox)
    test_content(sandbox)
    test_alert(sandbox)
